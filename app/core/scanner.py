"""Orquestrador principal da analise."""
import queue
import signal
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from app.config import DEV_MODE, DEV_PLAN, PLAN_TOOLS
from app.core.models import ScanResult
from app.core.language import detect_languages, count_files
from app.tools.semgrep import SemgrepTool
from app.tools.trufflehog import TrufflehogTool
from app.tools.grype import GrypeTool
from app.tools.gitleaks import GitleaksTool
from app.tools.trivy import TrivyTool
from app.tools.checkov import CheckovTool


class EventType(str, Enum):
    TOOL_START = "tool_start"
    TOOL_PROGRESS = "tool_progress"
    TOOL_DONE = "tool_done"
    TOOL_ERROR = "tool_error"
    SCAN_COMPLETE = "scan_complete"


@dataclass
class ProgressEvent:
    event_type: EventType
    tool: str
    message: str
    findings_count: int = 0


def _dedup_key(f) -> tuple | None:
    """Chave de deduplicação por categoria.

    DEPENDENCY (CVEs): (rule_id, snippet) — snippet = "pkg==version".
      Dois tools achando o mesmo CVE no mesmo pacote são duplicatas,
      independente do file_path que cada tool reporta.

    Demais categorias: (rule_id, file_path, line_number) — mesma regra
      na mesma linha do mesmo arquivo.

    Findings sem rule_id não são deduplicados (retorna None).
    """
    if not f.rule_id:
        return None
    from app.core.models import FindingCategory
    if f.category == FindingCategory.DEPENDENCY:
        return ("dep", f.rule_id.upper(), f.snippet.lower())
    return (f.category.value, f.rule_id, f.file_path, f.line_number)


def _deduplicate(findings: list) -> list:
    """Mescla findings duplicados de ferramentas diferentes.

    Quando duas ferramentas detectam o mesmo problema:
    - tool: lista com ambas, ex: ["grype", "trivy"]
    - tool_notes: descrição original de cada ferramenta
    - description: mantém a do primeiro finding
    """
    seen: dict[tuple, object] = {}
    for f in findings:
        key = _dedup_key(f)
        if key and key in seen:
            primary = seen[key]
            for t in f.tool:
                if t not in primary.tool:
                    primary.tool.append(t)
            for t in f.tool:
                if t not in primary.tool_notes:
                    primary.tool_notes[t] = f.description
        else:
            for t in f.tool:
                if t not in f.tool_notes:
                    f.tool_notes[t] = f.description
            if key:
                seen[key] = f
            else:
                seen[id(f)] = f
    return list(seen.values())




TOOL_MAP = {
    "semgrep":    SemgrepTool,
    "trufflehog": TrufflehogTool,
    "grype":      GrypeTool,
    "gitleaks":   GitleaksTool,
    "trivy":      TrivyTool,
    "checkov":    CheckovTool,
}


class ScanOrchestrator:
    """Runs all scanner tools concurrently via ThreadPoolExecutor.

    Emits ProgressEvent objects to a caller-provided queue.Queue.
    Never blocks the caller thread — designed for Tkinter root.after() polling.
    """

    def __init__(self, plan: Optional[str] = None) -> None:
        self.plan = plan or (DEV_PLAN if DEV_MODE else "free")
        self._cancel_event = threading.Event()
        self._active_processes: list[subprocess.Popen] = []
        self._lock = threading.Lock()

    def register_process(self, proc: subprocess.Popen) -> None:
        """Register an active subprocess for cancellation tracking."""
        with self._lock:
            self._active_processes.append(proc)

    def unregister_process(self, proc: subprocess.Popen) -> None:
        """Unregister a subprocess that has completed."""
        with self._lock:
            try:
                self._active_processes.remove(proc)
            except ValueError:
                pass

    @property
    def cancelled(self) -> bool:
        """Return True if a cancel has been requested."""
        return self._cancel_event.is_set()

    def cancel(self) -> None:
        """Signal cancellation and terminate all active subprocesses."""
        self._cancel_event.set()
        with self._lock:
            for proc in list(self._active_processes):
                try:
                    proc.terminate()
                except Exception:
                    pass

    def scan(
        self,
        project_path: Path,
        progress_queue: Optional[queue.Queue] = None,
    ) -> ScanResult:
        """Run all configured scanners concurrently. Thread-safe."""
        start = time.time()
        q = progress_queue or queue.Queue()

        languages = detect_languages(project_path)
        file_count = count_files(project_path)

        tool_names = PLAN_TOOLS.get(self.plan, [])
        tool_classes = [
            TOOL_MAP[name] for name in tool_names if name in TOOL_MAP
        ]

        all_findings = []
        all_errors = []
        tools_used = []

        def _run_tool(tool_cls):
            if self._cancel_event.is_set():
                return [], "", "Cancelled"
            tool = tool_cls()
            name = tool.tool_name
            q.put(ProgressEvent(EventType.TOOL_START, name, f"Starting {name}..."))
            try:
                findings = tool.run(project_path)
                q.put(ProgressEvent(
                    EventType.TOOL_DONE, name,
                    f"{name}: {len(findings)} findings", len(findings)
                ))
                return findings, name, None
            except Exception as e:
                q.put(ProgressEvent(EventType.TOOL_ERROR, name, str(e)))
                return [], name, str(e)

        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = {
                executor.submit(_run_tool, cls): cls
                for cls in tool_classes
            }
            for future in as_completed(futures):
                if self._cancel_event.is_set():
                    break
                findings, name, error = future.result()
                all_findings.extend(findings)
                if name:
                    tools_used.append(name)
                if error and name:
                    all_errors.append(f"{name}: {error}")

        deduped = _deduplicate(all_findings)
        duration = time.time() - start
        q.put(ProgressEvent(
            EventType.SCAN_COMPLETE, "",
            f"Done - {len(deduped)} findings",
            len(deduped),
        ))

        return ScanResult(
            project_path=str(project_path),
            scanned_files=file_count,
            languages_detected=languages,
            findings=deduped,
            scan_duration_seconds=duration,
            tools_used=tools_used,
            errors=all_errors,
        )


# Backward compatibility alias for existing test_scanner.py
class Scanner:
    """Legacy wrapper. Use ScanOrchestrator for new code."""

    def __init__(
        self,
        plan: Optional[str] = None,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._orchestrator = ScanOrchestrator(plan=plan)
        self._on_progress = on_progress or (lambda msg: None)
        self.plan = self._orchestrator.plan

    def _log(self, message: str) -> None:
        self._on_progress(message)

    def scan(self, project_path: Path) -> ScanResult:
        q: queue.Queue = queue.Queue()
        result = self._orchestrator.scan(project_path, progress_queue=q)
        # Drain queue and forward to callback
        while not q.empty():
            event = q.get_nowait()
            self._log(event.message)
        return result

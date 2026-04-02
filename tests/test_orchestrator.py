"""Testes do ScanOrchestrator com execucao concorrente e eventos de progresso."""
import queue
import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.scanner import ScanOrchestrator, ProgressEvent, EventType
from app.core.models import Finding, Severity, FindingCategory, ScanResult


def _make_finding(tool: str, title: str = "test") -> Finding:
    return Finding(
        id="test-id",
        title=title,
        severity=Severity.HIGH,
        category=FindingCategory.SECRET,
        file_path="test.py",
        line_number=1,
        snippet="...",
        description="test",
        tool=tool,
        rule_id="test-rule",
    )


def test_orchestrator_emits_progress_events(sample_project: Path) -> None:
    """ScanOrchestrator deve emitir TOOL_START, TOOL_DONE e SCAN_COMPLETE para cada ferramenta."""
    from app.tools.gitleaks import GitleaksTool
    from app.tools.trufflehog import TrufflehogTool

    q: queue.Queue = queue.Queue()

    with patch.object(GitleaksTool, "run", return_value=[_make_finding("gitleaks")]), \
         patch.object(TrufflehogTool, "run", return_value=[]):

        orchestrator = ScanOrchestrator(plan="free")
        orchestrator.scan(sample_project, progress_queue=q)

    events = []
    while not q.empty():
        events.append(q.get_nowait())

    event_types = [e.event_type for e in events]
    assert EventType.TOOL_START in event_types
    assert EventType.TOOL_DONE in event_types
    assert EventType.SCAN_COMPLETE in event_types


def test_orchestrator_returns_scan_result(sample_project: Path) -> None:
    """ScanOrchestrator.scan() deve retornar ScanResult com findings agregados de todas as ferramentas."""
    from app.tools.gitleaks import GitleaksTool
    from app.tools.trufflehog import TrufflehogTool

    gitleaks_finding = _make_finding("gitleaks")
    trufflehog_finding = _make_finding("trufflehog")

    with patch.object(GitleaksTool, "run", return_value=[gitleaks_finding]), \
         patch.object(TrufflehogTool, "run", return_value=[trufflehog_finding]):

        orchestrator = ScanOrchestrator(plan="free")
        result = orchestrator.scan(sample_project)

    assert isinstance(result, ScanResult)
    assert len(result.findings) == 2
    tool_names = {f.tool for f in result.findings}
    assert "gitleaks" in tool_names
    assert "trufflehog" in tool_names


def test_orchestrator_emits_tool_error_on_exception(sample_project: Path) -> None:
    """Quando uma ferramenta lancar Exception, deve emitir TOOL_ERROR e as demais ferramentas continuam."""
    from app.tools.gitleaks import GitleaksTool
    from app.tools.trufflehog import TrufflehogTool

    q: queue.Queue = queue.Queue()

    with patch.object(GitleaksTool, "run", side_effect=RuntimeError("binary not found")), \
         patch.object(TrufflehogTool, "run", return_value=[_make_finding("trufflehog")]):

        orchestrator = ScanOrchestrator(plan="free")
        result = orchestrator.scan(sample_project, progress_queue=q)

    events = []
    while not q.empty():
        events.append(q.get_nowait())

    event_types = [e.event_type for e in events]
    assert EventType.TOOL_ERROR in event_types

    # Trufflehog still completed
    assert EventType.TOOL_DONE in event_types

    # The failed tool logged an error
    error_events = [e for e in events if e.event_type == EventType.TOOL_ERROR]
    assert len(error_events) >= 1
    assert "gitleaks" in error_events[0].tool


def test_orchestrator_runs_tools_concurrently(sample_project: Path) -> None:
    """Ferramentas devem rodar em paralelo — 4 ferramentas x 0.1s cada deve terminar em < 0.5s."""
    from app.tools.gitleaks import GitleaksTool
    from app.tools.trufflehog import TrufflehogTool
    from app.tools.semgrep import SemgrepTool
    from app.tools.grype import GrypeTool

    def slow_run(self, path):
        time.sleep(0.1)
        return []

    with patch.object(GitleaksTool, "run", slow_run), \
         patch.object(TrufflehogTool, "run", slow_run), \
         patch.object(SemgrepTool, "run", slow_run), \
         patch.object(GrypeTool, "run", slow_run):

        orchestrator = ScanOrchestrator(plan="pro")
        t0 = time.time()
        orchestrator.scan(sample_project)
        elapsed = time.time() - t0

    # Sequential would take ~0.4s; parallel should be < 0.35s
    assert elapsed < 0.35, f"Execution took {elapsed:.3f}s — tools may not be running concurrently"


def test_orchestrator_respects_plan_tools(sample_project: Path) -> None:
    """Com plano 'free', apenas trufflehog e gitleaks devem ser invocados (nao semgrep/grype)."""
    from app.tools.gitleaks import GitleaksTool
    from app.tools.trufflehog import TrufflehogTool
    from app.tools.semgrep import SemgrepTool
    from app.tools.grype import GrypeTool

    with patch.object(GitleaksTool, "run", return_value=[]) as mock_gl, \
         patch.object(TrufflehogTool, "run", return_value=[]) as mock_th, \
         patch.object(SemgrepTool, "run", return_value=[]) as mock_sg, \
         patch.object(GrypeTool, "run", return_value=[]) as mock_gr:

        orchestrator = ScanOrchestrator(plan="free")
        orchestrator.scan(sample_project)

    mock_gl.assert_called_once()
    mock_th.assert_called_once()
    mock_sg.assert_not_called()
    mock_gr.assert_not_called()


def test_progress_event_has_required_fields() -> None:
    """ProgressEvent deve ter os campos event_type, tool, message, findings_count."""
    event = ProgressEvent(
        event_type=EventType.TOOL_START,
        tool="gitleaks",
        message="Starting gitleaks...",
        findings_count=0,
    )
    assert hasattr(event, "event_type")
    assert hasattr(event, "tool")
    assert hasattr(event, "message")
    assert hasattr(event, "findings_count")
    assert event.event_type == EventType.TOOL_START
    assert event.tool == "gitleaks"
    assert event.findings_count == 0


def test_event_type_enum_values() -> None:
    """EventType deve ter TOOL_START, TOOL_DONE, TOOL_ERROR e SCAN_COMPLETE."""
    assert EventType.TOOL_START
    assert EventType.TOOL_DONE
    assert EventType.TOOL_ERROR
    assert EventType.SCAN_COMPLETE


def test_orchestrator_scan_complete_event_has_total_count(sample_project: Path) -> None:
    """O evento SCAN_COMPLETE deve ter findings_count igual ao total de achados de todas as ferramentas."""
    from app.tools.gitleaks import GitleaksTool
    from app.tools.trufflehog import TrufflehogTool

    q: queue.Queue = queue.Queue()
    gl_findings = [_make_finding("gitleaks"), _make_finding("gitleaks", "finding2")]
    th_findings = [_make_finding("trufflehog")]

    with patch.object(GitleaksTool, "run", return_value=gl_findings), \
         patch.object(TrufflehogTool, "run", return_value=th_findings):

        orchestrator = ScanOrchestrator(plan="free")
        orchestrator.scan(sample_project, progress_queue=q)

    events = []
    while not q.empty():
        events.append(q.get_nowait())

    complete_events = [e for e in events if e.event_type == EventType.SCAN_COMPLETE]
    assert len(complete_events) == 1
    assert complete_events[0].findings_count == 3  # 2 gitleaks + 1 trufflehog

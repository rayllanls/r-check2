"""Semgrep SAST runner with --json parsing."""
import json
import subprocess
import uuid
from pathlib import Path

from app.tools.base import BaseTool
from app.core.models import Finding, Severity, FindingCategory
from app.core.language import detect_languages, select_rulesets

SEVERITY_MAP = {
    "ERROR": Severity.HIGH,
    "WARNING": Severity.MEDIUM,
    "INFO": Severity.LOW,
    "CRITICAL": Severity.CRITICAL,
}


class SemgrepTool(BaseTool):
    tool_name = "semgrep"

    def run(self, project_path: Path) -> list[Finding]:
        import sys
        # Semgrep pip wrapper pode ser incompatível no Windows 64-bit.
        # Invoca via sys.executable -m semgrep para garantir compatibilidade.
        try:
            binary = self.resolve_binary()
        except FileNotFoundError:
            binary = None

        # Detect languages and select rulesets
        languages = detect_languages(project_path)
        rulesets = select_rulesets(languages)
        if not rulesets:
            rulesets = ["assets/rules/generic"]

        base_cmd = [binary] if binary else [sys.executable, "-m", "semgrep"]
        cmd = base_cmd + ["--json"]
        for ruleset in rulesets:
            cmd.extend(["--config", ruleset])
        cmd.append(str(project_path))

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        # Semgrep exits 1 when findings exist — do NOT check returncode

        if not result.stdout or not result.stdout.strip():
            return []

        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        results = raw.get("results", [])
        return [self._normalize(item) for item in results]

    def _normalize(self, item: dict) -> Finding:
        extra = item.get("extra", {})
        severity_str = extra.get("severity", "WARNING")

        return Finding(
            id=str(uuid.uuid4()),
            title=item.get("check_id", "unknown").split(".")[-1].replace("-", " ").title(),
            severity=SEVERITY_MAP.get(severity_str, Severity.MEDIUM),
            category=FindingCategory.SAST,
            file_path=item.get("path", ""),
            line_number=item.get("start", {}).get("line", 0),
            snippet=extra.get("lines", ""),
            description=extra.get("message", ""),
            tool=["semgrep"],
            rule_id=item.get("check_id", ""),
        )

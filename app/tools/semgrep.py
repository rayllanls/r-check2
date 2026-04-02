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
        try:
            binary = self.resolve_binary()
        except FileNotFoundError:
            binary = None

        rulesets = select_rulesets(project_path)
        if not rulesets:
            # Fallback seguro para regras locais de uso genérico
            rulesets = [str((Path(__file__).parent.parent.parent / "assets" / "rules" / "generic").absolute())]

        # Garantir que os caminhos das regras sejam absolutos
        abs_rulesets = []
        for r in rulesets:
            if not Path(r).is_absolute():
                abs_r = (Path(__file__).parent.parent.parent / r).absolute()
                if abs_r.exists():
                    abs_rulesets.append(str(abs_r))
                else:
                    abs_rulesets.append(r) # fallback
            else:
                abs_rulesets.append(r)

        if binary:
            # Uso direto do binário (estável no Windows empacotado)
            cmd = [binary, "scan", "--json", "--quiet"]
        else:
            # Fallback via módulo (pode falhar no frozen app)
            cmd = [sys.executable, "-m", "semgrep", "scan", "--json", "--quiet"]

        for r in abs_rulesets:
            cmd.extend(["--config", r])

        cmd.append(str(project_path.absolute()))

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
            creationflags=self.get_creationflags()
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

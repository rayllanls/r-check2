"""Wrapper para gitleaks. Analisa repositório em busca de segredos vazados."""
import json
import subprocess
import tempfile
import uuid
from pathlib import Path

from app.core.models import Finding, FindingCategory, Severity
from app.tools.base import BaseTool


class GitleaksTool(BaseTool):
    tool_name = "gitleaks"

    def run(self, project_path: Path) -> list[Finding]:
        binary = self.resolve_binary()

        # gitleaks v8 requires a real file path — does not support "-" for stdout
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            report_path = tmp.name

        cmd = [binary, "detect", "--report-format", "json", "--report-path", report_path]

        # Use --no-git when directory has no .git folder
        if not (project_path / ".git").is_dir():
            cmd.append("--no-git")

        cmd.extend(["--source", str(project_path)])

        subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        # gitleaks exits 1 when findings exist — do NOT check returncode

        try:
            content = Path(report_path).read_text()
            if not content.strip():
                return []
            raw = json.loads(content)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
        finally:
            Path(report_path).unlink(missing_ok=True)

        return [self._normalize(item) for item in raw]

    def _normalize(self, item: dict) -> Finding:
        return Finding(
            id=str(uuid.uuid4()),
            title=f"Secret detected: {item.get('RuleID', 'unknown')}",
            severity=Severity.HIGH,
            category=FindingCategory.SECRET,
            file_path=item.get("File", ""),
            line_number=item.get("StartLine", 0),
            snippet=item.get("Match", ""),
            description=f"Gitleaks found a potential secret matching rule '{item.get('RuleID', '')}'",
            tool=["gitleaks"],
            rule_id=item.get("RuleID", ""),
        )

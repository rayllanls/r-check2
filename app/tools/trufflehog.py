"""Wrapper para trufflehog. Detecta segredos usando análise de entropy e padrões."""
import json
import subprocess
import uuid
from pathlib import Path

from app.core.models import Finding, FindingCategory, Severity
from app.tools.base import BaseTool


class TrufflehogTool(BaseTool):
    tool_name = "trufflehog"

    def run(self, project_path: Path) -> list[Finding]:
        binary = self.resolve_binary()

        # No Windows, file://D:\path pode falhar. Usamos formato de URI absoluto com 3 barras e forward slashes.
        if (project_path / ".git").is_dir():
            import platform
            if platform.system() == "Windows":
                # Converte backslashes para forward slashes e garante 3 barras na URI
                clean_path = str(project_path.absolute()).replace("\\", "/")
                path_uri = f"file:///{clean_path}"
            else:
                path_uri = f"file://{project_path.absolute()}"
            cmd = [binary, "git", path_uri, "--json"]
        else:
            cmd = [binary, "filesystem", str(project_path.absolute()), "--json"]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            creationflags=self.get_creationflags()
        )

        if not result.stdout or not result.stdout.strip():
            return []

        # NDJSON: one JSON object per line — NOT a JSON array
        findings = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                findings.append(self._normalize(item))
            except json.JSONDecodeError:
                continue
        return findings

    def _normalize(self, item: dict) -> Finding:
        # Extract file and line from SourceMetadata
        metadata = item.get("SourceMetadata", {}).get("Data", {})
        # Try Filesystem first, then Git
        source = metadata.get("Filesystem", metadata.get("Git", {}))
        file_path = source.get("file", "")
        line_number = source.get("line", 0)

        detector = item.get("DetectorName", "unknown")
        verified = item.get("Verified", False)

        return Finding(
            id=str(uuid.uuid4()),
            title=f"Secret detected: {detector}" + (" (verified)" if verified else ""),
            severity=Severity.CRITICAL if verified else Severity.HIGH,
            category=FindingCategory.SECRET,
            file_path=file_path,
            line_number=line_number,
            snippet=item.get("Redacted", item.get("Raw", "")),
            description=(
                f"Trufflehog detected a {detector} secret"
                + (". Verified against live API." if verified else ". Unverified — may be a false positive.")
            ),
            tool=["trufflehog"],
            rule_id=detector,
        )

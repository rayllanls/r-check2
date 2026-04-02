"""Grype CVE scanner with JSON parsing."""
import json
import subprocess
import uuid
from pathlib import Path

from app.tools.base import BaseTool
from app.core.models import Finding, Severity, FindingCategory

SEVERITY_MAP = {
    "Critical": Severity.CRITICAL,
    "High": Severity.HIGH,
    "Medium": Severity.MEDIUM,
    "Low": Severity.LOW,
    "Negligible": Severity.INFO,
}


class GrypeTool(BaseTool):
    tool_name = "grype"

    def run(self, project_path: Path) -> list[Finding]:
        binary = self.resolve_binary()
        cmd = [binary, f"dir:{project_path}", "-o", "json"]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=600,
            creationflags=self.get_creationflags()
        )
        # Grype may exit non-zero based on severity thresholds

        if not result.stdout or not result.stdout.strip():
            return []

        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        matches = raw.get("matches", [])
        return [self._normalize(match) for match in matches]

    def _normalize(self, match: dict) -> Finding:
        vuln = match.get("vulnerability", {})
        artifact = match.get("artifact", {})
        locations = artifact.get("locations", [{}])
        file_path = locations[0].get("path", "") if locations else ""

        severity_str = vuln.get("severity", "Medium")
        pkg_name = artifact.get("name", "unknown")
        pkg_version = artifact.get("version", "unknown")
        cve_id = vuln.get("id", "unknown")

        fix_info = vuln.get("fix", {})
        fix_versions = fix_info.get("versions", [])
        fix_text = f" Fix available in: {', '.join(fix_versions)}" if fix_versions else " No fix available."

        return Finding(
            id=str(uuid.uuid4()),
            title=f"{cve_id}: {pkg_name} {pkg_version}",
            severity=SEVERITY_MAP.get(severity_str, Severity.MEDIUM),
            category=FindingCategory.DEPENDENCY,
            file_path=file_path,
            line_number=0,
            snippet=f"{pkg_name}=={pkg_version}",
            description=f"{vuln.get('description', '')}.{fix_text}",
            tool=["grype"],
            rule_id=cve_id,
        )

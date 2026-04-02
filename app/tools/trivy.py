"""Trivy scanner: SCA (dependency vulns), IaC misconfigurations, and secrets."""
import json
import subprocess
import uuid
from pathlib import Path

from app.tools.base import BaseTool
from app.core.models import Finding, Severity, FindingCategory

SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH":     Severity.HIGH,
    "MEDIUM":   Severity.MEDIUM,
    "LOW":      Severity.LOW,
    "UNKNOWN":  Severity.INFO,
}


class TrivyTool(BaseTool):
    tool_name = "trivy"

    def run(self, project_path: Path) -> list[Finding]:
        binary = self.resolve_binary()
        cmd = [
            binary, "fs",
            "--scanners", "vuln,misconfig,secret",
            "--format", "json",
            "--quiet",
            str(project_path),
        ]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        # Trivy exits non-zero when findings exist — do NOT use check=True

        if not result.stdout or not result.stdout.strip():
            return []

        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        findings = []
        for result_block in raw.get("Results", []):
            target = result_block.get("Target", "")
            findings.extend(self._parse_vulns(result_block, target))
            findings.extend(self._parse_misconfs(result_block, target))
            findings.extend(self._parse_secrets(result_block, target))
        return findings

    def _parse_vulns(self, block: dict, target: str) -> list[Finding]:
        findings = []
        for v in block.get("Vulnerabilities", []):
            vuln_id = v.get("VulnerabilityID", "unknown")
            pkg_name = v.get("PkgName", "unknown")
            installed = v.get("InstalledVersion", "unknown")
            fixed = v.get("FixedVersion", "")
            fix_text = f" Fix in: {fixed}" if fixed else " No fix available."
            findings.append(Finding(
                id=str(uuid.uuid4()),
                title=f"{vuln_id}: {pkg_name} {installed}",
                severity=SEVERITY_MAP.get(v.get("Severity", "UNKNOWN"), Severity.INFO),
                category=FindingCategory.DEPENDENCY,
                file_path=target,
                line_number=0,
                snippet=f"{pkg_name}=={installed}",
                description=f"{v.get('Title', v.get('Description', ''))}.{fix_text}",
                tool=["trivy"],
                rule_id=vuln_id,
            ))
        return findings

    def _parse_misconfs(self, block: dict, target: str) -> list[Finding]:
        findings = []
        for m in block.get("Misconfigurations", []):
            if m.get("Status") != "FAIL":
                continue
            cause = m.get("CauseMetadata", {})
            line_number = cause.get("StartLine", 0) or 0
            findings.append(Finding(
                id=str(uuid.uuid4()),
                title=f"{m.get('ID', 'unknown')}: {m.get('Title', '')}",
                severity=SEVERITY_MAP.get(m.get("Severity", "UNKNOWN"), Severity.INFO),
                category=FindingCategory.IAC,
                file_path=target,
                line_number=line_number,
                snippet=m.get("Message", ""),
                description=f"{m.get('Description', '')} Resolution: {m.get('Resolution', '')}",
                tool=["trivy"],
                rule_id=m.get("ID", ""),
            ))
        return findings

    def _parse_secrets(self, block: dict, target: str) -> list[Finding]:
        findings = []
        for s in block.get("Secrets", []):
            findings.append(Finding(
                id=str(uuid.uuid4()),
                title=f"Secret detected: {s.get('Title', s.get('RuleID', 'unknown'))}",
                severity=SEVERITY_MAP.get(s.get("Severity", "HIGH"), Severity.HIGH),
                category=FindingCategory.SECRET,
                file_path=target,
                line_number=s.get("StartLine", 0) or 0,
                snippet=s.get("Match", ""),
                description=f"Trivy found a {s.get('Category', 'unknown')} secret matching rule '{s.get('RuleID', '')}'",
                tool=["trivy"],
                rule_id=s.get("RuleID", ""),
            ))
        return findings

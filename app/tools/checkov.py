"""Checkov IaC static analysis scanner with polymorphic JSON output handling."""
import json
import subprocess
import uuid
from pathlib import Path

from app.tools.base import BaseTool
from app.core.models import Finding, Severity, FindingCategory


class CheckovTool(BaseTool):
    """Checkov IaC static analysis scanner.

    Checkov is a Python CLI tool installed via pip. resolve_binary() finds it
    in ~/.local/bin/checkov or system PATH -- no vendor/ copy needed.

    NOTE: severity is always null in OSS Checkov (no Prisma Cloud API key).
    All findings default to Severity.MEDIUM. The rule_id field carries the
    check_id (e.g., CKV_AWS_23) for user reference.

    Phase 7 PyInstaller: use --collect-all checkov OR invoke via
    sys.executable + ['-m', 'checkov'] instead of resolve_binary().

    Checkov output is polymorphic — 3 possible shapes:
    1. dict with "check_type" key: single-framework result (e.g. terraform only)
    2. list of dicts each with "check_type": multi-framework result
    3. dict WITHOUT "check_type" key: summary-only (no IaC files found)
    """

    tool_name = "checkov"

    def run(self, project_path: Path) -> list[Finding]:
        import sys
        # Checkov pip wrapper (.exe) é incompatível no Windows 64-bit.
        # Invoca sempre via sys.executable -m checkov para garantir compatibilidade.
        cmd = [sys.executable, "-m", "checkov", "-d", str(project_path), "--output", "json", "--compact"]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300,
            creationflags=self.get_creationflags()
        )
        # No check=True — Checkov exits non-zero when findings are found

        if not result.stdout or not result.stdout.strip():
            return []

        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            return []

        blocks = self._normalize_to_blocks(raw)
        findings: list[Finding] = []
        for block in blocks:
            findings.extend(self._parse_failed_checks(block))
        return findings

    def _normalize_to_blocks(self, raw: object) -> list[dict]:
        """Normalize polymorphic Checkov output to a list of framework blocks.

        Returns:
            list of dicts, each containing a "check_type" and "results" key.
        """
        if isinstance(raw, list):
            # Multi-framework: list of per-framework dicts
            return raw
        if isinstance(raw, dict) and "check_type" in raw:
            # Single-framework: wrap in list
            return [raw]
        # Summary-only dict (no IaC files found) — no check_type key
        return []

    def _parse_failed_checks(self, block: dict) -> list[Finding]:
        """Parse failed_checks from a single framework block into Finding objects."""
        findings: list[Finding] = []
        check_type = block.get("check_type", "unknown")
        results = block.get("results", {})
        failed_checks = results.get("failed_checks", [])

        for chk in failed_checks:
            check_id = chk.get("check_id", "")
            check_name = chk.get("check_name", "")
            guideline = chk.get("guideline", "")
            file_line_range = chk.get("file_line_range", [0, 0])
            resource = chk.get("resource", "")

            # Strip leading slash so paths are relative to project root
            raw_path = chk.get("file_path", "")
            file_path = raw_path.lstrip("/")

            # line_number is the start of the range
            line_number = file_line_range[0] if file_line_range else 0

            # Build description with guideline only if non-empty
            if guideline:
                description = f"[{check_type}] {check_name}. See: {guideline}"
            else:
                description = f"[{check_type}] {check_name}"

            findings.append(Finding(
                id=str(uuid.uuid4()),
                title=f"{check_id}: {check_name}",
                severity=Severity.MEDIUM,  # OSS Checkov severity is always null
                category=FindingCategory.IAC,
                file_path=file_path,
                line_number=line_number,
                snippet=resource,
                description=description,
                tool=["checkov"],
                rule_id=check_id,
            ))

        return findings

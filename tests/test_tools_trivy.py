"""Fixture-based tests for TrivyTool."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tools.trivy import TrivyTool
from app.core.models import FindingCategory, Severity


@pytest.fixture
def tool():
    return TrivyTool()


def _make_result(stdout: str, returncode: int = 0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


def test_trivy_parses_all_finding_types(tool, trivy_fixture, tmp_path):
    """Mock subprocess with fixture JSON. Assert returns 3 findings (PASS misconfig filtered out)."""
    with patch("subprocess.run", return_value=_make_result(trivy_fixture)):
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            findings = tool.run(tmp_path)
    assert len(findings) == 3


def test_trivy_vuln_fields(tool, trivy_fixture, tmp_path):
    """Assert vuln finding has tool='trivy', category=DEPENDENCY, rule_id starts with 'CVE-', title contains package name."""
    with patch("subprocess.run", return_value=_make_result(trivy_fixture)):
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            findings = tool.run(tmp_path)
    vuln = next(f for f in findings if f.category == FindingCategory.DEPENDENCY)
    assert vuln.tool == ["trivy"]
    assert vuln.category == FindingCategory.DEPENDENCY
    assert vuln.rule_id.startswith("CVE-")
    assert "flask" in vuln.title.lower()
    assert vuln.severity == Severity.HIGH


def test_trivy_severity_mapping(tool, tmp_path):
    """Assert CRITICAL->Severity.CRITICAL, HIGH->Severity.HIGH, MEDIUM->Severity.MEDIUM,
    LOW->Severity.LOW, UNKNOWN->Severity.INFO."""
    severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
    fixture = {
        "SchemaVersion": 2,
        "Results": [
            {
                "Target": "requirements.txt",
                "Class": "lang-pkgs",
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": f"CVE-2023-{i:05d}",
                        "PkgName": f"pkg{i}",
                        "InstalledVersion": "1.0.0",
                        "Severity": sev,
                        "Title": f"Test {sev}",
                    }
                    for i, sev in enumerate(severities)
                ],
            }
        ],
    }
    import json
    with patch("subprocess.run", return_value=_make_result(json.dumps(fixture))):
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            findings = tool.run(tmp_path)
    sev_map = {f.rule_id[-5:]: f.severity for f in findings}
    assert findings[0].severity == Severity.CRITICAL
    assert findings[1].severity == Severity.HIGH
    assert findings[2].severity == Severity.MEDIUM
    assert findings[3].severity == Severity.LOW
    assert findings[4].severity == Severity.INFO


def test_trivy_misconf_only_fail(tool, trivy_fixture, tmp_path):
    """Assert only Status=='FAIL' misconfigs generate findings. category=IAC, line_number from CauseMetadata.StartLine."""
    with patch("subprocess.run", return_value=_make_result(trivy_fixture)):
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            findings = tool.run(tmp_path)
    misconf_findings = [f for f in findings if f.category == FindingCategory.IAC]
    assert len(misconf_findings) == 1
    misconf = misconf_findings[0]
    assert misconf.category == FindingCategory.IAC
    assert misconf.line_number == 5
    assert "DS-0002" in misconf.title


def test_trivy_secret_fields(tool, trivy_fixture, tmp_path):
    """Assert secret finding has category=SECRET, line_number from StartLine, snippet from Match field."""
    with patch("subprocess.run", return_value=_make_result(trivy_fixture)):
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            findings = tool.run(tmp_path)
    secret = next(f for f in findings if f.category == FindingCategory.SECRET)
    assert secret.category == FindingCategory.SECRET
    assert secret.line_number == 3
    assert secret.snippet == "AKIAIOSFODNN7EXAMPLE"
    assert secret.tool == ["trivy"]
    assert secret.severity == Severity.CRITICAL


def test_trivy_empty_output(tool, tmp_path):
    """Mock empty stdout. Assert returns []."""
    with patch("subprocess.run", return_value=_make_result("")):
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            findings = tool.run(tmp_path)
    assert findings == []


def test_trivy_uses_correct_flags(tool, tmp_path):
    """Assert subprocess.run called with correct trivy fs flags."""
    mock_result = _make_result('{"SchemaVersion": 2, "Results": []}')
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch.object(tool, "resolve_binary", return_value="trivy"):
            tool.run(tmp_path)
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "trivy"
    assert "fs" in cmd
    assert "--scanners" in cmd
    scanners_idx = cmd.index("--scanners")
    assert cmd[scanners_idx + 1] == "vuln,misconfig,secret"
    assert "--format" in cmd
    format_idx = cmd.index("--format")
    assert cmd[format_idx + 1] == "json"
    assert "--quiet" in cmd
    assert str(tmp_path) in cmd

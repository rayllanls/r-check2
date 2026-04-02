"""Fixture-based tests for GrypeTool."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tools.grype import GrypeTool
from app.core.models import FindingCategory, Severity


@pytest.fixture
def tool():
    return GrypeTool()


def _make_result(stdout: str, returncode: int = 0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


def test_grype_parses_findings(tool, grype_fixture, tmp_path):
    """Mock subprocess.run returning fixture JSON. Assert returns 3 Finding objects."""
    with patch("subprocess.run", return_value=_make_result(grype_fixture)):
        with patch.object(tool, "resolve_binary", return_value="grype"):
            findings = tool.run(tmp_path)
    assert len(findings) == 3


def test_grype_severity_mapping(tool, grype_fixture, tmp_path):
    """Assert findings map: 'Critical'->Severity.CRITICAL, 'High'->Severity.HIGH, 'Negligible'->Severity.INFO."""
    with patch("subprocess.run", return_value=_make_result(grype_fixture)):
        with patch.object(tool, "resolve_binary", return_value="grype"):
            findings = tool.run(tmp_path)
    severity_map = {f.rule_id: f.severity for f in findings}
    assert severity_map["CVE-2023-30861"] == Severity.HIGH       # High
    assert severity_map["CVE-2022-42969"] == Severity.CRITICAL   # Critical
    assert severity_map["CVE-2024-12345"] == Severity.INFO        # Negligible


def test_grype_finding_fields(tool, grype_fixture, tmp_path):
    """Assert first finding has: tool='grype', category=DEPENDENCY, rule_id='CVE-2023-30861', description contains 'Flask'."""
    with patch("subprocess.run", return_value=_make_result(grype_fixture)):
        with patch.object(tool, "resolve_binary", return_value="grype"):
            findings = tool.run(tmp_path)
    first = findings[0]
    assert first.tool == "grype"
    assert first.category == FindingCategory.DEPENDENCY
    assert first.rule_id == "CVE-2023-30861"
    assert "Flask" in first.description


def test_grype_artifact_info(tool, grype_fixture, tmp_path):
    """Assert first finding title contains package name 'flask' and file_path='requirements.txt'."""
    with patch("subprocess.run", return_value=_make_result(grype_fixture)):
        with patch.object(tool, "resolve_binary", return_value="grype"):
            findings = tool.run(tmp_path)
    first = findings[0]
    assert "flask" in first.title.lower()
    assert first.file_path == "requirements.txt"


def test_grype_no_matches(tool, tmp_path):
    """Mock stdout='{"matches":[]}'. Assert returns empty list."""
    with patch("subprocess.run", return_value=_make_result('{"matches":[]}')):
        with patch.object(tool, "resolve_binary", return_value="grype"):
            findings = tool.run(tmp_path)
    assert findings == []


def test_grype_uses_dir_prefix(tool, tmp_path):
    """Mock subprocess.run. Assert cmd contains 'dir:' prefix before project path."""
    mock_result = _make_result('{"matches":[]}')
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch.object(tool, "resolve_binary", return_value="grype"):
            tool.run(tmp_path)
    cmd = mock_run.call_args[0][0]
    assert any(arg.startswith("dir:") for arg in cmd)

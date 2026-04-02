"""Fixture-based tests for SemgrepTool."""
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tools.semgrep import SemgrepTool
from app.core.models import FindingCategory, Severity


@pytest.fixture
def tool():
    return SemgrepTool()


def _make_result(stdout: str, returncode: int = 0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


def test_semgrep_parses_findings(tool, semgrep_fixture, tmp_path):
    """Mock subprocess.run returning fixture JSON. Assert returns 3 Finding objects."""
    with patch("subprocess.run", return_value=_make_result(semgrep_fixture)):
        with patch.object(tool, "resolve_binary", return_value="semgrep"):
            findings = tool.run(tmp_path)
    assert len(findings) == 3


def test_semgrep_severity_mapping(tool, semgrep_fixture, tmp_path):
    """Assert findings map ERROR->Severity.HIGH, WARNING->Severity.MEDIUM, INFO->Severity.LOW."""
    with patch("subprocess.run", return_value=_make_result(semgrep_fixture)):
        with patch.object(tool, "resolve_binary", return_value="semgrep"):
            findings = tool.run(tmp_path)
    severity_map = {f.file_path: f.severity for f in findings}
    assert severity_map["app/db.py"] == Severity.HIGH      # ERROR
    assert severity_map["app/utils.py"] == Severity.MEDIUM  # WARNING
    assert severity_map["app/files.py"] == Severity.LOW     # INFO


def test_semgrep_finding_fields(tool, semgrep_fixture, tmp_path):
    """Assert first finding has correct fields."""
    with patch("subprocess.run", return_value=_make_result(semgrep_fixture)):
        with patch.object(tool, "resolve_binary", return_value="semgrep"):
            findings = tool.run(tmp_path)
    first = findings[0]
    assert first.tool == "semgrep"
    assert first.category == FindingCategory.SAST
    assert first.file_path == "app/db.py"
    assert first.line_number == 42
    assert "sql-query" in first.rule_id


def test_semgrep_no_results(tool, tmp_path):
    """Mock stdout='{"results":[],"errors":[]}'. Assert returns empty list."""
    stdout = '{"results":[],"errors":[]}'
    with patch("subprocess.run", return_value=_make_result(stdout)):
        with patch.object(tool, "resolve_binary", return_value="semgrep"):
            findings = tool.run(tmp_path)
    assert findings == []


def test_semgrep_empty_stdout(tool, tmp_path):
    """Mock stdout="". Assert returns empty list."""
    with patch("subprocess.run", return_value=_make_result("")):
        with patch.object(tool, "resolve_binary", return_value="semgrep"):
            findings = tool.run(tmp_path)
    assert findings == []


def test_semgrep_uses_config_flag(tool, tmp_path):
    """Mock subprocess.run. Assert cmd contains '--config' flag."""
    # Create a Python file so language detection finds Python
    (tmp_path / "main.py").write_text("x = 1")
    mock_result = _make_result('{"results":[],"errors":[]}')
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch.object(tool, "resolve_binary", return_value="semgrep"):
            tool.run(tmp_path)
    cmd = mock_run.call_args[0][0]
    assert "--config" in cmd

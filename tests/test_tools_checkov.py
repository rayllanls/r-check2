"""Fixture-based tests for CheckovTool."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.tools.checkov import CheckovTool
from app.core.models import FindingCategory, Severity


@pytest.fixture
def tool():
    return CheckovTool()


def _make_result(stdout: str, returncode: int = 0):
    mock = MagicMock()
    mock.stdout = stdout
    mock.returncode = returncode
    return mock


def test_checkov_parses_single_framework(tool, checkov_single_fixture, tmp_path):
    """Mock subprocess with single-framework fixture (dict with check_type).
    Assert returns 2 findings from failed_checks."""
    with patch("subprocess.run", return_value=_make_result(checkov_single_fixture)):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    assert len(findings) == 2


def test_checkov_parses_multi_framework(tool, checkov_multi_fixture, tmp_path):
    """Mock subprocess with multi-framework fixture (list of dicts).
    Assert returns findings from ALL framework blocks combined (2 terraform + 1 dockerfile = 3)."""
    with patch("subprocess.run", return_value=_make_result(checkov_multi_fixture)):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    assert len(findings) == 3
    # Verify findings come from both frameworks
    tools_used = {f.rule_id for f in findings}
    assert "CKV2_AWS_6" in tools_used     # terraform
    assert "CKV_DOCKER_4" in tools_used   # dockerfile


def test_checkov_no_iac_returns_empty(tool, checkov_no_iac_fixture, tmp_path):
    """Mock subprocess with no-IaC summary dict (no check_type key). Assert returns []."""
    with patch("subprocess.run", return_value=_make_result(checkov_no_iac_fixture)):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    assert findings == []


def test_checkov_finding_fields(tool, checkov_single_fixture, tmp_path):
    """Assert findings have tool='checkov', category=IAC, severity=MEDIUM, rule_id starts with 'CKV'."""
    with patch("subprocess.run", return_value=_make_result(checkov_single_fixture)):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    assert len(findings) > 0
    for f in findings:
        assert f.tool == ["checkov"]
        assert f.category == FindingCategory.IAC
        assert f.severity == Severity.MEDIUM
        assert f.rule_id.startswith("CKV")


def test_checkov_file_path_strips_leading_slash(tool, checkov_single_fixture, tmp_path):
    """Assert file_path does NOT start with '/' (e.g., 'main.tf' not '/main.tf')."""
    with patch("subprocess.run", return_value=_make_result(checkov_single_fixture)):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    for f in findings:
        assert not f.file_path.startswith("/"), f"file_path should not start with '/': {f.file_path}"
    # Verify the first finding has the correct stripped path
    assert findings[0].file_path == "main.tf"


def test_checkov_line_number_from_range(tool, checkov_single_fixture, tmp_path):
    """Assert line_number equals file_line_range[0] from fixture."""
    with patch("subprocess.run", return_value=_make_result(checkov_single_fixture)):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    # First finding: file_line_range=[1,3], so line_number should be 1
    assert findings[0].line_number == 1
    # Second finding: file_line_range=[10,15], so line_number should be 10
    assert findings[1].line_number == 10


def test_checkov_empty_output(tool, tmp_path):
    """Mock empty stdout. Assert returns []."""
    with patch("subprocess.run", return_value=_make_result("")):
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            findings = tool.run(tmp_path)
    assert findings == []


def test_checkov_uses_correct_flags(tool, tmp_path):
    """Assert subprocess.run called with ['checkov', '-d', str(path), '--output', 'json', '--compact']."""
    mock_result = _make_result('{"passed": 0, "failed": 0, "checkov_version": "3.2.0"}')
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        with patch.object(tool, "resolve_binary", return_value="checkov"):
            tool.run(tmp_path)
    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "checkov"
    assert "-d" in cmd
    assert str(tmp_path) in cmd
    assert "--output" in cmd
    assert "json" in cmd
    assert "--compact" in cmd

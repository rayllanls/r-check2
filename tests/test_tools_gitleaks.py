"""Tests for GitleaksTool runner."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.models import FindingCategory, Severity
from app.tools.gitleaks import GitleaksTool


class TestGitleaksParses:
    """GitleaksTool parsing behaviour."""

    def test_gitleaks_parses_findings(self, tmp_path: Path, gitleaks_fixture: str):
        """Mock subprocess returning fixture JSON. Assert returns 2 Finding objects."""
        mock_result = MagicMock()
        mock_result.stdout = gitleaks_fixture
        mock_result.returncode = 1  # gitleaks exits 1 when findings found

        with patch("subprocess.run", return_value=mock_result) as _mock_run:
            with patch.object(GitleaksTool, "resolve_binary", return_value="/usr/bin/gitleaks"):
                tool = GitleaksTool()
                findings = tool.run(tmp_path)

        assert len(findings) == 2

    def test_gitleaks_finding_fields(self, tmp_path: Path, gitleaks_fixture: str):
        """Assert first finding has correct field mapping."""
        mock_result = MagicMock()
        mock_result.stdout = gitleaks_fixture
        mock_result.returncode = 1

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(GitleaksTool, "resolve_binary", return_value="/usr/bin/gitleaks"):
                tool = GitleaksTool()
                findings = tool.run(tmp_path)

        first = findings[0]
        assert first.tool == "gitleaks"
        assert first.category == FindingCategory.SECRET
        assert first.file_path == "config.py"
        assert first.line_number == 1
        assert first.rule_id == "generic-api-key"
        assert first.severity == Severity.HIGH

    def test_gitleaks_no_findings(self, tmp_path: Path):
        """Mock returning empty JSON array. Assert returns empty list."""
        mock_result = MagicMock()
        mock_result.stdout = "[]"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(GitleaksTool, "resolve_binary", return_value="/usr/bin/gitleaks"):
                tool = GitleaksTool()
                findings = tool.run(tmp_path)

        assert findings == []

    def test_gitleaks_empty_stdout(self, tmp_path: Path):
        """Mock returning empty stdout. Assert returns empty list, not crash."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(GitleaksTool, "resolve_binary", return_value="/usr/bin/gitleaks"):
                tool = GitleaksTool()
                findings = tool.run(tmp_path)

        assert findings == []

    def test_gitleaks_uses_no_git_flag(self, tmp_path: Path):
        """Path without .git dir must use --no-git flag."""
        mock_result = MagicMock()
        mock_result.stdout = "[]"
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch.object(GitleaksTool, "resolve_binary", return_value="/usr/bin/gitleaks"):
                tool = GitleaksTool()
                tool.run(tmp_path)

        call_args = mock_run.call_args[0][0]  # positional first arg = cmd list
        assert "--no-git" in call_args

    def test_gitleaks_binary_not_found(self, tmp_path: Path):
        """resolve_binary raising FileNotFoundError must propagate from run()."""
        with patch.object(GitleaksTool, "resolve_binary", side_effect=FileNotFoundError("gitleaks not found")):
            tool = GitleaksTool()
            with pytest.raises(FileNotFoundError):
                tool.run(tmp_path)

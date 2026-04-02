"""Tests for TrufflehogTool runner."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.models import FindingCategory, Severity
from app.tools.trufflehog import TrufflehogTool


class TestTrufflehogParses:
    """TrufflehogTool parsing behaviour."""

    def test_trufflehog_parses_ndjson(self, tmp_path: Path, trufflehog_fixture: str):
        """Mock subprocess returning fixture NDJSON. Assert returns 2 Finding objects."""
        mock_result = MagicMock()
        mock_result.stdout = trufflehog_fixture
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(TrufflehogTool, "resolve_binary", return_value="/usr/bin/trufflehog"):
                tool = TrufflehogTool()
                findings = tool.run(tmp_path)

        assert len(findings) == 2

    def test_trufflehog_finding_fields(self, tmp_path: Path, trufflehog_fixture: str):
        """Assert first finding (verified AWS) has correct field mapping."""
        mock_result = MagicMock()
        mock_result.stdout = trufflehog_fixture
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(TrufflehogTool, "resolve_binary", return_value="/usr/bin/trufflehog"):
                tool = TrufflehogTool()
                findings = tool.run(tmp_path)

        first = findings[0]
        assert first.tool == "trufflehog"
        assert first.category == FindingCategory.SECRET
        assert first.file_path == "config/secrets.py"
        assert first.line_number == 7
        assert first.severity == Severity.CRITICAL  # Verified=True
        assert "AWS" in first.title

    def test_trufflehog_unverified_is_high(self, tmp_path: Path, trufflehog_fixture: str):
        """Assert second finding (unverified Stripe) gets Severity.HIGH."""
        mock_result = MagicMock()
        mock_result.stdout = trufflehog_fixture
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(TrufflehogTool, "resolve_binary", return_value="/usr/bin/trufflehog"):
                tool = TrufflehogTool()
                findings = tool.run(tmp_path)

        second = findings[1]
        assert second.severity == Severity.HIGH  # Verified=False

    def test_trufflehog_no_findings(self, tmp_path: Path):
        """Mock returning empty stdout. Assert returns empty list."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result):
            with patch.object(TrufflehogTool, "resolve_binary", return_value="/usr/bin/trufflehog"):
                tool = TrufflehogTool()
                findings = tool.run(tmp_path)

        assert findings == []

    def test_trufflehog_uses_git_subcommand_when_git_dir_exists(self, tmp_path: Path):
        """Path with .git dir must use 'git' subcommand and file:// URI."""
        (tmp_path / ".git").mkdir()
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch.object(TrufflehogTool, "resolve_binary", return_value="/usr/bin/trufflehog"):
                tool = TrufflehogTool()
                tool.run(tmp_path)

        call_args = mock_run.call_args[0][0]  # positional first arg = cmd list
        assert "git" in call_args
        assert any("file://" in arg for arg in call_args)

    def test_trufflehog_uses_filesystem_subcommand_when_no_git(self, tmp_path: Path):
        """Path without .git dir must use 'filesystem' subcommand."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.returncode = 0

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            with patch.object(TrufflehogTool, "resolve_binary", return_value="/usr/bin/trufflehog"):
                tool = TrufflehogTool()
                tool.run(tmp_path)

        call_args = mock_run.call_args[0][0]
        assert "filesystem" in call_args

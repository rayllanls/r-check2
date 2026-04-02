"""Unit tests for BinaryLocator 3-level fallback in BaseTool."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from app.tools.base import BaseTool


class ConcreteToolForTest(BaseTool):
    """Minimal concrete subclass used only in these tests."""

    tool_name = "mytool"

    def run(self, project_path):  # pragma: no cover
        return []


def test_binary_locator_uses_meipass_first(tmp_path):
    """When frozen=True and binary exists in _MEIPASS, it returns the MEIPASS path."""
    meipass_dir = tmp_path / "meipass"
    meipass_dir.mkdir()
    binary = meipass_dir / "mytool"
    binary.touch()

    tool = ConcreteToolForTest()

    with (
        patch.object(sys, "frozen", True, create=True),
        patch.object(sys, "_MEIPASS", str(meipass_dir), create=True),
        patch("platform.system", return_value="Linux"),
    ):
        result = tool.resolve_binary()

    assert result == str(binary)


def test_binary_locator_falls_back_to_vendor(tmp_path):
    """When not frozen and binary exists in vendor dir, it returns vendor path."""
    vendor_linux = tmp_path / "linux"
    vendor_linux.mkdir(parents=True)
    binary = vendor_linux / "mytool"
    binary.touch()

    tool = ConcreteToolForTest()

    with (
        patch("app.tools.base.VENDOR_DIR", tmp_path),
        patch("platform.system", return_value="Linux"),
        patch("sys.frozen", False, create=True),
    ):
        result = tool.resolve_binary()

    assert result == str(binary)


def test_binary_locator_falls_back_to_path():
    """When neither MEIPASS nor vendor has binary, uses shutil.which result."""
    fake_path = "/usr/local/bin/mytool"

    tool = ConcreteToolForTest()

    with (
        patch("app.tools.base.VENDOR_DIR", Path("/nonexistent-vendor-dir")),
        patch("platform.system", return_value="Linux"),
        patch("shutil.which", return_value=fake_path),
    ):
        result = tool.resolve_binary()

    assert result == fake_path


def test_binary_locator_raises_not_found():
    """When binary is not found anywhere, FileNotFoundError is raised."""
    tool = ConcreteToolForTest()

    with (
        patch("app.tools.base.VENDOR_DIR", Path("/nonexistent-vendor-dir")),
        patch("platform.system", return_value="Linux"),
        patch("shutil.which", return_value=None),
    ):
        with pytest.raises(FileNotFoundError):
            tool.resolve_binary()


def test_binary_locator_windows_exe_extension(tmp_path):
    """On Windows, binary name gets .exe extension appended."""
    meipass_dir = tmp_path / "meipass"
    meipass_dir.mkdir()
    binary = meipass_dir / "mytool.exe"
    binary.touch()

    tool = ConcreteToolForTest()

    with (
        patch.object(sys, "frozen", True, create=True),
        patch.object(sys, "_MEIPASS", str(meipass_dir), create=True),
        patch("platform.system", return_value="Windows"),
    ):
        result = tool.resolve_binary()

    assert result == str(binary)

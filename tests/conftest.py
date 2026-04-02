"""Fixtures globais do pytest."""
import queue
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_project(tmp_path: Path) -> Path:
    """Projeto de exemplo com arquivo suspeito para testes."""
    (tmp_path / "config.py").write_text('STRIPE_KEY = "sk_live_1234hardcoded"\n')
    (tmp_path / "app.py").write_text('import os\nprint("hello")\n')
    (tmp_path / "requirements.txt").write_text("django==2.0.0\nrequests==2.20.0\n")
    return tmp_path


@pytest.fixture
def fixture_path():
    """Return the path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def semgrep_fixture():
    return (FIXTURES_DIR / "semgrep_output.json").read_text()


@pytest.fixture
def trufflehog_fixture():
    return (FIXTURES_DIR / "trufflehog_output.ndjson").read_text()


@pytest.fixture
def grype_fixture():
    return (FIXTURES_DIR / "grype_output.json").read_text()


@pytest.fixture
def gitleaks_fixture():
    return (FIXTURES_DIR / "gitleaks_output.json").read_text()


@pytest.fixture
def trivy_fixture():
    return (FIXTURES_DIR / "trivy_output.json").read_text()


@pytest.fixture
def checkov_single_fixture():
    return (FIXTURES_DIR / "checkov_single_framework.json").read_text()


@pytest.fixture
def checkov_multi_fixture():
    return (FIXTURES_DIR / "checkov_multi_framework.json").read_text()


@pytest.fixture
def checkov_no_iac_fixture():
    return (FIXTURES_DIR / "checkov_no_iac.json").read_text()


@pytest.fixture
def mock_ctk():
    """Mock customtkinter to avoid requiring X11 display."""
    with patch.dict("sys.modules", {
        "customtkinter": MagicMock(),
        "tkinter": MagicMock(),
        "tkinter.filedialog": MagicMock(),
        "tkinter.messagebox": MagicMock(),
        "tkinter.font": MagicMock(),
    }) as mocked:
        yield mocked


@pytest.fixture
def mock_orchestrator():
    """Mock ScanOrchestrator for GUI tests."""
    orch = MagicMock()
    orch.plan = "team"
    orch.cancelled = False
    orch.cancel = MagicMock()
    orch.scan = MagicMock()
    return orch


@pytest.fixture
def progress_queue():
    """Fresh queue.Queue for progress event tests."""
    return queue.Queue()

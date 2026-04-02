"""Testes do orquestrador Scanner."""
import pytest
from pathlib import Path
from unittest.mock import patch
from app.core.scanner import Scanner, TOOL_MAP, ScanOrchestrator
from app.core.models import ScanResult
from app.config import PLAN_TOOLS


def test_scanner_returns_scan_result(sample_project: Path) -> None:
    """Scanner deve retornar ScanResult mesmo com ferramentas não implementadas."""
    scanner = Scanner(plan="free")
    result  = scanner.scan(sample_project)
    assert isinstance(result, ScanResult)
    assert result.scanned_files >= 0


def test_scanner_dev_mode_uses_team_plan() -> None:
    """Em DEV_MODE o Scanner usa plano team automaticamente."""
    from app.config import DEV_MODE, DEV_PLAN
    if DEV_MODE:
        scanner = Scanner()
        assert scanner.plan == DEV_PLAN


def test_scanner_progress_callback(sample_project: Path) -> None:
    """Callback de progresso deve ser chamado durante a análise."""
    messages = []
    scanner  = Scanner(plan="free", on_progress=messages.append)
    scanner.scan(sample_project)
    assert len(messages) > 0


def test_tool_map_has_six_entries() -> None:
    """TOOL_MAP deve conter exatamente 6 ferramentas."""
    assert len(TOOL_MAP) == 6
    expected = {"semgrep", "trufflehog", "grype", "gitleaks", "trivy", "checkov"}
    assert set(TOOL_MAP.keys()) == expected


def test_tool_map_trivy_is_trivy_tool() -> None:
    """TOOL_MAP['trivy'] deve apontar para TrivyTool."""
    from app.tools.trivy import TrivyTool
    assert TOOL_MAP["trivy"] is TrivyTool


def test_tool_map_checkov_is_checkov_tool() -> None:
    """TOOL_MAP['checkov'] deve apontar para CheckovTool."""
    from app.tools.checkov import CheckovTool
    assert TOOL_MAP["checkov"] is CheckovTool


def test_team_plan_resolves_all_six_tools() -> None:
    """Plano 'team' deve resolver 6 tool classes do TOOL_MAP."""
    tool_names = PLAN_TOOLS["team"]
    resolved = [TOOL_MAP[name] for name in tool_names if name in TOOL_MAP]
    assert len(resolved) == 6, f"Expected 6 tools, got {len(resolved)}: {tool_names}"

"""Unit tests for AI enrichment layer (Phase 04).

Covers:
- load_groq_token utility
- GroqAIClient.explain_finding and suggest_fix
- AIEnricher async enrichment, silent fallback paths
- Top-N Critical/High selection
"""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.models import Finding, FindingCategory, ScanResult, Severity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_finding(
    fid: str = "test-1",
    severity: Severity = Severity.CRITICAL,
) -> Finding:
    return Finding(
        id=fid,
        title="SQL Injection",
        severity=severity,
        category=FindingCategory.SAST,
        file_path="app.py",
        line_number=10,
        snippet="cursor.execute(f'SELECT * FROM users WHERE id={user_id}')",
        description="SQL injection via f-string",
        tool=["semgrep"],
    )


def _make_scan_result(findings: list[Finding]) -> ScanResult:
    return ScanResult(
        project_path="/tmp/project",
        scanned_files=10,
        languages_detected=["python"],
        findings=findings,
        scan_duration_seconds=1.0,
        tools_used=["semgrep"],
    )


def _mock_200_response(content: str = "Test explanation") -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": content}}]
    }
    return mock_response


def _mock_batch_response(items: int = 1, explanation: str = "AI content", fix: str = "AI content") -> MagicMock:
    """Mock no formato batch [N] EXPLICACAO/CORRECAO para enrich_batch."""
    blocks = "\n\n".join(
        f"[{i}]\nEXPLICACAO: {explanation}\nCORRECAO: {fix}"
        for i in range(1, items + 1)
    )
    return _mock_200_response(blocks)


def _mock_200_response_enriched(explanation: str = "AI content", fix: str = "AI content") -> MagicMock:
    """Compat: single finding batch."""
    return _mock_batch_response(1, explanation, fix)


def _mock_status_response(status_code: int) -> MagicMock:
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = {}
    return mock_response


# ---------------------------------------------------------------------------
# Tests: load_groq_token
# ---------------------------------------------------------------------------

def test_load_groq_token_reads_from_config(tmp_path: Path) -> None:
    """Token is read correctly from a valid config file."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({"groq_token": "gsk_test"}))

    with patch("app.config.CONFIG_FILE", config_file):
        from app.config import load_groq_token
        result = load_groq_token()

    assert result == "gsk_test"


def test_load_groq_token_missing_file(tmp_path: Path) -> None:
    """Returns empty string when config file does not exist."""
    missing_file = tmp_path / "nonexistent.json"

    with patch("app.config.CONFIG_FILE", missing_file):
        from app.config import load_groq_token
        result = load_groq_token()

    assert result == ""


def test_load_groq_token_malformed_json(tmp_path: Path) -> None:
    """Returns empty string when config file contains invalid JSON."""
    config_file = tmp_path / "config.json"
    config_file.write_text("{not valid json")

    with patch("app.config.CONFIG_FILE", config_file):
        from app.config import load_groq_token
        result = load_groq_token()

    assert result == ""


# ---------------------------------------------------------------------------
# Tests: GroqAIClient.explain_finding
# ---------------------------------------------------------------------------

def test_explain_finding_success() -> None:
    """explain_finding returns non-empty string on 200 response."""
    from app.ai.groq_client import GroqAIClient

    client = GroqAIClient("gsk_valid_token")
    finding = _make_finding()

    with patch("httpx.post", return_value=_mock_batch_response(1, "This is dangerous because...", "")):
        result = client.explain_finding(finding)

    assert result == "This is dangerous because..."


# ---------------------------------------------------------------------------
# Tests: GroqAIClient.suggest_fix
# ---------------------------------------------------------------------------

def test_suggest_fix_success() -> None:
    """suggest_fix returns non-empty string on 200 response."""
    from app.ai.groq_client import GroqAIClient

    client = GroqAIClient("gsk_valid_token")
    finding = _make_finding()

    with patch("httpx.post", return_value=_mock_batch_response(1, "Explanation", "Use parameterised queries...")):
        result = client.suggest_fix(finding)

    assert result == "Use parameterised queries..."


# ---------------------------------------------------------------------------
# Tests: AIEnricher
# ---------------------------------------------------------------------------

def test_enricher_populates_both_fields() -> None:
    """_run() populates ai_explanation and ai_fix_suggestion on a finding."""
    from app.ai.enricher import AIEnricher

    finding = _make_finding()
    result = _make_scan_result([finding])

    completed = []

    with patch("httpx.post", return_value=_mock_batch_response(1)):
        enricher = AIEnricher("gsk_valid_token")
        enricher._run(result, None, lambda: completed.append(True))

    assert finding.ai_explanation == "AI content"
    assert finding.ai_fix_suggestion == "AI content"
    assert completed == [True]


def test_enricher_empty_token_no_call() -> None:
    """Empty token causes immediate on_complete with no HTTP call."""
    from app.ai.enricher import AIEnricher

    finding = _make_finding()
    result = _make_scan_result([finding])

    completed = []

    with patch("httpx.post") as mock_post:
        enricher = AIEnricher("")
        enricher.enrich_async(result, on_complete=lambda: completed.append(True))

    mock_post.assert_not_called()
    assert completed == [True]


def test_enricher_401_silent() -> None:
    """401 response leaves finding fields as None, no exception raised."""
    from app.ai.enricher import AIEnricher

    finding = _make_finding()
    result = _make_scan_result([finding])

    with patch("httpx.post", return_value=_mock_status_response(401)):
        enricher = AIEnricher("gsk_valid_token")
        enricher._run(result, None, None)

    assert finding.ai_explanation is None
    assert finding.ai_fix_suggestion is None


def test_enricher_429_silent() -> None:
    """429 response leaves finding fields as None, no exception raised."""
    from app.ai.enricher import AIEnricher

    finding = _make_finding()
    result = _make_scan_result([finding])

    with patch("httpx.post", return_value=_mock_status_response(429)):
        enricher = AIEnricher("gsk_valid_token")
        enricher._run(result, None, None)

    assert finding.ai_explanation is None
    assert finding.ai_fix_suggestion is None


def test_enricher_only_top10_critical_high() -> None:
    """Only top 10 Critical+High findings are enriched; Medium is skipped."""
    from app.ai.enricher import AIEnricher

    # 5 critical + 5 high + 5 medium = 15 total
    critical_findings = [_make_finding(f"c-{i}", Severity.CRITICAL) for i in range(5)]
    high_findings = [_make_finding(f"h-{i}", Severity.HIGH) for i in range(5)]
    medium_findings = [_make_finding(f"m-{i}", Severity.MEDIUM) for i in range(5)]

    all_findings = critical_findings + high_findings + medium_findings
    result = _make_scan_result(all_findings)

    enriched_ids = []

    def on_enriched(f: Finding) -> None:
        enriched_ids.append(f.id)

    with patch("httpx.post", return_value=_mock_batch_response(10)):
        enricher = AIEnricher("gsk_valid_token")
        enricher._run(result, on_enriched, None)

    # Only 10 (5 critical + 5 high) should be enriched
    assert len(enriched_ids) == 10
    # No medium finding should be enriched
    for f in medium_findings:
        assert f.ai_explanation is None
        assert f.ai_fix_suggestion is None
    # All critical and high should be enriched
    for f in critical_findings + high_findings:
        assert f.ai_explanation == "AI content"
        assert f.ai_fix_suggestion == "AI content"

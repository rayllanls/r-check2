"""AI enrichment service — populates Finding.ai_explanation and ai_fix_suggestion.

Runs in a daemon thread. Silent fallback when token is absent or Groq call fails.
"""
import threading
from typing import Callable, Optional
from app.ai.groq_client import GroqAIClient
from app.core.models import Finding, ScanResult, Severity

_TOP_N = 10
_HIGH_SEVERITIES = {Severity.CRITICAL, Severity.HIGH}


class AIEnricher:
    def __init__(self, token: str) -> None:
        self._token = token.strip() if token else ""

    def enrich_async(
        self,
        result: ScanResult,
        on_finding_enriched: Optional[Callable[[Finding], None]] = None,
        on_complete: Optional[Callable[[], None]] = None,
    ) -> None:
        if not self._token:
            if on_complete:
                on_complete()
            return
        t = threading.Thread(
            target=self._run,
            args=(result, on_finding_enriched, on_complete),
            daemon=True,
        )
        t.start()

    def _run(self, result, on_finding_enriched, on_complete):
        try:
            client = GroqAIClient(self._token)
        except ValueError:
            if on_complete:
                on_complete()
            return

        candidates = sorted(
            [f for f in result.findings if f.severity in _HIGH_SEVERITIES],
            key=lambda f: (f.severity != Severity.CRITICAL, f.severity != Severity.HIGH),
        )[:_TOP_N]

        try:
            results = client.enrich_batch(candidates)
        except Exception:
            results = [("", "")] * len(candidates)

        for finding, (explanation, fix) in zip(candidates, results):
            if explanation:
                finding.ai_explanation = explanation
            if fix:
                finding.ai_fix_suggestion = fix
            if on_finding_enriched:
                on_finding_enriched(finding)

        if on_complete:
            on_complete()

---
phase: 04-ai-explanations
plan: 01
subsystem: ai
tags: [groq, llama, ai, enrichment, async, threading, httpx]

# Dependency graph
requires:
  - phase: 03.1-trivy-scanner-backend
    provides: Finding and ScanResult dataclasses with ai_explanation/ai_fix_suggestion fields
provides:
  - load_groq_token() utility in app/config.py
  - GroqAIClient.suggest_fix() method for code fix suggestions
  - AIEnricher service with daemon thread enrichment and silent fallback
  - 10 unit tests covering all AI backend paths
affects: [04-02-gui-wiring, report-generation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "AIEnricher calls _run() in daemon thread via threading.Thread(daemon=True)"
    - "Silent fallback: empty token short-circuits before any HTTP call; non-empty API responses only assigned"
    - "Top-N selection: filter by severity in _HIGH_SEVERITIES then slice [:_TOP_N]"

key-files:
  created:
    - app/ai/enricher.py
    - tests/test_ai.py
  modified:
    - app/config.py
    - app/ai/groq_client.py

key-decisions:
  - "AIEnricher only assigns ai_explanation/ai_fix_suggestion when result is non-empty string — preserves None when API returns 401/429"
  - "GROQ_MODEL changed from llama-3.1-70b-versatile (deprecated) to llama-3.1-8b-instant"
  - "load_groq_token() in config.py — mirrors settings_screen._load_token() pattern for consistency"

patterns-established:
  - "Silent fallback pattern: if not self._token -> on_complete() immediately, no HTTP call"
  - "Enricher _run() callable directly in tests to avoid threading complexity"

requirements-completed: [AI-01, AI-02, AI-03, AI-04]

# Metrics
duration: 8min
completed: 2026-04-01
---

# Phase 04 Plan 01: AI Backend Layer Summary

**Groq/Llama 3.1 AI enrichment backend with AIEnricher daemon service, suggest_fix() on GroqAIClient, load_groq_token() utility, and 10 unit tests covering all silent fallback paths**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-01T14:35:00Z
- **Completed:** 2026-04-01T14:43:00Z
- **Tasks:** 1 (TDD: RED already done, GREEN + commit)
- **Files modified:** 4

## Accomplishments

- Fixed deprecated GROQ_MODEL constant (`llama-3.1-70b-versatile` -> `llama-3.1-8b-instant`)
- Added `load_groq_token()` utility to `app/config.py` — reads token from `~/.secscan/config.json`, returns `""` on any failure
- Added `suggest_fix()` method to `GroqAIClient` — returns code fix suggestion with 400 token limit
- Created `AIEnricher` service in `app/ai/enricher.py` — runs in daemon thread, enriches top-10 Critical/High findings, silent fallback on empty token or API errors
- 10 unit tests passing covering: token loading (3 tests), explain/suggest_fix success (2), enricher happy path (1), silent fallbacks (empty token, 401, 429), top-10 selection (1)

## Task Commits

1. **Task 1: Fix GROQ_MODEL, add load_groq_token, suggest_fix, AIEnricher, tests** - `7757d55` (feat)

## Files Created/Modified

- `app/config.py` - Added `load_groq_token()` function; fixed `GROQ_MODEL` constant
- `app/ai/groq_client.py` - Added `suggest_fix()` method mirroring `explain_finding()` pattern
- `app/ai/enricher.py` - New AIEnricher service with async enrichment, daemon thread, top-10 Critical/High selection
- `tests/test_ai.py` - 10 unit tests for all AI backend paths

## Decisions Made

- `AIEnricher._run()` only assigns fields when result is truthy — this correctly preserves `None` when API returns non-200 (401/429), matching test expectation that "fields remain None"
- `load_groq_token()` placed directly in `config.py` (not in `ai/` package) to follow the existing settings_screen token-read pattern

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] AIEnricher sets fields to "" instead of leaving them None on 401/429**

- **Found during:** Task 1 (GREEN phase)
- **Issue:** Initial implementation assigned `client.explain_finding(finding)` directly, which returns `""` on failure. Tests expected `finding.ai_explanation is None` after 401/429 response.
- **Fix:** Added truthiness check before assignment — only set field if result is non-empty string
- **Files modified:** `app/ai/enricher.py`
- **Verification:** `test_enricher_401_silent` and `test_enricher_429_silent` both pass
- **Committed in:** `7757d55` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential for correct silent fallback behavior. No scope creep.

## Issues Encountered

Pre-existing test failures in `tests/test_tools_grype.py`, `tests/test_tools_semgrep.py`, `tests/test_tools_trufflehog.py`, and `tests/test_orchestrator.py` exist due to uncommitted Phase 3.1 changes (tool field changed from `str` to `list[str]`). These are out of scope for this plan and documented as deferred issues.

## Known Stubs

None — AIEnricher is fully wired. Token loading reads from `~/.secscan/config.json`. HTTP calls use real httpx client. No mock data flows to consumers.

## Next Phase Readiness

- AI backend complete and tested — `AIEnricher`, `GroqAIClient.suggest_fix()`, `load_groq_token()` all importable and working
- Plan 02 can wire `AIEnricher` into GUI `ResultsScreen` and report generator
- No blockers

---
*Phase: 04-ai-explanations*
*Completed: 2026-04-01*

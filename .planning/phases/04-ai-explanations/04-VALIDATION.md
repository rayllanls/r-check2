---
phase: 4
slug: ai-explanations
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-01
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` |
| **Quick run command** | `python3 -m pytest tests/test_ai.py -q` |
| **Full suite command** | `python3 -m pytest tests/ -q --ignore=tests/test_language.py` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_ai.py -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -q --ignore=tests/test_language.py`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | AI-01 | unit | `python3 -m pytest tests/test_ai.py::test_token_persistence -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | AI-01 | unit | `python3 -m pytest tests/test_ai.py::test_token_read -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | AI-02 | unit | `python3 -m pytest tests/test_ai.py::test_groq_explain -q` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | AI-02 | unit | `python3 -m pytest tests/test_ai.py::test_groq_fix -q` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | AI-03 | unit | `python3 -m pytest tests/test_ai.py::test_enricher_async -q` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 2 | AI-04 | unit | `python3 -m pytest tests/test_ai.py::test_enricher_no_token -q` | ❌ W0 | ⬜ pending |
| 4-04-01 | 04 | 3 | AI-02 | manual | GUI smoke test | N/A | ⬜ pending |
| 4-04-02 | 04 | 3 | AI-02 | manual | Report HTML smoke test | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ai.py` — stubs for AI-01, AI-02, AI-03, AI-04
- [ ] `tests/conftest.py` — add fixture for mock Groq responses (existing file, add fixture)

*Existing pytest infrastructure covers the framework requirement.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AI text appears in results pane without freezing GUI | AI-02, AI-03 | Tkinter threading behavior not testable in unit tests | Run scan with valid token; verify explanation appears in modal within 5s without GUI freeze |
| Silent fallback when no token configured | AI-04 | GUI state not assertable in unit tests | Run scan without token; verify no error dialog, findings show normally |
| Token field in Settings persists across restart | AI-01 | Requires app restart lifecycle | Enter token, close app, reopen, verify field is pre-filled |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

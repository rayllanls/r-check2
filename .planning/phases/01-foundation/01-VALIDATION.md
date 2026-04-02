---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-29
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` (testpaths=tests, addopts=-v --tb=short) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | DATA-01 | unit | `pytest tests/test_scanner.py -x -q` | ✅ | ⬜ pending |
| 1-01-02 | 01 | 1 | SCAN-01 | unit | `pytest tests/test_scanner.py::test_semgrep -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | SCAN-02 | unit | `pytest tests/test_scanner.py::test_trufflehog -x -q` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | SCAN-03 | unit | `pytest tests/test_scanner.py::test_grype -x -q` | ❌ W0 | ⬜ pending |
| 1-02-01 | 02 | 1 | BACK-01 | unit | `pytest tests/test_scanner.py::test_gitleaks -x -q` | ❌ W0 | ⬜ pending |
| 1-02-02 | 02 | 1 | BACK-02 | unit | `pytest tests/test_scanner.py::test_binary_locator -x -q` | ❌ W0 | ⬜ pending |
| 1-02-03 | 02 | 2 | BACK-03 | unit | `pytest tests/test_scanner.py::test_orchestrator -x -q` | ❌ W0 | ⬜ pending |
| 1-03-01 | 03 | 2 | BACK-04 | unit | `pytest tests/test_language.py -x -q` | ✅ | ⬜ pending |
| 1-03-02 | 03 | 2 | BACK-05 | integration | `pytest tests/ -x -q` | ✅ | ⬜ pending |
| 1-03-03 | 03 | 2 | DATA-02 | unit | `pytest tests/test_ingestion.py -x -q` | ✅ | ⬜ pending |
| 1-03-04 | 03 | 2 | DATA-03 | unit | `pytest tests/test_ingestion.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_scanner.py` — add stubs for SCAN-01, SCAN-02, SCAN-03, BACK-01, BACK-02, BACK-03 fixture-based tests
- [ ] `tests/conftest.py` — shared fixtures: sample Finding objects, mock subprocess.run, fixture JSON outputs for all 4 scanners
- [ ] `tests/fixtures/` — create fixture JSON/NDJSON files for Semgrep, Trufflehog (NDJSON), Grype, Gitleaks outputs

*Existing `pytest.ini`, `tests/test_language.py`, `tests/test_ingestion.py` already present.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Scanner binary resolution in PyInstaller frozen mode | BACK-03 | Cannot run PyInstaller build in CI | Build with PyInstaller, run binary against fixture dir, verify findings returned |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

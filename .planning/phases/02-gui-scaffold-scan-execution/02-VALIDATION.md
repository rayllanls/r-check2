---
phase: 2
slug: gui-scaffold-scan-execution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pytest.ini` or `pyproject.toml` (existing) |
| **Quick run command** | `pytest tests/ -x -q --ignore=tests/test_scanner.py` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q --ignore=tests/test_scanner.py`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-W0-01 | W0 | 0 | ENV | manual | `python3 -c "import tkinter; import PIL"` | ❌ W0 | ⬜ pending |
| 2-W0-02 | W0 | 0 | — | unit | `pytest tests/test_gui.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-01 | 01 | 1 | GUI-04 | unit | `pytest tests/test_gui.py::test_app_window -x -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | GUI-04 | unit | `pytest tests/test_gui.py::test_dev_mode_badge -x -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | GUI-01 | unit | `pytest tests/test_gui.py::test_main_screen_widgets -x -q` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | GUI-01 | unit | `pytest tests/test_gui.py::test_folder_selection -x -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 1 | GUI-03 | unit | `pytest tests/test_gui.py::test_settings_screen -x -q` | ❌ W0 | ⬜ pending |
| 2-04-01 | 04 | 2 | GUI-02 | unit | `pytest tests/test_gui.py::test_progress_screen -x -q` | ❌ W0 | ⬜ pending |
| 2-04-02 | 04 | 2 | GUI-02 | unit | `pytest tests/test_gui.py::test_queue_polling -x -q` | ❌ W0 | ⬜ pending |
| 2-05-01 | 05 | 2 | GUI-05 | unit | `pytest tests/test_gui.py::test_cancel_scan -x -q` | ❌ W0 | ⬜ pending |
| 2-05-02 | 05 | 2 | GUI-05 | unit | `pytest tests/test_gui.py::test_results_summary -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_gui.py` — stubs for all GUI requirement tests (mocked CTk, no display needed)
- [ ] `tests/conftest.py` — shared fixtures including mock ScanOrchestrator and mock CTk root
- [ ] `sudo apt-get install -y python3-tk` — required for Tkinter (currently not installed)
- [ ] `pip install pillow` — required for CTkImage / logo rendering

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GUI never freezes during 2-min scan | GUI-02 | Requires visual inspection of running app | Run real scan on mid-size project, verify log updates appear every few seconds |
| Cancel terminates subprocess tree | GUI-02 | Requires process list inspection | Start scan, click Cancel, run `ps aux` to confirm no orphan scanner processes |
| Plan badge shows "DEV" visually | GUI-04 | Visual verification of CTk widget rendering | Launch app with `DEV_MODE=True`, confirm badge text and color in window |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

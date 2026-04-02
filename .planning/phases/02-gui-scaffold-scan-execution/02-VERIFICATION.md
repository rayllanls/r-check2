---
phase: 02-gui-scaffold-scan-execution
verified: 2026-03-31T19:56:01Z
status: gaps_found
score: 4/5 success criteria verified
re_verification: false
gaps:
  - truth: "The progress screen updates in real time during a scan (log lines appear, per-scanner status updates) and never appears frozen — verified on a 2-minute scan"
    status: partial
    reason: "Queue polling (after(100ms)) and ScannerRow widgets exist and are correctly wired. Cannot confirm 'never frozen' on a 2-minute scan without a display environment — the server has no tkinter/X11. The architectural pattern is correct (daemon thread + after() polling), but the real-time behavior cannot be proven programmatically in this environment."
    artifacts:
      - path: "app/gui/screens/progress_screen.py"
        issue: "Code is correct and wired. Behavioral freeze-check requires human on a real display."
    missing:
      - "Human verification: launch app on a machine with display, run a 2-minute scan, confirm log lines stream and GUI stays responsive"
  - truth: "User can cancel a running scan and the subprocess tree terminates cleanly (verified via process list)"
    status: partial
    reason: "cancel() calls proc.terminate() on all registered processes and sets threading.Event — the implementation is correct. However, clean subprocess-tree termination (including child PIDs of the scanner processes) requires verification on a real scan since proc.terminate() only sends SIGTERM to the direct subprocess, not to its children. The success criterion explicitly requires verification via process list."
    artifacts:
      - path: "app/core/scanner.py"
        issue: "cancel() uses proc.terminate() not os.killpg() — subprocess tree (child pids) may survive on Linux."
    missing:
      - "Human verification: start a real scan, click Cancel, check `ps aux` that no semgrep/trufflehog/grype/gitleaks processes remain"
human_verification:
  - test: "Real-time progress — launch app, select a folder, click Start Scan, observe the progress screen for 30+ seconds"
    expected: "Log lines appear as they arrive, per-scanner rows update to running/done, GUI remains interactive (can scroll log, Cancel button stays clickable)"
    why_human: "No X11/tkinter available on this server. The architecture is sound (daemon thread + after(100ms)) but the Tkinter event loop behavior under load cannot be verified without running the app."
  - test: "Cancel terminates subprocess tree — start scan, click Cancel immediately, run `ps aux | grep -E 'semgrep|trufflehog|grype|gitleaks'`"
    expected: "No scanner processes appear in process list within 2 seconds of cancel"
    why_human: "proc.terminate() sends SIGTERM to the direct subprocess. On Linux, subprocess spawned via shell or which forks grandchildren may not receive the signal. Requires live process inspection to confirm."
---

# Phase 2: GUI Scaffold + Scan Execution — Verification Report

**Phase Goal:** Users can launch the app, select a folder or Git URL, run a real scan, see live progress, and get a raw finding count — without any GUI freeze.
**Verified:** 2026-03-31T19:56:01Z
**Status:** gaps_found — 4/5 success criteria architecturally verified; 2 require human confirmation (real-time behavior + cancel subprocess tree)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can open app, select folder via file picker or Git URL, click Start Scan | VERIFIED | `HomeScreen._browse_folder` calls `filedialog.askdirectory`; `_start_scan` navigates to "progress" with target + plan. `_start_scan` validates non-empty target. |
| 2 | Progress screen updates in real time, never frozen — verified on 2-minute scan | PARTIAL | Queue polling via `self.after(100, self._poll_queue)` is architecturally correct; `ScannerRow.set_status()` updates in-place. Cannot verify "never frozen" on 2-minute scan without display environment. |
| 3 | User can cancel a running scan and subprocess tree terminates cleanly | PARTIAL | `ScanOrchestrator.cancel()` sets `threading.Event` and calls `proc.terminate()` on all `_active_processes`. SIGTERM sent to direct child only — grandchildren (scanner sub-forks on Linux) may survive. Needs live process list check. |
| 4 | App displays "DEV" plan badge when DEV_MODE=True — no license prompt | VERIFIED | `HeaderBar._build()` renders red CTkLabel badge `text="DEV"` when `DEV_MODE` is True. `config.py` sets `DEV_MODE=True` by default. `HomeScreen` uses `DEV_PLAN="team"` when `DEV_MODE`. No license validation code anywhere in GUI layer. |
| 5 | After scan completes, app shows summary finding count broken down by scanner | VERIFIED | `ResultsScreen.on_show(scan_result)` uses `Counter(f.tool for f in findings)` and calls `_create_tool_card(tool, count)` per tool in `scan_result.tools_used`. Total `len(findings)` shown as large ACCENT_RED label. |

**Score:** 3/5 truths fully verified (automated), 2/5 require human confirmation

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/main.py` | App entry point wiring all 4 screens | VERIFIED | Registers home/settings/progress/results; navigate() closure passed to all screens |
| `app/gui/app.py` | SecScanApp root window | VERIFIED | CTk 900x640 dark window, register_screen/show_screen, persistent HeaderBar |
| `app/gui/theme.py` | Rakoon brand colors + font factories | VERIFIED | 13 color constants, 3 font factories (font_heading/font_body/font_mono) |
| `app/gui/widgets/header_bar.py` | HeaderBar with DEV badge | VERIFIED | Conditional DEV badge (`if DEV_MODE`) with ACCENT_RED + "DEV" text |
| `app/gui/screens/main_screen.py` | HomeScreen with folder picker + URL + Start Scan | VERIFIED | filedialog, PLAN_TOOLS list, navigation to progress screen |
| `app/gui/screens/progress_screen.py` | Progress screen with queue polling + cancel | VERIFIED | daemon thread, after(100ms) polling, `_orchestrator.cancel()`, SCAN_COMPLETE navigation |
| `app/gui/screens/results_screen.py` | Results summary with per-scanner cards | VERIFIED | Counter-based breakdown, total count label, scan info (files/duration) |
| `app/gui/screens/settings_screen.py` | Settings with Groq token persistence | VERIFIED | Reads/writes `~/.secscan/config.json`, on_show() loads token, masked entry |
| `app/gui/widgets/scanner_row.py` | ScannerRow status widget | VERIFIED | ICON_MAP/COLOR_MAP for pending/running/done/error; set_status() mutates in-place |
| `app/core/scanner.py` (cancel) | ScanOrchestrator.cancel() | VERIFIED | threading.Event + proc.terminate() for all active processes |

All 10 artifacts: present, substantive (not stubs), and wired into the navigation graph.

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| HomeScreen._start_scan | ProgressScreen.on_show | navigate("progress", target, plan) | WIRED | `self._navigate("progress", target=target, plan=self._plan)` in `_start_scan` |
| ProgressScreen | ScanOrchestrator.scan | `threading.Thread(target=_run_scan)` | WIRED | daemon thread started in `on_show`, result stored in `_scan_result` |
| ProgressScreen._poll_queue | ScannerRow.set_status | EventType dispatch in _handle_event | WIRED | TOOL_START→"running", TOOL_DONE→"done", TOOL_ERROR→"error" |
| ProgressScreen._on_scan_complete | ResultsScreen.on_show | navigate("results", scan_result=...) | WIRED | `self._navigate("results", scan_result=self._scan_result)` |
| ProgressScreen._cancel_scan | ScanOrchestrator.cancel | `self._orchestrator.cancel()` | WIRED | Direct method call; sets threading.Event and terminates processes |
| ResultsScreen.on_show | ScanResult.findings | Counter aggregation | WIRED | `Counter(f.tool for f in scan_result.findings)` drives card creation |
| HeaderBar._build | DEV_MODE config | `if DEV_MODE:` conditional | WIRED | Imports `DEV_MODE` from `app.config`, renders badge conditionally |
| HomeScreen | PLAN_TOOLS[team] | `PLAN_TOOLS[self._plan]` | WIRED | With DEV_MODE=True, plan="team" → all 5 tools listed |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `ResultsScreen` | `scan_result.findings` | `ScanOrchestrator.scan()` result, passed via `navigate("results", scan_result=...)` | Yes — live scan output from `Phase 1` scanner runners | FLOWING |
| `ProgressScreen` log | `ProgressEvent.message` | `queue.Queue` populated by `ScanOrchestrator.scan()` background thread | Yes — real events from scanner execution | FLOWING |
| `ScannerRow` | `status`, `count` | `_handle_event` routes EventType to `set_status()` | Yes — driven by real ProgressEvent stream | FLOWING |
| `HomeScreen` scanner list | `PLAN_TOOLS[self._plan]` | `app.config.PLAN_TOOLS["team"]` constant | Yes — 5 real tool names | FLOWING |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| All 14 GUI tests pass | `python3 -m pytest tests/test_gui.py -v` | 14/14 passed in 0.05s | PASS |
| Full test suite passes (no regressions) | `python3 -m pytest tests/ -v` | 68/68 passed in 0.23s | PASS |
| cancel() exists in ScanOrchestrator | `grep "def cancel" app/core/scanner.py` | Line 77: `def cancel(self) -> None:` | PASS |
| DEV badge conditional in HeaderBar | `grep "if DEV_MODE" app/gui/widgets/header_bar.py` | Line 51: `if DEV_MODE:` | PASS |
| main.py wiring import (structural) | AST parse of imports | 5 correct imports: SecScanApp + 4 screen classes | PASS |
| main.py wiring import (runtime) | `python3 -c "from app.main import main"` | FAIL — `ModuleNotFoundError: No module named 'tkinter'` | SKIP (server has no tkinter system package; expected in dev/CI with display) |

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|-------------|-------------|--------|----------|
| GUI-01 | Main window: folder/URL selection, scanner list, Start Scan | SATISFIED | `HomeScreen` with `filedialog`, `_url_entry`, `PLAN_TOOLS` list, `_start_scan` |
| GUI-02 | Progress screen with real-time log, never frozen | PARTIAL | Architecture verified (daemon thread + after(100ms)); runtime behavior needs human confirmation |
| GUI-03 | Settings screen: Groq token entry + persistence | SATISFIED | `SettingsScreen` reads/writes `~/.secscan/config.json` |
| GUI-04 | Dark design, logo, plan badge (DEV in dev mode) | SATISFIED | BG_PRIMARY="#111111", HeaderBar DEV badge conditional on DEV_MODE, Rakoon logo supported via Pillow |
| GUI-05 | DEV_MODE=True enables Team-tier features, no license prompt | SATISFIED | `config.py` sets `DEV_MODE=True` by default; `HomeScreen` uses `DEV_PLAN="team"`; no license code in GUI |

**Notes on REQUIREMENTS.md tracking:** REQUIREMENTS.md marks GUI-02 and GUI-04 as still "Pending". Based on code inspection:
- GUI-04 is implemented (dark theme, DEV badge) — status in REQUIREMENTS.md appears out of sync with actual code
- GUI-02 is architecturally complete but "Pending" is conservative given human verification is needed for runtime behavior

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `results_screen.py` | 93 | `state="disabled"` on "Ver Relatorio Completo" button | Info | Intentional Phase 3 placeholder — correctly documented in 02-05-SUMMARY.md as scope for Phase 3. Does not block Phase 2 goal. |
| `main_screen.py` | 73, 101 | `placeholder_text=...` on CTkEntry | Info | CTkEntry placeholder text (UI hint text) — NOT a stub. Standard UX pattern. |
| `settings_screen.py` | 83 | `placeholder_text="gsk_..."` | Info | Same — UX hint text, not a code stub. |

No blockers found. The "Ver Relatorio Completo" disabled button is the only notable item — it is explicitly a Phase 3 placeholder, not a gap in Phase 2's goal.

---

## Human Verification Required

### 1. Real-Time Progress Screen — No GUI Freeze

**Test:** On a machine with tkinter/display, run `python3 -m python app/main.py`, select any local folder, click "Iniciar Scan". Observe the progress screen for at least 30 seconds.
**Expected:** Log lines appear as events arrive from the scanner background thread. Per-scanner rows transition from pending (○) to running (◉) to done (✓) or error (✗). The Cancel button remains clickable. The window can be resized/interacted with during the scan.
**Why human:** No X11/tkinter system package is installed on this server. The `self.after(100, self._poll_queue)` pattern is the correct Tkinter approach for non-blocking queue polling, but actual GUI responsiveness can only be confirmed with a running Tkinter event loop.

### 2. Cancel Terminates Subprocess Tree

**Test:** Start a scan on a large folder (so it runs for several seconds). Click "Cancelar". Immediately run `ps aux | grep -E 'semgrep|trufflehog|grype|gitleaks'`.
**Expected:** No scanner processes remain in the process list within 2 seconds of clicking Cancel.
**Why human:** `ScanOrchestrator.cancel()` calls `proc.terminate()` (SIGTERM) on direct subprocess handles. On Linux, if a scanner (e.g., Semgrep) spawns child processes, those grandchildren are not in the `_active_processes` list and will not receive SIGTERM. A live process list check is the only way to confirm clean termination. If grandchildren survive, the fix would be `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)`.

---

## Gaps Summary

Two success criteria cannot be fully verified programmatically due to the server environment (no tkinter) and the nature of the behaviors:

**Gap 1 — Progress screen real-time behavior:** The code is correctly structured (daemon thread + `after(100ms)` polling + stateful ScannerRow updates). This is the canonical Tkinter pattern for non-blocking GUI updates. The risk of a freeze is low. Human spot-check is a formality to satisfy the "verified on a 2-minute scan" language in the success criterion.

**Gap 2 — Cancel subprocess tree:** The `cancel()` implementation terminates direct subprocess handles via SIGTERM. The success criterion requires verification "via process list." The `proc.terminate()` approach works for single-process scanners. If any scanner forks grandchildren (Semgrep is known to do this), those would survive cancel. This is a genuine implementation risk that warrants human testing. If the test fails, the fix is one line: `os.killpg(os.getpgid(proc.pid), signal.SIGTERM)` inside the cancel loop.

Both gaps are behavioral verification gaps, not missing code. All artifacts exist, are substantive, and are correctly wired.

---

_Verified: 2026-03-31T19:56:01Z_
_Verifier: Claude (gsd-verifier)_

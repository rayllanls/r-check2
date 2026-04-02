---
phase: "02-gui-scaffold-scan-execution"
plan: "02-03"
subsystem: "GUI screens"
tags: ["gui", "customtkinter", "screens", "settings", "home"]
dependency_graph:
  requires:
    - "02-02"      # theme.py, app.py, widgets package
    - "01-*"       # app.config (DEV_MODE, DEV_PLAN, PLAN_TOOLS, CONFIG_DIR, CONFIG_FILE)
  provides:
    - "app/gui/screens/main_screen.py — HomeScreen"
    - "app/gui/screens/settings_screen.py — SettingsScreen"
  affects:
    - "02-05"      # main.py wiring registers these screens with SecScanApp
tech_stack:
  added: []
  patterns:
    - "nav_callback: Callable pattern — screens receive navigation function, no circular imports"
    - "on_show(**kwargs) hook — allows screens to refresh data when navigated to"
    - "PLAN_TOOLS[plan] dynamic scanner list — DEV_MODE drives team-tier display"
key_files:
  created:
    - "app/gui/screens/__init__.py"
    - "app/gui/screens/main_screen.py"
    - "app/gui/screens/settings_screen.py"
    - "app/gui/theme.py"
    - "app/gui/widgets/__init__.py"
    - "app/config.py"
  modified: []
decisions:
  - "nav_callback passed at construction rather than imported — avoids circular imports between screens and app.py"
  - "PLAN_TOOLS[DEV_PLAN] used when DEV_MODE=True — matches existing config.py pattern"
  - "on_show() on SettingsScreen loads token fresh each visit — no stale token risk"
  - "_save_token merges into existing config JSON — preserves future config keys (groq_token is one field)"
metrics:
  duration: "2 min"
  completed_date: "2026-03-31"
  tasks_completed: 2
  files_created: 6
  files_modified: 0
---

# Phase 02 Plan 03: HomeScreen + SettingsScreen Summary

HomeScreen and SettingsScreen implemented — folder picker, URL entry, PLAN_TOOLS-driven scanner list, Start Scan navigation, and Groq token persistence to ~/.secscan/config.json.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | HomeScreen with folder picker, URL entry, scanner list, Start Scan | 6b55b7a | app/gui/screens/main_screen.py, app/gui/theme.py, app/gui/widgets/__init__.py, app/gui/screens/__init__.py, app/config.py |
| 2 | SettingsScreen with Groq token persistence | a0c82c0 | app/gui/screens/settings_screen.py |

## What Was Built

### HomeScreen (app/gui/screens/main_screen.py)

`HomeScreen(ctk.CTkFrame)` implements the primary scan target input screen:

- **Folder picker**: `filedialog.askdirectory` fills `_path_entry` from OS file picker.
- **URL entry**: `_url_entry` accepts Git URLs as scan target.
- **Scanner list**: Dynamically built from `PLAN_TOOLS[self._plan]`. With `DEV_MODE=True`, `self._plan = DEV_PLAN = "team"` — all five tools displayed (trufflehog, gitleaks, semgrep, grype, checkov).
- **Start Scan button**: Validates non-empty target, calls `self._navigate("progress", target=target, plan=self._plan)`.
- **Settings link**: Calls `self._navigate("settings")`.
- **nav_callback pattern**: No circular imports — navigation function injected at construction time.

### SettingsScreen (app/gui/screens/settings_screen.py)

`SettingsScreen(ctk.CTkFrame)` handles Groq API token configuration:

- **on_show()**: Called by SecScanApp when navigating to this screen — loads current token from disk.
- **_load_token()**: Reads `~/.secscan/config.json`, extracts `groq_token` field; handles missing file and parse errors silently.
- **_save_token()**: Merges `groq_token` into existing JSON (preserves other keys), shows "Salvo!" feedback for 2 seconds.
- **Token masking**: `show="*"` hides token characters in entry field.
- **Back button**: `self._navigate("home")`.

## Deviations from Plan

### Supporting Files Added

**1. [Rule 3 - Blocking] Created prerequisite files for parallel execution**
- **Found during:** Task 1 setup
- **Issue:** This worktree runs in parallel with plan 02-02 which creates theme.py, widgets/__init__.py, and app.py. Since those files don't exist yet in this worktree branch, screens cannot be imported or tested.
- **Fix:** Created `app/gui/theme.py`, `app/gui/widgets/__init__.py`, `app/gui/screens/__init__.py`, and copied `app/config.py` into the worktree. These files match the 02-02 plan spec exactly (same color constants, same font factories). The orchestrator merge will resolve any conflicts.
- **Files created:** app/gui/theme.py, app/gui/widgets/__init__.py, app/gui/screens/__init__.py, app/config.py
- **Commit:** 6b55b7a

### Import Verification Environment Constraint

The plan's verification step `python3 -c "from app.gui.screens.main_screen import HomeScreen"` cannot run in this CI environment because `tkinter` is not available as a system package (headless server, no Tk display libraries). Both files were verified via:
- AST parse (syntax correctness)
- All acceptance criteria grep checks (100% pass)
- Full pytest suite (43/43 pass)

## Known Stubs

None. Both screens have all UI and logic wired:
- HomeScreen scanner list reads live from `PLAN_TOOLS[plan]` (no mock data)
- SettingsScreen reads/writes real `~/.secscan/config.json` (no placeholder path)

## Self-Check: PASSED

Files exist:
- FOUND: app/gui/screens/main_screen.py
- FOUND: app/gui/screens/settings_screen.py
- FOUND: app/gui/theme.py
- FOUND: app/gui/widgets/__init__.py

Commits:
- FOUND: 6b55b7a — feat(02-03): implement HomeScreen
- FOUND: a0c82c0 — feat(02-03): implement SettingsScreen

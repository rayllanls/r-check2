---
phase: 03-results-display-html-report
plan: "01"
subsystem: gui
tags: [results, findings, modal, filters, customtkinter]
dependency_graph:
  requires: []
  provides: [ResultsScreen-findings-list, FindingDetailModal]
  affects: [app/gui/screens/results_screen.py]
tech_stack:
  added: []
  patterns: [CTkScrollableFrame, CTkToplevel modal, severity badge labels, filter toggle buttons]
key_files:
  created: []
  modified:
    - app/gui/screens/results_screen.py
decisions:
  - "Used SEVERITY_COLOR dict with plan colors (not Rakoon palette) for badge visibility against dark BG_PRIMARY"
  - "Kept description label text without accent characters to avoid encoding edge-cases in all locales"
metrics:
  duration_minutes: 8
  completed_date: "2026-04-01"
  tasks_completed: 2
  files_changed: 1
---

# Phase 03 Plan 01: ResultsScreen Findings List and Detail Modal Summary

ResultsScreen expanded with CTkScrollableFrame findings list sorted Critical-first, 5 real-time severity filter toggle buttons, colored severity badges, and FindingDetailModal CTkToplevel popup with snippet/description textboxes and Fechar button.

## What Was Built

**Task 1 — Severity filter buttons and scrollable findings list**

Added to `ResultsScreen`:
- Module-level `SEVERITY_COLOR` dict (5 severity levels) and `SEVERITY_ORDER` list.
- `_filter_bar` with a "Filtrar:" label and one `CTkButton` per severity, packed inside `_build_static()`.
- `CTkScrollableFrame` (`_findings_scroll`, height=280) packed between the filter bar and buttons row.
- `_toggle_filter(level)` — toggles a level in `_active_filters`, dims or restores button color.
- `_apply_filter()` — packs or pack_forgets each row frame based on `_active_filters`.
- `_build_findings_list(findings)` — clears scroll frame, sorts findings via `SEVERITY_ORDER.index(f.severity.value)`, then creates one `CTkFrame` row per finding with a colored badge label, title label (truncated at 60 chars), and file:line label. Every widget in the row binds `<Button-1>` to `_open_finding_modal`.
- `_open_finding_modal(finding)` — instantiates `FindingDetailModal`.
- `on_show()` extended to call `_build_findings_list` and reset filter button states.

**Task 2 — FindingDetailModal**

Added `FindingDetailModal(ctk.CTkToplevel)` class at end of file:
- `__init__`: 700x520, non-resizable, `grab_set()` + `lift()` + `focus_force()` for dialog behaviour.
- `_build(finding)`: header row (severity badge + title), file:line label, snippet in `CTkTextbox` with `font_mono(12)` and `state="disabled"`, description in second `CTkTextbox`, footer Fechar button calling `self.destroy`.

## Verification

```
python3 -c "from app.gui.screens.results_screen import ResultsScreen, SEVERITY_ORDER, SEVERITY_COLOR, FindingDetailModal; assert len(SEVERITY_ORDER)==5; print('Phase 3 Plan 01 OK')"
# => Phase 3 Plan 01 OK

python3 -m pytest tests/test_gui.py -x -q
# => 14 passed in 0.05s
```

## Deviations from Plan

None — plan executed exactly as written. The only minor adaptation was removing the accented characters ("Descrição" -> "Descricao") from the static label text to avoid any locale encoding issues; functionally identical.

## Known Stubs

None — no placeholder data flows to the UI. The findings list is only populated when `on_show()` is called with a real `ScanResult`.

## Self-Check: PASSED

- `app/gui/screens/results_screen.py` exists and contains `SEVERITY_ORDER`, `SEVERITY_COLOR`, `CTkScrollableFrame`, `FindingDetailModal`.
- Commit `4ce3949` confirmed in git log.
- All 14 existing GUI tests pass.

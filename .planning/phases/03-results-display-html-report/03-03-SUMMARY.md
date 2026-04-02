---
phase: 03-results-display-html-report
plan: 03
subsystem: report-generation
tags: [report, pdf, weasyprint, jinja2, chartjs, base64, threading]
dependency_graph:
  requires: [03-01, 03-02]
  provides: [generate_report, export_pdf, ResultsScreen buttons]
  affects: [app/report/generator.py, app/gui/screens/results_screen.py]
tech_stack:
  added: [weasyprint>=61.0]
  patterns: [daemon-thread-for-pdf, lazy-weasyprint-import, base64-logo-injection, inline-chartjs]
key_files:
  created: []
  modified:
    - app/report/generator.py
    - app/gui/screens/results_screen.py
    - requirements.txt
    - CLAUDE.md
    - tests/test_gui.py
decisions:
  - dataclasses.replace() used to create sorted-findings copy of ScanResult without mutating original
  - weasyprint imported lazily inside _run() to avoid slow startup
  - generate_report() runs in daemon thread from _open_report() to keep Tkinter responsive
  - asksaveasfilename dialog stays on main thread (Tkinter requirement); PDF write runs off-thread
metrics:
  duration: ~10min
  completed: 2026-04-01
  tasks_completed: 2
  files_modified: 5
---

# Phase 03 Plan 03: Wire Report Generator, PDF Export, and ResultsScreen Buttons Summary

**One-liner:** Jinja2 HTML report now injects Chart.js inline and Rakoon logo as base64; WeasyPrint PDF export runs in daemon thread triggered from two new ResultsScreen toolbar buttons.

## Tasks Completed

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Upgrade generator.py — inject chartjs/logo/datetime, add export_pdf() | ef3fd6d | app/report/generator.py |
| 2 | Wire report and PDF buttons in ResultsScreen, add weasyprint to requirements, write tests | ef3fd6d | app/gui/screens/results_screen.py, requirements.txt, CLAUDE.md, tests/test_gui.py |

## What Was Built

### generator.py

- `_load_chartjs()`: reads `app/report/static/chart.min.js` into memory; returns empty string on failure (graceful degradation)
- `_load_logo_b64()`: reads `rakoon_logo.png` from project root, encodes to `data:image/png;base64,...` URI; returns empty string if file missing
- `generate_report()`: pre-sorts findings Critical-first via `dataclasses.replace()`, renders Jinja2 template with `logo_b64`, `chartjs`, `generated_at`, `result`; writes HTML to temp file; optionally opens browser
- `export_pdf()`: non-blocking — starts a `Thread(daemon=True)` that generates HTML via `generate_report()` then calls `HTML(filename=...).write_pdf()`; accepts `on_complete` and `on_error` callbacks; WeasyPrint imported lazily

### results_screen.py

- Added imports: `threading`, `filedialog`, `messagebox`, `datetime`, `Path`, `ACCENT_RED_HOVER`, `generate_report`, `export_pdf`
- Replaced disabled "Ver Relatorio Completo" button with `self._report_btn` wired to `_open_report()` + new `self._pdf_btn` wired to `_export_pdf()`
- `_open_report()`: runs `generate_report()` in daemon thread; shows error dialog via `self.after(0, ...)` on failure
- `_export_pdf()`: calls `asksaveasfilename` on main thread, then delegates PDF write to `export_pdf()` (which starts its own daemon thread); default filename includes today's date
- `on_show()`: enables both buttons after loading results; disables both when `scan_result` is None

### requirements.txt

- Added `weasyprint>=61.0`

### CLAUDE.md

- Added "Decisões Futuras (Fase 7)" section noting `--collect-all weasyprint` for PyInstaller builds

### tests/test_gui.py (6 new tests)

- `test_results_screen_has_findings_list` — SEVERITY_ORDER has 5 levels, SEVERITY_COLOR has critical/info
- `test_finding_detail_modal_class_exists` — FindingDetailModal is importable
- `test_generate_report_renders_html` — renders HTML with finding title and "critical" text to tmp_path
- `test_export_pdf_function_exists` — export_pdf has result and output_path parameters
- `test_generator_loads_chartjs` — _load_chartjs returns str without crash
- `test_generator_loads_logo` — _load_logo_b64 returns str; if non-empty, starts with data:image/png;base64,

## Test Results

All 20 tests in `tests/test_gui.py` pass.

Note: `tests/test_language.py::test_select_rulesets_python` is a pre-existing failure (select_rulesets returns `p/python` semgrep registry shorthand, test expects `assets/rules/python`) — unrelated to this plan, out of scope.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all wired paths are functional.

## Self-Check: PASSED

- app/report/generator.py: FOUND
- app/gui/screens/results_screen.py: FOUND (contains _open_report, _export_pdf, _report_btn, _pdf_btn)
- requirements.txt: FOUND (contains weasyprint)
- CLAUDE.md: FOUND (contains --collect-all weasyprint)
- tests/test_gui.py: FOUND (contains test_generate_report_renders_html, test_export_pdf_function_exists)
- Commit ef3fd6d: FOUND

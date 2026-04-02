---
phase: 03-results-display-html-report
plan: 02
subsystem: report
tags: [html, jinja2, chartjs, offline, report]
dependency_graph:
  requires: [app/core/models.py, app/report/generator.py]
  provides: [app/report/templates/report.html, app/report/static/chart.min.js]
  affects: [app/report/generator.py]
tech_stack:
  added: [Chart.js 4.4.0]
  patterns: [Jinja2 template, inline base64 logo, offline-first JS bundling, expandable table rows]
key_files:
  created:
    - app/report/static/chart.min.js
  modified:
    - app/report/templates/report.html
decisions:
  - D-08: Light theme (white background, #f5f5f5 body) per project spec
  - D-10: Zero CDN calls — Chart.js injected inline via {{ chartjs }} Jinja2 variable
  - D-11: Severity colors critical=#e63946, high=#ff6b35, medium=#ffd166, low=#06d6a0, info=#888888
  - D-12: Findings table columns Severidade/Titulo/Ferramenta/Arquivo:Linha/Snippet
metrics:
  duration: ~5 minutes
  completed: "2026-04-01"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 03 Plan 02: HTML Report Template with Offline Chart.js Summary

Complete Jinja2 report template with doughnut chart (Chart.js 4.4.0 bundled offline), summary severity cards, and expandable findings table — zero CDN calls, works via file:// URI.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Download Chart.js and create static directory | ccfa362 | app/report/static/chart.min.js |
| 2 | Write full Jinja2 report.html template | ccfa362 | app/report/templates/report.html |

## What Was Built

### app/report/static/chart.min.js
- Chart.js v4.4.0 minified UMD build downloaded from cdn.jsdelivr.net
- File size: 205,222 bytes (well above the 200KB expected for real Chart.js 4.x)
- Contains `Chart` constructor confirming it is the real library, not a stub

### app/report/templates/report.html
Complete professional Jinja2 template replacing the stub:

- **Header:** conditional Rakoon logo (`{% if logo_b64 %}`), project path, generated_at timestamp, scanned_files count, total findings count (large red number)
- **Summary cards:** five cards (Critical / High / Medium / Low / Info) with D-11 severity colors
- **Doughnut chart:** Chart.js canvas with `type: 'doughnut'`, `cutout: '65%'`, D-11 colors, no legend (custom legend aside), Chart.js injected via `{{ chartjs }}` inline variable
- **Findings table:** columns Severidade / Titulo / Ferramenta / Arquivo:Linha / Snippet; badges per severity; description truncated at 120 chars; snippet toggle via `toggleSnippet()` JS function
- **Offline-safe:** zero CDN references confirmed (`grep -c "cdn." report.html` = 0); Chart.js injected from `chartjs` template variable supplied by generator.py (Plan 03 wires this)
- **Print/PDF:** `@media print` reveals all snippet-box elements for WeasyPrint

## Verification Results

| Check | Result |
|-------|--------|
| chart.min.js exists | PASS |
| chart.min.js > 1KB (205KB) | PASS |
| chart.min.js contains "Chart" | PASS (4 occurrences) |
| Jinja2 template parses OK | PASS |
| Zero CDN URLs in report.html | PASS (0 matches) |
| doughnut + toggleSnippet + badge-critical present | PASS (5 matches) |
| {{ chartjs }} injection present | PASS |
| {% if logo_b64 %} conditional | PASS |
| {{ generated_at }} variable | PASS |
| D-11 color #e63946 present | PASS (5 occurrences) |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

The template uses `{{ chartjs }}` which must be passed by generator.py. The current generator.py (pre-Plan 03) does not yet pass this variable — rendering the template directly will raise `UndefinedError`. Plan 03-03 (or the next generator.py update) must add:
- `logo_b64` — base64 data URI of rakoon_logo.png
- `chartjs` — contents of app/report/static/chart.min.js
- `generated_at` — datetime string

This is intentional and documented in the plan ("Plan 03 fixes generator.py").

## Self-Check: PASSED

- `app/report/static/chart.min.js` — EXISTS (205,222 bytes)
- `app/report/templates/report.html` — EXISTS (357 lines added)
- Commit `ccfa362` — EXISTS (confirmed via git log)

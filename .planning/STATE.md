---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: verifying
stopped_at: Completed 04-02-PLAN.md
last_updated: "2026-04-01T19:49:02.966Z"
last_activity: 2026-04-01
progress:
  total_phases: 8
  completed_phases: 5
  total_plans: 17
  completed_plans: 17
  percent: 43
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-29)

**Core value:** Find serious security flaws in AI-generated code before a bad actor does — locally, privately, no security expertise required.
**Current focus:** Phase 04 — ai-explanations

## Current Position

Phase: 04 (ai-explanations) — EXECUTING
Plan: 2 of 2
Status: Phase complete — ready for verification
Last activity: 2026-04-01

Progress: [███░░░░░░░] 43%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: -
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: n/a
- Trend: n/a

*Updated after each plan completion*
| Phase 01 P01 | 2min | 2 tasks | 6 files |
| Phase 01 P03 | 10 | 2 tasks | 9 files |
| Phase 01 P04 | 2 | 1 tasks | 2 files |
| Phase 02 P03 | 2 | 2 tasks | 6 files |
| Phase 02-gui-scaffold-scan-execution P02-05 | 15 | 2 tasks | 6 files |
| Phase 03 P01 | 8 | 2 tasks | 1 files |
| Phase 03 P02 | 5 | 2 tasks | 2 files |
| Phase 03 P03 | 10 | 2 tasks | 4 files |
| Phase 03.1 P01 | 5 | 1 tasks | 4 files |
| Phase 03.1 P02 | 2 | 1 tasks | 6 files |
| Phase 03.1 P03 | 5 | 2 tasks | 3 files |
| Phase 04-ai-explanations P01 | 8 | 1 tasks | 4 files |
| Phase 04-ai-explanations P04-02 | 3 | 2 tasks | 2 files |

## Accumulated Context

### Roadmap Evolution

- Phase 3.1 inserida após Phase 3: Trivy scanner backend — 5º scanner (SCA + IaC + secrets, complementa Grype) (URGENT)

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Init]: DEV_MODE=True unlocks Team plan — no license code until Phase 6
- [Init]: PyInstaller --onedir (not --onefile) — onefile causes 10-30s startup on Windows
- [Init]: Semgrep rules bundled locally in assets/rules/ — --config auto breaks offline use
- [Init]: queue.Queue + root.after(100ms) threading pattern mandatory from Phase 1 — retrofitting costs 2-3 days
- [Init]: BinaryLocator with sys._MEIPASS fallback established in Phase 1 — all runners must use it
- [Phase 01]: MEIPASS check first in resolve_binary() — vendor dir at dev path doesn't exist in frozen PyInstaller mode
- [Phase 01]: Fixture files in tests/fixtures/ drive all scanner tests without live binaries in CI
- [Phase 01-03]: Semgrep uses local assets/rules/ paths only — no --config auto or --config r/ for offline support
- [Phase 01-03]: Grype Negligible severity maps to Severity.INFO; uses dir: prefix for directory scanning
- [Phase 01-03]: No check=True in subprocess.run — Semgrep exits 1 with findings, Grype exits non-zero on severity thresholds
- [Phase 01-04]: Scanner kept as backward-compat wrapper around ScanOrchestrator — no test regressions, legacy callback API preserved
- [Phase 01-04]: Only coarse events emitted (TOOL_START/DONE/ERROR/SCAN_COMPLETE) — no per-finding events to avoid Tkinter queue overflow
- [Phase 01-04]: progress_queue=None default creates internal queue — Phase 2 GUI must always pass a queue to receive events
- [Phase 02-03]: nav_callback injected at screen construction — avoids circular imports between screens and app.py
- [Phase 02-03]: on_show() hook on SettingsScreen reloads token each visit — no stale token risk
- [Phase 02-gui-scaffold-scan-execution]: ResultsScreen uses Counter(f.tool for f in findings) to aggregate per-scanner counts from ScanResult
- [Phase 02-gui-scaffold-scan-execution]: ProgressScreen.on_show() starts scan in daemon Thread + schedules after(100ms) polling immediately
- [Phase 02-gui-scaffold-scan-execution]: Navigation wiring: single navigate() closure in main() captures app instance, passed as nav_callback to all screens
- [Phase 03]: ResultsScreen filter uses pack/pack_forget (not CTkScrollableFrame rebuild) — avoids flicker on toggle
- [Phase 03]: generator.py lazy-imports WeasyPrint inside daemon thread — avoids 2-3s startup penalty at GUI launch
- [Phase 03]: chart.min.js bundled at app/report/static/ — inlined via {{ chartjs }} in template, zero CDN calls
- [Phase 03]: export_pdf() accepts on_complete/on_error callbacks for future GUI feedback hooks
- [Phase 03.1]: TrivyTool uses UPPERCASE SEVERITY_MAP; no check=True in subprocess; PASS misconfigs filtered; StartLine defaults to 0 via 'or 0'
- [Phase 03.1]: CheckovTool severity hardcoded to MEDIUM — OSS Checkov returns null severity without Prisma Cloud key
- [Phase 03.1]: _normalize_to_blocks dispatcher abstracts 3 polymorphic Checkov output shapes before parsing
- [Phase 03.1]: PLAN_TOOLS['team'] tool order: trufflehog, gitleaks, semgrep, grype, trivy, checkov (secrets, SAST, SCA, IaC)
- [Phase 03.1]: max_workers=6 matches 6 registered tools — no thread starvation in team plan
- [Phase 04-ai-explanations]: AIEnricher only assigns ai_explanation/ai_fix_suggestion when result is non-empty string — preserves None when API returns 401/429
- [Phase 04-ai-explanations]: GROQ_MODEL changed from llama-3.1-70b-versatile (deprecated) to llama-3.1-8b-instant
- [Phase 04-ai-explanations]: FindingDetailModal height increased from 700x520 to 700x750 for AI sections
- [Phase 04-ai-explanations]: has_token flag controls placeholder text in FindingDetailModal: Buscando... vs IA indisponivel
- [Phase 04-ai-explanations]: AI enrichment deferred via self.after(0) in on_show() to prevent race with Tkinter rendering

### Pending Todos

None yet.

### Blockers/Concerns

- [Pre-Phase 1]: Scanner binary versions in research are from Aug 2025 training data — must re-verify against GitHub releases before pinning
- [Pre-Phase 1]: Semgrep ruleset bundling strategy (which rulesets, total size, license compliance) must be decided in Phase 1
- [Pre-Phase 4]: Groq model ID (`llama-3.1-70b-versatile`) and free-tier rate limits must be verified at Phase 4 start
- [Pre-Phase 7]: EV code signing certificate ($300-700/yr, 1-5 business days) must be initiated before Phase 7 — not on release day

## Session Continuity

Last session: 2026-04-01T19:49:02.960Z
Stopped at: Completed 04-02-PLAN.md
Resume file: None

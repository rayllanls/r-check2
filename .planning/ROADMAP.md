# Roadmap: SecScan

## Overview

SecScan is built in two stages across seven phases. Stage 1 (Phases 1-5) is 100% local development — no licensing, no compilation, `DEV_MODE=True` unlocks Team-tier everywhere. The build order follows the dependency graph: data models and scanner runners first (independently testable), GUI scaffold second, results display and HTML reports third, AI explanations fourth, then polish and performance validation. Only after everything works locally does Stage 2 begin: Phase 6 adds the licensing backend, Phase 7 produces the distributable Windows and Linux binaries.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Domain models, all four scanner runners, orchestrator, and thread-safe queue pattern (completed 2026-03-30)
- [ ] **Phase 2: GUI Scaffold + Scan Execution** - CustomTkinter app wired to real scanner execution with live progress
- [ ] **Phase 3: Results Display + HTML Report** - Finding list UI, severity filters, Chart.js HTML report, and PDF export
- [ ] **Phase 4: AI Explanations** - Groq/Llama 3.1 plain-language explanations and fix suggestions, graceful fallback
- [ ] **Phase 5: Polish + Integration** - End-to-end validation, performance SLA, suppress/ignore, error UX, integration tests
- [ ] **Phase 6: Licensing System** - Freemium/PRO/TEAM tier enforcement, JWT + device fingerprint, Stripe, 72-hour offline grace
- [ ] **Phase 7: Binary Packaging + Distribution** - PyInstaller --onedir, PyArmor obfuscation, GitHub Actions CI, EV-signed .exe

## Phase Details

### Phase 1: Foundation
**Goal**: All four scanner backends produce normalized Finding objects, the threading architecture is established, and the system is fully testable without any GUI.
**Depends on**: Nothing (first phase)
**Requirements**: SCAN-01, SCAN-02, SCAN-03, BACK-01, BACK-02, BACK-03, BACK-04, BACK-05, DATA-01, DATA-02, DATA-03
**Success Criteria** (what must be TRUE):
  1. Each of the four scanner runners (Semgrep, Trufflehog, Grype, Gitleaks) can be invoked against a fixture directory and returns a list of `Finding` objects with title, severity, file, line, description, source tool, and code snippet populated
  2. `ScanOrchestrator` executes all four runners concurrently and emits real-time `ProgressEvent` objects via `queue.Queue` without blocking the caller thread
  3. `BinaryLocator` resolves scanner binary paths correctly in both dev mode (project-relative) and PyInstaller frozen mode (`sys._MEIPASS`) — verified by a unit test that mocks both environments
  4. Language auto-detection correctly identifies the primary language(s) of a test project and selects the corresponding Semgrep rule set
  5. All runner and orchestrator tests pass with 100% coverage of the core data path using fixture JSON (no live scanner binaries required for tests)
**Plans**: 4 plans

### Phase 2: GUI Scaffold + Scan Execution
**Goal**: Users can launch the app, select a folder or Git URL, run a real scan, see live progress, and get a raw finding count — without any GUI freeze.
**Depends on**: Phase 1
**Requirements**: GUI-01, GUI-02, GUI-03, GUI-04, GUI-05
**Success Criteria** (what must be TRUE):
  1. User can open the app, select a local folder via file picker or type a Git repo URL, and click "Start Scan" to trigger real scanner execution
  2. The progress screen updates in real time during a scan (log lines appear, per-scanner status updates) and never appears frozen — verified on a 2-minute scan
  3. User can cancel a running scan and the subprocess tree terminates cleanly (verified via process list)
  4. The app displays "DEV" plan badge and all Team-tier features are accessible when `DEV_MODE=True` — no license prompt appears
  5. After scan completes, the app shows a summary finding count broken down by scanner
**Plans**: 5 plans
Plans:
- [x] 02-01-PLAN.md — Wave 0: dependencies, ScanOrchestrator.cancel(), test stubs, package structure
- [x] 02-02-PLAN.md — App skeleton: theme engine, SecScanApp root window, header bar with logo + DEV badge
- [x] 02-03-PLAN.md — Main screen (target input, scanner list) + Settings screen (Groq token)
- [ ] 02-04-PLAN.md — Progress screen with queue polling, scanner rows, log area, cancel
- [x] 02-05-PLAN.md — Results summary screen + full app wiring + test stub upgrades
**UI hint**: yes

### Phase 3: Results Display + HTML Report
**Goal**: Users can read their findings in the app and in a browser-based HTML report with charts, code snippets, and PDF export.
**Depends on**: Phase 2
**Requirements**: RPT-01, RPT-02, RPT-03, RPT-04, RPT-05
**Success Criteria** (what must be TRUE):
  1. After a scan, the results screen lists all findings sorted Critical-first, each showing title, severity badge, affected file, and line number — user can click a finding to see the code snippet and full description
  2. User can filter the finding list by severity level (Critical / High / Medium / Low / Info)
  3. An HTML report file is generated and opens automatically in the user's default browser, displaying a severity distribution chart (Chart.js, bundled locally — no CDN call) and a scrollable finding table with code snippets
  4. The HTML report renders correctly offline with no internet connection
  5. User can click "Export PDF" and receive a PDF file with the same content as the HTML report
**Plans**: 3 plans
Plans:
- [x] 03-01-PLAN.md — ResultsScreen: scrollable findings list, severity filter buttons, FindingDetailModal
- [ ] 03-02-PLAN.md — HTML report template (Jinja2, Chart.js bundled, doughnut chart, findings table) — parallel with 03-01
- [ ] 03-03-PLAN.md — Wire everything: generator.py upgrade, PDF export (WeasyPrint), button wiring, tests
**UI hint**: yes

### Phase 03.1: Trivy scanner backend (5º scanner: SCA + IaC + secrets, complementa Grype) (INSERTED)

**Goal:** [Urgent work - to be planned]
**Requirements**: TBD
**Depends on:** Phase 3
**Plans:** 3/3 plans complete

Plans:
- [x] TBD (run /gsd:plan-phase 03.1 to break down) (completed 2026-04-01)

### Phase 4: AI Explanations
**Goal**: Users with a Groq token see plain-language explanations and fix suggestions on their most critical findings; users without a token see the same findings without any error or degraded experience.
**Depends on**: Phase 3
**Requirements**: AI-01, AI-02, AI-03, AI-04
**Success Criteria** (what must be TRUE):
  1. User can enter and save a Groq API token in Settings; the token persists across app restarts (stored in `~/.secscan/config.json`)
  2. For scans with a configured token, each of the top 10 Critical/High findings displays a plain-language explanation ("an attacker could...") and a concrete fix suggestion — both visible in the results pane and in the HTML report
  3. AI explanation calls never block or delay report generation — the HTML report opens immediately after scan and AI content populates asynchronously
  4. When no Groq token is configured (or the token is invalid), the app works normally with no error dialog, no broken UI, and findings display without explanation text (silent fallback)
**Plans**: 2 plans
Plans:
- [x] 04-01-PLAN.md — AI backend: fix GROQ_MODEL, AIEnricher service, suggest_fix(), load_groq_token, unit tests
- [x] 04-02-PLAN.md — Wire AI into GUI (FindingDetailModal + ResultsScreen enrichment) + HTML report AI blocks
**UI hint**: yes

### Phase 5: Polish + Integration
**Goal**: The full scan-to-report workflow is validated end-to-end, meets the performance SLA, handles common errors gracefully, and has integration test coverage.
**Depends on**: Phase 4
**Requirements**: INT-01, INT-02, INT-03, INT-04
**Success Criteria** (what must be TRUE):
  1. The complete workflow — select folder → scan → view results → open HTML report → export PDF — works end-to-end without manual intervention
  2. Scanning a 500-file Python project completes in under 3 minutes on a standard developer machine
  3. Common error conditions (non-existent folder, invalid Git URL, scanner binary missing, network timeout during Git clone) display a friendly user-facing message with no stack trace visible and no jargon
  4. Integration tests cover the full GUI-to-report path and pass in CI; Gitleaks gracefully skips (with a "skipped" status badge) when scanning a directory that has no `.git` folder
**Plans**: TBD
**UI hint**: yes

### Phase 6: Licensing System
**Goal**: The app enforces Freemium/PRO/TEAM feature tiers via a cloud license backend, supports 72-hour offline use, and integrates Stripe for subscription billing.
**Depends on**: Phase 5
**Requirements**: LIC-01, LIC-02, LIC-03, LIC-04, LIC-05, LIC-06
**Success Criteria** (what must be TRUE):
  1. A new user on the FREE plan can scan secrets/keys on up to 100 files; attempting SAST, CVE scan, PDF export, or AI explanations displays an upgrade prompt — not an error
  2. A PRO subscriber can run full SAST, CVE, PDF, and AI on unlimited files from one device; attempting activation on a second device requires deactivating the first
  3. App continues to function fully for 72 hours after the last successful license validation with no internet connection; after 72 hours, it degrades gracefully with a revalidation prompt
  4. Stripe checkout flow completes in the browser and the app reflects the new plan within one launch cycle without manual token entry
  5. License validation is gated at scan start only — no license dialog can interrupt an in-progress scan
**Plans**: TBD

### Phase 7: Binary Packaging + Distribution
**Goal**: SecScan ships as a code-signed, self-contained Windows .exe and Linux binary built automatically by GitHub Actions, with no Python or scanner installation required by end users.
**Depends on**: Phase 6
**Requirements**: BUILD-01, BUILD-02, BUILD-03, BUILD-04
**Success Criteria** (what must be TRUE):
  1. The Windows `.exe` (built via PyInstaller `--onedir`) launches in under 5 seconds on a clean Windows 10/11 machine with no Python installed and no Windows Defender / SmartScreen warning
  2. The Linux binary runs correctly on Ubuntu 20.04+ with no Python or scanner binaries pre-installed
  3. All four embedded scanner binaries execute correctly from within the distributed package — verified by running a full scan on a test project from the installed binary
  4. GitHub Actions produces both binaries automatically on a tagged release and publishes them to GitHub Releases; the build fails explicitly (not silently) if any scanner binary is missing
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 4/4 | Complete   | 2026-03-30 |
| 2. GUI Scaffold + Scan Execution | 0/5 | Planning complete | - |
| 3. Results Display + HTML Report | 1/3 | In Progress|  |
| 4. AI Explanations | 0/2 | Planned    |  |
| 5. Polish + Integration | 0/? | Skipped (validado manualmente) | - |
| 6. Licensing System | 0/? | Deferido (pós-empacotamento) | - |
| 7. Binary Packaging + Distribution | 0/? | Next | - |

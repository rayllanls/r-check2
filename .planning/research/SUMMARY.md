# Project Research Summary

**Project:** SecScan
**Domain:** Desktop SAST tool — Python/CustomTkinter GUI wrapping embedded security scanner binaries
**Researched:** 2026-03-29
**Confidence:** MEDIUM (architecture and pitfalls HIGH; stack versions MEDIUM; scanner binary versions LOW — re-verify before pinning)

## Executive Summary

SecScan is a desktop Static Application Security Testing tool targeting developers who use AI coding assistants (Cursor, Claude, ChatGPT) but have no security background. The product wraps four mature open-source scanners (Semgrep, Trufflehog, Grype, Gitleaks) behind a jargon-free CustomTkinter GUI, adds plain-language AI explanations via Groq/Llama 3.1, and distributes as a self-contained binary with no user installation required. The gap it fills is real and unoccupied: every existing SAST tool (Snyk, SonarQube, Semgrep CLI) assumes security knowledge the target user does not have. The "local-only, zero-install, AI-explained" combination has no direct free competitor.

The recommended architecture is a clear four-layer Python application: GUI (main thread only, CustomTkinter), orchestration (ThreadPoolExecutor + queue.Queue), scanner runners (one subprocess wrapper per tool), and services (BinaryLocator, AIExplainer, ReportBuilder). This layering directly informs a build order: models and runners first (independently testable), orchestrator second, GUI third, reports and AI fourth — then licensing and binary packaging as entirely separate later stages. The project's own two-stage strategy (Phases 1–5 local dev, Phases 6–7 cloud+distribution) aligns well with this architecture.

The highest-risk engineering challenges are: (1) getting all four scanner binaries to resolve correctly inside a PyInstaller bundle without hardcoded paths, (2) keeping the Tkinter GUI responsive during multi-minute scans via strict thread-safe queue patterns established from day one, and (3) avoiding antivirus false positives on the final Windows binary, which requires an Extended Validation code signing certificate budgeted before Phase 7 begins. None of these are exotic problems — all have well-documented solutions — but skipping the preventive patterns in early phases forces expensive rewrites later.

## Key Findings

### Recommended Stack

The stack is Python 3.11.x (pinned for PyInstaller+PyArmor stability — 3.12 has regressions in both), CustomTkinter 5.2.2 for the GUI (the only maintained modern Tkinter wrapper), Pydantic v2 for normalizing cross-scanner JSON output into a unified Finding schema, Jinja2+WeasyPrint for HTML and PDF report generation, and the Groq Python SDK for optional AI explanations. PyInstaller 6.6.0 and PyArmor 8.x are build-only dependencies, not development dependencies. Scanner binaries (Semgrep, Trufflehog, Grype, Gitleaks) are downloaded at build time via a CI script and embedded under `tools/`.

The critical dependency chain is: Python 3.11 → PyInstaller 6.6.0 → PyArmor 8.x → all must be pinned together and tested as a unit in CI. Mixing Python 3.12 with PyArmor is a known breakage path. All scanner binary versions listed in STACK.md are from training knowledge (Aug 2025) and must be re-verified against GitHub releases before the first build.

**Core technologies:**
- Python 3.11.x: runtime — only tested-stable version for PyInstaller+PyArmor combination
- CustomTkinter 5.2.2: GUI framework — only actively-maintained modern Tkinter wrapper with dark mode
- Pydantic v2: data modeling — handles cross-scanner JSON normalization via `model_validator`
- Jinja2 + WeasyPrint: reports — HTML templates → PDF without external binary dependencies
- groq SDK: AI layer — official Groq client; async-capable; user supplies own token
- concurrent.futures.ThreadPoolExecutor: concurrency — IO-bound scanner subprocesses, 4 threads max
- psutil: process management — required on Windows to kill scanner subprocess trees reliably
- platformdirs: config storage — correct OS paths for settings/tokens (`%APPDATA%` on Windows)

### Expected Features

The product gap is well-defined. No existing free tool combines: GUI, multi-scanner, plain-language explanations, and zero-install. All four of those properties are required together for the target user — any one missing collapses the value proposition.

**Must have (table stakes):**
- Folder scan with language auto-detection — the single trigger action; users expect "just scan this folder"
- All four scanner backends running: Semgrep (code bugs), Gitleaks (secrets in files), Trufflehog (secrets in git history), Grype (dependency CVEs)
- Normalized finding list (title, severity, file, line) — core data structure everything else depends on
- Severity tier display (Critical/High/Medium/Low) with summary counts — first thing users read
- Real-time scan progress — prevents "is it frozen?" abandonment on 3-minute scans
- HTML report with charts and code snippets — shareable artifact
- Re-scan button — second scan must be one click

**Should have (competitive differentiators):**
- Plain-language explanation per finding via Groq/Llama 3.1 — transforms "sql-injection/tainted-input" into "an attacker could delete your database"; graceful fallback if no token
- Code-level fix suggestion (v1.x) — upgrade from diagnosis to prescription; requires prompt engineering validation
- Ignore/suppress false positives — first power-user request when false positives appear
- PDF export — requested by users sharing reports with clients or employers
- Triage ordering ("fix these first") — heuristic severity weighting by file importance
- Privacy-first UX messaging — "your code never leaves your machine" must be prominent in UI

**Defer (v2+):**
- Scan history and delta view — requires SQLite storage layer; adds complexity without validating core value
- IDE plugin (VS Code/Cursor) — separate engineering track; validate desktop first
- CI/CD integration — different buyer persona; do not build into the GUI
- Team dashboard/cloud sync — destroys local-only differentiator until explicitly designed
- Auto-fix / one-click patch application — high liability; defer until AI fix quality is proven
- Custom rule editor — power-user feature; not the target persona

### Architecture Approach

The application maps cleanly to four independent layers with well-defined boundaries: (1) GUI layer (CustomTkinter, main thread only, no business logic), (2) Orchestration layer (ThreadPoolExecutor manages 4 concurrent scanner threads via a queue.Queue event bus), (3) Runner layer (one BaseRunner subclass per scanner tool, each translating native JSON to Finding dataclasses), and (4) Services layer (BinaryLocator, AIExplainer, ReportBuilder, AppConfig as stateless or lightly-stateful utilities). The layers can be built and tested incrementally — runners are independently testable with fixture JSON before any GUI exists.

**Major components:**
1. ScanOrchestrator — spawns 4 scanner threads, collects ProgressEvents via queue.Queue, emits ScanCompleteEvent; owns all concurrency
2. BaseRunner + 4 subclasses — subprocess.Popen wrappers; stream stdout line-by-line; normalize to Finding dataclass; never touch the GUI
3. BinaryLocator — single choke point for all binary path resolution; resolves sys._MEIPASS when frozen, project-relative paths in dev
4. FindingModel (dataclass) — shared schema consumed by runners (write), GUI (read), ReportBuilder (read), AIExplainer (mutate ai_explanation post-scan)
5. GUI Views (ScanView, ResultsView, SettingsView) — display only; communicate with orchestrator via method calls and queue polling via root.after(100ms)
6. ReportBuilder — Jinja2 template + bundled Chart.js → HTML file opened in browser; WeasyPrint for PDF
7. AIExplainer — optional Groq API calls post-scan; batched, capped, never blocks report generation
8. LicenseGate — Phase 6+ only; DEV_MODE bypass short-circuits all checks during Phases 1–5

### Critical Pitfalls

1. **GUI thread blocking from scanner subprocesses** — Establish queue.Queue + root.after(100ms) polling pattern in Phase 1 before any scanner is wired up. Any subprocess.run() or .communicate() on the main thread causes "Not Responding" on Windows. Recovery cost is a full rewrite of the scanner layer.

2. **Hardcoded binary paths breaking PyInstaller builds** — Write BinaryLocator with sys._MEIPASS fallback in Phase 2 (first scanner). All 4 runner classes must use it. Never construct binary paths inline. Verify by running the built .exe on a no-Python VM before Phase 7 completes.

3. **Subprocess output buffering killing real-time progress** — Child processes detect no TTY and switch to full buffering. Use `subprocess.Popen` with `bufsize=1`, read with `iter(proc.stdout.readline, b'')`. Establish in Phase 2 with the first scanner; wrong patterns spread to all four if caught late.

4. **Antivirus false positives on the final Windows binary** — PyInstaller stubs + security tool binaries (Gitleaks, Trufflehog) are near-certain to trigger Windows Defender/SmartScreen. Budget for an EV code signing certificate ($300–700/year) before Phase 7. Submit to Microsoft Defender portal before public release. No workaround exists without code signing.

5. **Groq API rate limits blocking AI explanation phase** — Free tier is ~30 req/min. A scan with 40 findings triggers 40 sequential calls. Cap AI calls at top 10 Critical/High findings; batch similar rule types; never block report generation on AI completion. Design this pattern in Phase 5 before the first Groq call.

6. **JWT license validation blocking offline users** — Implement two-layer model (online validation + 72-hour cached JWT grace period) from the start of Phase 6. Never gate app launch on live API reachability alone. Recovery requires a hotfix and user communication.

7. **Semgrep fetching rules at runtime** — `--config auto` downloads rulesets from the Semgrep registry. Bundle YAML rules in `assets/rules/` and pass `--config assets/rules/`. Verify offline scan produces results before claiming local-only operation.

## Implications for Roadmap

Based on combined research, the architecture's dependency graph directly prescribes build order. The project's own two-stage strategy (Phases 1–5 local, 6–7 cloud+dist) is validated by research.

### Phase 1: Foundation — Models, Runners, Orchestrator

**Rationale:** Runners are the foundation of all features. They can be built and unit-tested with fixture JSON before any GUI exists. The threading architecture must also be established here — retrofitting it later is a full rewrite. This phase has no UI dependencies and is independently verifiable.
**Delivers:** All four scanner runners producing normalized Finding objects from fixture JSON; ThreadPoolExecutor orchestration; BinaryLocator utility; queue.Queue event bus; 100% test coverage on core data path.
**Addresses:** Normalized finding list (table stakes); language auto-detection hooks; scanner backend execution.
**Avoids:** Hardcoded binary paths (BinaryLocator established here); subprocess buffering (streaming pattern established here); GUI thread blocking (queue pattern established before GUI exists).

### Phase 2: GUI Scaffold + Scan Execution

**Rationale:** Wire real scan execution to a working GUI as early as possible to surface integration issues. The GUI needs the orchestrator and runners from Phase 1. Progress feedback and cancel functionality require the queue pattern to already exist.
**Delivers:** CustomTkinter app skeleton (ScanView, SettingsView); folder picker; scan button triggering real scanner execution; per-scanner progress bars updating in real time; cancel scan terminating subprocess trees via psutil; scan completes and shows raw finding count.
**Uses:** CustomTkinter 5.2.2, Pillow, ThreadPoolExecutor, psutil, queue.Queue, BinaryLocator.
**Implements:** ScanView, ScanOrchestrator wired to GUI, ProgressEvent polling.
**Avoids:** GUI thread freeze (queue/after pattern enforced); subprocess buffering (streaming pattern verified with real binaries).

### Phase 3: Results Display + HTML Report

**Rationale:** Findings exist from Phase 2; this phase is pure display and output. ResultsView and ReportBuilder both consume the FindingModel schema already defined. HTML report is the canonical output artifact that everything else (PDF, AI explanations) builds on.
**Delivers:** ResultsView with finding list, severity filter, finding detail pane, code snippet display; summary counts and severity breakdown; HTML report with Chart.js severity charts and finding table; "Open Report" button opens in browser; severity sorting (Critical first).
**Uses:** Jinja2, Chart.js (bundled locally), webbrowser.open().
**Implements:** ResultsView, ReportBuilder.
**Avoids:** CDN-linked Chart.js (bundle locally in assets/); raw CVE IDs shown to users (map to plain-language titles).

### Phase 4: AI Explanations (Groq/Llama)

**Rationale:** Entirely additive — findings already display correctly without AI. Adding explanations at this point enhances an already-working product. The batching and rate-limit pattern must be designed before the first Groq call.
**Delivers:** Plain-language explanation per finding in ResultsView and HTML report; graceful fallback ("No AI explanation available") when no token configured; fix suggestion text in finding detail pane; Groq token configuration in SettingsView; AI explanation capped at top 10 Critical/High findings; async, never blocks report.
**Uses:** groq SDK, platformdirs (token storage).
**Implements:** AIExplainer service, settings persistence via AppConfig.
**Avoids:** One Groq call per finding in a loop (batch by rule_id); blocking report generation on AI completion; sending raw secrets to Groq (redact literal secret values from snippets).

### Phase 5: Polish + v1.x Features

**Rationale:** Core product is working after Phase 4. This phase adds the first post-launch feature requests (suppress, PDF) and validates performance against the 3-minute SLA before the complexity of licensing is introduced.
**Delivers:** Ignore/suppress finding (persisted per project path); PDF export via WeasyPrint; triage ordering heuristic ("fix these first"); performance verification on 500-file project under 3 minutes; Gitleaks graceful skip for non-git directories; per-scanner status summary in UI ("Semgrep: 12 | Gitleaks: skipped").
**Uses:** WeasyPrint, platformdirs.
**Implements:** Suppress/ignore persistence, PDF export in ReportBuilder.
**Avoids:** Silent scanner failures (explicit per-scanner status); Gitleaks error on non-git dir (check .git before invoking).

### Phase 6: Licensing System

**Rationale:** Core product is fully validated before any licensing complexity is introduced. DEV_MODE=True has provided full Team-tier access throughout Phases 1–5 with zero licensing code. Phase 6 is now purely additive.
**Delivers:** Freemium/PRO/TEAM tier enforcement; JWT license validation with 72-hour offline grace period; device fingerprint using machine UUID + CPU model + OS install date (2-of-3 matching); license activation flow in UI; Stripe payment integration; FastAPI license API on Railway + Supabase.
**Uses:** FastAPI, Supabase, Stripe, JWT, platformdirs (license cache in %APPDATA%/~/.config/).
**Avoids:** License blocking offline users (72-hour grace period mandatory); volatile fingerprint (no MAC address, no IP); license token stored next to .exe (always use platformdirs); mid-scan license dialog (gate at scan start only).

### Phase 7: Binary Packaging + Distribution

**Rationale:** Final phase only after everything works, is tested, and licensing is live. PyArmor is never applied during development — stack traces become unreadable. Build environment must be isolated with Python 3.11 pinned.
**Delivers:** Windows .exe and Linux binary via PyInstaller --onedir (not --onefile); PyArmor 8.x obfuscation; GitHub Actions build pipeline; EV code-signed Windows binary; Grype DB handling (bundled or first-run update); download page with SmartScreen warning note.
**Uses:** PyInstaller 6.6.0, PyArmor 8.x, Python 3.11.x pinned in build environment.
**Avoids:** PyInstaller --onefile (Windows Defender 10-30s startup delay for 600MB bundle); PyArmor on Python 3.12 (incompatibility); unsigned release (AV false positives will cause early adopter churn); hardcoded binary paths (already solved in Phase 1).

### Phase Ordering Rationale

- Runners before GUI: runners are independently testable; building GUI first leads to entangling business logic with presentation, which is the single largest source of unmaintainable code in Tkinter apps.
- Queue/threading pattern in Phase 1: the single highest-recovery-cost pitfall (GUI freeze) must be established before any scanner is wired to any UI element — retrofitting costs 2-3 days.
- HTML report before PDF: PDF is a transformation of HTML; building PDF first (or instead) loses the browser-preview workflow and forces WeasyPrint layout debugging without a browser comparison.
- AI explanations after core display: AI is additive. Gating Phase 3 on AI working delays user feedback on the core scan-and-display loop by a phase.
- Licensing after full feature validation: building licensing before the product is validated risks investing in gating a product that needs to change. DEV_MODE bypass makes this deferral zero-cost.
- Binary packaging last: PyArmor obfuscation makes development debugging nearly impossible. PyInstaller bundling surfaces path issues that only matter when everything else is stable.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 6 (Licensing):** FastAPI + Supabase + Stripe + JWT + device fingerprint is a multi-service integration. Supabase schema design, Stripe webhook handling, and JWT refresh token flow each deserve pre-implementation research. Row Level Security policies for multi-tenant license data need explicit design.
- **Phase 7 (Distribution):** EV certificate acquisition process, PyInstaller .spec configuration for all four scanner binaries + Grype DB, and GitHub Actions Windows runner setup are all operationally complex. Recommend a research spike on the specific PyInstaller spec before writing it.
- **Phase 4 (AI Explanations):** Groq rate limit tiers, current model availability (`llama-3.1-70b-versatile` may have changed), and prompt engineering for fix suggestions warrant a verification pass against current Groq documentation.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Models/Runners):** All four scanner JSON output formats are well-documented. Pydantic v2 model_validator patterns are established. subprocess.Popen streaming is standard Python.
- **Phase 2 (GUI Scaffold):** CustomTkinter patterns are stable. The queue.Queue + root.after() threading pattern is canonical Tkinter. No novel integrations.
- **Phase 3 (Results + Report):** Jinja2 templating and Chart.js integration are mature. WeasyPrint HTML→PDF conversion is straightforward with the chosen HTML structure.
- **Phase 5 (Polish):** Suppress/ignore persistence (JSON file via platformdirs) and PDF export are additive to already-built components.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM | Library versions from training knowledge (Aug 2025); all versions must be re-verified with `pip index versions` and GitHub releases before pinning. Architecture pattern choices (CustomTkinter, WeasyPrint, Pydantic v2) are HIGH confidence; version numbers are MEDIUM. |
| Features | MEDIUM | Competitor feature analysis (Snyk, SonarQube, Semgrep) from training data. Feature existence is HIGH confidence; current pricing/tier details are MEDIUM. Target user persona gap analysis is well-reasoned and HIGH confidence. |
| Architecture | HIGH | Well-established Python patterns: subprocess.Popen streaming, queue.Queue + Tkinter after() polling, sys._MEIPASS PyInstaller resolution. All cited against official documentation. No experimental patterns. |
| Pitfalls | HIGH | GUI threading, subprocess buffering, and PyInstaller path resolution are mature, well-documented failure modes with established solutions. AV false-positive and EV certificate requirements are confirmed operational realities. Groq rate limit specifics are MEDIUM (subject to change). |

**Overall confidence:** MEDIUM-HIGH. Architecture and pitfall avoidance patterns are HIGH confidence. Technology choices are sound. Version numbers and third-party API specifics need verification at implementation time.

### Gaps to Address

- **Scanner binary versions:** Semgrep 1.7x, Trufflehog 3.8x, Grype 0.7x, Gitleaks 8.x are from Aug 2025 knowledge. Verify current stable releases on GitHub before downloading in Phase 1/2. Use latest stable unless a specific version issue is found.
- **Semgrep ruleset bundling strategy:** Which rulesets to bundle (p/python, p/javascript, p/owasp-top-ten, etc.), their total size, and whether bundling creates a license compliance issue (Semgrep rules have their own license) must be resolved in Phase 1.
- **Grype vulnerability database size:** Research estimated ~200 MB. If actual DB pushes the binary over 600 MB, the strategy shifts to first-run download. Verify actual DB size before Phase 7 planning.
- **Groq model availability:** `llama-3.1-70b-versatile` model ID must be verified against current Groq API documentation at Phase 4 start. Model IDs and free-tier availability change.
- **EV certificate timeline:** EV certificate issuance typically takes 1-5 business days and requires business verification. Must be initiated well before Phase 7 final build — not the day of release.
- **WeasyPrint CSS compatibility:** WeasyPrint does not support all CSS features. Report template must be designed and tested against WeasyPrint rendering early in Phase 3, not after the full template is built.

## Sources

### Primary (HIGH confidence)
- PyInstaller documentation — sys._MEIPASS, sys.frozen, datas bundling, --onedir vs --onefile behavior
- Python stdlib documentation — subprocess.Popen, queue.Queue, threading module, concurrent.futures
- Tkinter documentation — main-thread-only widget access requirement
- Semgrep CLI documentation — --json output, --config flag, offline mode behavior
- Microsoft SmartScreen documentation — EV certificate requirement for SmartScreen trust
- CustomTkinter GitHub (github.com/TomSchimansky/CustomTkinter) — widget API, CTkScrollableFrame, threading model
- Groq API documentation — OpenAI-compatible endpoint, model IDs

### Secondary (MEDIUM confidence)
- PyArmor 8.x changelog and GitHub issues — Python 3.12 incompatibility
- CustomTkinter community examples — threading patterns with root.after()
- Gitleaks GitHub issues — non-git-directory exit behavior
- Trufflehog filesystem mode documentation — NDJSON streaming behavior
- Grype README — dir: scanning scope (dependency manifests only, not source code)
- Snyk, SonarQube, Semgrep feature documentation (training knowledge, Aug 2025)
- Groq developer documentation — rate limit tiers (subject to change)

### Tertiary (LOW confidence)
- Scanner binary versions (Semgrep 1.7x, Trufflehog 3.8x, Grype 0.7x, Gitleaks 8.x) — training knowledge Aug 2025; must be verified before pinning
- Groq free-tier rate limits (~30 req/min) — training knowledge; verify at Phase 4
- EV certificate pricing ($300–700/year) — market rates as of Aug 2025; verify current pricing

---
*Research completed: 2026-03-29*
*Ready for roadmap: yes*

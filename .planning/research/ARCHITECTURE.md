# Architecture Research

**Domain:** Python desktop security scanner (SAST tool wrapper with GUI)
**Researched:** 2026-03-29
**Confidence:** HIGH (well-established Python patterns; verified against known PyInstaller, CustomTkinter, subprocess documentation)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  CustomTkinter GUI (main thread only)                    │   │
│  │  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │   │
│  │  │  ScanView   │  │  ResultsView │  │  SettingsView   │ │   │
│  │  └──────┬──────┘  └──────┬───────┘  └────────┬────────┘ │   │
│  └─────────┼────────────────┼───────────────────┼──────────┘   │
│            │  (callbacks / after() polling)      │              │
├────────────┼────────────────┼───────────────────┼──────────────┤
│                        ORCHESTRATION LAYER                       │
│  ┌─────────┴────────────────┴───────────────────┴──────────┐   │
│  │  ScanOrchestrator (ThreadPoolExecutor, event queue)      │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │  ProgressEventQueue  (thread-safe Queue.Queue)      │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──┬──────────┬──────────────┬──────────────┬──────────────┘   │
│     │          │              │              │                    │
├─────┼──────────┼──────────────┼──────────────┼────────────────── ┤
│                        SCANNER LAYER                             │
│  ┌──┴───┐  ┌──┴──────┐  ┌────┴────┐  ┌──────┴──────┐           │
│  │Semgr-│  │Truffle- │  │  Grype  │  │  Gitleaks   │           │
│  │epRunner│ │hogRunner│  │ Runner  │  │   Runner    │           │
│  └──┬───┘  └──┬──────┘  └────┬────┘  └──────┬──────┘           │
│     │          │              │              │                    │
│  ┌──┴──────────┴──────────────┴──────────────┴──────────────┐   │
│  │  BaseRunner (subprocess.Popen, stdout parsing, timeout)   │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                        SERVICES LAYER                            │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ BinaryLocator │  │  AIExplainer│  │  LicenseGate         │  │
│  │ (finds tools  │  │  (Groq API, │  │  (DEV_MODE bypass,   │  │
│  │  in bundle)   │  │   optional) │  │   Phase 6+)          │  │
│  └───────────────┘  └─────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        DATA / OUTPUT LAYER                       │
│  ┌───────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ FindingModel  │  │ ReportBuilder│  │  AppConfig           │  │
│  │ (dataclasses) │  │ (Jinja2 →   │  │  (settings file,     │  │
│  │               │  │  HTML+Chart)│  │   Groq token)        │  │
│  └───────────────┘  └─────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| GUI Views (ScanView, ResultsView, SettingsView) | Render UI, accept user input, display progress and findings | CustomTkinter widgets; MUST run on main thread only |
| ScanOrchestrator | Spawn scanner threads, collect results, emit progress events | `concurrent.futures.ThreadPoolExecutor`; coordinates all runners |
| ProgressEventQueue | Decouple scanner threads from GUI thread | `queue.Queue`; GUI polls via `root.after(100, poll_fn)` |
| BaseRunner | Abstract subprocess wrapper; handles Popen, stdout/stderr streaming, timeout, process kill | `subprocess.Popen` with `stdout=PIPE`; reads line-by-line |
| SemgrepRunner / TrufflehogRunner / GrypeRunner / GitleaksRunner | Parse tool-specific JSON output; translate to FindingModel | Each tool outputs JSON with `--json` flag; runner normalises to common schema |
| BinaryLocator | Resolve path to embedded scanner binaries at runtime | `sys._MEIPASS` when frozen by PyInstaller; falls back to PATH in dev |
| FindingModel | Shared data schema for all findings | Python `dataclasses`; fields: tool, severity, rule_id, file, line, message, snippet, ai_explanation |
| ReportBuilder | Render HTML report from findings list | Jinja2 template + Chart.js CDN (or bundled JS); `webbrowser.open()` to show result |
| AIExplainer | Optional: send finding to Groq API, get plain-language explanation | `httpx` async or plain `requests`; called per-finding post-scan if token configured |
| AppConfig | Persist user settings (Groq token, last scan path, theme) | `platformdirs` + JSON or TOML file in user data dir |
| LicenseGate | Gate PRO/TEAM features; bypass in DEV_MODE | Phase 6 only; `DEV_MODE=True` short-circuits all checks |

## Recommended Project Structure

```
secscan/
├── main.py                   # Entry point; creates CTk root, starts App
├── app.py                    # App class; wires views + orchestrator
│
├── gui/                      # Presentation layer — all CustomTkinter code
│   ├── __init__.py
│   ├── views/
│   │   ├── scan_view.py      # Folder picker, scan button, progress bars
│   │   ├── results_view.py   # Finding list, severity filter, detail pane
│   │   └── settings_view.py  # Groq token input, theme, about
│   ├── components/
│   │   ├── progress_bar.py   # Reusable per-scanner progress widget
│   │   └── finding_card.py   # Single finding display component
│   └── theme.py              # Color constants, font sizes
│
├── orchestrator/             # Scan coordination
│   ├── __init__.py
│   ├── scan_orchestrator.py  # ThreadPoolExecutor; submits runners; collects events
│   └── event_queue.py        # ProgressEvent dataclass; Queue wrapper
│
├── runners/                  # One file per scanner
│   ├── __init__.py
│   ├── base_runner.py        # Popen wrapper, timeout, line streaming, kill()
│   ├── semgrep_runner.py
│   ├── trufflehog_runner.py
│   ├── grype_runner.py
│   └── gitleaks_runner.py
│
├── models/                   # Shared data structures
│   ├── __init__.py
│   ├── finding.py            # Finding dataclass (normalised schema)
│   └── scan_result.py        # ScanResult: list of findings + metadata
│
├── services/                 # Cross-cutting services
│   ├── __init__.py
│   ├── binary_locator.py     # sys._MEIPASS vs PATH resolution
│   ├── ai_explainer.py       # Groq API calls (optional)
│   ├── report_builder.py     # Jinja2 → HTML; webbrowser.open()
│   └── app_config.py         # Read/write user settings JSON
│
├── templates/                # Jinja2 HTML templates
│   └── report.html.j2        # Report template embedding Chart.js
│
├── assets/                   # Icons, fonts bundled in binary
│   ├── icon.ico
│   └── fonts/
│
├── tools/                    # Scanner binaries (git-ignored, populated by build script)
│   ├── semgrep(.exe)
│   ├── trufflehog(.exe)
│   ├── grype(.exe)
│   └── gitleaks(.exe)
│
├── build/
│   ├── secscan.spec          # PyInstaller spec (adds tools/ as datas)
│   └── download_tools.py     # CI script: downloads correct platform binaries
│
└── tests/
    ├── fixtures/             # Sample scan outputs (JSON) for unit testing runners
    └── test_runners/
```

### Structure Rationale

- **gui/:** Isolated from all business logic. Views only call orchestrator methods and read FindingModel data. Never imports subprocess or file I/O directly.
- **runners/:** One class per tool means each can be independently tested with fixture JSON. BaseRunner holds all Popen complexity so runners stay thin.
- **models/:** Single source of truth for the data schema. Defined once; consumed by runners (write), GUI (read), and ReportBuilder (read).
- **services/binary_locator.py:** The `sys._MEIPASS` resolution is a single choke point. All runners ask BinaryLocator for paths — never hardcode paths in runners.
- **tools/:** Excluded from git (binaries are large). Build script downloads them. PyInstaller spec adds the entire directory as `datas`.
- **templates/:** Jinja2 templates shipped inside the binary via PyInstaller `datas`. Chart.js should be bundled locally (not CDN) so reports work offline.

## Architectural Patterns

### Pattern 1: Thread-Safe GUI Updates via Queue + `after()` Polling

**What:** Scanner threads post `ProgressEvent` objects to a `queue.Queue`. The GUI main thread polls the queue every 100ms using `root.after(100, self._poll_queue)` and updates widgets.

**When to use:** Mandatory. CustomTkinter (Tkinter) is not thread-safe. Any widget update from a background thread causes silent corruption or crashes.

**Trade-offs:** 100ms polling latency is imperceptible to users. Adds a small loop overhead but negligible at this event rate.

**Example:**
```python
# In ScanOrchestrator (background thread):
self.event_queue.put(ProgressEvent(tool="semgrep", pct=45, status="running"))

# In GUI (main thread):
def _poll_queue(self):
    try:
        while True:
            event = self.event_queue.get_nowait()
            self._handle_event(event)
    except queue.Empty:
        pass
    finally:
        self.after(100, self._poll_queue)  # reschedule
```

### Pattern 2: BaseRunner with Streaming Stdout

**What:** `subprocess.Popen` with `stdout=PIPE, stderr=PIPE`. Read stdout line-by-line in a loop. Accumulate JSON lines. Post progress events. Never use `communicate()` (blocks until process exits; no real-time progress possible).

**When to use:** All four scanners. Each supports `--json` output mode that emits one JSON object per line (NDJSON) or a single JSON array at the end.

**Trade-offs:** Line-by-line streaming works for NDJSON tools (Semgrep, Trufflehog, Gitleaks). Grype emits a single JSON blob at the end — must buffer full stdout then parse once. Handle both modes in BaseRunner.

**Example:**
```python
# NDJSON streaming (Semgrep, Trufflehog, Gitleaks)
proc = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE, text=True)
for line in proc.stdout:
    line = line.strip()
    if line:
        finding = self._parse_line(line)
        if finding:
            self.emit(ProgressEvent(finding=finding))

# Single-blob (Grype)
stdout, _ = proc.communicate(timeout=self.timeout)
findings = self._parse_blob(stdout)
```

### Pattern 3: BinaryLocator with `sys._MEIPASS` Fallback

**What:** A single service resolves binary paths. When frozen by PyInstaller, binaries live in `sys._MEIPASS/tools/`. In dev, fall back to the `tools/` directory relative to project root or `PATH`.

**When to use:** Every call to a scanner binary must go through BinaryLocator. Never construct paths inline in runners.

**Trade-offs:** Adds one indirection layer. Required for PyInstaller compatibility — without this, the frozen binary cannot find embedded tools.

**Example:**
```python
import sys, os

def get_binary(name: str) -> str:
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(__file__), "..", "..", "tools")
    suffix = ".exe" if sys.platform == "win32" else ""
    path = os.path.join(base, "tools", name + suffix)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Scanner binary not found: {path}")
    return path
```

### Pattern 4: Normalised Finding Schema

**What:** Each runner translates its tool's native JSON format into a shared `Finding` dataclass. Downstream components (GUI, ReportBuilder, AIExplainer) only ever see `Finding` objects.

**When to use:** Essential. Each tool has a different JSON schema. Centralising translation in runners prevents schema leakage into GUI and report code.

**Trade-offs:** Requires writing a parser for each tool's JSON format. The upside is that adding a 5th tool only requires a new runner — zero changes to GUI or report.

## Data Flow

### Scan Initiation Flow

```
User clicks "Scan" (GUI main thread)
    │
    ▼
ScanView.on_scan_click()
    │  calls
    ▼
ScanOrchestrator.start_scan(target_path)
    │  creates ThreadPoolExecutor(max_workers=4)
    │  submits one future per runner
    ▼
[Thread 1: SemgrepRunner]  [Thread 2: TrufflehogRunner]
[Thread 3: GrypeRunner  ]  [Thread 4: GitleaksRunner  ]
    │  each runner:
    │  1. BinaryLocator.get_binary(name) → resolved path
    │  2. subprocess.Popen(cmd, ...)
    │  3. Stream stdout → parse lines → emit ProgressEvents
    │
    ▼
event_queue.put(ProgressEvent)   ← from any runner thread
    │
    ▼
GUI poll (root.after 100ms)
    │
    ▼
ScanView._handle_event(event)
    │  updates progress bars, finding count labels
    ▼
[All futures done]
    │
ScanOrchestrator collects all findings → ScanResult
    │
    ▼
event_queue.put(ScanCompleteEvent(scan_result))
    │
    ▼
GUI shows ResultsView.display(scan_result)
```

### Report Generation Flow

```
User clicks "Generate Report" (ResultsView)
    │
    ▼
ReportBuilder.build(scan_result) → renders Jinja2 template
    │  findings serialised to JSON for Chart.js
    │  template written to temp file / user-chosen path
    ▼
webbrowser.open(report_path)     ← opens in default browser
```

### Optional AI Explanation Flow

```
ScanCompleteEvent received by GUI
    │  if Groq token configured
    ▼
AIExplainer.explain_batch(findings)
    │  for each finding (or high/critical only):
    │  POST to Groq API → get plain-language explanation
    │  finding.ai_explanation = response_text
    ▼
GUI re-renders finding cards with explanation text
```

### Key Data Flows

1. **Scanner output → Finding objects:** Runners translate raw JSON (tool-specific) into `Finding` dataclass instances. This is the most critical normalisation step — errors here corrupt everything downstream.
2. **Background thread → GUI:** All thread-to-GUI communication is via `queue.Queue` + `after()` polling. No direct widget manipulation from background threads.
3. **Findings → HTML report:** `ScanResult.findings` (list of `Finding`) serialised to a JSON blob embedded in the Jinja2 template. Chart.js consumes the JSON to render severity charts. No server required.
4. **PyInstaller bundle → binary resolution:** At runtime, `sys._MEIPASS` is set to the temp directory where PyInstaller extracted the bundle. All file path lookups (binaries, templates, assets) must use this base path when `sys.frozen` is True.

## Build Order (Phase Dependencies)

The architecture has a clear dependency graph that maps directly to build phases:

```
Phase 1: models/ + runners/ (no GUI, no orchestrator)
    │  Reason: runners are independently testable with fixture JSON.
    │  Output: parse Semgrep/Trufflehog/Grype/Gitleaks JSON → Finding objects.
    ▼
Phase 2: orchestrator/ (depends on runners + models)
    │  Reason: orchestrator needs runners to exist. GUI not required yet.
    │  Output: parallel scan execution, event queue populated.
    ▼
Phase 3: gui/ — basic scaffold + ScanView (depends on orchestrator)
    │  Reason: wire real scan execution to the UI. Progress visible.
    │  Output: functional scan with real-time progress bars.
    ▼
Phase 4: gui/ — ResultsView + services/report_builder (depends on models)
    │  Reason: findings already exist; this is pure display + HTML output.
    │  Output: viewable results list + HTML report with charts.
    ▼
Phase 5: services/ai_explainer (depends on models, optional)
    │  Reason: entirely additive; findings work without it.
    │  Output: plain-language explanations on findings.
    ▼
Phase 6: services/license_gate (depends on nothing core)
    │  Reason: DEV_MODE bypass means Phase 6 is pure add-on.
    │  Output: Freemium/PRO/TEAM enforcement.
    ▼
Phase 7: build/ — PyInstaller spec + download_tools.py
    Reason: Binary bundling is the final step; all components must be stable first.
    Output: single .exe / Linux binary.
```

## Anti-Patterns

### Anti-Pattern 1: Direct Widget Updates from Scanner Threads

**What people do:** Call `label.configure(text=...)` or `progressbar.set(...)` directly from the background scanner thread for "simplicity."

**Why it's wrong:** Tkinter (and CustomTkinter) is not thread-safe. Direct widget access from non-main threads causes intermittent crashes, silent data corruption, or frozen UIs — bugs that are hard to reproduce.

**Do this instead:** Post a `ProgressEvent` to the `queue.Queue`. Let `root.after()` polling handle all widget updates on the main thread.

### Anti-Pattern 2: Hardcoded Binary Paths

**What people do:** `cmd = ["C:/tools/semgrep.exe", ...]` or `cmd = ["./tools/semgrep", ...]` hardcoded in runner files.

**Why it's wrong:** The path does not exist inside a PyInstaller-frozen binary. The frozen app extracts to a temp directory with a path like `C:\Users\user\AppData\Local\Temp\_MEI12345\`. Hardcoded paths break silently on every user's machine.

**Do this instead:** Use `BinaryLocator.get_binary("semgrep")` which resolves `sys._MEIPASS` when frozen and falls back to dev paths otherwise.

### Anti-Pattern 3: `subprocess.communicate()` for Real-Time Progress

**What people do:** `stdout, stderr = proc.communicate()` then parse the entire output at once.

**Why it's wrong:** `communicate()` blocks until the process exits. For a 500-file Semgrep scan this can take 60+ seconds with zero feedback. The GUI appears frozen. Users quit.

**Do this instead:** Use `proc.stdout` line iterator or `proc.stdout.readline()` in a loop. Emit a `ProgressEvent` for each parsed finding or percentage milestone.

### Anti-Pattern 4: Bundling Chart.js from CDN in Report Template

**What people do:** `<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>` in the report template.

**Why it's wrong:** SecScan's value proposition includes working offline. Reports generated while offline (or on machines with firewall restrictions) will render without charts — a broken experience.

**Do this instead:** Copy the minified `chart.min.js` into `assets/` and bundle it via PyInstaller `datas`. Reference it in the Jinja2 template with a relative path or inline it in the template.

### Anti-Pattern 5: Running All Four Scanners Sequentially

**What people do:** `semgrep_runner.run()` → wait → `trufflehog_runner.run()` → wait → etc.

**Why it's wrong:** Sequential execution on a 500-file project takes 4x as long. Semgrep alone can take 60+ seconds. Sequential scanning likely blows the 3-minute SLA.

**Do this instead:** `ThreadPoolExecutor(max_workers=4)` — one thread per scanner, all four run concurrently. Scanner binaries do their own internal parallelism; Python threads here are just managing processes, not CPU-bound.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Semgrep binary | `subprocess.Popen(["semgrep", "--json", "--config=auto", target])` | Use `--config=auto` for language auto-detection; outputs NDJSON per finding |
| Trufflehog binary | `subprocess.Popen(["trufflehog", "filesystem", "--json", target])` | NDJSON output; detects secrets in files and git history |
| Grype binary | `subprocess.Popen(["grype", "dir:"+target, "-o", "json"])` | Single JSON blob at end; requires SBOMs for full accuracy on source dirs |
| Gitleaks binary | `subprocess.Popen(["gitleaks", "detect", "--report-format=json", "--source", target])` | Single JSON array; only meaningful if target is a git repo |
| Groq API | `requests.post("https://api.groq.com/openai/v1/chat/completions", ...)` | Optional; user supplies API key; called post-scan; use `httpx` with timeout |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| GUI ↔ Orchestrator | Method call (start_scan, cancel_scan) + queue.Queue events | One-way events from orchestrator to GUI; commands from GUI to orchestrator |
| Orchestrator ↔ Runners | ThreadPoolExecutor futures; runners call `self.emit(event)` which posts to shared queue | Runners are stateless workers; orchestrator owns the queue |
| Runners ↔ BinaryLocator | Direct function call at runner startup | BinaryLocator is a pure function; no state |
| Runners ↔ FindingModel | Runners instantiate `Finding` dataclasses and return them | No shared mutable state; runners produce, everything else consumes |
| ReportBuilder ↔ FindingModel | ReportBuilder receives `ScanResult` containing `list[Finding]` | ReportBuilder is read-only; never mutates findings |
| AIExplainer ↔ FindingModel | AIExplainer mutates `finding.ai_explanation` field post-scan | This is the only post-scan mutation; safe because scan is already complete |

## Scaling Considerations

This is a desktop application — "scaling" means handling larger codebases and more features, not user concurrency.

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Small projects (< 100 files) | No adjustment needed; all 4 scanners finish in under 60 seconds |
| Medium projects (100–500 files) | ThreadPoolExecutor(4) is sufficient; target is under 3 minutes |
| Large projects (500–5000 files) | Add per-scanner timeout (e.g. 120s); allow user to select which scanners to run; Semgrep may need `--max-memory` flag |
| Monorepo / large git repos | Trufflehog scanning git history can be extremely slow; add `--since-commit HEAD~50` option; Gitleaks similarly needs depth limiting |

### Scaling Priorities

1. **First bottleneck:** Semgrep on large codebases. Fix with `--max-memory 2000` and `--timeout 60` flags; expose as settings.
2. **Second bottleneck:** Trufflehog on deep git history. Fix with `--since-commit` depth limit option.

## Sources

- PyInstaller documentation on `sys._MEIPASS` and `datas` bundling (HIGH confidence — well-documented official pattern)
- Python `subprocess` module documentation — `Popen` vs `communicate()` streaming (HIGH confidence)
- Tkinter threading model — main-thread-only widget access requirement (HIGH confidence — documented in Tkinter internals)
- CustomTkinter README — no additional threading guarantees beyond Tkinter (MEDIUM confidence — training knowledge, should verify against current CustomTkinter docs)
- Semgrep CLI `--json` / `--config=auto` flags (HIGH confidence — stable CLI interface)
- Trufflehog `filesystem --json` mode (MEDIUM confidence — CLI flags may have changed; verify against current release)
- Grype `-o json` output flag (MEDIUM confidence — verify against current release)
- Gitleaks `--report-format=json` flag (MEDIUM confidence — verify against current release)
- Groq OpenAI-compatible API endpoint (HIGH confidence — publicly documented)

---
*Architecture research for: Python desktop SAST scanner (SecScan)*
*Researched: 2026-03-29*

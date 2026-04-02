# Phase 1: Foundation - Research

**Researched:** 2026-03-29
**Domain:** Python scanner wrappers, subprocess/threading architecture, binary resolution, domain models
**Confidence:** HIGH

---

## Summary

Phase 1 establishes the entire non-GUI backend of SecScan. The project scaffold already exists: domain models (`Finding`, `ScanResult`, `Severity`) are implemented in `app/core/models.py`, `BaseTool` in `app/tools/base.py`, and all four tool wrappers (`semgrep.py`, `trufflehog.py`, `grype.py`, `gitleaks.py`) exist as `NotImplementedError` stubs. The `Scanner` orchestrator (`app/core/scanner.py`) is also scaffolded but runs tools sequentially using a callback, not concurrently with a `queue.Queue`.

The work in this phase is filling those stubs: implement each tool's `run()` method to subprocess-invoke the binary, parse its JSON output, and return `list[Finding]`; then replace the sequential orchestrator with a `ThreadPoolExecutor` + `queue.Queue` model that emits `ProgressEvent` objects. The existing test suite (14 tests, all passing) covers models, language detection, and ingestion — Phase 1 must add runner tests driven entirely by fixture JSON files (no live binaries in CI).

Two critical gaps in the existing scaffold: (1) `BaseTool.resolve_binary()` handles vendor vs. system PATH but does NOT handle PyInstaller `sys._MEIPASS` — that needs to be added as `BinaryLocator`. (2) The `Scanner` class uses a synchronous callback; it must be refactored to `queue.Queue` + `threading.Thread` so it never blocks the Tkinter main thread.

**Primary recommendation:** Implement tools in this order: models/data (done), Gitleaks (simplest JSON), Trufflehog filesystem, Semgrep, Grype. Each tool gets a fixture JSON file in `tests/fixtures/` and tests that mock `subprocess.run`. Upgrade BaseTool to BinaryLocator with `sys._MEIPASS` support. Rewrite Scanner to `ThreadPoolExecutor` + `queue.Queue`.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SCAN-01 | User can select a local folder for recursive security scan | `ingestion.resolve_local_path()` already implemented; needs to be wired to orchestrator |
| SCAN-02 | User can provide a public Git repo URL to clone and scan | `ingestion.clone_repository()` already implemented; needs integration test |
| SCAN-03 | System auto-detects project language(s) and selects appropriate rules | `language.detect_languages()` already implemented; needs mapping to Semgrep rule sets |
| BACK-01 | Semgrep runs SAST and returns findings with file, line, description | Implement `SemgrepTool.run()` using `--json` flag; map `check_id`→title, `start.line`→line, `extra.lines`→snippet, `extra.severity`→Severity |
| BACK-02 | Trufflehog scans Git history for exposed secrets | Implement `TrufflehogTool.run()` using `trufflehog git` subcommand with `--json`; parse `SourceMetadata.Data.Git` OR `filesystem` depending on context |
| BACK-03 | Grype checks project dependencies against CVE database | Implement `GrypeTool.run()` using `grype dir:<path> -o json`; parse `matches[].vulnerability` and `matches[].artifact` |
| BACK-04 | Gitleaks scans project files for exposed keys/credentials | Implement `GitleaksTool.run()` using `gitleaks detect --no-git --report-format json --report-path -`; parse array of `{RuleID, Secret, File, StartLine}` |
| BACK-05 | Orchestrator runs all 4 tools concurrently with real-time progress callbacks | Rewrite `Scanner` to use `ThreadPoolExecutor` + `queue.Queue` + `ProgressEvent` dataclass |
| DATA-01 | `Finding` model: title, severity, file, line, description, source tool, code snippet | Already implemented in `app/core/models.py` — verify fields are sufficient for all tool outputs |
| DATA-02 | `ScanResult` model: findings list, scan metadata, duration | Already implemented in `app/core/models.py` |
| DATA-03 | `Severity` enum: Critical, High, Medium, Low, Info | Already implemented as `Severity(str, Enum)` in `app/core/models.py` |
</phase_requirements>

---

## Project Constraints (from CLAUDE.md)

- Python 3.11+ (confirmed: 3.12.3 on this machine)
- Stack: CustomTkinter, Semgrep, Trufflehog, Grype, Gitleaks, Groq/Llama 3.1, Jinja2, WeasyPrint, PyInstaller, PyArmor
- Phases 1–5: 100% local, no license, no compilation, `DEV_MODE=True` enables all Team-tier features
- Binaries go in `tools/` (but scaffold uses `vendors/`; see Architecture Patterns) and resolved via `BinaryLocator` with `sys._MEIPASS` fallback
- All scanner execution MUST run off the Tkinter main thread via `queue.Queue`
- `DEV_MODE=True` is set via `SECSCAN_DEV` env var in `app/config.py`
- Semgrep rules bundled locally in `assets/rules/` — `--config auto` is offline-incompatible (LOCKED from STATE.md)
- `queue.Queue` + `root.after(100ms)` threading pattern MANDATORY from Phase 1 (LOCKED from STATE.md)
- `BinaryLocator` with `sys._MEIPASS` fallback established in Phase 1 (LOCKED from STATE.md)

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `subprocess` | 3.12 builtin | Invoke scanner binaries | Only correct way to run external processes; `asyncio.subprocess` adds complexity without benefit for this use case |
| Python stdlib `threading` | 3.12 builtin | Run orchestrator off main thread | Required by Tkinter threading constraint |
| Python stdlib `concurrent.futures.ThreadPoolExecutor` | 3.12 builtin | Parallel scanner execution | Higher-level than raw Thread; handles exceptions, futures, and cleanup automatically |
| Python stdlib `queue.Queue` | 3.12 builtin | Thread-safe progress events to caller | Mandated by project decisions; compatible with Tkinter `root.after()` polling |
| Python stdlib `dataclasses` | 3.12 builtin | `Finding`, `ScanResult`, `ProgressEvent` | Already used in project; clean, zero-dependency |
| `pytest` | 8.2.0 (pinned) | Test framework | Already in requirements.txt |
| `pytest-cov` | 5.0.0 (pinned) | Coverage measurement | Already in requirements.txt |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python stdlib `json` | 3.12 builtin | Parse scanner JSON output | All four scanners output JSON |
| Python stdlib `shutil` | 3.12 builtin | Binary PATH resolution | Already used in `BaseTool.resolve_binary()` |
| Python stdlib `unittest.mock` | 3.12 builtin | Mock subprocess in tests | Mandatory — tests must not require live binaries |
| `pydantic` | 2.7.0 (pinned) | Optional: validate scanner JSON | Available but dataclasses are sufficient for Phase 1 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ThreadPoolExecutor` | `asyncio` | asyncio would require rewriting Tkinter integration; threads are simpler for subprocess I/O |
| `queue.Queue` | `asyncio.Queue` | Project mandates `queue.Queue` for Tkinter compatibility |
| `subprocess.run()` | `subprocess.Popen()` | `run()` is simpler for capturing full output; `Popen()` needed only for streaming stdout line-by-line (not needed here — output buffered then parsed) |
| dataclasses | pydantic | Pydantic adds validation but dataclasses are zero-overhead and already used in existing models |

**Installation:** All dependencies already in `requirements.txt`. No new packages needed for Phase 1.

---

## Architecture Patterns

### Recommended Project Structure

The scaffold is already laid out. Phase 1 fills these files:

```
app/
├── core/
│   ├── models.py        # DONE: Finding, ScanResult, Severity, FindingCategory
│   ├── language.py      # DONE: detect_languages(), count_files()
│   ├── ingestion.py     # DONE: resolve_local_path(), clone_repository()
│   └── scanner.py       # REFACTOR: replace sequential Scanner with ScanOrchestrator
├── tools/
│   ├── base.py          # REFACTOR: add sys._MEIPASS support → rename class to BinaryLocator
│   ├── semgrep.py       # IMPLEMENT: run() method
│   ├── trufflehog.py    # IMPLEMENT: run() method
│   ├── grype.py         # IMPLEMENT: run() method
│   └── gitleaks.py      # IMPLEMENT: run() method
assets/
└── rules/
    ├── python.yaml      # Bundled Semgrep ruleset — NEW
    ├── javascript.yaml  # Bundled Semgrep ruleset — NEW
    └── ...              # One per supported language
tests/
├── fixtures/
│   ├── semgrep_output.json    # Sample semgrep --json output — NEW
│   ├── trufflehog_output.json # Sample trufflehog --json output — NEW
│   ├── grype_output.json      # Sample grype -o json output — NEW
│   └── gitleaks_output.json   # Sample gitleaks --report-format json output — NEW
├── test_tools_semgrep.py      # NEW
├── test_tools_trufflehog.py   # NEW
├── test_tools_grype.py        # NEW
├── test_tools_gitleaks.py     # NEW
├── test_orchestrator.py       # NEW (replaces/extends test_scanner.py)
└── test_binary_locator.py     # NEW
```

### Pattern 1: BinaryLocator — sys._MEIPASS + vendor + PATH fallback chain

**What:** Resolves scanner binary path through three-level fallback: (1) `sys._MEIPASS` (PyInstaller frozen), (2) project `vendors/` directory, (3) system PATH.
**When to use:** Every tool `run()` method calls `self.resolve_binary()` before building the subprocess command.

```python
# Source: PyInstaller docs (https://pyinstaller.org/en/stable/runtime-information.html)
# + existing app/tools/base.py pattern

import sys
import platform
import shutil
from pathlib import Path

VENDOR_DIR = Path(__file__).parent.parent.parent / "vendors"

def resolve_binary(tool_name: str) -> str:
    system = "win" if platform.system() == "Windows" else "linux"
    ext = ".exe" if system == "win" else ""

    # 1. PyInstaller frozen: sys._MEIPASS contains bundled binaries
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        frozen_bin = Path(sys._MEIPASS) / f"{tool_name}{ext}"
        if frozen_bin.exists():
            return str(frozen_bin)

    # 2. Dev mode: vendor directory bundled with repo
    vendor_bin = VENDOR_DIR / system / f"{tool_name}{ext}"
    if vendor_bin.exists():
        return str(vendor_bin)

    # 3. System PATH fallback
    system_bin = shutil.which(tool_name)
    if system_bin:
        return system_bin

    raise FileNotFoundError(
        f"'{tool_name}' not found. Install globally or place in vendors/{system}/."
    )
```

### Pattern 2: Tool runner — subprocess + JSON parsing + Finding normalization

**What:** Every runner follows the same pattern: resolve binary → build args → subprocess.run → json.loads → normalize to `list[Finding]`.
**When to use:** All four scanner tools.

```python
# Source: verified pattern from semgrep/gitleaks/grype CLI docs

import subprocess
import json
from pathlib import Path

def run(self, project_path: Path) -> list[Finding]:
    binary = self.resolve_binary()
    cmd = [binary, "--json", str(project_path)]  # varies per tool
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,  # 5 minutes max per tool
    )
    # Note: most security tools use non-zero exit code to signal "findings found"
    # Do NOT check returncode == 0; instead parse stdout regardless
    raw = json.loads(result.stdout or "[]")
    return self._normalize(raw)
```

**Critical note on exit codes:** Semgrep exits 1 when it finds issues. Gitleaks exits 1 when secrets are found. Grype exits non-zero based on severity thresholds. Do NOT use `check=True` or filter on `returncode == 0`.

### Pattern 3: ScanOrchestrator — ThreadPoolExecutor + queue.Queue

**What:** Runs all four scanner tools concurrently in a thread pool; emits typed `ProgressEvent` objects to a caller-owned `queue.Queue` without blocking the caller.
**When to use:** The single entry point for all scan operations.

```python
# Source: Python stdlib docs + project mandate from STATE.md

import queue
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum

class EventType(str, Enum):
    TOOL_START = "tool_start"
    TOOL_PROGRESS = "tool_progress"
    TOOL_DONE = "tool_done"
    TOOL_ERROR = "tool_error"
    SCAN_COMPLETE = "scan_complete"

@dataclass
class ProgressEvent:
    event_type: EventType
    tool: str
    message: str
    findings_count: int = 0

class ScanOrchestrator:
    def scan(
        self,
        project_path: Path,
        progress_queue: queue.Queue,
        plan: str = "team",
    ) -> ScanResult:
        """Run all scanners concurrently. Thread-safe: puts ProgressEvents into queue."""
        findings = []
        errors = []
        tools_used = []

        tool_classes = [SemgrepTool, TrufflehogTool, GrypeTool, GitleaksTool]

        def run_tool(tool_cls):
            tool = tool_cls()
            progress_queue.put(ProgressEvent(EventType.TOOL_START, tool.tool_name, "Starting..."))
            try:
                result = tool.run(project_path)
                progress_queue.put(ProgressEvent(
                    EventType.TOOL_DONE, tool.tool_name,
                    f"Found {len(result)} issues", len(result)
                ))
                return result, tool.tool_name, None
            except Exception as e:
                progress_queue.put(ProgressEvent(EventType.TOOL_ERROR, tool.tool_name, str(e)))
                return [], tool.tool_name, str(e)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(run_tool, cls): cls for cls in tool_classes}
            for future in as_completed(futures):
                result, name, error = future.result()
                findings.extend(result)
                tools_used.append(name)
                if error:
                    errors.append(f"{name}: {error}")

        progress_queue.put(ProgressEvent(EventType.SCAN_COMPLETE, "", f"Done — {len(findings)} findings"))
        # ... build and return ScanResult
```

### Pattern 4: Scanner JSON output formats

#### Semgrep `--json`
```json
{
  "results": [
    {
      "check_id": "python.lang.security.audit.formatted-sql-query.formatted-sql-query",
      "path": "app/db.py",
      "start": {"line": 42, "col": 4, "offset": 1204},
      "end":   {"line": 42, "col": 58, "offset": 1258},
      "extra": {
        "message": "Detected use of f-string formatting in SQL query...",
        "severity": "ERROR",
        "lines": "    cursor.execute(f\"SELECT * FROM users WHERE id={uid}\")"
      }
    }
  ],
  "errors": []
}
```
Severity mapping: `ERROR` → High, `WARNING` → Medium, `INFO` → Low. (Note: some rules emit `CRITICAL` in newer semgrep versions — map to `Severity.CRITICAL`.)

#### Trufflehog `filesystem <path> --json`
```json
{
  "SourceMetadata": {
    "Data": {
      "Filesystem": {
        "file": "config/secrets.py",
        "line": 7
      }
    }
  },
  "SourceName": "trufflehog - filesystem",
  "DetectorName": "AWS",
  "Verified": true,
  "Raw": "AKIAYVP4CIPPERUVIFXG",
  "Redacted": "AKIAxxxxxxxxxxxxxxxxxxxG"
}
```
**Important:** Trufflehog outputs one JSON object per line (NDJSON), NOT a JSON array. Must use `for line in stdout.splitlines()` and `json.loads(line)`. For git history scanning (BACK-02), use `trufflehog git file:///path/to/repo --json` — `filesystem` only scans working tree; `git` scans all commits.

#### Grype `dir:<path> -o json`
```json
{
  "matches": [
    {
      "vulnerability": {
        "id": "CVE-2023-1234",
        "severity": "High",
        "description": "...",
        "fix": {"state": "fixed", "versions": ["2.28.2"]}
      },
      "artifact": {
        "name": "requests",
        "version": "2.20.0",
        "type": "python",
        "locations": [{"path": "requirements.txt"}]
      }
    }
  ]
}
```
Severity values: `Critical`, `High`, `Medium`, `Low`, `Negligible` — map Negligible → `Severity.INFO`.

#### Gitleaks `detect --no-git --report-format json --report-path -`
```json
[
  {
    "RuleID": "generic-api-key",
    "Secret": "sk_live_1234hardcoded",
    "File": "config.py",
    "StartLine": 1,
    "EndLine": 1,
    "Match": "STRIPE_KEY = \"sk_live_1234hardcoded\"",
    "Author": "",
    "Commit": "",
    "Date": ""
  }
]
```
Use `--no-git` when the scanned directory is not a git repo (or when scanning working tree only). Use without `--no-git` for git repos to also scan staged changes. When the directory has no `.git` folder and `--no-git` is omitted, gitleaks exits with an error — graceful skip required (Phase 5 concern, but the runner must not crash).

### Pattern 5: Language → Semgrep ruleset mapping

```python
# Source: STATE.md decision + semgrep-rules repo structure
# Rules stored locally in assets/rules/ (offline-safe; --config auto banned)

LANGUAGE_TO_RULESET: dict[str, str] = {
    "Python":     "assets/rules/python",
    "JavaScript": "assets/rules/javascript",
    "TypeScript": "assets/rules/typescript",
    "Go":         "assets/rules/go",
    "Java":       "assets/rules/java",
    "Ruby":       "assets/rules/ruby",
    "PHP":        "assets/rules/php",
}

def select_rulesets(languages: list[str]) -> list[str]:
    """Return list of --config args for detected languages."""
    return [LANGUAGE_TO_RULESET[lang] for lang in languages if lang in LANGUAGE_TO_RULESET]
```

Semgrep accepts multiple `--config` flags. If no language matches (e.g., pure YAML/JSON project), fall back to `assets/rules/generic` or skip Semgrep with a warning.

### Anti-Patterns to Avoid

- **Checking `returncode == 0` for security tools:** Most security scanners exit non-zero when they find issues. Always parse stdout regardless of exit code; only treat stderr + non-zero as a true error.
- **Parsing trufflehog output as a JSON array:** Trufflehog emits NDJSON (one JSON object per line). `json.loads(stdout)` will raise `JSONDecodeError`. Use `[json.loads(line) for line in stdout.splitlines() if line.strip()]`.
- **Running scanners on the main thread:** The Tkinter `root.mainloop()` must never block. Every scanner invocation must be in a thread.
- **`--config auto` for Semgrep:** This requires network access and breaks offline use. Only local `--config path/to/rules` is acceptable.
- **Placing BinaryLocator detection after vendor check:** `sys._MEIPASS` check MUST come first; in frozen mode, the vendor directory won't exist at its development path.
- **Hardcoding the vendor directory path in tests:** Unit tests for `BinaryLocator` must mock `sys._MEIPASS` and `platform.system()`; never assume a specific file system layout.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SAST rule authoring | Custom regex-based AST scanner | Semgrep with bundled rules | Rule quality, false positive rate, language coverage — months of engineering |
| Secret pattern detection | Custom regex matcher | Trufflehog + Gitleaks | 700+ detector patterns, verification against live APIs, entropy analysis |
| CVE database | Local CVE lookup | Grype | Grype ships its own offline-capable DB; maintaining CVE currency is a full-time job |
| JSON schema validation for scanner output | pydantic models for each scanner's output | Simple dict access with `.get()` and defaults | Scanner output shapes are well-known; full schema validation adds overhead without benefit for this phase |
| Thread pool management | Manual `threading.Thread` list | `concurrent.futures.ThreadPoolExecutor` | Exception propagation, result collection, and cleanup are handled automatically |

**Key insight:** The entire value of this project is integrating four best-in-class security tools — not reimplementing their core logic. Phase 1 is pure glue code.

---

## Common Pitfalls

### Pitfall 1: Scanner exit codes signal findings, not errors
**What goes wrong:** `subprocess.run(..., check=True)` raises `CalledProcessError` when a scanner finds issues (exit code 1), causing the tool to appear as "failed" when it found real security issues.
**Why it happens:** Security tools use exit codes to signal "clean/not-clean" rather than "success/failure."
**How to avoid:** Never use `check=True`. Capture both stdout and stderr. Treat stderr + empty stdout as an error condition.
**Warning signs:** Tool wrapper catches CalledProcessError and returns empty list even though findings exist.

### Pitfall 2: Trufflehog NDJSON output
**What goes wrong:** `json.loads(result.stdout)` raises `JSONDecodeError` because trufflehog emits one JSON object per line, not a JSON array.
**Why it happens:** Trufflehog uses NDJSON (newline-delimited JSON) format.
**How to avoid:** Parse with `[json.loads(line) for line in result.stdout.splitlines() if line.strip()]`.
**Warning signs:** Tests pass with fixture data but fail on real trufflehog output.

### Pitfall 3: Gitleaks crashes on non-git directories
**What goes wrong:** `gitleaks detect` (without `--no-git`) on a directory without `.git` folder prints an error to stderr and exits non-zero with no JSON output. Treating this as an empty result silently masks the error.
**Why it happens:** Gitleaks requires a git repo for its default mode. `--no-git` bypasses this but skips commit history scanning.
**How to avoid:** Check for `.git` directory existence before running gitleaks. Use `--no-git` if absent. Emit a `ProgressEvent` with status "skipped" if `.git` is missing and the runner is configured for git-history mode.
**Warning signs:** `result.stderr` contains "not a git repo" or similar.

### Pitfall 4: Semgrep rule bundling strategy
**What goes wrong:** `--config auto` works in dev but fails in the distributed binary (no network). Forgetting to bundle rules during Phase 1 means Phase 7 packaging fails late.
**Why it happens:** `--config auto` fetches rules from semgrep.dev at runtime.
**How to avoid:** Download the `semgrep/semgrep-rules` repository (or selected subsets) into `assets/rules/` during Phase 1. Use `--config assets/rules/python` etc. This path must also be resolved via `BinaryLocator`-style logic in frozen mode.
**Warning signs:** Tests pass locally (network available) but fail in CI or offline.

### Pitfall 5: BinaryLocator path ordering in frozen mode
**What goes wrong:** If vendor path is checked before `sys._MEIPASS`, the frozen app cannot find its bundled binaries because the `vendors/` directory doesn't exist in the PyInstaller `_internal` folder at the development path.
**Why it happens:** PyInstaller flattens all bundled data under `sys._MEIPASS`; the source tree's directory structure doesn't exist.
**How to avoid:** Always check `sys._MEIPASS` first. Unit test must mock `sys.frozen = True`, `sys._MEIPASS = "/fake/meipass"`, and verify the frozen path is tried.
**Warning signs:** BinaryLocator unit test passes but frozen binary can't find scanners.

### Pitfall 6: queue.Queue filled too fast for slow Tkinter polling
**What goes wrong:** If a scanner emits hundreds of progress events before the GUI polls the queue, events back up and the queue grows unbounded.
**Why it happens:** Tkinter polls with `root.after(100ms)` — if scanners emit events faster than 10/sec this builds up.
**How to avoid:** Emit coarse-grained events only: TOOL_START, TOOL_DONE, TOOL_ERROR, SCAN_COMPLETE. Avoid per-finding events. Use `queue.Queue(maxsize=0)` (unbounded) but keep event volume low.
**Warning signs:** Memory grows during long scans, or Tkinter becomes unresponsive despite non-blocking design.

---

## Code Examples

### Fixture-based test for a tool runner

```python
# Source: Python unittest.mock docs + project test pattern in tests/conftest.py

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from app.tools.gitleaks import GitleaksTool
from app.core.models import Severity

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "gitleaks_output.json"

@pytest.fixture
def gitleaks_fixture():
    return FIXTURE_PATH.read_text()

def test_gitleaks_parses_findings(tmp_path, gitleaks_fixture):
    mock_result = MagicMock()
    mock_result.stdout = gitleaks_fixture
    mock_result.stderr = ""
    mock_result.returncode = 1  # gitleaks exits 1 when findings exist

    with patch("subprocess.run", return_value=mock_result):
        tool = GitleaksTool()
        findings = tool.run(tmp_path)

    assert len(findings) > 0
    assert findings[0].tool == "gitleaks"
    assert findings[0].severity in list(Severity)
    assert findings[0].file_path != ""
    assert findings[0].line_number > 0
```

### BinaryLocator unit test for sys._MEIPASS

```python
# Source: PyInstaller runtime-information docs

import sys
from unittest.mock import patch, MagicMock
from app.tools.base import resolve_binary  # after refactor

def test_binary_locator_uses_meipass_first(tmp_path):
    fake_meipass = tmp_path / "_internal"
    fake_meipass.mkdir()
    fake_bin = fake_meipass / "gitleaks"
    fake_bin.write_text("")
    fake_bin.chmod(0o755)

    with patch.object(sys, "frozen", True, create=True), \
         patch.object(sys, "_MEIPASS", str(fake_meipass), create=True):
        result = resolve_binary("gitleaks")
        assert result == str(fake_bin)

def test_binary_locator_falls_back_to_vendor(tmp_path):
    # sys.frozen not set → skip MEIPASS, go to vendor check
    vendor_bin = tmp_path / "linux" / "gitleaks"
    vendor_bin.parent.mkdir()
    vendor_bin.write_text("")
    with patch("app.tools.base.VENDOR_DIR", tmp_path):
        result = resolve_binary("gitleaks")
        assert result == str(vendor_bin)
```

### ScanOrchestrator queue usage in caller thread

```python
# Pattern for how GUI (Phase 2) will consume the queue
import queue
import threading

def start_scan_in_background(project_path):
    q = queue.Queue()
    orchestrator = ScanOrchestrator()

    def _run():
        orchestrator.scan(project_path, progress_queue=q)

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return q  # GUI polls this with root.after(100, poll_queue)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Semgrep `--config auto` (fetches from network) | `--config path/to/local/rules` | Always existed, but auto became default | Must bundle rules; project decision enforces this |
| Trufflehog v2 (Python, different output) | Trufflehog v3 (Go binary, NDJSON output) | ~2022 | All output parsing must assume Go binary NDJSON format |
| `gitleaks protect` for directory scan | `gitleaks detect --no-git` | v8.x | `protect` only works on git repos; `detect --no-git` for plain dirs |
| Grype `image:` prefix | `dir:` prefix for directory scanning | Current | Must prefix path with `dir:` to scan a filesystem directory |
| PyInstaller `--onefile` | `--onefile` banned; use `--onedir` | Project decision | `--onefile` causes 10-30s Windows startup delay |

**Deprecated/outdated:**
- Trufflehog v2 Python pip package: replaced by Go binary v3. Do not `pip install trufflehog`.
- `semgrep --config r/all`: downloads all rules, extremely slow and network-dependent. Never use.
- BaseTool class name: will be refactored to include BinaryLocator logic; plan tasks should reference the updated class.

---

## Open Questions

1. **Semgrep ruleset bundling: which rulesets and what is the total size?**
   - What we know: `semgrep/semgrep-rules` on GitHub is the community ruleset; individual language packs are subdirectories. Total repo is ~100MB+ but language-specific subsets are much smaller.
   - What's unclear: Which specific rule files to bundle? Size constraint for the distributed binary?
   - Recommendation: For Phase 1, bundle `p/python` and `p/javascript` rulesets by downloading them via `semgrep --config p/python --dry-run` and caching to `assets/rules/`. Document the chosen set in a `assets/rules/MANIFEST.md`. Full ruleset selection should be a sub-task in the plan.

2. **Trufflehog: git subcommand vs filesystem subcommand for BACK-02**
   - What we know: `trufflehog git` scans full commit history; `trufflehog filesystem` scans working tree only. BACK-02 says "scans Git history."
   - What's unclear: Should the runner always use `git` subcommand? What if the scanned dir is not a git repo?
   - Recommendation: Use `trufflehog git file:///absolute/path` when `.git` exists, fallback to `trufflehog filesystem` when not. This mirrors the gitleaks `--no-git` pattern.

3. **Scanner binary versions: need re-verification before pinning**
   - What we know: STATE.md flags this explicitly: "Scanner binary versions in research are from Aug 2025 training data — must re-verify against GitHub releases before pinning."
   - What's unclear: Current stable versions of semgrep, trufflehog, grype, gitleaks.
   - Recommendation: First task in the plan should be verifying current releases on GitHub. Do NOT pin versions from this research document.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ | All code | Yes | 3.12.3 | — |
| pytest 8.2.0 | Tests | Yes (installed) | 8.2.0 | — |
| pytest-cov 5.0.0 | Coverage | Yes (installed) | 5.0.0 | — |
| semgrep binary | BACK-01 | No | — | Tests use fixture JSON only (mocked subprocess) |
| trufflehog binary | BACK-02 | No | — | Tests use fixture JSON only (mocked subprocess) |
| grype binary | BACK-03 | No | — | Tests use fixture JSON only (mocked subprocess) |
| gitleaks binary | BACK-04 | No | — | Tests use fixture JSON only (mocked subprocess) |
| git CLI | SCAN-02 (clone) | Not confirmed | — | Required for `clone_repository()`; verify with `command -v git` |
| vendors/linux/ | BinaryLocator | Yes (empty dir) | — | Populated when binaries are downloaded |
| vendors/win/ | BinaryLocator | Yes (empty dir) | — | Populated when binaries are downloaded |

**Missing dependencies with no fallback:**
- None for Phase 1 — all scanner invocations are mocked in tests; live binaries not required to pass the test suite.

**Missing dependencies with fallback:**
- All four scanner binaries: tests mock `subprocess.run`, so Phase 1 passes 100% in CI without any scanner installed. Live binaries needed only for manual integration verification.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.2.0 |
| Config file | `pytest.ini` (exists: `testpaths = tests`, `addopts = -v --tb=short`) |
| Quick run command | `python3 -m pytest tests/ -q` |
| Full suite command | `python3 -m pytest tests/ --cov=app/core --cov=app/tools -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SCAN-01 | `resolve_local_path()` accepts valid dir, rejects invalid | unit | `pytest tests/test_ingestion.py -x` | Yes |
| SCAN-02 | `clone_repository()` clones git URL to temp dir | unit (mock subprocess) | `pytest tests/test_ingestion.py -x` | Yes |
| SCAN-03 | `detect_languages()` + `select_rulesets()` mapping | unit | `pytest tests/test_language.py -x` | Yes (partial — `select_rulesets` missing) |
| BACK-01 | `SemgrepTool.run()` parses fixture JSON to Finding list | unit | `pytest tests/test_tools_semgrep.py -x` | No — Wave 0 |
| BACK-02 | `TrufflehogTool.run()` parses NDJSON to Finding list | unit | `pytest tests/test_tools_trufflehog.py -x` | No — Wave 0 |
| BACK-03 | `GrypeTool.run()` parses grype JSON to Finding list | unit | `pytest tests/test_tools_grype.py -x` | No — Wave 0 |
| BACK-04 | `GitleaksTool.run()` parses JSON array to Finding list | unit | `pytest tests/test_tools_gitleaks.py -x` | No — Wave 0 |
| BACK-05 | `ScanOrchestrator` runs tools concurrently, emits ProgressEvents | unit | `pytest tests/test_orchestrator.py -x` | No — Wave 0 |
| DATA-01 | `Finding` dataclass has all required fields | unit (existing) | `pytest tests/test_scanner.py -x` | Yes |
| DATA-02 | `ScanResult` has findings, metadata, duration | unit (existing) | `pytest tests/test_scanner.py -x` | Yes |
| DATA-03 | `Severity` enum has Critical/High/Medium/Low/Info | unit (existing) | `pytest tests/ -k severity` | Yes (implicit) |
| (cross) | `BinaryLocator` resolves MEIPASS and vendor paths | unit | `pytest tests/test_binary_locator.py -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `python3 -m pytest tests/ -q`
- **Per wave merge:** `python3 -m pytest tests/ --cov=app/core --cov=app/tools --cov-fail-under=90`
- **Phase gate:** Full suite green + coverage >= 90% on core data path before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/fixtures/semgrep_output.json` — realistic semgrep JSON fixture
- [ ] `tests/fixtures/trufflehog_output.json` — realistic trufflehog NDJSON fixture
- [ ] `tests/fixtures/grype_output.json` — realistic grype JSON fixture
- [ ] `tests/fixtures/gitleaks_output.json` — realistic gitleaks JSON fixture
- [ ] `tests/test_tools_semgrep.py` — covers BACK-01
- [ ] `tests/test_tools_trufflehog.py` — covers BACK-02
- [ ] `tests/test_tools_grype.py` — covers BACK-03
- [ ] `tests/test_tools_gitleaks.py` — covers BACK-04
- [ ] `tests/test_orchestrator.py` — covers BACK-05
- [ ] `tests/test_binary_locator.py` — covers BinaryLocator MEIPASS + vendor + PATH

---

## Sources

### Primary (HIGH confidence)
- Python stdlib docs (threading, concurrent.futures, queue, subprocess) — threading/queue architecture
- PyInstaller official docs https://pyinstaller.org/en/stable/runtime-information.html — `sys._MEIPASS` and `sys.frozen` patterns
- Semgrep official docs https://semgrep.dev/docs/semgrep-appsec-platform/json-and-sarif — JSON output schema
- Grype DeepWiki https://deepwiki.com/anchore/grype/4.2-json-output — JSON output structure
- Existing project code (`app/core/models.py`, `app/tools/base.py`, `app/core/scanner.py`) — confirmed scaffold state

### Secondary (MEDIUM confidence)
- Trufflehog GitHub README https://github.com/trufflesecurity/trufflehog/blob/main/README.md — NDJSON format confirmed from example + GitHub issue #705
- Gitleaks GitHub https://github.com/gitleaks/gitleaks — `detect --no-git` flag; JSON field names `RuleID`, `Secret`, `File`, `StartLine`
- Semgrep severity KB https://semgrep.dev/docs/kb/rules/understand-severities — ERROR/WARNING/INFO → High/Medium/Low mapping
- TruffleHog commands blog https://trufflesecurity.com/blog/trufflehog-commands-git-vs-filesystem — git vs filesystem subcommand distinction

### Tertiary (LOW confidence — flag for validation)
- Scanner binary current versions: NOT researched. STATE.md explicitly flags this as stale. Must be verified against GitHub releases as first task.
- Semgrep ruleset bundle size and specific YAML files to include: not verified. Depends on which `semgrep/semgrep-rules` subdirectories are selected.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all Python stdlib; existing requirements.txt confirmed
- Architecture: HIGH — existing code scaffold confirmed; patterns from official docs
- Scanner JSON formats: MEDIUM — semgrep and grype from official docs; trufflehog/gitleaks from GitHub + secondary sources
- Pitfalls: HIGH — scanner exit code behavior is well-documented; NDJSON format confirmed from GitHub issue
- Binary versions: LOW — explicitly flagged as stale in STATE.md; must re-verify

**Research date:** 2026-03-29
**Valid until:** 2026-04-28 (stable Python stdlib patterns; scanner binary versions should be re-verified before implementation)

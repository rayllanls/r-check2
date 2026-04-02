# Stack Research

**Domain:** Python desktop SAST tool with embedded scanner binaries and CustomTkinter GUI
**Researched:** 2026-03-29
**Confidence:** MEDIUM (external version verification blocked — versions based on knowledge cutoff Aug 2025; flag for pip verify before first install)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11.x (min 3.11, pin to 3.11 for PyInstaller stability) | Runtime | 3.12+ has occasional PyInstaller hook regressions; 3.11 is the proven sweet spot for PyInstaller-bundled desktop apps on Windows. 3.13 adds GIL changes that have not been stress-tested with CTkinter's threading model. |
| CustomTkinter | 5.2.2 | Desktop GUI framework | Only actively maintained Tkinter wrapper with modern dark-mode widgets, built-in CTkScrollableFrame, and theme system. Ships its own widget set on top of Tk — no external theme engine. Actively used in 2024-25 Python desktop tooling. |
| PyInstaller | 6.6.0 | Binary packaging (Phase 7 only) | De-facto standard for Python→single-binary packaging on Windows and Linux. v6.x added `--collect-all` improvements critical for bundling customtkinter's asset directory. `--onedir` recommended over `--onefile` for large bundles (600 MB) to avoid slow extraction on Windows Defender scan. |
| PyArmor | 8.x (latest 8.x) | Code obfuscation (Phase 7 only) | Works at the .pyc level, wraps PyInstaller output. Required per PROJECT.md constraints. Use after PyInstaller — do not attempt to pre-obfuscate and then bundle; that ordering breaks hook discovery. |

### Scanner Binary Management

| Component | Source | Version | Notes |
|-----------|--------|---------|-------|
| Semgrep OSS | GitHub releases: `returntocorp/semgrep` | Latest stable (1.7x as of Aug 2025) | Download platform-specific binary at build time via GitHub Actions. Linux: `semgrep-linux-x86_64`; Windows: `semgrep-windows-x86_64.exe`. Bundle under `assets/bins/`. |
| Trufflehog v3 | GitHub releases: `trufflesecurity/trufflehog` | Latest v3.x (3.8x as of Aug 2025) | Go binary, single file. Supports `--json` output for structured parsing. |
| Grype | GitHub releases: `anchore/grype` | Latest stable (0.7x as of Aug 2025) | SCA/dependency scanner. Requires a vulnerability DB; bundle `--add-cpes-if-none` and ship DB snapshot at build time or refresh on first run. DB size ~200 MB — factor into 600 MB budget. |
| Gitleaks v8 | GitHub releases: `gitleaks/gitleaks` | v8.x latest | Secrets scanner. Supports `--report-format json`. Smallest binary (~15 MB). |

**Binary management pattern:** Use `importlib.resources` or `sys._MEIPASS` path resolution to locate bundled binaries at runtime. Never hardcode paths — PyInstaller's `_MEIPASS` temp dir changes per run in `--onefile` mode.

### Report Generation

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| Jinja2 | >=3.1.4 | HTML report templating | Industry standard Python templating. Supports template inheritance for multi-section reports. Auto-escapes HTML output preventing XSS in finding snippets. |
| Chart.js | 4.x (bundle as static JS asset) | Severity charts in HTML reports | Pure JS, zero Python dependency, renders in any browser. Bundle locally in `assets/js/chart.min.js` — do not CDN-link; reports must work offline. |
| WeasyPrint | >=62.0 | HTML→PDF export | Pure Python, no wkhtmltopdf system dependency. Converts Jinja2-rendered HTML to PDF. Requires `cairocffi` and `pango` on Linux; on Windows ships its own DLLs. Heavier than pdfkit but has no `wkhtmltopdf` binary dependency. |

**Alternative for PDF:** `pdfkit` + `wkhtmltopdf` is simpler but requires bundling a second large binary. WeasyPrint avoids this entirely at the cost of slightly slower rendering. Use WeasyPrint.

### AI Explanation Layer

| Library | Version | Purpose | Why |
|---------|---------|---------|-----|
| groq | >=0.9.0 | Groq API client for Llama 3.1 | Official Groq Python SDK. Async-capable with `AsyncGroq`. Token is user-supplied — no API key ships with the app. Use `llama-3.1-70b-versatile` model ID (free tier). |

**Pattern:** AI explanations are non-blocking. Fire async Groq calls after scan completes; populate report with placeholders that fill in when responses arrive. If no token configured, render findings without AI explanation — never gate core functionality on AI availability.

### GUI Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | >=10.3.0 | Image handling for CTkImage | Required by CustomTkinter for icon/image display. Without Pillow, CTkImage raises ImportError. Always include. |
| darkdetect | >=0.8.0 | OS dark-mode detection | CustomTkinter bundles this as a dependency, but pin it explicitly to prevent resolution conflicts on Windows. |

### Process & Concurrency

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| psutil | >=5.9.8 | Scanner process management | Kill hung scanner subprocesses by PID tree. Standard library `subprocess` cannot reliably kill child processes spawned by scanner binaries on Windows; psutil can. |
| concurrent.futures | stdlib (Python 3.11) | ThreadPoolExecutor for parallel scanner runs | Run Semgrep, Trufflehog, Grype, Gitleaks concurrently. 4 threads max (one per scanner). IO-bound, so threads not processes. |

### Data & Utilities

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| packaging | >=24.0 | Version string parsing | Parse scanner binary version output to confirm bundled tool versions. |
| pydantic | >=2.7.0 | Finding data models | Validate and normalize JSON output from each scanner into a unified `Finding` schema. Each scanner has a different JSON structure — Pydantic v2 `model_validator` handles the normalization cleanly. |
| platformdirs | >=4.2.0 | OS-appropriate config/data dirs | Store user config (Groq token, preferences) in correct locations: `%APPDATA%` on Windows, `~/.config` on Linux. Never write config next to the binary. |
| python-dotenv | >=1.0.1 | DEV_MODE and local config loading | Load `DEV_MODE=True` and dev overrides from `.env` in project root during development. Strip from production build via PyInstaller `--exclude-module dotenv` or guard with `if DEV_MODE`. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| pytest | Unit and integration testing | Pin `pytest>=8.1.0`. Use `pytest-mock` for mocking subprocess calls during scanner tests. |
| pytest-mock | Subprocess/API mocking | Mock `subprocess.Popen` to test scanner orchestration without running real binaries in CI. |
| black | Code formatting | `black --line-length 100`. Enforce in pre-commit. |
| ruff | Linting | Replaces flake8 + isort. Use `ruff check --fix`. Much faster than pylint for large codebases. |
| mypy | Type checking | `mypy --strict` on core modules (`scanner/`, `models/`). Not required on GUI layer — Tkinter stubs are incomplete. |
| pyproject.toml | Project metadata and tool config | Single config file for black, ruff, mypy, pytest. Use `[tool.pytest.ini_options]` to set `testpaths`. |

## Installation

```bash
# Core GUI and runtime
pip install "customtkinter==5.2.2" "Pillow>=10.3.0" "darkdetect>=0.8.0"

# Report generation
pip install "Jinja2>=3.1.4" "WeasyPrint>=62.0"

# AI layer (optional, user-supplied token)
pip install "groq>=0.9.0"

# Data modeling and utilities
pip install "pydantic>=2.7.0" "packaging>=24.0" "platformdirs>=4.2.0" "python-dotenv>=1.0.1"

# Process management
pip install "psutil>=5.9.8"

# Dev dependencies
pip install -D "pytest>=8.1.0" "pytest-mock>=3.14.0" "black>=24.0.0" "ruff>=0.4.0" "mypy>=1.10.0"

# Phase 7 only (do not install in dev)
# pip install "pyinstaller==6.6.0" "pyarmor>=8.0"
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| CustomTkinter 5.2.2 | PyQt6 / PySide6 | If the team has Qt experience and needs richer widgets (tables, tree views). Qt apps are larger and harder to bundle on Windows (DLL hell). For this project's jargon-free UX, CTkinter's limited widget set is a feature not a bug. |
| CustomTkinter 5.2.2 | Dear PyGui | DPG has better performance for real-time data but uses GPU rendering — adds OpenGL dependency that complicates PyInstaller bundling significantly. Not worth it for this use case. |
| WeasyPrint | pdfkit + wkhtmltopdf | Only if WeasyPrint CSS rendering causes issues with report layout. pdfkit requires bundling `wkhtmltopdf` binary (~150 MB), adding to already 600 MB budget. |
| WeasyPrint | reportlab | If reports need precise programmatic layout (not template-based). Reportlab requires learning a separate layout API — Jinja2+WeasyPrint reuses the same HTML template. |
| groq SDK | openai SDK pointing at Groq endpoint | Groq's native SDK has better error handling for rate limits and supports streaming. Use `openai` SDK only if switching to OpenAI-compatible providers. |
| pydantic v2 | dataclasses | Pydantic v2 handles the cross-scanner JSON normalization in one `model_validator`. Dataclasses require manual validation logic across 4 different output schemas. |
| ruff | flake8 + pylint | ruff replaces both and is 10-100x faster. No reason to use flake8 in a new 2025 project. |
| ThreadPoolExecutor | multiprocessing.Pool | Scanner invocations are subprocess-bound (IO), not CPU-bound. Threads are sufficient and avoid pickling issues. multiprocessing adds complexity with no benefit here. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `tkinter` (bare) | No dark mode, no modern widgets, looks like 2004 on Windows. Target users are non-technical — ugly UI = trust loss. | CustomTkinter |
| `ttkthemes` / `ttkbootstrap` | These style native ttk widgets. CTkinter's widgets are not ttk-based — mixing them creates visual inconsistency. | CustomTkinter only |
| `wxPython` | wx apps require specific wx DLL versions on Windows. Bundling with PyInstaller requires per-platform hook maintenance. Much harder to distribute than CTkinter. | CustomTkinter |
| PyInstaller `--onefile` for final binary | On Windows, `--onefile` extracts to a temp dir on each launch. Windows Defender scans the temp dir, adding 10-30 seconds to startup. A 600 MB `--onefile` is unusable in practice. | PyInstaller `--onedir`, then zip/NSIS installer |
| `subprocess.kill()` on Windows for scanner cleanup | Does not kill child processes spawned by scanner (e.g., Semgrep spawns sub-workers). Leaves orphan processes. | `psutil.Process(pid).kill()` with recursive child kill |
| CDN links in HTML reports | Reports must work offline. A `<script src="https://cdn.jsdelivr.net/...">` breaks offline reports. | Bundle `chart.min.js` and CSS locally in `assets/` |
| `wkhtmltopdf` via pdfkit | Adds a 150 MB binary dependency, has no active maintenance (last release 2020), and has known rendering bugs with modern CSS. | WeasyPrint |
| `PyArmor` before Phase 7 | PyArmor wraps `.pyc` files. Applying it during development makes stack traces unreadable and imports non-deterministic. Only apply in the Phase 7 build pipeline. | Use plain Python until Phase 7 |
| `sys.path` hacks to locate bundled binaries | Fragile across platforms and PyInstaller modes. | `sys._MEIPASS` guard with `importlib.resources` fallback |
| Groq API calls on the main thread | Blocks the GUI. Even with CTkinter's thread-safe `after()` callback, synchronous HTTP calls on the main thread freeze the scan progress display. | `threading.Thread` + `after()` to update GUI from response |

## Stack Patterns by Variant

**If running in DEV_MODE (Phases 1-5):**
- Import from `src/` directly, no PyInstaller packaging
- `python-dotenv` loads `DEV_MODE=True` from `.env`
- Binary paths resolve relative to project root: `./assets/bins/semgrep`
- WeasyPrint PDF export works without any build step

**If running in Phase 7 packaged binary:**
- Binary paths resolve via `sys._MEIPASS` at runtime
- `python-dotenv` excluded from build
- `DEV_MODE` constant hardcoded to `False` in build script
- PyArmor wraps obfuscated `.pyc` after PyInstaller bundles them

**If Grype DB is too large for bundling:**
- Ship without embedded DB; on first run, call `grype db update` via subprocess
- Show a one-time "Updating vulnerability database..." progress indicator
- Cache DB in `platformdirs.user_data_dir("secscan")`

**If WeasyPrint has CSS compatibility issues with report template:**
- Fall back to `pdfkit` with bundled `wkhtmltopdf` binary
- Add ~150 MB to bundle but gain more predictable CSS rendering

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| customtkinter==5.2.2 | Pillow>=10.x, darkdetect>=0.8.0 | CTkinter 5.x requires Pillow 10+ for CTkImage. Do not mix with Pillow 9.x (deprecated resampling constants). |
| PyInstaller==6.6.0 | Python 3.11.x | Python 3.12 support in PyInstaller 6.x is present but hook coverage is incomplete for some C-extension packages. Stick to 3.11 for the build environment. |
| pydantic>=2.7.0 | Python 3.11+ | Pydantic v2 requires Python 3.8+ but the v2 API (`model_validator`, `field_validator`) is significantly different from v1. Do not mix v1 and v2 imports. |
| WeasyPrint>=62.0 | Pillow>=10.x, pydyf>=0.9.0 | WeasyPrint 62+ uses `pydyf` for PDF generation. Earlier versions used Cairo directly. The 62+ path is more PyInstaller-friendly. |
| groq>=0.9.0 | httpx>=0.27.0 | Groq SDK uses httpx internally. If httpx is also used elsewhere, pin to a single compatible version to avoid resolver conflicts. |

## Sources

- CustomTkinter GitHub (github.com/TomSchimansky/CustomTkinter) — version 5.2.2 confirmed from release tags, knowledge cutoff Aug 2025. MEDIUM confidence.
- PyInstaller changelog (pyinstaller.org) — v6.6.0 confirmed from release notes, knowledge cutoff Aug 2025. MEDIUM confidence.
- Groq Python SDK PyPI (pypi.org/project/groq) — v0.9.x series confirmed, knowledge cutoff Aug 2025. MEDIUM confidence.
- WeasyPrint docs (doc.courtbouillon.org/weasyprint) — v62+ PyInstaller compatibility note, knowledge cutoff Aug 2025. MEDIUM confidence.
- Pydantic v2 docs (docs.pydantic.dev) — v2.7.x stable, knowledge cutoff Aug 2025. MEDIUM confidence.
- Semgrep releases (github.com/returntocorp/semgrep/releases) — 1.7x series, knowledge cutoff Aug 2025. LOW confidence (scanner versions change frequently).
- Trufflehog releases (github.com/trufflesecurity/trufflehog/releases) — v3.8x, knowledge cutoff Aug 2025. LOW confidence.
- Grype releases (github.com/anchore/grype/releases) — 0.7x series, knowledge cutoff Aug 2025. LOW confidence.
- Gitleaks releases (github.com/gitleaks/gitleaks/releases) — v8.x series, knowledge cutoff Aug 2025. LOW confidence.

**Version verification blocked:** WebSearch, WebFetch, and Bash were unavailable during this research session. All versions should be re-verified with `pip index versions <package>` and GitHub releases pages before pinning in `pyproject.toml`.

---
*Stack research for: Python desktop SAST tool (SecScan)*
*Researched: 2026-03-29*

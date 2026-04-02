# Pitfalls Research

**Domain:** Desktop SAST Tool — Python/CustomTkinter wrapping CLI scanners, PyInstaller distribution, cloud licensing
**Researched:** 2026-03-29
**Confidence:** HIGH (PyInstaller/subprocess/GUI threading patterns are mature and well-documented; JWT licensing patterns from known implementations; distribution pitfalls from well-established community knowledge)

---

## Critical Pitfalls

### Pitfall 1: PyInstaller `sys.executable` vs `sys._MEIPASS` path confusion for bundled binaries

**What goes wrong:**
When bundled as a PyInstaller one-file `.exe`, the app extracts to a temp directory (`_MEIPASS`). Code that resolves binary paths using `os.path.dirname(sys.executable)` or relative paths finds nothing. Semgrep, Grype, Gitleaks, and Trufflehog binaries all fail silently or throw `FileNotFoundError` at runtime — on the user's machine, not yours.

**Why it happens:**
Developers test with `python main.py` where `__file__` and relative paths work fine. PyInstaller one-file mode extracts to a random temp path like `C:\Users\user\AppData\Local\Temp\_MEI12345\`. The relative path that worked in dev is now broken. One-dir mode is safer but gets path-fumbled differently.

**How to avoid:**
Use a single utility function for all binary resolution, established before Phase 7 begins:

```python
import sys, os

def get_bundled_binary(name: str) -> str:
    """Resolve binary path whether running from source or PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # PyInstaller one-file or one-dir
        base = sys._MEIPASS
    else:
        base = os.path.join(os.path.dirname(__file__), 'bin')
    path = os.path.join(base, name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Bundled binary not found: {path}")
    return path
```

Add all four binaries to the `.spec` file `binaries` list explicitly, not via glob patterns. Verify the `.spec` file is committed to version control.

**Warning signs:**
- "Works on my machine" with the source tree but fails after `pyinstaller build.spec`
- Subprocess `FileNotFoundError` or return code 127 on first production run
- Binary path hard-coded anywhere in the codebase (`./bin/semgrep`, `bin/grype`)

**Phase to address:** Phase 7 (Build/Distribution) — but the utility function should be written in Phase 2 (scanner integration) so no path assumptions are baked in early.

---

### Pitfall 2: Tkinter/CustomTkinter GUI thread freeze from subprocess blocking

**What goes wrong:**
Running `subprocess.run()` or any blocking I/O on the main GUI thread causes the entire window to freeze — no redraws, no button clicks, no cancel functionality — until the scan completes. For a 500-file project that takes up to 3 minutes, this is a fatal UX failure. On Windows, the OS marks the window as "Not Responding."

**Why it happens:**
CustomTkinter (like all Tkinter) runs a single-threaded event loop. Any blocking call on that thread blocks the loop. Developers prototype with a button callback that calls `subprocess.run()` directly, it "works" in testing because scans on small dirs are fast, and the problem only manifests with real workloads.

**How to avoid:**
Establish the threading pattern in Phase 1 before writing any scanner integration:

1. All subprocess calls run in a `threading.Thread` (not `concurrent.futures`, which has pickling issues with Tkinter callbacks)
2. The thread communicates with the GUI **only** via `root.after(0, callback)` — never directly calling `.configure()` or `.insert()` from a worker thread
3. Use a `queue.Queue` to pass output lines from worker thread to GUI
4. The GUI polls the queue with a periodic `root.after(50, poll_queue)` loop

Never use `thread.join()` on the main thread. Never call Tkinter methods from worker threads directly — Tkinter is not thread-safe.

**Warning signs:**
- Window title shows "(Not Responding)" during scan
- Progress bar or log widget stops updating mid-scan
- Cancel button stops responding
- Any `subprocess.run()` or `subprocess.Popen(...).communicate()` called without being in a separate thread

**Phase to address:** Phase 1 (GUI scaffolding) — establish threading architecture before any scanner is wired up.

---

### Pitfall 3: Semgrep binary size and startup latency on first invocation

**What goes wrong:**
Semgrep's binary (semgrep-core or the compiled semgrep OSS binary) takes 2–8 seconds to cold-start, especially on Windows with antivirus scanning the newly-extracted `_MEIPASS` directory. Users perceive the app as broken or hung before the first result appears. Additionally, Semgrep CLI downloads rulesets at runtime unless explicitly told to use local rules — this breaks offline usage and makes scan times non-deterministic.

**Why it happens:**
Developers test locally where Semgrep is already warm and rules are cached. The production user has neither. Semgrep's default behavior fetches rules from the Semgrep registry unless `--config` points to a local path.

**How to avoid:**
- Bundle the Semgrep ruleset files (the YAML rules for the languages you support) inside the app distribution, not fetched at runtime
- Show a "Initializing scanners..." spinner on first launch, not when the user clicks "Scan"
- Pass `--config ./rules/` (bundled path) to Semgrep, never `--config auto` or `--config p/ci`
- Run a no-op Semgrep probe call on app startup in a background thread to warm the process

**Warning signs:**
- Semgrep invocations include `--config auto` or `--config p/`
- No rules directory is bundled in the repo
- First scan on a cold machine takes >30 seconds
- Scan times vary between runs by more than 20%

**Phase to address:** Phase 2 (Semgrep integration) — decide rule bundling strategy immediately, not after the scanner is wired up.

---

### Pitfall 4: Windows Defender and antivirus false-positives on PyInstaller executables

**What goes wrong:**
PyInstaller-built executables are a well-known antivirus false-positive vector. Windows Defender, Malwarebytes, and corporate EDR tools (CrowdStrike, SentinelOne) flag PyInstaller stubs as Trojan:Win32/Wacatac or similar — especially when bundling security tools like Gitleaks or Trufflehog. Users get a "Windows protected your PC" SmartScreen block or an outright quarantine. The scanner binaries themselves may also be flagged independently.

**Why it happens:**
PyInstaller's bootloader is heavily used in malware packaging. Security tools like Gitleaks (which searches for secrets) look behaviorally identical to credential-harvesting malware. The combination is nearly guaranteed to trigger heuristic detection.

**How to avoid:**
- Code-sign the `.exe` with an EV (Extended Validation) code signing certificate — this is the only reliable fix. OV certificates are insufficient for SmartScreen. Budget $300–700/year for the EV cert
- Submit the first build to Microsoft's Defender portal for whitelisting before any public release
- Compile PyInstaller's bootloader from source (rather than using the stock bootloader) to avoid the shared-signature heuristic
- Add a "SmartScreen warning is expected — click More Info → Run Anyway" note to the download page and onboarding
- Consider signing each bundled binary (Grype, Gitleaks, etc.) separately as well

**Warning signs:**
- GitHub Actions build artifact gets quarantined when downloaded
- Beta testers report "virus detected" before you've done anything
- VirusTotal scan of the build shows >3 engines flagging it

**Phase to address:** Phase 7 (Distribution) — budget for EV certificate before the first public build. Do not release unsigned.

---

### Pitfall 5: JWT license validation that breaks offline-first UX

**What goes wrong:**
The app makes a license validation call to the cloud API on startup. When the user is offline (airplane, corporate VPN that blocks outbound, flaky hotel WiFi), the validation fails, the app refuses to start, and the user loses all access to a tool they paid for. This is the single most common user complaint in desktop SaaS licensing.

**Why it happens:**
Web developers port JWT validation patterns from SaaS web apps where network is assumed. Desktop apps need an offline-first posture. The naïve implementation: `if validate_jwt_online() else block_launch()`.

**How to avoid:**
Implement a two-layer license model from day one of the licensing phase:

1. **Online validation**: On startup (or periodically every N hours), hit the license API, get a signed JWT, store it locally with an expiry timestamp
2. **Offline grace period**: If the API call fails, check the locally-cached JWT. If the cached JWT is still within its grace window (72 hours per project constraints), allow full access. Log the offline state.
3. **Hard expiry**: Only block if the cached JWT has expired AND the API is unreachable — not just API unreachable

Store the cached token in a platform-appropriate location: `%APPDATA%\SecScan\license.json` on Windows, `~/.config/secscan/license.json` on Linux. Never in the install directory (requires admin rights, fails on read-only installs).

**Warning signs:**
- License check has no `try/except` around the HTTP call
- App raises an error dialog on network timeout
- License token stored next to the `.exe`
- No local cache of the license state anywhere

**Phase to address:** Phase 6 (Licensing) — offline-first pattern must be designed before any license code is written, not retrofitted.

---

### Pitfall 6: Subprocess output buffering causes stale/absent real-time logs

**What goes wrong:**
Semgrep, Grype, and Gitleaks buffer their stdout when they detect they're not writing to a TTY (which is always the case when called from Python subprocess). The result: the GUI log widget shows nothing for 2 minutes, then dumps 500 lines at once when the process exits. The "real-time progress" feature does not work.

**Why it happens:**
Python's subprocess captures stdout via a pipe. The child process detects no TTY and switches to full buffering (typically 4KB or 8KB). Most developers notice this in testing with `print()` statements that do appear in real-time (because Python itself is unbuffered when you run interactively), and miss that the child process has its own buffering.

**How to avoid:**
- Use `subprocess.Popen` with `stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1` (line-buffered)
- For tools that ignore line-buffering hints, use the `unbuffer` wrapper on Linux; on Windows use `winpty` or pass the tool-specific flag (`--no-color` often disables buffering too)
- Semgrep: use `--json` output mode and parse JSON output — Semgrep flushes JSON completely when done, so this doesn't help real-time, but it gives structured data. For progress, parse Semgrep's stderr which it writes incrementally
- Grype: use `--output json` and monitor stderr for progress
- Read stdout in a daemon thread with `iter(process.stdout.readline, b'')` — never `process.stdout.read()`

**Warning signs:**
- Log widget updates in large batches rather than line by line
- Scan appears frozen then produces all output at once
- Using `subprocess.run(..., capture_output=True)` anywhere for a scanner (this captures everything until completion)
- Reading from `process.stdout` without line-by-line iteration

**Phase to address:** Phase 2 (Scanner integration) — establish the streaming pattern with the first scanner wired up, not after all four are integrated.

---

### Pitfall 7: PyArmor obfuscation breaks PyInstaller on Python 3.12+

**What goes wrong:**
PyArmor versions below 8.x use a native extension hook that is incompatible with Python 3.11+ in specific configurations, and with Python 3.12 in almost all configurations. The combination of PyArmor + PyInstaller + Python 3.12 commonly produces an `ImportError` or silent launch failure in the final binary. PyArmor 8.x (RFT mode) addresses this but requires code-path changes.

**Why it happens:**
The project specifies Python 3.11+ (which allows 3.12). PyArmor is added in Phase 7 after everything else works, and the incompatibility only surfaces when building the final binary — not during development.

**How to avoid:**
- Pin Python to **3.11.x** (not 3.12.x) for the PyInstaller+PyArmor build environment explicitly
- Test the full build pipeline (PyArmor obfuscate → PyInstaller bundle) in CI on every merge, not just before release
- Use PyArmor 8.x with RFT (Restrict Function Type) mode, not the legacy 7.x mode
- Keep a `requirements-build.txt` separate from `requirements.txt` with pinned build tool versions

**Warning signs:**
- Build environment uses `python3` without a pinned version
- PyArmor version not pinned in build requirements
- Build pipeline only tested manually, not in CI
- The word "later" appears near "PyArmor" in any planning doc

**Phase to address:** Phase 7 (Build) — pin the build Python version before writing any CI pipeline. Create `build/` directory with `.python-version` file early.

---

### Pitfall 8: Groq API rate limits and latency blocking the scan completion flow

**What goes wrong:**
Groq's free tier has aggressive rate limits (typically ~30 requests/minute on llama-3.1-70b-versatile). A scan that finds 40 findings would generate 40 sequential API calls, taking 60+ seconds and hitting rate limits, causing the "AI explanation" phase to fail for half the findings. Even worse: if this is awaited synchronously, it stalls the report generation.

**Why it happens:**
AI explanation is added as a post-scan step without thinking about volume. One API call per finding sounds simple. It fails when there are many findings.

**How to avoid:**
- Batch findings before sending to Groq: summarize groups of similar findings in one API call ("explain these 5 SQL injection findings")
- Cap AI explanations at the top N most severe findings (e.g., 10 Critical/High findings only)
- Run Groq calls concurrently with `asyncio` + `httpx` but with a semaphore limiting to 5 concurrent requests
- Never block report generation on AI completion — generate the HTML report with "AI explanation loading..." placeholders and fill them in asynchronously
- Cache AI responses keyed by `(rule_id, cwe_id)` — the same rule type usually gets the same explanation

**Warning signs:**
- One `groq.chat.completions.create()` call per finding in a loop
- Report generation `await`s all AI calls before writing HTML
- No retry logic or exponential backoff for 429 responses
- No cap on the number of AI calls in a single scan session

**Phase to address:** Phase 4 (AI explanations) — design the batching and async pattern before implementing the first Groq call.

---

### Pitfall 9: Device fingerprint instability causes license invalidation on normal system events

**What goes wrong:**
The license system uses a device fingerprint to bind licenses to machines. If the fingerprint includes volatile hardware identifiers (MAC address, disk serial, current IP), normal system events — VPN connection, network card replacement, Windows Update, VM migration — silently change the fingerprint, invalidate the cached license, and lock the user out until they re-activate. This is the second most common support ticket in desktop SaaS.

**Why it happens:**
Developers pick "stable" hardware IDs that turn out to not be stable. MAC addresses change with VPNs. Disk serials change with drive replacement. Windows volume GUIDs change after OS reinstall.

**How to avoid:**
Use a **combination fingerprint** that degrades gracefully: machine UUID + CPU model + OS install date. Require only 2 of 3 to match for license validation. The machine UUID (from `wmic csproduct get UUID` on Windows, `/etc/machine-id` on Linux) is the most stable single identifier.

Fingerprint generation should be deterministic — the same inputs always produce the same hash. Store the fingerprint as part of the license activation record on the server side, so minor drift can be detected and the user can re-activate once without a support ticket.

**Warning signs:**
- Fingerprint built from MAC address alone
- Fingerprint built from IP address
- No tolerance for partial fingerprint match
- Support workflow requires manual intervention for "wrong device" errors

**Phase to address:** Phase 6 (Licensing) — design the fingerprint algorithm before building any activation endpoints.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| `subprocess.run()` on main thread for quick integration test | Fast first pass at scanner wiring | GUI freezes in production; full rewrite of scanner integration layer | Never — threading pattern costs 1 hour upfront, saves days of refactoring |
| Hard-code binary paths for dev testing | Skip `sys._MEIPASS` complexity in early phases | Binary path logic spread across 10 files, broken on first PyInstaller build | Only if wrapped in `if not getattr(sys, 'frozen', False)` and centralized in one util |
| Use `--config auto` for Semgrep rules | Always get latest rules | Downloads at runtime; breaks offline; non-deterministic scan results | Never for a product claiming offline/local operation |
| Skip code signing for beta | Save $300-700 upfront | Antivirus blocks beta testers' machines; early adopters churn; hard to recover trust | Only if beta is closed/internal and testers are explicitly warned |
| One Groq call per finding in a loop | Simplest possible AI integration | Rate limit failures at scale; blocks report generation | Only in a single-user dev prototype, never in shipped code |
| Store license token in `./license.json` next to `.exe` | Simple path resolution | Fails on read-only installs; Admin elevation required; tokens lost on reinstall | Never — always use `%APPDATA%` / `~/.config/` |
| Use `threading.Thread` without daemon flag | Simple implementation | App hangs on close if scanner subprocess is still running | Never — all worker threads should be daemon threads |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Semgrep | Passing a directory path with spaces unquoted to subprocess | Always use `subprocess.Popen([...], ...)` list form, never shell string form — handles spaces automatically |
| Semgrep | Using `--config auto` in production | Bundle rules as YAML in `assets/rules/` and pass `--config assets/rules/` |
| Grype | Scanning a directory with `grype dir:.` — it doesn't scan source code, it scans for SBOM/dependency files | Grype targets dependency manifests (`package.json`, `requirements.txt`, etc.); clarify in UI what it does vs Semgrep |
| Gitleaks | Running on a directory without a `.git` folder — exits with error code 126 | Check for `.git` presence before invoking; show "Not a git repository — Gitleaks skipped" |
| Trufflehog | Default filesystem scan mode is slow and emits JSON lines (not JSON array) — naive `json.loads()` fails | Use `json.loads(line)` per line in streaming mode, or use `--json` flag and buffer entire stdout |
| Groq API | Sending raw code snippets as-is (may include API keys, tokens) to the AI API | Strip or redact literal secret values from code snippets before sending; ironic given the product's privacy promise |
| Stripe webhooks | Validating the webhook signature with a hardcoded secret in source code | Use environment variable injection; never commit Stripe webhook secrets |
| Supabase JWT | Using Supabase anon key client-side in desktop app — it's public but it exposes your project URL | This is acceptable; use Row Level Security to prevent unauthorized data access |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Running all four scanners sequentially | 500-file scan takes 8+ minutes | Run Semgrep, Grype, Gitleaks, Trufflehog in parallel via `ThreadPoolExecutor` | Any project >50 files |
| Semgrep scanning all languages when project is Python-only | 3x scan time, irrelevant results | Auto-detect project language from file extensions before invoking Semgrep; pass `--lang python` | Any multi-language project or large JS project |
| Reading all scanner output into memory before displaying | UI unresponsive for large scans; MemoryError on 10,000+ finding scans | Stream output line by line; update UI progressively; cap in-memory finding list at 5,000 | Monorepos, projects >500 files |
| Generating PDF by rendering HTML in a full browser engine (Playwright/Selenium) | PDF export takes 30+ seconds; 500MB extra dependency | Use `weasyprint` or `reportlab` for PDF generation from HTML template | Always with browser-based PDF |
| Building the HTML report DOM in Python string concatenation | Report generation time grows O(n) with finding count; XSS in findings | Use Jinja2 templating with auto-escaping; render once at end | Any project with >100 findings |
| CustomTkinter widget creation in a tight loop (one widget per finding) | GUI freezes building result list | Use a `CTkScrollableFrame` with virtual/windowed rendering; or render in a webview | >200 findings displayed simultaneously |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Sending raw code snippets to Groq API without redaction | App promises "code never leaves machine" but silently sends code containing hardcoded secrets to Groq | Make Groq AI calls explicitly opt-in per session; redact literal secret patterns from snippets; document clearly that Groq calls send code |
| Storing Groq API token in plaintext config file | Token theft; unauthorized API usage billed to user | Store in OS keychain (`keyring` library) — `keyring.set_password("secscan", "groq_token", token)` |
| JWT license validation only on client side | License trivially bypassed by patching the JWT verification function | Validate license server-side for sensitive operations (e.g., report export in TEAM tier); keep PyArmor obfuscation as second layer, not first |
| Device fingerprint stored in a user-writable registry key | User modifies fingerprint to clone license to other machines | Store fingerprint hash in HKLM (requires admin) or use the server-side fingerprint record as the authority |
| Subprocess shell injection via unvalidated scan path | User selects a folder with shell metacharacters in the path | Always use list-form subprocess (`Popen([binary, arg1, arg2])`) — never `shell=True` with user-supplied paths |
| Embedding plaintext license API URL + public key in Python source | Trivially inspectable before PyArmor; enables crafting bypass | Embed only the public key (acceptable); obfuscate API endpoint; PyArmor provides second layer |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Showing raw CVE IDs and CWE numbers to beginner users | "CVE-2021-44228" means nothing to a developer who doesn't know what SAST is | Map all findings to plain-language titles: "Log4Shell Remote Code Execution" not "CVE-2021-44228"; this is the product's core value prop |
| Displaying all findings with equal weight | User sees 200 Low findings first and misses the 2 Critical ones | Default sort: Critical → High → Medium → Low; default filter: show Critical/High only on first open |
| No progress indication during scan | 3-minute scan with no feedback looks broken after 10 seconds | Show per-scanner progress bars with estimated completion; show rolling log of files being scanned |
| Scan "fails" with no error message when a scanner binary isn't found | User stares at a blank results page | Validate all four binary paths on app startup and show a clear health check status |
| License upgrade dialog appears mid-scan | Jarring interruption; user loses scan results | Gate on tier at scan start, not mid-scan; show upgrade prompt before scan begins |
| "Scan complete" with 0 findings on a project that definitely has issues | Semgrep ran with wrong rules or Gitleaks skipped non-git dir — silent failure | Show per-scanner status summary: "Semgrep: 12 findings | Grype: 0 findings | Gitleaks: skipped (no .git)" |

---

## "Looks Done But Isn't" Checklist

- [ ] **Real-time log streaming:** Shows output during scan — verify with a 200-file project on a cold machine, not a 3-file hello-world
- [ ] **Binary bundling:** Works after `pyinstaller build.spec` — verify by running the built `.exe` on a fresh VM with no Python installed
- [ ] **Offline license grace period:** Fires correctly — verify by setting system clock forward 71 hours and disconnecting network, then 73 hours
- [ ] **Semgrep rules bundled:** Scan produces results without internet — verify by disconnecting network before scan and confirming finding count matches online run
- [ ] **Cancel scan:** Actually terminates all four subprocess trees — verify with `tasklist` on Windows that semgrep.exe, grype.exe, etc. are gone after cancel
- [ ] **AI explanations optional:** App works fully (scan, report, PDF) with no Groq token configured — verify by deleting token and running a full scan
- [ ] **Report HTML escape:** Finding with `<script>alert(1)</script>` in a code comment doesn't execute in the report — verify with a crafted test file
- [ ] **Path with spaces:** Scan of `C:\Users\John Smith\my project\` works correctly — verify explicitly on Windows
- [ ] **Non-git directory:** Gitleaks is skipped gracefully (not erroring) when scanning a folder without `.git`
- [ ] **Large scan performance:** 500-file project completes under 3 minutes — verify with an actual 500-file Python project, not synthetic files

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Binary path hardcoded throughout codebase | HIGH | Grep all subprocess calls; centralize to one `binary_resolver.py`; re-test all four scanners |
| Threading added late (scanner wired to main thread) | HIGH | Must rewrite the entire scanner invocation layer; GUI callbacks must be redesigned; typically 2-3 days |
| Semgrep using `--config auto` in production | MEDIUM | Replace with bundled rules dir; requires deciding which rulesets to ship; re-validate scan results haven't changed |
| AV false positive after public release | HIGH | Code-sign immediately; submit to Defender portal; notify all users with workaround; trust damage is hard to recover |
| Offline license blocks users | MEDIUM | Hotfix to extend grace period server-side; communicate to affected users; 1-2 day turnaround |
| PyArmor+Python version incompatibility | MEDIUM | Pin Python version in CI; rebuild with 3.11; may require re-testing full binary |
| Device fingerprint too volatile | MEDIUM | Add server-side fingerprint tolerance; push license re-activation to users; adds support burden |
| Groq rate limiting in production | LOW | Add batching and caching; can be deployed as hotfix without user impact |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Binary path confusion (`sys._MEIPASS`) | Phase 2 (first scanner) + Phase 7 (build) | Run built `.exe` on a no-Python VM; all four scanners return results |
| GUI thread freeze | Phase 1 (GUI scaffolding) | Window remains responsive during a 2-minute simulated scan |
| Semgrep startup latency + online rules | Phase 2 (Semgrep integration) | Offline scan produces results within 30s on a cold machine |
| AV false positives | Phase 7 (Distribution) | VirusTotal scan of release build shows <3 flagging engines |
| JWT offline grace period | Phase 6 (Licensing) | App launches with 71-hour-old cached token and no network |
| Subprocess output buffering | Phase 2 (first scanner) | Log widget updates line-by-line during scan, not in batches |
| PyArmor+Python 3.12 incompatibility | Phase 7 (Build) | CI builds on pinned Python 3.11; build fails fast on version drift |
| Groq rate limits | Phase 4 (AI explanations) | Scan with 50 findings completes AI phase under 60s without 429 errors |
| Device fingerprint instability | Phase 6 (Licensing) | License valid after VPN connect/disconnect and network card change |
| Cancel scan leaves zombie processes | Phase 2/3 (scanner integration) | `tasklist`/`ps` shows no scanner processes after cancel |

---

## Sources

- PyInstaller documentation: `sys._MEIPASS` and `sys.frozen` patterns — official PyInstaller docs (HIGH confidence)
- Python `threading` + Tkinter thread-safety: Python docs explicitly state Tkinter is not thread-safe (HIGH confidence)
- Subprocess buffering behavior: Python docs on `bufsize`, `Popen` — TTY detection and buffering modes (HIGH confidence)
- Semgrep CLI `--config` behavior and offline mode: Semgrep OSS docs (HIGH confidence)
- Grype usage: `grype dir:` vs dependency manifest scanning — Anchore Grype GitHub README (HIGH confidence)
- Gitleaks non-git-dir behavior: Gitleaks GitHub issues (MEDIUM confidence — known behavior from community)
- PyArmor 8.x Python 3.12 compatibility: PyArmor changelog and GitHub issues thread (MEDIUM confidence — version-specific, verify at build time)
- Windows SmartScreen / EV code signing requirement: Microsoft SmartScreen documentation (HIGH confidence)
- Groq rate limits: Groq developer docs (MEDIUM confidence — limits subject to change, verify at implementation time)
- JWT offline grace period pattern: Standard desktop SaaS licensing practice (HIGH confidence — multiple products implement this)
- Device fingerprint stability: OS documentation for machine-id / WMIC UUID (HIGH confidence)

---
*Pitfalls research for: Desktop SAST tool — Python/CustomTkinter/PyInstaller/Cloud licensing*
*Researched: 2026-03-29*

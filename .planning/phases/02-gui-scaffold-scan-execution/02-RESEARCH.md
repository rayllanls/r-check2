# Phase 2: GUI Scaffold + Scan Execution - Research

**Researched:** 2026-03-30
**Domain:** CustomTkinter desktop GUI + queue.Queue threading pattern
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **Color palette**: Dark background (#111111 or #0d0d0d), red primary accent (#e63946), teal/cyan secondary accent (#00b4d8). Card panels with dark border (#2a2a2a or similar).
- **Font**: Poppins via CTkFont — weights 300, 400, 600, 700.
- **Logo**: `rakoon_logo.png` from project root shown in app header/sidebar.
- **Design language**: Cybersecurity aesthetic — card-style panels, terminal-style log area.
- **Plan badge**: Always shows "DEV" chip (red accent) next to plan name in header when DEV_MODE=True.
- **App screens**: Main window (target input + scanner list + Start Scan), Progress screen (per-scanner rows + scrollable log + cancel), Settings screen (Groq token), Results summary screen (finding count per scanner).
- **Navigation**: Single-window frame-switching — not multiple Toplevel windows.
- **DEV_MODE**: `DEV_MODE=True` via SECSCAN_DEV env var unlocks all TEAM features. No license check. Badge = "DEV". Read from `app/config.py`.
- **Threading**: ScanOrchestrator (Phase 1) runs off main thread via ThreadPoolExecutor + queue.Queue. GUI polls queue via Tkinter `after()` — never blocks main loop.
- **Cancel**: Call `ScanOrchestrator.cancel()` which terminates subprocess tree.
- **CTk widgets**: CTkFrame, CTkButton, CTkLabel, CTkEntry, CTkTextbox (log), CTkScrollableFrame (finding lists). Theme: `customtkinter.set_appearance_mode("dark")`. Colors via `fg_color`, `text_color`, `hover_color` params.

### Claude's Discretion

- Exact navigation pattern between screens (frame switching vs. toplevel windows — prefer frame switching in single window for desktop feel).
- Icon choices for scanner status rows.
- Exact shade values for hover states and borders.

### Deferred Ideas (OUT OF SCOPE)

- Full report viewer (Phase 3).
- License gate UI (Phase 6).
- Dark/light theme toggle — dark only in this phase.
- Animations beyond what CTk provides natively.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| GUI-01 | Main window allows selecting local folder or entering Git URL, lists available scans by plan, has Start Scan button | Frame switching pattern + CTkButton + filedialog.askdirectory + CTkEntry + PLAN_TOOLS from config.py |
| GUI-02 | Progress screen shows real-time log during scan (never appears frozen) | queue.Queue + root.after(100) polling loop + CTkTextbox insert/see END + per-scanner status rows |
| GUI-03 | Settings screen allows entering and saving Groq token | CTkEntry (show="*") + CONFIG_FILE (~/.secscan/config.json) read/write via json module |
| GUI-04 | Dark modern design with logo and plan badge (always shows "DEV" in dev mode) | customtkinter.set_appearance_mode("dark") + CTkFont(family="Poppins") + CTkImage(PIL.Image) + DEV_MODE from config.py |
| GUI-05 | DEV_MODE=True enables all TEAM features without license validation | PLAN_TOOLS["team"] from config.py, DEV_PLAN="team", no license import needed |
</phase_requirements>

---

## Summary

Phase 2 builds the full CustomTkinter GUI for SecScan, wiring it to the ScanOrchestrator built in Phase 1. The GUI consists of four screens navigated by frame-switching inside a single CTk window. The critical constraint is that scan execution must never block the Tkinter main thread — the existing ScanOrchestrator already handles this via ThreadPoolExecutor + queue.Queue, and the GUI must poll that queue with `root.after()` to update the progress screen in real time.

The environment is a headless Ubuntu server (no X11/Wayland display), which means GUI cannot be run interactively during development. This is a known condition: the code must be written correctly and tested via mocking. All GUI tests must use `unittest.mock` to stub CTk widget instantiation rather than invoking the real display. The existing test infrastructure (pytest + fixtures) already follows this headless-safe pattern.

The major dependency gap discovered is that `python3-tk` (the Tcl/Tk system package) is NOT installed, and Pillow is NOT installed — both are needed for a real GUI run. These must be added to requirements and documented as Wave 0 setup steps, while tests mock around them.

**Primary recommendation:** Implement screens as CTkFrame subclasses, use a single `CTk` root window, switch screens by calling `.pack_forget()` on the current frame and `.pack()` on the next. Poll `progress_queue` in the progress screen via `self.after(100, self._poll_queue)`. Tests mock all CTk classes and never instantiate a real display.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| customtkinter | 5.2.2 (pinned in requirements.txt) | All GUI widgets and window | Already installed; project requirement; modern dark-mode Tk |
| python3-tk | 3.12.3-0ubuntu1 (apt) | Tcl/Tk system dependency for customtkinter | Required by tkinter which CTk wraps |
| Pillow | latest compatible with Python 3.12 | PIL.Image required by CTkImage for logo display | CTkImage constructor requires PIL.Image objects |
| tkinter.filedialog | stdlib | Native OS folder picker dialog | No external dep; askdirectory() works on Linux/Windows/macOS |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| tkinter.messagebox | stdlib | Error dialogs (invalid path, etc.) | Friendly error messages without jargon |
| json | stdlib | Read/write ~/.secscan/config.json for Groq token | Settings persistence |
| queue.Queue | stdlib | Inter-thread communication from ScanOrchestrator | Already used by orchestrator |
| threading.Thread | stdlib (or ThreadPoolExecutor) | Wrapping orchestrator.scan() call | Needed to call blocking .scan() off main thread |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| frame-switching navigation | CTkTabview or multiple Toplevel windows | Toplevel creates separate OS windows (worse UX); CTkTabview shows tabs permanently which doesn't match flow-based scan UX |
| root.after() polling | threading.Event + callback | after() is the canonical Tkinter threading pattern; callbacks into Tkinter from non-main threads cause crashes |
| CTkTextbox for log | tk.Text directly | CTkTextbox wraps tk.Text with themed styling; safe to use all tk.Text methods (insert, see, configure) on the underlying widget |

### Installation

```bash
# System package (required first)
sudo apt-get install python3-tk

# Python packages
pip install pillow
# customtkinter 5.2.2 is already in requirements.txt
```

**Version verification (current as of 2026-03-30):**
- customtkinter 5.2.2 — confirmed installed at `/home/admin/.local/lib/python3.12/site-packages/customtkinter/`
- python3-tk 3.12.3-0ubuntu1 — available in apt but NOT installed (status: `un`)
- Pillow — NOT installed (confirmed by `ModuleNotFoundError: No module named 'PIL'`)

---

## Architecture Patterns

### Recommended Project Structure

```
app/gui/
├── __init__.py
├── main_window.py       # CTk root window, screen registry, frame-switch logic
├── screens/
│   ├── __init__.py
│   ├── home_screen.py   # GUI-01: target input, scanner list, Start Scan
│   ├── progress_screen.py  # GUI-02: per-scanner rows, log, cancel
│   ├── settings_screen.py  # GUI-03: Groq token entry + save
│   └── summary_screen.py   # finding count per scanner after scan
├── widgets/
│   ├── __init__.py
│   ├── header_bar.py    # logo + plan badge (shared across screens)
│   └── scanner_row.py   # reusable per-scanner status row widget
└── theme.py             # color constants and CTkFont factories
```

### Pattern 1: Frame-Switching Navigation

**What:** A single CTk root window holds a dict of CTkFrame subclasses. Navigation calls `.pack_forget()` on the active frame and `.pack(fill="both", expand=True)` on the target frame.

**When to use:** Always — single-window desktop app, no Toplevel windows.

**Example:**
```python
# app/gui/main_window.py
import customtkinter as ctk
from app.gui.screens.home_screen import HomeScreen
from app.gui.screens.progress_screen import ProgressScreen

class MainWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("SecScan")
        self.root.geometry("900x640")
        customtkinter.set_appearance_mode("dark")

        self._screens: dict[str, ctk.CTkFrame] = {}
        self._active: ctk.CTkFrame | None = None

    def register_screen(self, name: str, screen: ctk.CTkFrame) -> None:
        self._screens[name] = screen

    def show_screen(self, name: str) -> None:
        if self._active:
            self._active.pack_forget()
        self._active = self._screens[name]
        self._active.pack(fill="both", expand=True)

    def run(self) -> None:
        self.show_screen("home")
        self.root.mainloop()
```

### Pattern 2: Queue Polling with after()

**What:** Progress screen starts a scan in a background thread, then polls the `queue.Queue` every 100ms via `self.after()`. Each event updates the UI. Never calls any CTk method from the background thread.

**When to use:** All scanner execution — required by GUI-02 and Phase 1 decision.

**Example:**
```python
# app/gui/screens/progress_screen.py
import queue
import threading
import customtkinter as ctk
from app.core.scanner import ScanOrchestrator, EventType

class ProgressScreen(ctk.CTkFrame):
    def __init__(self, master, nav_callback, **kwargs):
        super().__init__(master, **kwargs)
        self._q: queue.Queue = queue.Queue()
        self._orchestrator: ScanOrchestrator | None = None
        self._scan_thread: threading.Thread | None = None
        self._log_box = ctk.CTkTextbox(self, font=("Courier", 12), state="disabled")
        # ... layout ...

    def start_scan(self, project_path, plan: str) -> None:
        self._orchestrator = ScanOrchestrator(plan=plan)
        self._scan_thread = threading.Thread(
            target=self._orchestrator.scan,
            args=(project_path,),
            kwargs={"progress_queue": self._q},
            daemon=True,
        )
        self._scan_thread.start()
        self.after(100, self._poll_queue)

    def _poll_queue(self) -> None:
        try:
            while True:
                event = self._q.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        if self._scan_thread and self._scan_thread.is_alive():
            self.after(100, self._poll_queue)

    def _handle_event(self, event) -> None:
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"{event.tool}: {event.message}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
        if event.event_type == EventType.SCAN_COMPLETE:
            self._on_scan_complete(event)

    def cancel(self) -> None:
        if self._orchestrator:
            self._orchestrator.cancel()
```

**Critical note:** `ScanOrchestrator` currently has no `cancel()` method. This must be added in Wave 0 (or as the first implementation task). The method must set a threading.Event flag that each tool runner checks, and call `subprocess.terminate()` on active subprocesses.

### Pattern 3: Theme and Color Constants

**What:** Centralize all color hex values and CTkFont factories in `app/gui/theme.py` so screens import from one place.

**Example:**
```python
# app/gui/theme.py
import customtkinter as ctk

BG_PRIMARY    = "#111111"
BG_CARD       = "#1a1a1a"
BG_BORDER     = "#2a2a2a"
ACCENT_RED    = "#e63946"
ACCENT_TEAL   = "#00b4d8"
TEXT_PRIMARY  = "#f0f0f0"
TEXT_SECONDARY = "#888888"

def font_heading(size: int = 18) -> ctk.CTkFont:
    return ctk.CTkFont(family="Poppins", size=size, weight="bold")

def font_body(size: int = 13) -> ctk.CTkFont:
    return ctk.CTkFont(family="Poppins", size=size)

def font_mono(size: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(family="Courier", size=size)
```

### Pattern 4: Logo Loading with CTkImage

**What:** CTkImage requires PIL.Image objects (light + dark variants). For a single logo, pass the same image for both.

**Example:**
```python
# Source: customtkinter/windows/widgets/image/ctk_image.py (inspected directly)
from PIL import Image
import customtkinter as ctk

logo_pil = Image.open("rakoon_logo.png").resize((40, 40))
logo_ctk = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(40, 40))
label = ctk.CTkLabel(parent, image=logo_ctk, text="")
```

### Pattern 5: Settings Persistence

**What:** Groq token stored in `~/.secscan/config.json` (path defined in `app/config.py` as `CONFIG_FILE`). Load on settings screen init, save on button press.

**Example:**
```python
import json
from app.config import CONFIG_DIR, CONFIG_FILE

def load_groq_token() -> str:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text()).get("groq_token", "")
    return ""

def save_groq_token(token: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    data = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
    data["groq_token"] = token
    CONFIG_FILE.write_text(json.dumps(data, indent=2))
```

### Anti-Patterns to Avoid

- **Calling CTk widget methods from background threads:** CTk/Tkinter is NOT thread-safe. All `.configure()`, `.insert()`, `.pack()` calls must happen in the main thread. The only safe cross-thread operation is `queue.Queue.put()`.
- **Blocking main thread with orchestrator.scan():** Calling `orchestrator.scan()` directly in the main thread will freeze the GUI. Always wrap in `threading.Thread(daemon=True)`.
- **Using tk.StringVar / tk.IntVar from background threads:** Same thread-safety issue. Update them only from `after()` callbacks or main thread.
- **Creating CTk widgets before `CTk()` root exists:** CTkFont and CTkImage require the root window to exist first. Instantiate root before any widget or font.
- **Multiple CTk() instances:** Only one `CTk()` root per process. All screens must share the same root.
- **Hardcoding plan in screens:** Always read plan from `DEV_PLAN` (when `DEV_MODE=True`) or from future license module. `PLAN_TOOLS[plan]` from config.py drives the scanner list shown in GUI-01.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Folder picker dialog | Custom path text entry | `tkinter.filedialog.askdirectory()` | Native OS dialog, handles edge cases (permissions, symlinks, cancellation) |
| Log autoscroll | Manual canvas scroll | `CTkTextbox.see("end")` | Built into CTk/Tk text widget |
| Cross-thread UI update | Shared state + polling custom code | `queue.Queue` + `root.after()` | Standard Tkinter threading pattern; alternatives cause crashes |
| Color theme management | Inline hex everywhere | `app/gui/theme.py` module | Single source of truth for brand colors |
| Token file I/O | Custom serialization | `json.loads / json.dumps` + `CONFIG_FILE` from config.py | CONFIG_DIR/CONFIG_FILE already defined in app/config.py |

**Key insight:** Tkinter's threading model is single-threaded by design. The `after()` + `queue.Queue` pattern is the only safe way to update UI from background work — it has been part of Tkinter since Python 2.6 and is the community-standard approach. Any alternative (event.wait, Tkinter variables written from threads) will cause intermittent crashes on Windows and macOS.

---

## Common Pitfalls

### Pitfall 1: tkinter Not Installed (Blocking)

**What goes wrong:** `import customtkinter` raises `ModuleNotFoundError: No module named 'tkinter'` — confirmed on this machine.

**Why it happens:** `python3-tk` is a separate apt package (3.12.3-0ubuntu1) not installed by default on Ubuntu server.

**How to avoid:** Add `sudo apt-get install python3-tk` as a Wave 0 environment step. Add to project README/setup docs. Tests must mock CTk imports to avoid requiring tk in CI.

**Warning signs:** Any `import customtkinter` at module level will fail CI if tkinter is absent.

### Pitfall 2: Pillow Not Installed (CTkImage Fails)

**What goes wrong:** `from PIL import Image` raises `ModuleNotFoundError: No module named 'PIL'` when trying to use logo.

**Why it happens:** Pillow is not in requirements.txt and not installed on this machine.

**How to avoid:** Add `pillow` to requirements.txt. Add to Wave 0 install. For tests, mock `PIL.Image.open()`.

**Warning signs:** CTkImage constructor silently checks PIL import — runtime error when logo code runs.

### Pitfall 3: ScanOrchestrator Has No cancel() Method

**What goes wrong:** GUI-02 success criterion requires "cancel a running scan and subprocess tree terminates cleanly" — but `ScanOrchestrator` in `app/core/scanner.py` has no `cancel()` method.

**Why it happens:** Phase 1 plan referenced `ScanOrchestrator.cancel()` in STATE.md decisions but the implementation was not completed (scanner.py has no cancel method as of current code).

**How to avoid:** Wave 0 must add `cancel()` to `ScanOrchestrator`. Implementation: set a `threading.Event` flag; each tool's `run()` method should check it before subprocess invocation; the cancel method should also call `process.terminate()` on any live subprocess handle. The plan must include this as an explicit pre-GUI task.

**Warning signs:** The cancel button in the progress screen will silently do nothing if `cancel()` is missing.

### Pitfall 4: CTkFont Requires Root Window

**What goes wrong:** `ctk.CTkFont(family="Poppins", size=14)` raises `RuntimeError` if called before `ctk.CTk()` root is instantiated.

**Why it happens:** CTkFont inherits from `tkinter.font.Font` which requires an active Tk interpreter.

**How to avoid:** Always instantiate `CTk()` root first, then create fonts. In screens, create fonts in `__init__()` (which is called after root exists) not at class level.

### Pitfall 5: Poppins Font Not Available on Linux

**What goes wrong:** `CTkFont(family="Poppins")` silently falls back to a default font if Poppins is not installed on the system.

**Why it happens:** Poppins is a Google Font not bundled with Ubuntu. CTk does not raise an error — it just substitutes.

**How to avoid:** Bundle Poppins `.ttf` files in `assets/fonts/` and load them via `tkinter.font` before CTk initialization, or accept system fallback for Phase 2. The CONTEXT.md says "via CTkFont or bundled" — bundling is the safe path for distribution but for Phase 2 development fallback is acceptable.

**Warning signs:** UI looks correct in design but uses different font on clean systems.

### Pitfall 6: CTkTextbox state Must Be "normal" Before Insert

**What goes wrong:** `CTkTextbox.insert("end", text)` raises `TclError: text is disabled` when textbox state is "disabled".

**Why it happens:** CTkTextbox (like tk.Text) is read-only when state="disabled". The log area should be disabled to prevent user editing but enabled briefly to insert text.

**How to avoid:** Pattern is `configure(state="normal") → insert() → see("end") → configure(state="disabled")` on every log update. Already shown in code examples above.

---

## Code Examples

### Full CTk Window Setup (Dark Theme + Brand Colors)

```python
# Source: customtkinter source + CTk() constructor (inspected at ctk_tk.py)
import customtkinter as ctk

customtkinter.set_appearance_mode("dark")
root = ctk.CTk()
root.title("SecScan")
root.geometry("900x640")
root.configure(fg_color="#111111")
root.resizable(True, True)
root.minsize(800, 560)
```

### DEV Mode Badge Widget

```python
# Read from app/config.py — DEV_MODE is bool, DEV_PLAN is "team"
from app.config import DEV_MODE, DEV_PLAN, APP_VERSION

if DEV_MODE:
    badge = ctk.CTkLabel(
        header_frame,
        text="DEV",
        fg_color="#e63946",
        text_color="#ffffff",
        corner_radius=4,
        font=ctk.CTkFont(family="Poppins", size=10, weight="bold"),
        width=36,
        height=20,
    )
    badge.pack(side="right", padx=8)
```

### Folder Picker Integration

```python
# Source: Python stdlib tkinter.filedialog
from tkinter import filedialog

def browse_folder(self) -> None:
    path = filedialog.askdirectory(title="Selecione a pasta do projeto")
    if path:  # user may cancel — returns "" on cancel
        self._path_var.set(path)
```

### Per-Scanner Status Row (reusable widget)

```python
# Icons via Unicode or CTkImage; status updated by event type
import customtkinter as ctk
from app.core.scanner import EventType

ICON_MAP = {
    "pending": "○",
    "running": "◉",
    "done":    "✓",
    "error":   "✗",
}
COLOR_MAP = {
    "pending": "#888888",
    "running": "#00b4d8",
    "done":    "#4caf50",
    "error":   "#e63946",
}

class ScannerRow(ctk.CTkFrame):
    def __init__(self, master, tool_name: str, **kwargs):
        super().__init__(master, fg_color="#1a1a1a", corner_radius=6, **kwargs)
        self._status = "pending"
        self._icon_label = ctk.CTkLabel(self, text=ICON_MAP["pending"], text_color="#888888")
        self._name_label = ctk.CTkLabel(self, text=tool_name.capitalize(), text_color="#f0f0f0")
        self._count_label = ctk.CTkLabel(self, text="", text_color="#888888")
        self._icon_label.pack(side="left", padx=8)
        self._name_label.pack(side="left")
        self._count_label.pack(side="right", padx=8)

    def set_status(self, status: str, count: int = 0) -> None:
        self._status = status
        self._icon_label.configure(text=ICON_MAP.get(status, "?"), text_color=COLOR_MAP.get(status, "#888888"))
        if status == "done":
            self._count_label.configure(text=f"{count} findings")
```

### Results Summary Cards

```python
# After SCAN_COMPLETE event, show per-scanner count
from app.core.models import ScanResult
from collections import Counter

def build_summary(result: ScanResult) -> dict[str, int]:
    counts = Counter(f.tool for f in result.findings)
    return dict(counts)
```

---

## Runtime State Inventory

> Not applicable — this is a greenfield GUI implementation with no rename/refactor/migration concerns.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Raw tkinter.Tk | CustomTkinter CTk() wrapping Tk | 2022 (CTk first release) | Dark mode, rounded corners, HiDPI scaling built in |
| tk.Thread with direct widget.config() | queue.Queue + root.after() polling | Established pattern, unchanged | Required for thread safety |
| tk.PhotoImage for images | CTkImage (wraps PIL.Image) | CTk 5.x | Supports HiDPI by providing light/dark variants |
| tk.font.Font | CTkFont | CTk 5.x | Pixel-based sizing, scaling-aware |

**Deprecated/outdated:**
- `ttk` (themed Tk): CTk supersedes it for modern dark-mode apps; ttk has poor dark mode support
- `tkinter.messagebox` for styled dialogs: acceptable for errors but doesn't match brand theme; for Phase 2, native dialogs are fine per CONTEXT.md

---

## Open Questions

1. **ScanOrchestrator.cancel() implementation**
   - What we know: Cancel button is a success criterion for GUI-02; `cancel()` is referenced in STATE.md decisions but not implemented in `app/core/scanner.py`
   - What's unclear: Whether cancel should kill ThreadPoolExecutor futures or only signal tool processes; how to get subprocess handles out of tool runners
   - Recommendation: Plan must include a Wave 0 task to add `cancel()` to ScanOrchestrator before the progress screen can be wired. Simplest implementation: `threading.Event` checked in `_run_tool`, plus storing `subprocess.Popen` handle in each tool runner.

2. **Poppins font bundling**
   - What we know: Poppins is not on Ubuntu server; CTk silently falls back; CONTEXT.md says "via CTkFont or bundled"
   - What's unclear: Whether to bundle `.ttf` in Phase 2 or defer to Phase 7 (PyInstaller embed)
   - Recommendation: For Phase 2 dev mode, accept system font fallback. Add `assets/fonts/Poppins-*.ttf` bundle task to Phase 7 plan. Note in code with a comment.

3. **Headless CI test strategy for GUI code**
   - What we know: No X11/Wayland display on this machine; CTk cannot be instantiated without display; existing tests all use `unittest.mock`
   - What's unclear: Whether to use `pytest-mock` or plain `unittest.mock.patch`; whether to test screen logic separately from widget instantiation
   - Recommendation: All GUI tests must mock `customtkinter` at the import level or use `MagicMock()` for the root window. Test screen _logic_ (queue polling, event handling, config save/load) separately from widget _construction_. No integration test that opens a real window until Phase 5 manual QA.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3-tk (apt) | customtkinter / all GUI | No (status: `un`) | — | None — must install |
| Pillow | CTkImage (logo) | No (ModuleNotFoundError) | — | Skip logo display until installed |
| customtkinter | All GUI widgets | Yes (pip) | 5.2.2 | — |
| X11 display | Running GUI interactively | No (DISPLAY="") | — | Mock in tests; real display needed for manual QA |
| Python 3.12.3 | All code | Yes | 3.12.3 | — |
| tkinter.filedialog | Folder picker | Blocked by missing python3-tk | — | Manual text entry as fallback |

**Missing dependencies with no fallback:**
- `python3-tk` — blocks any real GUI run; must be installed before manual QA (`sudo apt-get install python3-tk`)

**Missing dependencies with fallback:**
- `Pillow` — logo image will not display until installed; app still launches without it if logo loading is guarded with `try/except ImportError`
- `X11 display` — all tests run headless via mocking; manual QA requires a desktop environment

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.2.0 |
| Config file | `/home/admin/raksaas/pytest.ini` |
| Quick run command | `pytest tests/test_gui.py -x -v --ignore=tests/test_scanner.py` |
| Full suite command | `pytest -v --tb=short` |

### Phase Requirements → Test Map

All GUI tests live in a single consolidated file `tests/test_gui.py` (created in Wave 0).

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GUI-01 | HomeScreen renders input area and Start Scan button | unit (mocked CTk) | `pytest tests/test_gui.py::test_main_screen_widgets -x` | No — Wave 0 |
| GUI-01 | Folder picker populates path var | unit | `pytest tests/test_gui.py::test_folder_selection -x` | No — Wave 0 |
| GUI-02 | Progress screen polls queue and inserts log lines | unit (mocked CTk) | `pytest tests/test_gui.py::test_poll_queue_inserts_log -x` | No — Wave 0 |
| GUI-02 | SCAN_COMPLETE event triggers navigation to summary | unit | `pytest tests/test_gui.py::test_scan_complete_navigates -x` | No — Wave 0 |
| GUI-02 | Cancel calls orchestrator.cancel() | unit | `pytest tests/test_gui.py::test_cancel_scan -x` | No — Wave 0 |
| GUI-03 | Settings screen saves Groq token | unit | `pytest tests/test_gui.py::test_settings_screen -x` | No — Wave 0 |
| GUI-04 | DEV badge visible when DEV_MODE=True | unit | `pytest tests/test_gui.py::test_dev_mode_badge -x` | No — Wave 0 |
| GUI-05 | ResultsScreen importable and processes ScanResult | unit | `pytest tests/test_gui.py::test_results_summary -x` | No — Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_gui.py -x -v --ignore=tests/test_scanner.py`
- **Per wave merge:** `pytest -v --tb=short`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_gui.py` — single consolidated test file covering all GUI requirements (GUI-01..GUI-05)
- [ ] `tests/conftest.py` — shared fixtures: `mock_ctk`, `mock_orchestrator`
- [ ] `app/gui/theme.py` — brand colors and font factories (no test needed, but must exist before screens import it)
- [ ] `app/gui/screens/` directory and `__init__.py` files
- [ ] `ScanOrchestrator.cancel()` method in `app/core/scanner.py` — required for GUI-02 cancel test
- [ ] Install: `sudo apt-get install python3-tk && pip install pillow` — Wave 0 environment step

---

## Sources

### Primary (HIGH confidence)

- CustomTkinter source code at `/home/admin/.local/lib/python3.12/site-packages/customtkinter/` — widget constructors, parameter names, CTkFont/CTkImage/CTkTextbox/CTkScrollableFrame signatures inspected directly
- `app/core/scanner.py` — ScanOrchestrator, ProgressEvent, EventType definitions inspected directly
- `app/config.py` — DEV_MODE, DEV_PLAN, PLAN_TOOLS, CONFIG_DIR, CONFIG_FILE inspected directly
- `app/gui/main_window.py` — current stub implementation inspected
- `pytest.ini` and `tests/conftest.py` — existing test infrastructure confirmed

### Secondary (MEDIUM confidence)

- Ubuntu apt package `python3-tk` version 3.12.3-0ubuntu1 — confirmed available but not installed via `dpkg -l`
- Pillow absence confirmed via `pip list` and `python3 -c "import PIL"` error

### Tertiary (LOW confidence)

- None

---

## Project Constraints (from CLAUDE.md)

| Directive | Constraint |
|-----------|------------|
| Stack | Python 3.11+, CustomTkinter, Semgrep + Trufflehog + Grype + Gitleaks, Groq/Llama 3.1, Jinja2 + WeasyPrint, PyInstaller + PyArmor |
| DEV_MODE | `DEV_MODE=True` enables all TEAM features without license |
| Phases 1-5 | 100% local, no license, no compilation |
| Phases 6-7 | Licensing and build ONLY after Phases 1-5 working |
| Scanner binaries | In `tools/`, resolved via `BinaryLocator` with `sys._MEIPASS` fallback |
| Threading | All scanner execution must run off Tkinter main thread via `queue.Queue` |

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — verified by inspecting installed packages and source files directly
- Architecture: HIGH — CTk frame-switching and queue polling are well-established patterns, verified in CTk source
- Pitfalls: HIGH — tkinter/Pillow absence confirmed by live environment probing; cancel() absence confirmed by code inspection
- Environment gaps: HIGH — confirmed by running actual commands on the machine

**Research date:** 2026-03-30
**Valid until:** 2026-05-01 (stable stack; customtkinter 5.x API is stable)

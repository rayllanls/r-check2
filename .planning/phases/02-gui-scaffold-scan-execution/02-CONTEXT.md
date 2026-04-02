# Phase 2: GUI Scaffold + Scan Execution - Context

**Gathered:** 2026-03-30
**Status:** Ready for planning
**Source:** User design decisions

<domain>
## Phase Boundary

Build the full CustomTkinter GUI: main window (target selection + start scan), real-time progress screen, settings screen (Groq token), and post-scan summary screen. Wire the GUI to the ScanOrchestrator built in Phase 1. All scan execution must happen off the main thread via queue.Queue to prevent GUI freeze.

</domain>

<decisions>
## Implementation Decisions

### Visual Theme — Rakoon Brand
- **Color palette**: Dark background (#111111 or #0d0d0d), red primary accent (#e63946 or similar red matching Rakoon logo), teal/cyan secondary accent (#00b4d8 or similar — matches circuit elements in logo)
- **Font**: Poppins (via CTkFont or bundled) — weights 300, 400, 600, 700
- **Logo**: Use `rakoon_logo.png` from project root in the app header/sidebar
- **Design language**: Cybersecurity aesthetic — hexagon motifs, subtle circuit-board texture references, card-style panels with dark borders
- **Plan badge**: Always shows "DEV" badge (red accent) when DEV_MODE=True, styled like a tag/chip near the logo

### App Structure — Screens
- **Main window**: Logo + app title top bar, input area (local folder picker button OR Git URL text field), list of available scan types filtered by plan tier, "Start Scan" CTA button
- **Progress screen**: Per-scanner status rows (pending/running/done icons), scrollable live log area (tail of scanner output), cancel button, overall progress indicator
- **Settings screen**: Groq API token input + save button, accessible from main window
- **Results summary screen**: Finding count per scanner in card grid, total count highlighted, "View Full Report" placeholder (Phase 3)

### DEV_MODE Behavior
- `DEV_MODE=True` in environment → all TEAM-tier features unlocked, no license check, badge shows "DEV"
- License validation is skipped entirely in this phase (Phases 6+)
- `app/config.py` already has DEV_MODE logic — plans must read it before implementing

### Threading Model
- All scanner execution via `ScanOrchestrator` (built in Phase 1) which uses `queue.Queue` + `ThreadPoolExecutor`
- GUI polls the queue (via `after()` loop or dedicated thread) — never blocks Tkinter main loop
- Cancel: call `ScanOrchestrator.cancel()` which terminates subprocess tree

### CustomTkinter Specifics
- Use `customtkinter` (CTk) widgets throughout — not raw Tkinter
- `CTkFrame`, `CTkButton`, `CTkLabel`, `CTkEntry`, `CTkTextbox` for log area
- `CTkScrollableFrame` for finding lists
- Theme set to "dark" mode via `customtkinter.set_appearance_mode("dark")`
- Custom colors applied via `fg_color`, `text_color`, `button_color` params

### Claude's Discretion
- Exact navigation pattern between screens (frame switching vs. toplevel windows — prefer frame switching in single window for desktop feel)
- Icon choices for scanner status rows
- Exact shade values for hover states and borders

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Foundation (already built)
- `app/core/ingestion.py` — TargetIngestion, BinaryLocator, scanner wrappers
- `app/main.py` — App entry point (may be stub, check current state)
- `app/config.py` — DEV_MODE, plan tier logic
- `app/gui/` — Existing GUI files if any (check before creating new)
- `tests/test_scanner.py` — Scanner integration tests pattern

### Design Reference
- `rakoon_logo.png` — Official Rakoon logo (root of project)
- `inspiracao/index.html` — Rakoon site layout reference
- `inspiracao/decoder.html` — Rakoon tool page reference

### Project Constraints
- `CLAUDE.md` — Stack constraints: CustomTkinter, Python 3.11+, queue.Queue off main thread
- `.planning/REQUIREMENTS.md` — GUI-01 through GUI-05 full text
- `.planning/STATE.md` — Current project decisions

</canonical_refs>

<specifics>
## Specific Ideas

- Rakoon logo shown prominently in top-left of main window
- Red accent for primary buttons (Start Scan, Save)
- Teal accent for informational elements (scanner status "running", links)
- Dark card panels with subtle border (#2a2a2a or similar) for input areas and result cards
- Progress log uses monospace font (Courier or similar) on dark background — terminal aesthetic
- "DEV" badge: small red chip/label next to plan name in header
</specifics>

<deferred>
## Deferred Ideas

- Full report viewer (Phase 3)
- License gate UI (Phase 6)
- Dark/light theme toggle (not in scope — dark only)
- Animations beyond what CTk provides natively

</deferred>

---

*Phase: 02-gui-scaffold-scan-execution*
*Context gathered: 2026-03-30*

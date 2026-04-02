---
phase: 01-foundation
plan: 01
subsystem: testing
tags: [pytest, binary-locator, pyinstaller, meipass, fixtures, semgrep, trufflehog, grype, gitleaks]

# Dependency graph
requires: []
provides:
  - BinaryLocator with sys._MEIPASS > vendor > PATH 3-level fallback in BaseTool
  - Realistic fixture JSON/NDJSON files for all 4 scanners in tests/fixtures/
  - Shared conftest.py fixture helpers for scanner test infrastructure
affects: [01-02, 01-03, 01-04, all scanner runner plans]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "BinaryLocator pattern: MEIPASS first (PyInstaller frozen), vendor dir second, system PATH third"
    - "TDD pattern: write failing tests, commit RED, implement GREEN, verify no regressions"
    - "Scanner fixture pattern: one fixture JSON file per scanner tool in tests/fixtures/"

key-files:
  created:
    - tests/test_binary_locator.py
    - tests/fixtures/semgrep_output.json
    - tests/fixtures/trufflehog_output.ndjson
    - tests/fixtures/grype_output.json
    - tests/fixtures/gitleaks_output.json
  modified:
    - app/tools/base.py
    - tests/conftest.py

key-decisions:
  - "MEIPASS check added as first priority in resolve_binary() — in frozen mode, vendor dir at dev path does not exist"
  - "Fixture files use realistic scanner output to enable mocked subprocess testing without live binaries"

patterns-established:
  - "resolve_binary() fallback chain: sys._MEIPASS > VENDOR_DIR/system/ > shutil.which()"
  - "TDD RED commit before GREEN commit for test-first development"
  - "tests/fixtures/ directory holds static scanner output files used by all runner tests"

requirements-completed: [DATA-01, DATA-02, DATA-03, SCAN-01, SCAN-02]

# Metrics
duration: 3min
completed: 2026-03-30
---

# Phase 1 Plan 01: Test Infrastructure and BinaryLocator Foundation Summary

**BinaryLocator with sys._MEIPASS PyInstaller support added to BaseTool, plus realistic JSON fixture files for all 4 scanners and shared conftest.py helpers for mocked subprocess testing**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-30T20:14:13Z
- **Completed:** 2026-03-30T20:17:00Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Upgraded `app/tools/base.py` with sys._MEIPASS as first binary resolution step, enabling PyInstaller frozen mode support
- Created 5 unit tests for BinaryLocator covering all 3 fallback levels, FileNotFoundError, and Windows .exe extension — all pass
- Created `tests/fixtures/` directory with 4 realistic scanner output files: semgrep (3 SAST findings), trufflehog (2 NDJSON secret detections), grype (3 CVE matches), gitleaks (2 hardcoded secrets)
- Updated `tests/conftest.py` with FIXTURES_DIR constant and 4 fixture helper functions for use in Plans 02-04

## Task Commits

Each task was committed atomically:

1. **TDD RED: BinaryLocator failing tests** - `8d8d880` (test)
2. **Task 1: BinaryLocator implementation** - `5eaabeb` (feat)
3. **Task 2: Scanner fixtures + conftest** - `ab36073` (feat)

## Files Created/Modified
- `app/tools/base.py` - Added `import sys`, `getattr(sys, "frozen", False)` MEIPASS check as priority 1 in resolve_binary()
- `tests/test_binary_locator.py` - 5 unit tests covering MEIPASS, vendor, PATH, not-found, Windows extension
- `tests/fixtures/semgrep_output.json` - 3 realistic Semgrep findings (SQL injection, eval, file handle)
- `tests/fixtures/trufflehog_output.ndjson` - 2 NDJSON secret detections (AWS key, Stripe key)
- `tests/fixtures/grype_output.json` - 3 CVE vulnerability matches (High, Critical, Negligible)
- `tests/fixtures/gitleaks_output.json` - 2 hardcoded secret findings (generic-api-key, aws-access-key-id)
- `tests/conftest.py` - Added FIXTURES_DIR, fixture_path, semgrep_fixture, trufflehog_fixture, grype_fixture, gitleaks_fixture

## Decisions Made
- MEIPASS check must come first in resolve_binary() because in frozen/PyInstaller mode, the development-path vendor directory does not exist
- Fixture files use realistic output matching actual scanner JSON schemas so Plans 02-04 can mock subprocess.run without needing live binaries installed

## Deviations from Plan

None — plan executed exactly as written. TDD process followed: RED commit first, then GREEN implementation, verified no regressions.

## Issues Encountered
None.

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Plan 02 (Semgrep + Gitleaks runners) can proceed — fixtures and conftest helpers are ready
- Plan 03 (Trufflehog + Grype runners) can proceed in parallel — all fixture files exist
- Plan 04 (Scanner orchestrator) depends on Plans 02 and 03 completing first
- All 19 existing tests pass with no regressions

## Known Stubs
None — all deliverables are fully implemented. Fixture files contain complete realistic scanner output. BinaryLocator is production-ready with all 3 fallback levels.

---
*Phase: 01-foundation*
*Completed: 2026-03-30*

## Self-Check: PASSED

- All 8 expected files found on disk
- All 3 task commits verified in git log (8d8d880, 5eaabeb, ab36073)
- All 19 tests pass with no regressions

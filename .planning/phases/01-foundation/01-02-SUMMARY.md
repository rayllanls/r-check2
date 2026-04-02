---
phase: 01-foundation
plan: 02
subsystem: testing
tags: [gitleaks, trufflehog, subprocess, ndjson, json, secret-detection, tdd]

# Dependency graph
requires:
  - phase: 01-01
    provides: BaseTool with BinaryLocator (resolve_binary), fixture files for all scanners

provides:
  - GitleaksTool: runs gitleaks binary, parses JSON array output into list[Finding]
  - TrufflehogTool: runs trufflehog binary, parses NDJSON output into list[Finding]
  - fixture-based tests for both tools (12 tests total)

affects: [01-03, 01-04, scanner orchestration, report generation]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD: test file written before implementation, RED confirmed, then GREEN"
    - "subprocess.run without check=True — security scanners exit 1 on findings"
    - "NDJSON parsing via splitlines() loop with per-line json.loads and graceful skip on decode errors"
    - "git vs filesystem subcommand detection via (project_path / '.git').is_dir()"

key-files:
  created:
    - app/tools/gitleaks.py
    - app/tools/trufflehog.py
    - tests/test_tools_gitleaks.py
    - tests/test_tools_trufflehog.py
    - app/__init__.py
    - app/core/__init__.py
    - app/core/models.py
    - app/tools/__init__.py
    - pytest.ini
  modified: []

key-decisions:
  - "All gitleaks findings default to Severity.HIGH and FindingCategory.SECRET — no per-rule severity mapping needed at this stage"
  - "Trufflehog Verified=True gets Severity.CRITICAL; Verified=False gets Severity.HIGH — differentiates live leaks from potential leaks"
  - "subprocess.run without check=True — gitleaks exits 1 when secrets found, not an error condition"
  - "Worktree required app/core/models.py and __init__ files to be created locally (worktree is sparse, not full repo clone)"

patterns-established:
  - "BaseTool inheritance: class FooTool(BaseTool) with tool_name = 'foo' and run(project_path) -> list[Finding]"
  - "Empty stdout guard: if not result.stdout or not result.stdout.strip(): return []"
  - "UUID ids: id=str(uuid.uuid4()) for every Finding"
  - "Mock pattern for tests: patch('subprocess.run') + patch.object(Tool, 'resolve_binary', return_value='...')"

requirements-completed: [BACK-04, BACK-02]

# Metrics
duration: 4min
completed: 2026-03-30
---

# Phase 01 Plan 02: Gitleaks and Trufflehog Runners Summary

**GitleaksTool and TrufflehogTool runners using subprocess + JSON/NDJSON parsing, each validated by 6 fixture-based TDD tests without live binaries**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-30T20:18:17Z
- **Completed:** 2026-03-30T20:21:44Z
- **Tasks:** 2
- **Files modified:** 9 created

## Accomplishments

- GitleaksTool.run() parses gitleaks JSON array output into list[Finding] with correct field mapping (tool, category, file_path, line_number, rule_id, severity all Severity.HIGH)
- TrufflehogTool.run() parses NDJSON (one JSON per line) into list[Finding] with verified=True -> CRITICAL, verified=False -> HIGH severity
- Both tools use BaseTool.resolve_binary() for binary location (BinaryLocator pattern)
- Both tools handle empty stdout, non-zero exit codes, and git vs no-git directory detection
- 12 fixture-based tests pass without any live scanner binaries

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement GitleaksTool runner** - `ed109ac` (feat)
2. **Task 2: Implement TrufflehogTool runner** - `c11c28d` (feat)

_Note: TDD tasks — tests written first (RED confirmed), then implementation (GREEN)_

## Files Created/Modified

- `app/tools/gitleaks.py` - GitleaksTool: subprocess call, JSON array parsing, Finding normalization
- `app/tools/trufflehog.py` - TrufflehogTool: subprocess call, NDJSON splitlines parsing, verified severity mapping
- `tests/test_tools_gitleaks.py` - 6 tests: parse findings, field mapping, no findings, empty stdout, --no-git flag, binary not found
- `tests/test_tools_trufflehog.py` - 6 tests: parse NDJSON, finding fields, unverified HIGH, no findings, git subcommand, filesystem subcommand
- `app/core/models.py` - Finding, Severity, FindingCategory, ScanResult models (created in worktree)
- `app/__init__.py`, `app/core/__init__.py`, `app/tools/__init__.py` - Package init files (created in worktree)
- `pytest.ini` - Test configuration for worktree

## Decisions Made

- All gitleaks findings default to Severity.HIGH — gitleaks does not provide per-finding severity in its JSON output; HIGH is appropriate for any detected secret
- Trufflehog Verified=True gets Severity.CRITICAL — a verified live secret is a confirmed breach-level finding
- No `check=True` in subprocess.run — gitleaks exits 1 when it finds secrets, which is normal operation not an error

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created missing package infrastructure in worktree**
- **Found during:** Task 1 (GitleaksTool implementation)
- **Issue:** Git worktree is sparse — only `app/tools/base.py` was present. `app/core/models.py`, `app/__init__.py`, `app/core/__init__.py`, `app/tools/__init__.py`, and `pytest.ini` were all missing, causing import failures
- **Fix:** Created all missing files by copying from main repo (models.py) or creating as empty init files; added pytest.ini to worktree root
- **Files modified:** app/__init__.py, app/core/__init__.py, app/core/models.py, app/tools/__init__.py, pytest.ini
- **Verification:** `python3 -m pytest tests/ -x -q` passes 17 tests
- **Committed in:** ed109ac (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing worktree infrastructure)
**Impact on plan:** Infrastructure gap in sparse worktree; required creating standard package files. No scope creep.

## Issues Encountered

None beyond the worktree infrastructure gap documented above.

## Known Stubs

None — both tools have complete implementations with real parsing logic. No hardcoded empty returns or placeholder data.

## Next Phase Readiness

- GitleaksTool and TrufflehogTool are fully implemented and tested
- Ready for Plan 03: Semgrep and Grype runners (more complex output formats)
- BaseTool pattern and fixture-based test approach validated — Plans 03 and 04 can follow same structure
- All 17 tests pass including Plan 01 BinaryLocator tests (no regressions)

---
*Phase: 01-foundation*
*Completed: 2026-03-30*

## Self-Check: PASSED

- app/tools/gitleaks.py: FOUND
- app/tools/trufflehog.py: FOUND
- tests/test_tools_gitleaks.py: FOUND
- tests/test_tools_trufflehog.py: FOUND
- .planning/phases/01-foundation/01-02-SUMMARY.md: FOUND
- Commit ed109ac (Task 1): FOUND
- Commit c11c28d (Task 2): FOUND
- 12 tests pass: VERIFIED

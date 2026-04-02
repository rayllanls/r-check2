---
phase: 01-foundation
plan: "03"
subsystem: scanning
tags: [semgrep, grype, sast, cve, python, language-detection, subprocess]

requires:
  - phase: 01-01
    provides: BaseTool with resolve_binary() 3-level fallback pattern

provides:
  - SemgrepTool.run() parsing --json output into list[Finding] with language-aware rule selection
  - GrypeTool.run() parsing -o json output into list[Finding] with CVE data
  - select_rulesets() mapping detected languages to assets/rules/ paths
  - app/core/models.py with Finding, Severity, FindingCategory, ScanResult
  - app/core/language.py with detect_languages, count_files, select_rulesets

affects: [01-04, phase-02, phase-03, phase-04, phase-05]

tech-stack:
  added: [json, subprocess, uuid (stdlib only)]
  patterns:
    - SemgrepTool follows BaseTool pattern with resolve_binary() + subprocess.run (no check=True)
    - GrypeTool uses dir: prefix for directory scanning
    - SEVERITY_MAP dict normalizes tool-specific severity strings to Severity enum
    - Language detection feeds into ruleset selection via select_rulesets()

key-files:
  created:
    - app/core/models.py
    - app/core/language.py
    - app/tools/semgrep.py
    - app/tools/grype.py
    - tests/test_tools_semgrep.py
    - tests/test_tools_grype.py
    - tests/test_language.py
  modified: []

key-decisions:
  - "Semgrep does NOT use --config auto or --config r/ — local assets/rules/ paths only (offline support)"
  - "Semgrep exits 1 when findings exist — no check=True in subprocess.run"
  - "Grype uses dir: prefix for directory scanning: grype dir:/path -o json"
  - "Grype Negligible severity maps to Severity.INFO (not Low)"
  - "select_rulesets falls back to assets/rules/generic when no language matches"

patterns-established:
  - "Pattern: SEVERITY_MAP dict for each tool to normalize severity strings to Severity enum"
  - "Pattern: _normalize() method in each tool converts raw dict to Finding dataclass"
  - "Pattern: subprocess.run without check=True — tools may exit non-zero with valid findings"

requirements-completed: [BACK-01, BACK-03, SCAN-03]

duration: 10min
completed: 2026-03-30
---

# Phase 01 Plan 03: Semgrep SAST Runner and Grype CVE Scanner Summary

**SemgrepTool and GrypeTool runners with language-aware rule selection via select_rulesets(), 15 fixture-based tests covering severity mapping, CVE fields, and subprocess behavior**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-30T20:11:00Z
- **Completed:** 2026-03-30T20:21:40Z
- **Tasks:** 2
- **Files modified:** 9 (7 created + 2 package init files)

## Accomplishments
- SemgrepTool.run() parses --json output into list[Finding] with ERROR->HIGH, WARNING->MEDIUM, INFO->LOW severity mapping
- GrypeTool.run() parses -o json output into list[Finding] with CVE IDs, Negligible->INFO mapping, and dir: prefix
- select_rulesets() maps detected languages (Python, JS, TS, Go, Java, Ruby, PHP) to assets/rules/ paths
- app/core/models.py and app/core/language.py established as shared domain models

## Task Commits

Each task was committed atomically:

1. **Task 1: SemgrepTool runner and language-to-ruleset mapping** - `36c27f0` (feat)
2. **Task 2: GrypeTool CVE scanner** - `6ef009e` (feat)

**Plan metadata:** (docs commit — see below)

_Note: TDD tasks follow RED (failing test) → GREEN (implementation) pattern_

## Files Created/Modified
- `app/core/models.py` - Finding, Severity, FindingCategory, ScanResult dataclasses
- `app/core/language.py` - detect_languages, count_files, LANGUAGE_TO_RULESET, select_rulesets
- `app/tools/semgrep.py` - SemgrepTool with --json parsing, SEVERITY_MAP, language-aware --config
- `app/tools/grype.py` - GrypeTool with dir: prefix, -o json parsing, Negligible->INFO mapping
- `tests/test_tools_semgrep.py` - 6 fixture-based tests for SemgrepTool
- `tests/test_tools_grype.py` - 6 fixture-based tests for GrypeTool
- `tests/test_language.py` - 6 tests (3 detect_languages/count_files + 3 select_rulesets)
- `app/__init__.py`, `app/core/__init__.py`, `app/tools/__init__.py` - package init files

## Decisions Made
- Used `assets/rules/generic` as fallback when no language-specific rulesets match — ensures Semgrep always runs even for unknown languages
- Grype's "Negligible" severity maps to Severity.INFO (not Low) to match plan specification
- No `check=True` in any subprocess.run() call — both Semgrep and Grype may exit non-zero with valid findings

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Worktree has separate `app/` from main repo; created package __init__.py files to ensure proper Python imports from worktree context.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- SemgrepTool and GrypeTool are ready for integration in the scan orchestrator (Plan 04)
- Plan 02 (Trufflehog + Gitleaks) follows the same BaseTool + SEVERITY_MAP pattern established here
- All 23 tests pass (no regressions against Plan 01 binary locator tests)

---
*Phase: 01-foundation*
*Completed: 2026-03-30*

## Self-Check: PASSED

- FOUND: app/tools/semgrep.py
- FOUND: app/tools/grype.py
- FOUND: app/core/language.py (with select_rulesets)
- FOUND: app/core/models.py
- FOUND: tests/test_tools_semgrep.py
- FOUND: tests/test_tools_grype.py
- FOUND: tests/test_language.py
- FOUND: commit 36c27f0 (Task 1)
- FOUND: commit 6ef009e (Task 2)
- FOUND: commit 3c1912e (metadata)

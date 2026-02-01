---
phase: 02-core-bug-fixes
plan: 01
subsystem: core
tags: [yt-dlp, windows, pyinstaller, filenames, version-detection]

# Dependency graph
requires:
  - phase: 01-logging-foundation
    provides: Logging infrastructure for debugging
provides:
  - Windows-safe filename handling via windowsfilenames option
  - Robust yt-dlp version detection with fallback strategies
  - Graceful exit handling with atexit
affects: [02-02, 03-error-ux]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Defensive attribute access with getattr for bundled app compatibility"
    - "yt-dlp windowsfilenames option for cross-platform filename safety"

key-files:
  created: []
  modified:
    - src/core/downloader.py
    - src/core/updater.py
    - src/ui/settings_dialog.py
    - src/main.py
    - build.spec

key-decisions:
  - "Use yt-dlp windowsfilenames option instead of manual sanitization"
  - "Multi-strategy version detection with getattr fallback"
  - "Let OS handle MEI cleanup rather than custom cleanup code"

patterns-established:
  - "Defensive imports: Use getattr for module attributes in bundled apps"
  - "yt-dlp options: Always enable windowsfilenames for Windows compatibility"

# Metrics
duration: 2min
completed: 2026-02-01
---

# Phase 2 Plan 1: Core Bug Fixes Summary

**Fixed Errno 22 filename errors, yt-dlp version detection, and PyInstaller cleanup using yt-dlp's windowsfilenames option and defensive getattr patterns**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-01T09:51:52Z
- **Completed:** 2026-02-01T09:53:25Z
- **Tasks:** 3/3
- **Files modified:** 5

## Accomplishments

- Enabled Windows-safe filename sanitization via `windowsfilenames: True` (BUG-01)
- Implemented defensive yt-dlp version detection with fallback strategies (BUG-02)
- Added graceful exit handler and documented MEI cleanup approach (BUG-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix Errno 22 with Windows-safe filenames** - `412cc94` (fix)
2. **Task 2: Fix yt-dlp version detection** - `b72177d` (fix)
3. **Task 3: Handle PyInstaller MEI cleanup gracefully** - `6bf4aff` (fix)

## Files Created/Modified

- `src/core/downloader.py` - Added `windowsfilenames: True` to base options
- `src/core/updater.py` - Added `_get_current_version()` with getattr fallback
- `src/ui/settings_dialog.py` - Updated `_get_ytdlp_version()` with same pattern
- `src/main.py` - Added atexit handler for graceful shutdown logging
- `build.spec` - Added explanatory comments for runtime_tmpdir and console settings

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| Use `windowsfilenames` option | yt-dlp handles all edge cases (Unicode, reserved names, path limits) - no need for manual sanitization |
| Multi-strategy version detection | PyInstaller bundling can cause import issues; getattr provides safe fallback |
| Let OS handle MEI cleanup | Custom cleanup is error-prone due to Windows file locking; OS handles it on reboot |

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

- BUG-01, BUG-02, BUG-03 fixes complete and committed
- Ready for 02-02-PLAN.md (BUG-04: yt-dlp update loop)
- Logging from Phase 1 available for debugging remaining bugs

---
*Phase: 02-core-bug-fixes*
*Completed: 2026-02-01*

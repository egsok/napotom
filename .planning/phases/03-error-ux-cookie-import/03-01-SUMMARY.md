---
phase: 03-error-ux-cookie-import
plan: 01
subsystem: error-handling
tags: [error-messages, ux, user-friendly, patterns]

dependency_graph:
  requires:
    - "01-logging-foundation: Logging for error context"
    - "02-core-bug-fixes: Core functionality stable"
  provides:
    - "ERROR_PATTERNS list with 29 error patterns"
    - "Enhanced _translate_error() method"
    - "_clean_error_message() fallback cleanup"
  affects:
    - "03-02: Cookie import UI (error messages will guide users)"
    - "All future error handling: Consistent user-facing messages"

tech_stack:
  added: []
  patterns:
    - "Pattern tuple list for error translation"
    - "Regex-based message cleanup for fallback"

file_tracking:
  key_files:
    created: []
    modified:
      - "src/core/downloader.py"

decisions:
  - id: "pattern-order"
    choice: "Most specific patterns first"
    rationale: "Ensures precise matches take precedence over generic ones"
  - id: "cookie-actionable-hint"
    choice: "Include 'Import browser cookies in Settings' in cookie-solvable errors"
    rationale: "Guides users to next step for age/auth/403 errors"
  - id: "fallback-cleanup"
    choice: "Regex-based URL/prefix removal with 200 char truncation"
    rationale: "Ensures even unknown errors are clean and readable"

metrics:
  tasks: 1
  completed: 1
  duration: "~3 minutes"
  completed_date: "2026-02-01"
---

# Phase 03 Plan 01: Error Translation Summary

**One-liner:** Pattern-based error translation with 29 patterns, cookie hints, and clean fallback messages.

## What Was Built

Expanded the `_translate_error()` method to provide comprehensive user-friendly error messages:

1. **ERROR_PATTERNS List** (module-level constant)
   - 29 error patterns covering: age restriction, login required, availability, geo-restriction, live content, HTTP errors, network errors, technical errors
   - Ordered by specificity (most specific first)
   - Cookie-solvable errors include actionable hint: "Import browser cookies in Settings"

2. **Enhanced _translate_error()** Method
   - Checks error message against all patterns in order
   - Returns first matching friendly message
   - Falls back to `_clean_error_message()` for unknown errors

3. **New _clean_error_message()** Method
   - Strips GitHub/wiki URLs from error messages
   - Removes "ERROR:" prefixes and yt-dlp technical prefixes
   - Collapses whitespace and truncates to 200 characters
   - Returns "Download failed. Please try again." if empty after cleanup

## Key Implementation Details

```python
# Error patterns (excerpt)
ERROR_PATTERNS = [
    ('sign in to confirm your age', 'This video requires age verification. Import browser cookies in Settings.'),
    ('video unavailable', 'This video is unavailable. It may have been removed or made private.'),
    ('403', 'Access denied. Try importing browser cookies in Settings.'),
    # ... 26 more patterns
]

# Translation method
def _translate_error(self, error: Exception) -> str:
    msg = str(error).lower()
    for pattern, friendly_msg in ERROR_PATTERNS:
        if pattern in msg:
            return friendly_msg
    return self._clean_error_message(str(error))
```

## Commits

| Hash | Type | Description |
|------|------|-------------|
| bc83d42 | feat | Expand error translation with comprehensive patterns |

## Verification Results

- [x] ERROR_PATTERNS exists with 29 patterns
- [x] _clean_error_message() exists for fallback cleanup
- [x] Cookie-solvable errors include "Import browser cookies in Settings" (4 patterns)
- [x] Import check passes: `from src.core.downloader import Downloader`
- [x] No raw URLs in error message strings
- [x] All messages under 200 characters

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for 03-02:** Cookie import UI can now:
- Rely on error messages guiding users to Settings
- Implement the cookie import functionality that error messages reference
- Users will see clear actionable messages when they need cookies

**No blockers identified.**

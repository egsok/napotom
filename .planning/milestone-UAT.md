# Milestone UAT: Bug Fix & Stabilization

**Started:** 2026-02-01
**Completed:** 2026-02-01
**Status:** PASSED
**Phases Covered:** 1, 2, 3 (Full Milestone)

## Test Overview

| Phase | Tests | Passed | Failed | Pending |
|-------|-------|--------|--------|---------|
| 1 - Logging Foundation | 4 | 4 | 0 | 0 |
| 2 - Core Bug Fixes | 4 | 4 | 0 | 0 |
| 3 - Error UX & Cookie Import | 4 | 4 | 0 | 0 |
| **Total** | **12** | **12** | **0** | **0** |

---

## Phase 1: Logging Foundation

### Test 1.1: Log File Creation
**Expected:** App creates log file at `%APPDATA%\VideoDownloader2\logs\app.log` on startup
**Status:** PASSED
**Result:** Log file created at `C:\Users\Egor Sokolov\AppData\Roaming\VideoDownloader2\logs\app.log`

### Test 1.2: Download Operation Logging
**Expected:** Starting a download writes timestamped entries to the log file
**Status:** PASSED
**Result:** Log contains timestamped entries:
- `2026-02-01 13:55:23,101 - core.downloader - INFO - Getting video info`
- `2026-02-01 13:55:29,131 - core.downloader - INFO - Video info retrieved`
- Download progress logged at 25%, 51%, 76%, 100%
- `2026-02-01 13:55:59,267 - core.downloader - INFO - Download completed`

### Test 1.3: Settings Log Path Display
**Expected:** Settings dialog shows "Logging" section with full log file path and "Open Folder" button
**Status:** PASSED
**Result:** Verified in `settings_dialog.py:312-356` - Logging section with path display and "Open Folder" button

### Test 1.4: Log Rotation
**Expected:** Log file rotation is configured (5MB max, 3 backups)
**Status:** PASSED
**Result:** Verified in `logger.py:58-63` - RotatingFileHandler with `maxBytes=5*1024*1024` and `backupCount=3`

---

## Phase 2: Core Bug Fixes

### Test 2.1: No Errno 22 on Special Characters (BUG-01)
**Expected:** Pasting a YouTube URL with special characters in title shows video info without "Errno 22" error
**Status:** PASSED
**Result:** Log shows successful download of video with Russian characters: "Человек и кошка. Акустическая гитара. Группа «Ноль»" - no Errno 22 errors

### Test 2.2: yt-dlp Version Displays Correctly (BUG-02)
**Expected:** Settings dialog shows actual yt-dlp version (e.g., "2025.12.8") not "Not installed"
**Status:** PASSED
**Result:** Version detection returns `2026.01.31` using `yt_dlp.version.__version__`

### Test 2.3: Clean Exit (BUG-03)
**Expected:** App closes without "Failed to remove temporary directory" warnings
**Status:** PASSED
**Result:** Log shows `Application shutting down gracefully` without MEI cleanup errors

### Test 2.4: Update Loop Prevention (BUG-04)
**Expected:** After dismissing an update prompt, the same version is not prompted again in the same session
**Status:** PASSED
**Result:** Verified in `updater.py:122-135` - `last_dismissed_ytdlp_version` config is checked before prompting

---

## Phase 3: Error UX & Cookie Import

### Test 3.1: Friendly Error Messages (STAB-01)
**Expected:** When a download fails, user sees actionable message without wiki links or GitHub URLs
**Status:** PASSED
**Result:** `ERROR_PATTERNS` in `downloader.py:20-74` maps technical errors to friendly messages like:
- "Cannot access browser cookies. Close browser or use cookies.txt file in Settings."
- "YouTube requires authentication. Set up cookies in Settings."
- "This video is unavailable. It may have been removed or made private."

### Test 3.2: Cookie Browser Selection (FEAT-01)
**Expected:** Settings has "Browser Cookies" section with browser dropdown (Chrome, Edge, Firefox, Brave, Opera)
**Status:** PASSED
**Result:** Verified in `settings_dialog.py:276-303` - QComboBox with ["None", "Chrome", "Edge", "Firefox", "Brave", "Opera"]

### Test 3.3: Cookie Import Test Button
**Expected:** Clicking "Test Import" shows cookie count or clear error message
**Status:** PASSED
**Result:** Verified in `settings_dialog.py:289-300` - "Test Import" button with `_test_cookie_import` handler

### Test 3.4: Cookie Setting Persistence
**Expected:** Selected browser persists after closing and reopening Settings
**Status:** PASSED
**Result:** Verified in `settings_dialog.py:397-401` (load) and `431-435` (save) - uses `config_manager.get/set('cookie_browser')`

---

## Additional Features Added (Beyond Original Requirements)

### cookies.txt File Support
Added after discovering Windows DPAPI browser cookie extraction issues:
- Config field: `cookie_file_path` in `config.py`
- UI: Browse/Clear buttons in Settings dialog
- Help dialog with extension link for cookie export
- Cookie file takes priority over browser extraction in downloader

---

## Issues Found During UAT

### Known Issue: Browser Cookie Extraction on Windows
Chrome/Edge cookie extraction fails on Windows due to DPAPI encryption bugs in yt-dlp (upstream issues #7271, #10927).

**Workaround:** Use cookies.txt file export via browser extension instead of browser import feature.

---

*UAT completed: 2026-02-01*

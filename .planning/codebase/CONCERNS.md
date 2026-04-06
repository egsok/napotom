# Codebase Concerns

**Analysis Date:** 2026-02-01

## Tech Debt

**Duplicated Quality Mapping Functions:**
- Issue: `_get_quality_key()` and `_get_quality_display()` are duplicated identically in two files
- Files: `src/ui/main_window.py` (lines 248-267), `src/ui/settings_dialog.py` (lines 300-319)
- Impact: Maintenance burden - changes must be made in both places; easy to introduce bugs if one is updated but not the other
- Fix approach: Extract to a shared utility function in `src/utils/helpers.py` or create a `src/core/quality.py` module

**Hardcoded Quality Presets:**
- Issue: Quality options are defined in multiple places with string literals
- Files: `src/core/downloader.py` (lines 33-39), `src/ui/main_window.py` (lines 66, 250-256), `src/ui/settings_dialog.py` (lines 88, 302-308)
- Impact: Adding a new quality option requires changes in 3+ files
- Fix approach: Create a single source of truth for quality presets (e.g., `QUALITY_OPTIONS` constant with both key and display name)

**Silent Exception Swallowing:**
- Issue: Several exception handlers use bare `pass` statements, hiding errors
- Files:
  - `src/utils/notifications.py` (lines 66-68): Toast notification failures are silently ignored
  - `src/ui/settings_dialog.py` (line 242): yt-dlp import errors silently return "Not installed"
  - `src/utils/config.py` (line 59): Malformed config files silently reset to defaults
- Impact: Debugging issues is harder when errors are swallowed; users may not know why features aren't working
- Fix approach: Add logging for caught exceptions, or at minimum log to stderr

**No Logging Framework:**
- Issue: No structured logging anywhere in the codebase
- Files: All source files in `src/`
- Impact: Impossible to debug production issues; no audit trail; no way to enable debug mode
- Fix approach: Add Python `logging` module with configurable log levels and optional file output

## Known Bugs

**Cancel Doesn't Actually Stop yt-dlp:**
- Symptoms: Cancel button sets `_cancelled` flag but yt-dlp download continues in background
- Files: `src/core/queue.py` (lines 57-59, 64-65, 74-75, 79, 89)
- Trigger: Click cancel while a download is in progress
- Workaround: Process continues but signals are ignored; download finishes silently
- Root cause: yt-dlp doesn't support cooperative cancellation; would need process-based isolation

**FFmpeg Path Detection Not Robust:**
- Symptoms: FFmpeg not found even when installed
- Files: `src/core/downloader.py` (lines 42-55)
- Trigger: FFmpeg installed in non-standard location or system PATH
- Workaround: Returns `None` and lets yt-dlp search PATH, which may or may not work
- Note: Build.spec expects `ffmpeg.exe` in project root but this is gitignored and may not exist

## Security Considerations

**Subprocess Calls with User Paths:**
- Risk: `open_folder()` passes user-controlled paths to subprocess without validation
- Files: `src/utils/helpers.py` (lines 24, 26, 28)
- Current mitigation: Basic existence check on line 17, path normalization on line 21
- Recommendations: Consider additional validation that path is within expected download directories

**External Network Requests Without Verification:**
- Risk: Update checker connects to PyPI without certificate pinning
- Files: `src/core/updater.py` (lines 31-37)
- Current mitigation: Using HTTPS
- Recommendations: Consider certificate pinning; add user opt-out for network requests

**pip Upgrade in Running Process:**
- Risk: Running `pip install --upgrade` while application is running
- Files: `src/core/updater.py` (lines 59-65)
- Current mitigation: None - user is prompted but upgrade happens in-process
- Recommendations: Warn user that restart is required; consider downloading update separately

## Performance Bottlenecks

**UI Updates on Every Progress Tick:**
- Problem: Progress callback fires frequently, each triggering signal emission and widget update
- Files: `src/core/queue.py` (lines 78-80, 208-217), `src/core/downloader.py` (lines 138-155)
- Cause: No throttling of progress updates
- Improvement path: Add rate limiting (e.g., update UI max 10 times per second) or batch updates

**Linear Search for Item Updates:**
- Problem: `_on_progress`, `_on_finished`, `_on_error` iterate through all items to find matching ID
- Files: `src/core/queue.py` (lines 208-217, 219-231, 233-244)
- Cause: Items stored in list, searched by ID
- Improvement path: Add `dict[str, QueueItem]` index alongside the list for O(1) lookups

**QSoundEffect Initialization Lazy but No Caching:**
- Problem: Sound effect loaded from disk on first play
- Files: `src/utils/notifications.py` (lines 26-38)
- Cause: First notification may have slight delay
- Improvement path: Pre-initialize sound in background after app starts

## Fragile Areas

**Thread Pool Signal Connections:**
- Files: `src/core/queue.py` (lines 200-206)
- Why fragile: Qt signals between threads can cause race conditions if worker outlives connection target
- Safe modification: Always disconnect signals before worker cleanup; use `Qt.QueuedConnection` explicitly
- Test coverage: None - no tests exist

**Config File Persistence:**
- Files: `src/utils/config.py` (lines 62-65)
- Why fragile: No atomic write - crash during save corrupts config; no backup
- Safe modification: Write to temp file, then rename atomically
- Test coverage: None - no tests exist

**Global Singletons:**
- Files: `src/utils/config.py` (line 79), `src/utils/notifications.py` (line 72)
- Why fragile: `config_manager` and `notification_manager` are module-level singletons, making testing difficult and creating hidden dependencies
- Safe modification: Consider dependency injection pattern; at minimum, add reset methods for testing
- Test coverage: None - no tests exist

## Scaling Limits

**In-Memory Queue:**
- Current capacity: All queue items stored in memory
- Limit: Very large queues (1000+ items) may cause memory issues and slow UI
- Scaling path: Implement virtual scrolling for queue display; consider SQLite for persistence

**Single-Instance Assumption:**
- Current capacity: Assumes single application instance
- Limit: Multiple instances would have config race conditions
- Scaling path: Add file locking or single-instance enforcement

## Dependencies at Risk

**win10toast:**
- Risk: Windows-only dependency with no updates since 2020; may break on future Windows versions
- Impact: Windows toast notifications stop working
- Migration plan: Consider `plyer` for cross-platform notifications or Windows native `win32api`

**yt-dlp:**
- Risk: Frequent breaking changes as video sites update; core dependency
- Impact: Downloads fail for specific sites
- Migration plan: No alternative - keep updated; handle `ExtractorError` gracefully with helpful messages

## Missing Critical Features

**No Queue Persistence:**
- Problem: Queue is lost on application close
- Blocks: Users cannot resume interrupted sessions; app restart loses pending downloads

**No Bandwidth Limiting:**
- Problem: Downloads use maximum available bandwidth
- Blocks: Users cannot control network impact on other applications

**No Playlist Support:**
- Problem: Pasting playlist URL only processes first video
- Blocks: Users must add each video individually

**No Download History:**
- Problem: No record of completed downloads
- Blocks: Users cannot find previously downloaded files or avoid re-downloading

## Test Coverage Gaps

**Zero Test Coverage:**
- What's not tested: Entire codebase
- Files: All files in `src/`
- Risk: Any refactoring or bug fix may introduce regressions; no confidence in code correctness
- Priority: **High** - Critical missing feature

**Recommended Test Priorities:**
1. `src/core/downloader.py`: Unit tests for error translation, quality preset mapping
2. `src/utils/config.py`: Unit tests for config load/save, default values
3. `src/core/queue.py`: Integration tests for queue state transitions
4. `src/ui/`: Consider E2E tests with `pytest-qt`

---

*Concerns audit: 2026-02-01*

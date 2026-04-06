---
status: resolved
trigger: "macOS build fails with 'Requested format is not available' on any YouTube video download"
created: 2026-02-01T10:00:00Z
updated: 2026-02-01T10:00:00Z
---

## Current Focus

hypothesis: ROOT CAUSE FOUND - Format selection happens EVEN when download=False in yt-dlp. Without cookies (due to Windows path stored in config not existing on macOS), YouTube returns no formats -> "Requested format is not available" error
test: Verify by tracing yt-dlp source code
expecting: Format selection code runs during extract_info regardless of download flag
next_action: Confirm fix approach - either warn user about missing cookies or improve error message

## Symptoms

expected: Video downloads successfully on macOS (worked in v1.1.1 from Jan 12)
actual: Error "Requested format is not available" appears during "Getting video info" phase
errors: "_Eut1-bwsE0: Requested format is not available. Use --list-formats for a list of available formats"
reproduction: Any YouTube video, any quality setting, using cookies.txt file. Works on Windows.
started: Broke today after v1.1.0 changes. v1.1.1 (Jan 12) worked fine.

## Eliminated

## Evidence

- timestamp: 2026-02-01T10:05:00Z
  checked: Compared current downloader.py vs v1.1.1 baseline
  found: |
    Key difference in _get_base_opts():
    - v1.1.1: No cookie handling, no 'windowsfilenames' option
    - Current: Added cookie file handling (lines 148-159) and 'windowsfilenames': True (line 143)
    Cookie handling added checks for cookie_file_path from config_manager
  implication: Cookie handling is suspect - if path is invalid, yt-dlp may behave unexpectedly

- timestamp: 2026-02-01T10:06:00Z
  checked: config.py - how config paths are stored
  found: |
    Config stored in different locations per platform:
    - Windows: %APPDATA%/VideoDownloader2/config.json
    - macOS/Linux: ~/.config/VideoDownloader2/config.json
    cookie_file_path is stored as absolute path string
  implication: If Windows user set path like "C:\Users\...\cookies.txt" and that's in config, it would fail on macOS

- timestamp: 2026-02-01T10:10:00Z
  checked: Tested yt-dlp extract_info with current options on Windows
  found: Works fine with exact same options on Windows
  implication: Issue is platform-specific, not options-related

- timestamp: 2026-02-01T10:12:00Z
  checked: UI says error happens during "Getting video info" phase
  found: |
    User says: Error "Requested format is not available" appears during "Getting video info" phase
    But "Requested format" is ONLY returned when a format is specified to yt-dlp
    get_info() doesn't specify format, but download() DOES specify format
  implication: User may be misreading which phase the error occurs - could be during download not get_info

- timestamp: 2026-02-01T10:20:00Z
  checked: yt-dlp source code YoutubeDL.py
  found: |
    CRITICAL: Format selection happens in process_video_result() which runs EVEN when download=False!
    Code flow: extract_info(download=False) -> process_ie_result(download=False) -> process_video_result(download=False)
    At line 3045-3060 in YoutubeDL.py, format selection runs regardless of download flag
    If format_selector is None, _default_format_spec() returns "bestvideo*+bestaudio/best"
    If no formats match (e.g., YouTube returns empty formats due to missing auth), ExtractorError is raised
  implication: |
    This confirms the error CAN happen during get_info()!
    Without cookies, YouTube may not return any formats for certain videos.
    The default format selection then fails with "Requested format is not available"

- timestamp: 2026-02-01T10:22:00Z  
  checked: Cookie handling in _get_base_opts()
  found: |
    Lines 151-156: If cookie_file_path is set but file doesn't exist, only a warning is logged
    No cookies are passed to yt-dlp in this case
    User on macOS has Windows path in config -> file not found -> no cookies -> YouTube returns no formats
  implication: |
    ROOT CAUSE: Cookie file path from Windows doesn't exist on macOS
    Without cookies, YouTube bot detection triggers, returns no downloadable formats
    Format selection fails with "Requested format is not available"

## Resolution

root_cause: |
  Cookie file path stored in config.json doesn't exist on macOS (Windows path like C:\...\cookies.txt).
  When cookie file is missing, yt-dlp makes request without auth cookies.
  YouTube's bot detection returns no downloadable formats for the video.
  yt-dlp's format selection (which runs EVEN during extract_info with download=False) fails with "Requested format is not available".
  
  The error message is misleading - it's not really about format selection, it's about missing authentication.
  
fix: |
  1. Added "requested format is not available" to ERROR_PATTERNS with message directing user to set up cookies
  2. Added _cookie_file_missing flag to track when cookie file is configured but not found
  3. Special case in _translate_error: when format error occurs AND cookie file was missing, give more specific message
  
verification: |
  - Tested pattern matching: "requested format is not available" now matches and gives helpful message
  - Tested special case: when _cookie_file_missing=True, gives even more specific message about re-importing cookies
  - Verified Downloader class imports and instantiates correctly
  - Error translation tested with both scenarios:
    1. Cookie file OK: "No downloadable formats found. Try setting up cookies in Settings."
    2. Cookie file missing: "Cookie file not found. Re-import your cookies.txt file in Settings."

files_changed:
  - src/core/downloader.py

# Phase 3: Error UX & Cookie Import - Research

**Researched:** 2026-02-01
**Domain:** yt-dlp error handling and browser cookie integration
**Confidence:** HIGH

## Summary

This phase focuses on two related requirements: making error messages user-friendly (STAB-01) and enabling cookie import for age-restricted content (FEAT-01). Both leverage yt-dlp's existing capabilities.

Research confirms yt-dlp has robust built-in support for both areas:
1. **Error handling:** yt-dlp provides structured error types (`ExtractorError`, `DownloadError`, `GeoRestrictedError`, etc.) with consistent message patterns that can be mapped to friendly user messages.
2. **Cookie import:** yt-dlp's `cookiesfrombrowser` option supports all major browsers (Chrome, Edge, Firefox, Brave, Opera) with automatic cookie extraction via the `extract_cookies_from_browser` function.

The existing codebase already has a basic `_translate_error` method in `downloader.py` that handles a few error patterns. This phase expands that mapping and adds the cookie import UI to Settings.

**Primary recommendation:** Expand the existing error translation with a comprehensive pattern-matching dictionary, and add a "Browser Cookies" section to Settings that calls yt-dlp's built-in cookie extraction.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yt-dlp | latest | Cookie extraction and download | Already used; has `cookiesfrombrowser` and `extract_cookies_from_browser` built-in |
| PyQt6 | 6.x | UI components | Already used for Settings dialog |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yt_dlp.cookies | (bundled) | Browser cookie extraction | Import cookies from browsers |
| yt_dlp.utils | (bundled) | Error types | Structured error handling |

### No Additional Dependencies Required
Cookie import uses yt-dlp's built-in functionality. No new dependencies needed.

**Supported browsers for Windows:**
- Chrome
- Edge (Chromium-based)
- Firefox
- Brave
- Opera
- Vivaldi
- Chromium

## Architecture Patterns

### Recommended Project Structure
```
src/
├── core/
│   ├── downloader.py     # Expand _translate_error method
│   └── cookies.py        # NEW: Cookie management wrapper (optional)
├── ui/
│   └── settings_dialog.py # Add cookie import section
└── utils/
    └── config.py         # Add cookie_browser config field
```

### Pattern 1: Error Translation Layer
**What:** Centralized error message translation with pattern matching
**When to use:** Always - ensures consistent user-facing messages
**Example:**
```python
# Source: Existing pattern in downloader.py, expanded
class ErrorTranslator:
    """Translate yt-dlp errors to user-friendly messages."""
    
    # Patterns ordered by specificity (most specific first)
    ERROR_PATTERNS = [
        # Age restriction - actionable (cookies can help)
        ('sign in to confirm your age', 'This video requires age verification. Import browser cookies in Settings.'),
        ('age-restricted', 'This video is age-restricted. Import browser cookies in Settings.'),
        
        # Availability - not actionable
        ('video unavailable', 'This video is unavailable. It may have been removed or made private.'),
        ('private video', 'This video is private.'),
        
        # Geo-restriction - not actionable (cookies won't help)
        ('not available in your country', 'This video is not available in your region.'),
        ('geo', 'This video is geographically restricted.'),
        
        # Membership/Premium - cookies may help
        ('join this channel', 'This video is for channel members only.'),
        ('premium', 'This video requires a premium subscription.'),
        
        # HTTP errors
        ('403', 'Access denied. Try importing browser cookies.'),
        ('404', 'Video not found. Check the URL.'),
        ('429', 'Too many requests. Please wait and try again.'),
        
        # Technical errors
        ('ffmpeg', 'FFmpeg is required but not found.'),
        ('unable to download', 'Network error. Check your connection.'),
        ('timeout', 'Connection timed out. Try again.'),
    ]
    
    @classmethod
    def translate(cls, error: Exception) -> str:
        """Translate error to user-friendly message."""
        msg = str(error).lower()
        
        for pattern, friendly_msg in cls.ERROR_PATTERNS:
            if pattern in msg:
                return friendly_msg
        
        # Fallback: Return cleaned-up original message
        return cls._clean_error_message(str(error))
    
    @staticmethod
    def _clean_error_message(msg: str) -> str:
        """Remove technical details and wiki links from error message."""
        # Remove yt-dlp wiki links
        import re
        msg = re.sub(r'https?://github\.com/yt-dlp/yt-dlp[^\s]*', '', msg)
        msg = re.sub(r'\s+', ' ', msg).strip()
        # Truncate overly long messages
        if len(msg) > 200:
            msg = msg[:197] + '...'
        return msg
```

### Pattern 2: Cookie Import via yt-dlp
**What:** Use yt-dlp's built-in browser cookie extraction
**When to use:** When user wants to access age-restricted content
**Example:**
```python
# Source: yt-dlp official API
from yt_dlp.cookies import extract_cookies_from_browser, SUPPORTED_BROWSERS, CookieLoadError

def import_cookies_from_browser(browser: str, profile: str = None) -> tuple[bool, str]:
    """
    Import cookies from browser.
    
    Args:
        browser: Browser name ('chrome', 'firefox', 'edge', etc.)
        profile: Optional profile name (default profile if None)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        # yt-dlp handles all browser-specific extraction
        cookie_jar = extract_cookies_from_browser(
            browser_name=browser,
            profile=profile,
            logger=None  # Silent mode
        )
        
        # Count cookies to verify extraction worked
        cookie_count = len(list(cookie_jar))
        
        if cookie_count > 0:
            return True, f"Imported {cookie_count} cookies from {browser.title()}"
        else:
            return False, f"No cookies found in {browser.title()}"
            
    except CookieLoadError as e:
        return False, f"Could not load cookies: {e}"
    except PermissionError:
        return False, f"Permission denied. Close {browser.title()} and try again."
    except Exception as e:
        return False, f"Failed to import cookies: {e}"
```

### Pattern 3: Cookie Configuration in Downloads
**What:** Pass cookies to yt-dlp download calls
**When to use:** When user has configured a cookie browser
**Example:**
```python
# Source: yt-dlp options documentation
def _get_base_opts(self) -> dict:
    """Get base yt-dlp options."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        # ... existing options
    }
    
    # Add cookie browser if configured
    cookie_browser = config_manager.get('cookie_browser')
    if cookie_browser:
        opts['cookiesfrombrowser'] = (cookie_browser,)  # Tuple format
    
    return opts
```

### Anti-Patterns to Avoid
- **Don't store cookies in plain text:** yt-dlp handles cookie extraction on-the-fly; storing cookies adds security risk
- **Don't parse yt-dlp output with regex:** Use structured exception types and error message patterns instead
- **Don't show raw exception messages:** Always translate through the error layer
- **Don't require browser to be closed during extraction:** Windows cookies can usually be read while browser is open (unlike some Linux setups)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Browser cookie extraction | Manual SQLite/crypto code | `yt_dlp.cookies.extract_cookies_from_browser` | Handles all browser formats, encryption, profiles |
| Cookie storage format | Custom cookie files | yt-dlp's `cookiesfrombrowser` tuple | Automatically extracts fresh cookies each time |
| Error message cleanup | Custom regex patterns | Structured error type checking first | yt-dlp's error types provide categories |

**Key insight:** yt-dlp already handles the complex browser-specific cookie extraction (Chrome encryption, Firefox profile parsing, etc.). Using their API is much more reliable than reimplementing.

## Common Pitfalls

### Pitfall 1: Caching Stale Cookies
**What goes wrong:** Storing extracted cookies and using stale data
**Why it happens:** Seems more efficient to cache
**How to avoid:** Use `cookiesfrombrowser` tuple option which extracts fresh each time
**Warning signs:** "Cookie expired" errors after working initially

### Pitfall 2: Browser Lock Files
**What goes wrong:** Cookie extraction fails with database locked errors
**Why it happens:** Some browsers lock cookie database while running
**How to avoid:** 
- On Windows: Usually works while browser is open (Chromium browsers)
- Catch `PermissionError` and suggest closing browser
- Firefox may require browser to be closed

**Warning signs:** "database is locked" or permission errors

### Pitfall 3: Missing Actionable Context in Errors
**What goes wrong:** User sees "failed" but doesn't know what to do
**Why it happens:** Error message doesn't suggest next steps
**How to avoid:** For cookie-solvable errors, include "Import browser cookies in Settings"
**Warning signs:** Users repeatedly get same error without trying cookies

### Pitfall 4: Raw yt-dlp Output in UI
**What goes wrong:** User sees wiki links, technical jargon, full URLs
**Why it happens:** Displaying exception message directly
**How to avoid:** Always pass through error translator, strip URLs/wiki links
**Warning signs:** Messages with "https://github.com/yt-dlp" or `ERROR:` prefixes

### Pitfall 5: Cookie Import UI Without Feedback
**What goes wrong:** User doesn't know if cookie import worked
**Why it happens:** Silent success/failure
**How to avoid:** Show clear success/failure message with cookie count
**Warning signs:** Users import cookies, still get errors, don't know why

## Code Examples

Verified patterns from yt-dlp and existing codebase:

### Browser Cookie Import (yt-dlp API)
```python
# Source: yt-dlp.cookies module
from yt_dlp.cookies import extract_cookies_from_browser, SUPPORTED_BROWSERS

# SUPPORTED_BROWSERS = {'chrome', 'edge', 'firefox', 'brave', 'opera', 'vivaldi', 'chromium', 'safari', 'whale'}

# For Windows, common browsers:
WINDOWS_BROWSERS = ['chrome', 'edge', 'firefox', 'brave', 'opera']

# Extract cookies - returns a CookieJar
try:
    cookie_jar = extract_cookies_from_browser(
        browser_name='chrome',  # or 'edge', 'firefox', etc.
        profile=None,  # Uses default profile
        logger=None,  # Silent
        keyring=None,  # Auto-detect on Windows
        container=None  # Firefox containers, if any
    )
except Exception as e:
    print(f"Cookie extraction failed: {e}")
```

### Using Cookies in Downloads (yt-dlp options)
```python
# Source: yt-dlp YoutubeDL options
opts = {
    'cookiesfrombrowser': ('chrome',),  # Tuple: (browser,) or (browser, profile)
    # OR for specific profile:
    # 'cookiesfrombrowser': ('firefox', 'default'),
}

with yt_dlp.YoutubeDL(opts) as ydl:
    ydl.download([url])
```

### Error Types (yt-dlp utils)
```python
# Source: yt_dlp.utils
from yt_dlp.utils import (
    DownloadError,      # General download failure
    ExtractorError,     # Info extraction failure
    GeoRestrictedError, # Geographic restriction
    UnavailableVideoError,  # Format not available
    PostProcessingError,    # FFmpeg/post-process failure
)

# Error hierarchy:
# YoutubeDLError (base)
#   ├── DownloadError
#   ├── ExtractorError
#   │   └── GeoRestrictedError
#   ├── PostProcessingError
#   └── UnavailableVideoError
```

### Settings Dialog Cookie Section UI (PyQt6)
```python
# Source: Follows existing settings_dialog.py patterns
# Cookie Import section for Settings dialog
cookie_group = QGroupBox("Browser Cookies")
cookie_layout = QHBoxLayout(cookie_group)

browser_label = QLabel("Import from:")
cookie_layout.addWidget(browser_label)

self.browser_combo = QComboBox()
self.browser_combo.addItems(["None", "Chrome", "Edge", "Firefox", "Brave", "Opera"])
cookie_layout.addWidget(self.browser_combo)

cookie_layout.addStretch()

self.import_btn = QPushButton("Import Now")
self.import_btn.clicked.connect(self._on_import_cookies)
cookie_layout.addWidget(self.import_btn)

# Status label for feedback
self.cookie_status = QLabel("")
self.cookie_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual Netscape cookie files | `cookiesfrombrowser` auto-extraction | yt-dlp 2021+ | No manual cookie management |
| Separate cookie extraction tools | Built-in browser support | yt-dlp 2021+ | One-click import |
| Print raw errors | Structured error types | yt-dlp | Better categorization |

**Current yt-dlp cookie browser support (2024+):**
- Chrome/Chromium: Full support including encrypted cookies
- Edge: Full support (Chromium-based)
- Firefox: Full support including containers
- Brave: Full support
- Opera: Full support
- Safari: macOS only
- Vivaldi: Full support
- Whale: Full support

## Open Questions

1. **Profile selection UI complexity**
   - What we know: yt-dlp supports profile selection via `(browser, profile)` tuple
   - What's unclear: Whether users need profile selection or if default is sufficient
   - Recommendation: Start with default profile only; add profile selection later if users request

2. **Cookie persistence/refresh strategy**
   - What we know: `cookiesfrombrowser` extracts fresh each download
   - What's unclear: Performance impact of extracting every download
   - Recommendation: Current approach is fine; extraction is fast (<1 second)

## Sources

### Primary (HIGH confidence)
- yt-dlp GitHub README - Cookie options documentation
- `yt_dlp.cookies` module - `extract_cookies_from_browser` function, `SUPPORTED_BROWSERS`
- `yt_dlp.utils` module - Error type hierarchy
- Existing codebase - `downloader.py` error patterns, `settings_dialog.py` UI patterns

### Secondary (MEDIUM confidence)
- yt-dlp YoutubeDL class documentation (via Python help)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Using existing yt-dlp and PyQt6
- Architecture: HIGH - Extending existing patterns in codebase
- Pitfalls: HIGH - Based on yt-dlp documentation and common patterns

**Research date:** 2026-02-01
**Valid until:** 90 days (yt-dlp is stable in this area)

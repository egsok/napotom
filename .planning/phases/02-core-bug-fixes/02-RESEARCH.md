# Phase 2: Core Bug Fixes - Research

**Researched:** 2026-02-01
**Domain:** yt-dlp integration, PyInstaller bundling, Windows file system
**Confidence:** HIGH

## Summary

This phase addresses four distinct bugs in the video downloader application:

1. **BUG-01 (Errno 22)**: The "Invalid argument" error when calling `extract_info()` is caused by invalid characters in video titles that violate Windows filename restrictions. When yt-dlp prepares the output path template, titles containing characters like `?`, `*`, `"`, `<`, `>`, `|`, `:`, or `/` cause OS-level errors. The fix is to enable yt-dlp's built-in `restrictfilenames` or `windowsfilenames` option.

2. **BUG-02 (Version detection)**: The `_get_ytdlp_version()` function correctly accesses `yt_dlp.version.__version__`, but in a PyInstaller-bundled environment, the import can fail silently due to module resolution issues. The fix is to add better error handling and potentially use a subprocess fallback.

3. **BUG-03 (MEI cleanup warning)**: PyInstaller's one-file mode extracts to a temporary `_MEI*` directory. On Windows, if files are still locked when cleanup occurs, a warning appears. The fix involves either using `runtime_tmpdir` to specify a persistent temp location, or implementing graceful cleanup with `atexit` handlers.

4. **BUG-04 (Update loop)**: After updating yt-dlp via pip, the old version remains cached in the running Python process. The `yt_dlp.version.__version__` still returns the old version until restart. The fix is to store the "skipped version" or "last checked version" in config to prevent immediate re-prompting.

**Primary recommendation:** Fix each bug independently with minimal code changes, using yt-dlp's built-in options where possible.

## Standard Stack

This phase uses existing dependencies - no new libraries needed.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| yt-dlp | 2025.12.08+ | Video extraction/download | Already in use, has built-in filename sanitization |
| PyInstaller | 6.x | Application bundling | Already configured in build.spec |
| PyQt6 | 6.x | GUI framework | Already in use for dialogs |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| packaging | any | Version comparison | Could be used for robust version parsing (optional) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `restrictfilenames` option | Manual sanitization | Manual approach is error-prone, yt-dlp handles edge cases |
| subprocess version check | Direct import | Subprocess is more reliable in bundled apps but slower |
| Version in config | importlib.reload() | Reload is fragile; config approach is simpler |

## Architecture Patterns

### Bug Fix Pattern: Minimal Change, Maximum Verification

**What:** Each bug fix should be isolated, targeted, and include verification logging
**When to use:** All bug fixes in this phase
**Example:**
```python
# Before fix - add logging to understand the issue
logger.debug('Attempting operation X with params: %s', params)
try:
    result = risky_operation()
    logger.info('Operation X succeeded: %s', result)
except Exception as e:
    logger.error('Operation X failed: %s', e, exc_info=True)
    # Handle gracefully
```

### Defensive Options Pattern (BUG-01)

**What:** Use yt-dlp's built-in safeguards rather than custom code
**When to use:** Configuring yt-dlp options
**Example:**
```python
# Source: yt-dlp README - Filesystem Options
def _get_base_opts(self) -> dict:
    opts = {
        'quiet': True,
        'no_warnings': True,
        # CRITICAL: Enable Windows-safe filenames to avoid Errno 22
        'windowsfilenames': True,  # Sanitizes filenames for Windows
        # ... other options
    }
    return opts
```

### Config-Based State Pattern (BUG-04)

**What:** Store state that needs to persist across app restarts
**When to use:** Tracking update state
**Example:**
```python
# In Config dataclass
@dataclass
class Config:
    # ... existing fields
    last_ytdlp_version_check: str = ""  # e.g., "2025.12.08"
    last_ytdlp_update_dismissed: str = ""  # Version user dismissed
```

### Anti-Patterns to Avoid
- **Swallowing exceptions silently:** Always log errors, even if handling gracefully
- **Assuming import always works:** In bundled apps, imports can fail unexpectedly
- **Modifying sys.modules at runtime:** Can cause subtle bugs; prefer restart prompts
- **Assuming atomic file operations:** Windows file locking is aggressive

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Filename sanitization | Custom regex for invalid chars | yt-dlp's `windowsfilenames` option | yt-dlp handles all edge cases including Unicode, reserved names (CON, PRN), path length limits |
| Version comparison | String comparison like `"2025.12.08" > "2025.12.8"` | Tuple comparison after split: `tuple(int(x) for x in v.split('.'))` | String comparison fails: "8" > "12" alphabetically |
| Temp directory cleanup | `shutil.rmtree()` on exit | PyInstaller's `runtime_tmpdir` or let OS handle | File locking issues on Windows make manual cleanup error-prone |
| Subprocess pip commands | os.system() | subprocess.run() with proper flags | Need `CREATE_NO_WINDOW` on Windows, proper error capture |

**Key insight:** yt-dlp has spent years handling cross-platform edge cases. Use its options before building custom solutions.

## Common Pitfalls

### Pitfall 1: Windows Filename Restrictions
**What goes wrong:** Video titles often contain `?`, `"`, `:`, `|`, `<`, `>`, `*`, `/`, `\` which Windows prohibits in filenames
**Why it happens:** YouTube/other sites allow these characters in titles but Windows filesystem doesn't
**How to avoid:** Always set `windowsfilenames: True` in yt-dlp options
**Warning signs:** `OSError: [Errno 22] Invalid argument` during download or extract_info

### Pitfall 2: Cached Module State After pip Upgrade  
**What goes wrong:** After `pip install --upgrade yt-dlp`, calling `yt_dlp.version.__version__` still returns old version
**Why it happens:** Python caches imported modules in `sys.modules`; pip upgrade modifies files on disk but doesn't reload
**How to avoid:** Don't check version immediately after upgrade; prompt user to restart, or track state in config
**Warning signs:** Update dialog appearing repeatedly after "successful" update

### Pitfall 3: PyInstaller Temp Directory Locked Files
**What goes wrong:** Warning message "Failed to remove temporary directory" on Windows app exit
**Why it happens:** PyInstaller extracts to `_MEI*` temp folder; if any files (DLLs, pyd files) are still loaded when cleanup runs, Windows prevents deletion
**How to avoid:** Use `runtime_tmpdir=None` (default, lets OS clean up), or use `--onedir` mode
**Warning signs:** Accumulating `_MEI*` folders in temp directory, exit warnings

### Pitfall 4: Import Failures in Bundled Apps
**What goes wrong:** `import yt_dlp` works in dev but fails/behaves differently when bundled
**Why it happens:** PyInstaller's import hooks behave differently; hidden imports may be missing
**How to avoid:** Always wrap imports in try/except; add to hiddenimports if needed; test bundled app
**Warning signs:** "Not installed" shown when library clearly works for other operations

## Code Examples

Verified patterns for each bug fix:

### BUG-01: Enable Windows-Safe Filenames
```python
# Source: yt-dlp README, Filesystem Options section
def _get_base_opts(self) -> dict:
    """Get base yt-dlp options."""
    opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'retries': 10,
        'fragment_retries': 10,
        # CRITICAL: Sanitize filenames for Windows compatibility
        'windowsfilenames': True,
        # ... rest of options
    }
    return opts
```

### BUG-02: Robust Version Detection
```python
# Pattern: Defensive import with fallback
def _get_ytdlp_version(self) -> str:
    """Get installed yt-dlp version with multiple fallback strategies."""
    # Strategy 1: Direct import (fastest)
    try:
        import yt_dlp
        version = getattr(yt_dlp, 'version', None)
        if version:
            return getattr(version, '__version__', None) or "Unknown"
    except ImportError:
        pass
    except Exception as e:
        logger.debug('Version check via import failed: %s', e)
    
    # Strategy 2: Try yt_dlp.version module directly
    try:
        from yt_dlp import version
        return version.__version__
    except Exception as e:
        logger.debug('Version check via yt_dlp.version failed: %s', e)
    
    return "Not installed"
```

### BUG-03: PyInstaller Cleanup Handling
```python
# Option A: Accept the warning (simplest)
# Do nothing - the OS cleans up temp files eventually

# Option B: Suppress the warning via spec file (if warning is user-visible)
# In build.spec:
exe = EXE(
    # ... other args
    runtime_tmpdir=None,  # Default, let OS handle cleanup
    # Or specify a persistent location:
    # runtime_tmpdir='C:\\Users\\Public\\AppData\\VideoDownloader',
)

# Option C: Log but don't error (in main.py)
import atexit
import logging

def graceful_exit():
    """Perform cleanup on exit."""
    logger = logging.getLogger(__name__)
    logger.info('Application shutting down')
    # Don't try to delete MEI folder - let OS handle it
    
atexit.register(graceful_exit)
```

### BUG-04: Prevent Update Loop
```python
# In config.py - add field to Config dataclass
@dataclass
class Config:
    # ... existing fields
    last_ytdlp_update_check: str = ""  # ISO date of last check
    last_dismissed_ytdlp_version: str = ""  # Version user dismissed

# In updater.py or main.py
def should_prompt_for_update(current: str, latest: str) -> bool:
    """Check if we should prompt user about update."""
    # Don't prompt if user already dismissed this version
    dismissed = config_manager.get('last_dismissed_ytdlp_version', '')
    if dismissed == latest:
        logger.debug('User previously dismissed version %s', latest)
        return False
    return True

def on_update_available(current: str, latest: str):
    """Handle update available signal."""
    if not should_prompt_for_update(current, latest):
        return
        
    reply = QMessageBox.question(...)
    if reply == QMessageBox.StandardButton.Yes:
        # Do update
        pass
    else:
        # User dismissed - remember this
        config_manager.set('last_dismissed_ytdlp_version', latest)

def on_update_complete(success: bool, message: str):
    """Handle update completion."""
    if success:
        # Clear dismissed version since they accepted update
        config_manager.set('last_dismissed_ytdlp_version', '')
        # Prompt for restart instead of re-checking version
        QMessageBox.information(
            window, 
            "Update Complete", 
            "yt-dlp has been updated. Please restart the application to use the new version."
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual filename sanitization | yt-dlp's `windowsfilenames` option | Always available | Handles all edge cases automatically |
| `restrictfilenames` (ASCII only) | `windowsfilenames` (Unicode safe) | yt-dlp 2023+ | Preserves Unicode while sanitizing |
| One-file PyInstaller default temp | `runtime_tmpdir` option | PyInstaller 4.x | Better control over temp location |
| Checking version after pip upgrade | Prompt restart instead | Best practice | Avoids module caching issues |

**Deprecated/outdated:**
- `youtube-dl` compatibility mode: Not needed, yt-dlp is the maintained fork
- Manual `--restrict-filenames`: Unnecessary if using programmatic API with `windowsfilenames`

## Open Questions

Things that couldn't be fully resolved:

1. **Exact cause of BUG-01**
   - What we know: Errno 22 happens with invalid filename characters
   - What's unclear: Is it during `extract_info()` or only during actual download? The code shows `extract_info()` is called with `download=False` for info retrieval
   - Recommendation: Add logging before/after `extract_info()` to confirm; may need to also set `windowsfilenames` or investigate if yt-dlp creates temp files during extraction

2. **BUG-02 specific failure mode**
   - What we know: Returns "Not installed" despite yt-dlp working
   - What's unclear: Does it fail only in bundled mode? Only after update? 
   - Recommendation: Add debug logging to track exactly when/why the import fails

3. **BUG-03 user impact**
   - What we know: Warning appears on exit about MEI folder
   - What's unclear: Is this a console warning (invisible with `console=False`)? Or a dialog?
   - Recommendation: Test bundled app to reproduce; may not be user-visible at all

## Sources

### Primary (HIGH confidence)
- yt-dlp README.md - Filesystem Options section (`windowsfilenames`, `restrictfilenames`)
- yt-dlp FAQ - "incorrect codec parameters" / "Invalid argument" explanation
- PyInstaller documentation - runtime-information.html, advanced-topics.html
- Codebase analysis - src/core/downloader.py, src/core/updater.py, src/ui/settings_dialog.py

### Secondary (MEDIUM confidence)
- PyInstaller issues - common MEI cleanup problems on Windows
- yt-dlp GitHub issues - version detection in bundled apps

### Tertiary (LOW confidence)
- General Python knowledge about sys.modules caching after pip upgrade

## Metadata

**Confidence breakdown:**
- BUG-01 fix (windowsfilenames): HIGH - documented yt-dlp option, standard solution
- BUG-02 fix (robust import): MEDIUM - pattern is sound but needs testing in bundled app
- BUG-03 fix (MEI cleanup): MEDIUM - depends on whether warning is user-visible
- BUG-04 fix (update loop): HIGH - config-based state management is straightforward

**Research date:** 2026-02-01
**Valid until:** 60 days (yt-dlp updates frequently but these patterns are stable)

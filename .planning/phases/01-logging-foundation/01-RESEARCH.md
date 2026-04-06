# Phase 1: Logging Foundation - Research

**Researched:** 2026-02-01
**Domain:** Python logging with Qt multi-threaded application
**Confidence:** HIGH

## Summary

This phase establishes application logging for a PyQt6 desktop application that uses QThreadPool for background downloads. The Python standard library's `logging` module is the definitive solution - it's thread-safe by design, provides built-in file rotation, and integrates cleanly with the existing architecture.

Key challenges addressed:
1. **Thread safety**: Python's logging module is inherently thread-safe (handlers use locks)
2. **Log rotation**: `RotatingFileHandler` provides size-based rotation with backup files
3. **%APPDATA% integration**: Existing `get_app_data_dir()` in config.py handles path resolution
4. **Qt integration**: Logging from QRunnable workers requires no special handling

**Primary recommendation:** Use Python's built-in `logging` module with `RotatingFileHandler`, configure once at startup in main.py, then use `logging.getLogger(__name__)` throughout all modules.

## Standard Stack

The established libraries/tools for this domain:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| logging | stdlib | Core logging facility | Thread-safe, hierarchical, flexible - no alternatives needed |
| logging.handlers | stdlib | RotatingFileHandler | Built-in rotation, size limits, backup files |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| logging.config | stdlib | Dictionary-based configuration | Complex configs, but not needed here |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| logging (stdlib) | loguru | Simpler API but adds dependency; stdlib is sufficient |
| RotatingFileHandler | TimedRotatingFileHandler | Time-based vs size-based rotation; size-based better for desktop app |

**Installation:**
```bash
# No installation needed - Python standard library
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── utils/
│   ├── config.py        # Existing - path resolution
│   └── logger.py        # NEW - logging setup
├── core/
│   ├── downloader.py    # Uses logger
│   └── queue.py         # Uses logger
├── ui/
│   └── ...              # Uses logger
└── main.py              # Initializes logging
```

### Pattern 1: Module-level Logger Pattern
**What:** Each module gets its own logger via `logging.getLogger(__name__)`
**When to use:** Always - this is the standard Python idiom
**Example:**
```python
# Source: https://docs.python.org/3/library/logging.html
# In any module (e.g., src/core/downloader.py)
import logging

logger = logging.getLogger(__name__)

class Downloader:
    def download(self, url: str):
        logger.info('Starting download: %s', url)
        try:
            # ... download logic
            logger.debug('Download progress: %d%%', percent)
        except Exception as e:
            logger.exception('Download failed for %s', url)
            raise
```

### Pattern 2: Centralized Configuration
**What:** Configure logging once at application startup, not in individual modules
**When to use:** Desktop applications with single entry point
**Example:**
```python
# Source: https://docs.python.org/3/library/logging.html
# In src/utils/logger.py
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from utils.config import get_app_data_dir

def setup_logging(level: int = logging.DEBUG) -> Path:
    """
    Configure application logging.
    
    Returns:
        Path to the log file
    """
    # Create logs directory
    log_dir = get_app_data_dir() / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'app.log'
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create rotating file handler
    # 5 MB per file, keep 3 backups = max 20MB total
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    
    return log_file
```

### Pattern 3: Structured Log Format for Downloads
**What:** Include contextual information in log messages for debugging
**When to use:** When logging operations that need tracking
**Example:**
```python
# Source: https://docs.python.org/3/howto/logging-cookbook.html
# Logging download operations with context
logger.info('[%s] Download started: %s', item_id, url[:50])
logger.info('[%s] Progress: %d%%, Speed: %.2f MB/s', item_id, percent, speed)
logger.info('[%s] Download completed: %s', item_id, file_path)
logger.error('[%s] Download failed: %s', item_id, error_message)
```

### Anti-Patterns to Avoid
- **Creating loggers in __init__:** Use module-level `logger = logging.getLogger(__name__)` instead
- **Using print() for debugging:** Replace all print statements with logger calls
- **Configuring logging in multiple places:** Configure once in main.py only
- **Opening log file multiple times:** Python's logging handlers manage file access
- **Storing loggers as instance attributes:** Use module-level loggers, not `self.logger`

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Log rotation | Custom file size checking | RotatingFileHandler | Handles race conditions, atomic operations |
| Thread-safe logging | Custom locks | logging module | Already thread-safe with handler locks |
| Timestamp formatting | strftime calls | Formatter with datefmt | Consistent, handles timezone issues |
| Log levels | Custom severity constants | logging.DEBUG/INFO/etc | Standard, filterable, well-understood |
| Exception formatting | Manual traceback printing | logger.exception() | Includes full traceback automatically |

**Key insight:** Python's logging module is battle-tested and handles edge cases (thread safety, file locking, encoding) that custom solutions typically miss.

## Common Pitfalls

### Pitfall 1: Forgetting to Configure Logging Before Use
**What goes wrong:** Log messages disappear silently or print warnings to stderr
**Why it happens:** Logging must be configured before getLogger() calls produce output
**How to avoid:** Call setup_logging() at the very start of main()
**Warning signs:** "No handlers could be found for logger" warnings

### Pitfall 2: Logging in Module Import Time
**What goes wrong:** Logs occur before logging is configured
**Why it happens:** Module-level code runs during import
**How to avoid:** Only log inside functions/methods, not at module level
**Warning signs:** Some early logs missing, order seems wrong

### Pitfall 3: Using f-strings for Log Messages
**What goes wrong:** String formatting happens even when log level filters the message
**Why it happens:** f-strings evaluate immediately
**How to avoid:** Use %-style formatting with logger methods
**Warning signs:** Performance issues with verbose logging
```python
# BAD - string always formatted
logger.debug(f'Processing {expensive_operation()}')

# GOOD - only formatted if DEBUG level is enabled
logger.debug('Processing %s', expensive_operation())
```

### Pitfall 4: Not Encoding Log Files as UTF-8
**What goes wrong:** Unicode errors when logging video titles with special characters
**Why it happens:** Default encoding may not handle all characters
**How to avoid:** Always specify `encoding='utf-8'` for FileHandler/RotatingFileHandler
**Warning signs:** UnicodeEncodeError exceptions

### Pitfall 5: Log File Permissions on Windows
**What goes wrong:** PermissionError when trying to delete/rotate log files
**Why it happens:** File still open by another process or antivirus
**How to avoid:** RotatingFileHandler handles this; don't manually manage log files
**Warning signs:** Rotation failures, locked files

## Code Examples

Verified patterns from official sources:

### Basic Logging Setup
```python
# Source: https://docs.python.org/3/library/logging.html
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logging(log_dir: Path) -> Path:
    """Configure application logging with rotation."""
    log_file = log_dir / 'app.log'
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3,
        encoding='utf-8'
    )
    handler.setFormatter(formatter)
    
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(handler)
    
    return log_file
```

### RotatingFileHandler Configuration
```python
# Source: https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler
from logging.handlers import RotatingFileHandler

# Parameters:
# - filename: Path to log file
# - mode: 'a' for append (default)
# - maxBytes: Maximum file size before rotation (0 = no rotation)
# - backupCount: Number of backup files to keep
# - encoding: File encoding (use 'utf-8')
# - delay: If True, file opening deferred until first emit

handler = RotatingFileHandler(
    'app.log',
    maxBytes=5*1024*1024,  # 5 MB
    backupCount=3,
    encoding='utf-8'
)

# Results in: app.log, app.log.1, app.log.2, app.log.3
# When app.log exceeds 5MB, it rotates to app.log.1, etc.
# Total max size: 20 MB (5 MB * 4 files)
```

### Logging with Exception Information
```python
# Source: https://docs.python.org/3/library/logging.html#logging.Logger.exception
import logging

logger = logging.getLogger(__name__)

try:
    risky_operation()
except Exception:
    # Automatically includes traceback
    logger.exception('Operation failed')
```

### Logging from Worker Threads
```python
# Source: https://docs.python.org/3/howto/logging-cookbook.html#logging-from-multiple-threads
# Python logging is thread-safe by default - no special handling needed

from PyQt6.QtCore import QRunnable
import logging

logger = logging.getLogger(__name__)

class DownloadWorker(QRunnable):
    def run(self):
        # This is safe to call from any thread
        logger.info('Worker started')
        try:
            # ... work ...
            logger.info('Worker completed')
        except Exception:
            logger.exception('Worker failed')
```

### Format String for Download Operations
```python
# Recommended format for video downloader logs
FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Example output:
# 2026-02-01 14:30:45 - core.queue - INFO - [abc123] Download started: https://youtube.com/watch?v=...
# 2026-02-01 14:30:50 - core.downloader - DEBUG - [abc123] Progress: 45%, Speed: 2.5 MB/s
# 2026-02-01 14:31:00 - core.queue - INFO - [abc123] Download completed: C:\Users\...\video.mp4
# 2026-02-01 14:31:05 - core.downloader - ERROR - [def456] Download failed: Video unavailable
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| print() debugging | logging module | Always was better | Professional debugging, persistence |
| Custom log rotation | RotatingFileHandler | Python 2.4+ | Reliable, battle-tested |
| Single log file | Rotating backups | Best practice | Prevents disk fill |

**Deprecated/outdated:**
- `logging.warn()`: Deprecated, use `logging.warning()` instead
- Custom thread locks for logging: Not needed, logging is thread-safe

## Open Questions

Things that couldn't be fully resolved:

1. **Console output in development**
   - What we know: Can add StreamHandler for console output
   - What's unclear: Whether to include by default or only in dev mode
   - Recommendation: Add console handler only when running from source (not frozen exe)

2. **Log level configuration**
   - What we know: Can be set per-logger or globally
   - What's unclear: Whether users need to configure log level
   - Recommendation: Default to DEBUG for file, expose no user config initially

## Sources

### Primary (HIGH confidence)
- Python 3.14 logging documentation - https://docs.python.org/3/library/logging.html
- Python 3.14 logging.handlers documentation - https://docs.python.org/3/library/logging.handlers.html
- Python 3.14 Logging Cookbook - https://docs.python.org/3/howto/logging-cookbook.html

### Secondary (MEDIUM confidence)
- Existing codebase patterns (config.py, queue.py) - verified thread patterns

### Tertiary (LOW confidence)
- None required - stdlib documentation is authoritative

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python stdlib, extensively documented
- Architecture: HIGH - Standard patterns from official cookbook
- Pitfalls: HIGH - Common issues documented in official docs

**Research date:** 2026-02-01
**Valid until:** 90+ days (stdlib is stable, rarely changes)

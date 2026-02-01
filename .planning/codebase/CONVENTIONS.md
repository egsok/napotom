# Coding Conventions

**Analysis Date:** 2026-02-01

## Naming Patterns

**Files:**
- snake_case for all Python files: `main_window.py`, `queue_item_widget.py`
- Descriptive module names: `downloader.py`, `notifications.py`, `helpers.py`

**Functions:**
- snake_case for all functions: `get_asset_path()`, `_setup_ui()`, `_on_add_clicked()`
- Private methods prefixed with underscore: `_get_base_opts()`, `_translate_error()`
- Callback handlers use `_on_` prefix: `_on_progress()`, `_on_finished()`, `_on_item_added()`

**Variables:**
- snake_case for variables: `item_widgets`, `output_path`, `progress_callback`
- Constants use UPPER_SNAKE_CASE: `QUALITY_PRESETS`, `COLORS`, `STYLESHEET`
- Type hints used consistently on function signatures

**Classes:**
- PascalCase for classes: `MainWindow`, `DownloadQueue`, `QueueItemWidget`
- Dataclasses for data structures: `VideoInfo`, `QueueItem`, `Config`
- Custom exceptions end with `Error`: `DownloaderError`
- Qt signal classes end with `Signals`: `WorkerSignals`, `UpdaterSignals`

## Code Style

**Formatting:**
- No dedicated formatter config file detected
- Consistent 4-space indentation throughout
- Line length appears to be ~100 characters max
- Single blank line between methods
- Two blank lines between top-level definitions

**Linting:**
- No .pylintrc, .flake8, or ruff.toml detected
- Code follows PEP 8 conventions implicitly

**Type Hints:**
- Used on all function parameters and return types
- `Optional[T]` for nullable values: `Optional[str]`, `Optional[Callable]`
- `List[T]` for collections: `List[QueueItem]`
- Union types with `|` in Python 3.10+ style: `QSoundEffect | None`

## Import Organization

**Order:**
1. Standard library imports (os, sys, json, subprocess, pathlib)
2. Third-party imports (PyQt6, yt_dlp)
3. Local imports (from core.*, from ui.*, from utils.*)

**Pattern:**
```python
"""Module docstring."""

import os
import sys
from dataclasses import dataclass
from typing import Optional, List

from PyQt6.QtWidgets import QMainWindow, QWidget
from PyQt6.QtCore import Qt, pyqtSignal

from core.queue import DownloadQueue
from utils.config import config_manager
```

**Path Aliases:**
- No path aliases configured
- Direct relative imports: `from .downloader import Downloader`
- Absolute imports from package: `from core.queue import DownloadQueue`

## Error Handling

**Patterns:**
- Custom exception classes: `DownloaderError` in `src/core/downloader.py`
- Try/except blocks with specific exception types
- User-friendly error translation in `_translate_error()` method
- Silent failures with `pass` for non-critical operations (notifications)

**Error Translation Pattern:**
```python
def _translate_error(self, error: Exception) -> str:
    """Translate yt-dlp errors to user-friendly messages."""
    msg = str(error).lower()
    if 'video unavailable' in msg:
        return "Video unavailable or private"
    elif '403' in msg:
        return "Access denied to video"
    else:
        return str(error)
```

**Signal-based Error Propagation:**
- Worker threads emit error signals: `signals.error.emit(item_id, str(e))`
- Parent handles errors via connected slots: `worker.signals.error.connect(self._on_error)`

## Logging

**Framework:** None (no logging library used)

**Patterns:**
- Console print for build script only
- yt-dlp configured with `quiet: True` and `no_warnings: True`
- No application-level logging implemented

## Comments

**When to Comment:**
- Module docstrings on all files: `"""Video Downloader 2 - Main entry point."""`
- Class docstrings describing purpose: `"""Manages download queue with sequential processing."""`
- Method docstrings for non-trivial functions with Args/Returns sections
- Inline comments for non-obvious logic only

**Docstring Style (Google-style):**
```python
def download(
    self,
    url: str,
    output_path: str,
    quality: str = "best",
    progress_callback: Optional[Callable[[int, float, str], None]] = None,
) -> str:
    """
    Download video.

    Args:
        url: Video URL
        output_path: Directory to save to
        quality: Quality preset key
        progress_callback: Callback(percent, speed_mbps, status)

    Returns:
        Path to downloaded file
    """
```

## Function Design

**Size:** 
- Most functions are 10-30 lines
- Largest functions are UI setup methods (~50 lines)
- Logic split into smaller private methods

**Parameters:**
- Positional required parameters first
- Keyword arguments with defaults last
- Callback functions as optional parameters
- Type hints on all parameters

**Return Values:**
- Explicit return types in signature
- Single return value or dataclass for complex returns
- `None` for side-effect-only methods
- Early returns for guard clauses

## Module Design

**Exports:**
- Minimal `__init__.py` files with docstring only
- No explicit `__all__` declarations
- Import directly from modules: `from core.downloader import Downloader`

**Barrel Files:**
- Not used; direct imports preferred

**Singletons:**
- Global instances for managers: `config_manager = ConfigManager()`
- Global instances for notifications: `notification_manager = NotificationManager()`

## Class Design

**Dataclasses:**
- Used for data containers with `@dataclass` decorator
- Default values via `field(default_factory=...)` for mutable defaults
- `__post_init__` for initialization logic

```python
@dataclass
class QueueItem:
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    url: str = ""
    status: QueueItemStatus = QueueItemStatus.PENDING
```

**Qt Classes:**
- Inherit from appropriate Qt base: `QMainWindow`, `QDialog`, `QWidget`
- `_setup_ui()` method for UI initialization
- `_connect_signals()` for signal/slot connections
- Private methods for event handlers

## UI Patterns

**Widget Styling:**
- Central stylesheet in `src/ui/styles.py`
- `COLORS` dict for color palette
- `STYLESHEET` string for Qt stylesheet
- Inline styles via `setStyleSheet()` for overrides

**Signal/Slot Pattern:**
- Custom signals defined at class level: `cancel_clicked = pyqtSignal(str)`
- Slots connected in `_connect_signals()` method
- Lambda for simple signal forwarding: `lambda: self.cancel_clicked.emit(self.item.id)`

**Layout Pattern:**
```python
def _setup_ui(self):
    central = QWidget()
    self.setCentralWidget(central)
    
    layout = QVBoxLayout(central)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(16)
    
    # Section layouts nested
    section = QHBoxLayout()
    section.addWidget(widget)
    layout.addLayout(section)
```

## Threading Patterns

**QThreadPool + QRunnable:**
- Worker classes inherit `QRunnable`
- Signals via separate `QObject` subclass
- `@pyqtSlot()` decorator on `run()` method

```python
class DownloadWorker(QRunnable):
    def __init__(self, item: QueueItem):
        super().__init__()
        self.signals = WorkerSignals()
        
    @pyqtSlot()
    def run(self):
        # Background work
        self.signals.finished.emit(item_id, result)
```

---

*Convention analysis: 2026-02-01*

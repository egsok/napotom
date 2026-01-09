# Video Downloader 2 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a desktop video downloader for YouTube, VK, Vimeo, Wistia, X with modern dark UI.

**Architecture:** PyQt6 GUI with QThreadPool for background downloads. yt-dlp as external binary (allows runtime updates). Custom QSS dark theme with purple/magenta accents.

**Tech Stack:** Python 3.11+, PyQt6, yt-dlp (external binary), FFmpeg (bundled), PyInstaller

---

## Pre-Implementation Setup

### Task 0: Project Setup

**Files:**
- Create: `requirements.txt`
- Create: `src/main.py`
- Create: `.gitignore`

**Step 1: Create requirements.txt**

```txt
PyQt6>=6.6.0
yt-dlp>=2024.01.01
pyinstaller>=6.0.0
```

**Step 2: Create .gitignore**

```gitignore
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
build/
*.spec
.venv/
venv/
*.exe
ffmpeg.exe
ffprobe.exe
```

**Step 3: Create minimal main.py**

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader 2")
        self.setMinimumSize(600, 400)

        label = QLabel("Video Downloader 2", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Step 4: Create virtual environment and install**

```bash
cd D:\dev\video-downloader2
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**Step 5: Run to verify setup**

```bash
python src/main.py
```
Expected: Window opens with "Video Downloader 2" text

**Step 6: Commit**

```bash
git add .
git commit -m "chore: initial project setup with PyQt6"
```

---

## Task 1: Dark Theme Stylesheet

**Files:**
- Create: `src/ui/styles.py`
- Modify: `src/main.py`

**Step 1: Create styles.py with color constants and QSS**

```python
"""Dark theme stylesheet with purple/magenta accents."""

# Color palette
COLORS = {
    "bg_dark": "#1a1a2e",
    "bg_card": "#16213e",
    "bg_input": "#0f1526",
    "accent_purple": "#9b59b6",
    "accent_magenta": "#e91e9b",
    "text_primary": "#eaeaea",
    "text_secondary": "#a0a0a0",
    "border": "#2a2a4a",
    "error": "#e74c3c",
    "success": "#2ecc71",
}

STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS["bg_dark"]};
    color: {COLORS["text_primary"]};
    font-family: "Segoe UI", sans-serif;
    font-size: 14px;
}}

QLabel {{
    color: {COLORS["text_primary"]};
    background-color: transparent;
}}

QLabel#sectionTitle {{
    font-size: 12px;
    font-weight: bold;
    color: {COLORS["text_secondary"]};
    text-transform: uppercase;
    letter-spacing: 1px;
}}

QPushButton {{
    background-color: {COLORS["accent_purple"]};
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    color: white;
    font-weight: bold;
}}

QPushButton:hover {{
    background-color: {COLORS["accent_magenta"]};
}}

QPushButton:pressed {{
    background-color: #7b2d8e;
}}

QPushButton:disabled {{
    background-color: #3a3a5a;
    color: #6a6a8a;
}}

QPushButton#iconButton {{
    padding: 8px;
    min-width: 40px;
    max-width: 40px;
}}

QLineEdit {{
    background-color: {COLORS["bg_input"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 10px 14px;
    color: {COLORS["text_primary"]};
    selection-background-color: {COLORS["accent_purple"]};
}}

QLineEdit:focus {{
    border-color: {COLORS["accent_purple"]};
}}

QLineEdit::placeholder {{
    color: {COLORS["text_secondary"]};
}}

QComboBox {{
    background-color: {COLORS["bg_input"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 8px 14px;
    color: {COLORS["text_primary"]};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {COLORS["accent_purple"]};
}}

QComboBox::drop-down {{
    border: none;
    width: 30px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {COLORS["text_secondary"]};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["bg_card"]};
    border: 2px solid {COLORS["border"]};
    border-radius: 6px;
    selection-background-color: {COLORS["accent_purple"]};
    outline: none;
}}

QProgressBar {{
    background-color: {COLORS["bg_input"]};
    border: none;
    border-radius: 4px;
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {COLORS["accent_purple"]},
        stop:1 {COLORS["accent_magenta"]}
    );
    border-radius: 4px;
}}

QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollBar:vertical {{
    background-color: {COLORS["bg_dark"]};
    width: 10px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS["border"]};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["accent_purple"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QCheckBox {{
    spacing: 8px;
    color: {COLORS["text_primary"]};
}}

QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid {COLORS["border"]};
    background-color: {COLORS["bg_input"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent_purple"]};
    border-color: {COLORS["accent_purple"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent_purple"]};
}}
"""
```

**Step 2: Update main.py to use stylesheet**

```python
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt6.QtCore import Qt

from ui.styles import STYLESHEET


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader 2")
        self.setMinimumSize(600, 400)

        label = QLabel("Video Downloader 2", self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCentralWidget(label)


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Step 3: Run to verify dark theme**

```bash
python src/main.py
```
Expected: Dark window with purple styling

**Step 4: Commit**

```bash
git add .
git commit -m "feat: add dark theme with purple/magenta accents"
```

---

## Task 2: Configuration System

**Files:**
- Create: `src/utils/config.py`

**Step 1: Create config.py**

```python
"""Configuration management with JSON persistence."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


def get_app_data_dir() -> Path:
    """Get application data directory."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:  # Linux/Mac
        base = Path.home() / '.config'

    app_dir = base / 'VideoDownloader2'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_default_download_dir() -> str:
    """Get default download directory."""
    downloads = Path.home() / 'Downloads' / 'Videos'
    downloads.mkdir(parents=True, exist_ok=True)
    return str(downloads)


@dataclass
class Config:
    """Application configuration."""
    download_path: str = ""
    default_quality: str = "best"
    notifications_enabled: bool = True
    sound_enabled: bool = True
    check_updates: bool = True

    def __post_init__(self):
        if not self.download_path:
            self.download_path = get_default_download_dir()


class ConfigManager:
    """Manages loading and saving configuration."""

    def __init__(self):
        self.config_path = get_app_data_dir() / 'config.json'
        self.config = self._load()

    def _load(self) -> Config:
        """Load config from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return Config()

    def save(self) -> None:
        """Save config to file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        """Get config value."""
        return getattr(self.config, key, default)

    def set(self, key: str, value) -> None:
        """Set config value and save."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save()


# Global config instance
config_manager = ConfigManager()
```

**Step 2: Test config manually**

```bash
python -c "from src.utils.config import config_manager; print(config_manager.config)"
```
Expected: Config object with default values printed

**Step 3: Commit**

```bash
git add .
git commit -m "feat: add configuration system with JSON persistence"
```

---

## Task 3: Downloader Core (yt-dlp wrapper)

**Files:**
- Create: `src/core/downloader.py`

**Step 1: Create downloader.py with VideoInfo dataclass**

```python
"""yt-dlp wrapper for video downloading."""

import os
import sys
from dataclasses import dataclass
from typing import Optional, Callable, List
from pathlib import Path

import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError


@dataclass
class VideoInfo:
    """Video metadata."""
    url: str
    title: str
    duration: int  # seconds
    thumbnail: Optional[str]
    uploader: Optional[str]
    extractor: str  # youtube, vimeo, etc.

    @property
    def duration_str(self) -> str:
        """Format duration as HH:MM:SS or MM:SS."""
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"


# Quality presets mapping to yt-dlp format strings
QUALITY_PRESETS = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "audio": "bestaudio/best",
}


def get_ffmpeg_path() -> Optional[str]:
    """Get FFmpeg path, handling PyInstaller bundling."""
    if getattr(sys, 'frozen', False):
        # Running as bundled exe
        base_path = sys._MEIPASS
    else:
        # Running as script - check project root
        base_path = Path(__file__).parent.parent.parent

    ffmpeg = Path(base_path) / 'ffmpeg.exe'
    if ffmpeg.exists():
        return str(ffmpeg.parent)

    return None  # Let yt-dlp find it in PATH


class Downloader:
    """Video downloader using yt-dlp."""

    def __init__(self):
        self.ffmpeg_location = get_ffmpeg_path()

    def _get_base_opts(self) -> dict:
        """Get base yt-dlp options."""
        opts = {
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
        }
        if self.ffmpeg_location:
            opts['ffmpeg_location'] = self.ffmpeg_location
        return opts

    def get_info(self, url: str) -> VideoInfo:
        """Extract video information without downloading."""
        opts = self._get_base_opts()

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
                info = ydl.sanitize_info(info)

                return VideoInfo(
                    url=url,
                    title=info.get('title', 'Unknown'),
                    duration=info.get('duration', 0) or 0,
                    thumbnail=info.get('thumbnail'),
                    uploader=info.get('uploader'),
                    extractor=info.get('extractor', 'unknown'),
                )
            except ExtractorError as e:
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                raise DownloaderError(f"Failed to get video info: {e}")

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
        opts = self._get_base_opts()
        opts['format'] = QUALITY_PRESETS.get(quality, QUALITY_PRESETS['best'])
        opts['outtmpl'] = os.path.join(output_path, '%(title)s.%(ext)s')
        opts['merge_output_format'] = 'mp4'

        # Extract audio only for audio preset
        if quality == 'audio':
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]

        downloaded_file = None

        def progress_hook(d):
            nonlocal downloaded_file

            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                speed = d.get('speed') or 0

                if total > 0:
                    percent = int(downloaded / total * 100)
                    speed_mbps = speed / 1_000_000  # Convert to MB/s
                    if progress_callback:
                        progress_callback(percent, speed_mbps, 'downloading')

            elif d['status'] == 'finished':
                downloaded_file = d.get('filename')
                if progress_callback:
                    progress_callback(100, 0, 'processing')

        opts['progress_hooks'] = [progress_hook]

        with yt_dlp.YoutubeDL(opts) as ydl:
            try:
                ydl.download([url])
                if progress_callback:
                    progress_callback(100, 0, 'completed')
                return downloaded_file or output_path
            except DownloadError as e:
                raise DownloaderError(self._translate_error(e))
            except Exception as e:
                raise DownloaderError(f"Download failed: {e}")

    def _translate_error(self, error: Exception) -> str:
        """Translate yt-dlp errors to user-friendly messages."""
        msg = str(error).lower()

        if 'video unavailable' in msg or 'private video' in msg:
            return "Video unavailable or private"
        elif 'sign in' in msg or 'age' in msg:
            return "Video requires age verification"
        elif 'geo' in msg or 'not available in your country' in msg:
            return "Video not available in your region"
        elif '403' in msg:
            return "Access denied to video"
        elif '404' in msg:
            return "Video not found"
        elif '429' in msg:
            return "Too many requests, try again later"
        elif 'ffmpeg' in msg:
            return "FFmpeg required but not found"
        else:
            return str(error)


class DownloaderError(Exception):
    """Custom exception for download errors."""
    pass
```

**Step 2: Test downloader with a public video**

```bash
python -c "
from src.core.downloader import Downloader
d = Downloader()
info = d.get_info('https://www.youtube.com/watch?v=jNQXAC9IVRw')
print(f'Title: {info.title}')
print(f'Duration: {info.duration_str}')
"
```
Expected: Video info printed (Me at the zoo - first YouTube video)

**Step 3: Commit**

```bash
git add .
git commit -m "feat: add yt-dlp downloader wrapper with error handling"
```

---

## Task 4: Download Queue System

**Files:**
- Create: `src/core/queue.py`

**Step 1: Create queue.py with QueueItem and DownloadQueue**

```python
"""Download queue management with Qt signals."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from uuid import uuid4

from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot

from .downloader import Downloader, VideoInfo, DownloaderError


class QueueItemStatus(Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"  # FFmpeg merge phase
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class QueueItem:
    """Represents a download in the queue."""
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    url: str = ""
    info: Optional[VideoInfo] = None
    quality: str = "best"
    output_path: str = ""
    status: QueueItemStatus = QueueItemStatus.PENDING
    progress: int = 0
    speed: float = 0.0  # MB/s
    error: Optional[str] = None
    file_path: Optional[str] = None


class WorkerSignals(QObject):
    """Signals for download worker."""
    progress = pyqtSignal(str, int, float, str)  # item_id, percent, speed, status
    finished = pyqtSignal(str, str)  # item_id, file_path
    error = pyqtSignal(str, str)  # item_id, error_message
    info_ready = pyqtSignal(str, object)  # item_id, VideoInfo


class DownloadWorker(QRunnable):
    """Background worker for downloading."""

    def __init__(self, item: QueueItem):
        super().__init__()
        self.item = item
        self.signals = WorkerSignals()
        self.downloader = Downloader()
        self._cancelled = False

    def cancel(self):
        """Request cancellation."""
        self._cancelled = True

    @pyqtSlot()
    def run(self):
        """Execute download in background thread."""
        if self._cancelled:
            return

        try:
            # First get video info if not available
            if not self.item.info:
                info = self.downloader.get_info(self.item.url)
                self.signals.info_ready.emit(self.item.id, info)
                self.item.info = info

            if self._cancelled:
                return

            # Download with progress callback
            def on_progress(percent: int, speed: float, status: str):
                if not self._cancelled:
                    self.signals.progress.emit(self.item.id, percent, speed, status)

            file_path = self.downloader.download(
                url=self.item.url,
                output_path=self.item.output_path,
                quality=self.item.quality,
                progress_callback=on_progress,
            )

            if not self._cancelled:
                self.signals.finished.emit(self.item.id, file_path)

        except DownloaderError as e:
            self.signals.error.emit(self.item.id, str(e))
        except Exception as e:
            self.signals.error.emit(self.item.id, f"Unexpected error: {e}")


class DownloadQueue(QObject):
    """Manages download queue with sequential processing."""

    # Signals for UI updates
    item_added = pyqtSignal(object)  # QueueItem
    item_updated = pyqtSignal(object)  # QueueItem
    item_removed = pyqtSignal(str)  # item_id
    queue_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.items: List[QueueItem] = []
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)  # Sequential downloads
        self._current_worker: Optional[DownloadWorker] = None

    def add(self, url: str, quality: str, output_path: str) -> QueueItem:
        """Add URL to download queue."""
        item = QueueItem(
            url=url,
            quality=quality,
            output_path=output_path,
        )
        self.items.append(item)
        self.item_added.emit(item)

        # Start processing if this is the only item
        self._process_next()

        return item

    def remove(self, item_id: str) -> None:
        """Remove item from queue."""
        for i, item in enumerate(self.items):
            if item.id == item_id:
                if item.status == QueueItemStatus.DOWNLOADING:
                    self.cancel(item_id)
                self.items.pop(i)
                self.item_removed.emit(item_id)
                break

    def cancel(self, item_id: str) -> None:
        """Cancel download."""
        for item in self.items:
            if item.id == item_id:
                item.status = QueueItemStatus.CANCELLED
                if self._current_worker and self._current_worker.item.id == item_id:
                    self._current_worker.cancel()
                self.item_updated.emit(item)
                break

    def clear_completed(self) -> None:
        """Remove all completed/failed/cancelled items."""
        self.items = [
            item for item in self.items
            if item.status in (QueueItemStatus.PENDING, QueueItemStatus.DOWNLOADING)
        ]

    def _process_next(self) -> None:
        """Start next pending download."""
        # Find next pending item
        for item in self.items:
            if item.status == QueueItemStatus.PENDING:
                self._start_download(item)
                return

        # No more pending items
        if not any(item.status == QueueItemStatus.DOWNLOADING for item in self.items):
            self.queue_finished.emit()

    def _start_download(self, item: QueueItem) -> None:
        """Start downloading an item."""
        item.status = QueueItemStatus.DOWNLOADING
        self.item_updated.emit(item)

        worker = DownloadWorker(item)
        self._current_worker = worker

        # Connect signals
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.info_ready.connect(self._on_info_ready)

        self.thread_pool.start(worker)

    def _on_progress(self, item_id: str, percent: int, speed: float, status: str):
        """Handle progress update."""
        for item in self.items:
            if item.id == item_id:
                item.progress = percent
                item.speed = speed
                if status == 'processing':
                    item.status = QueueItemStatus.PROCESSING
                self.item_updated.emit(item)
                break

    def _on_finished(self, item_id: str, file_path: str):
        """Handle download completion."""
        for item in self.items:
            if item.id == item_id:
                item.status = QueueItemStatus.COMPLETED
                item.progress = 100
                item.file_path = file_path
                self.item_updated.emit(item)
                break

        self._current_worker = None
        self._process_next()

    def _on_error(self, item_id: str, error: str):
        """Handle download error."""
        for item in self.items:
            if item.id == item_id:
                item.status = QueueItemStatus.FAILED
                item.error = error
                self.item_updated.emit(item)
                break

        self._current_worker = None
        self._process_next()

    def _on_info_ready(self, item_id: str, info: VideoInfo):
        """Handle video info extraction."""
        for item in self.items:
            if item.id == item_id:
                item.info = info
                self.item_updated.emit(item)
                break
```

**Step 2: Verify imports work**

```bash
python -c "from src.core.queue import DownloadQueue, QueueItem; print('OK')"
```
Expected: "OK"

**Step 3: Commit**

```bash
git add .
git commit -m "feat: add download queue with background threading"
```

---

## Task 5: Main Window UI

**Files:**
- Create: `src/ui/main_window.py`
- Create: `src/ui/widgets/queue_item_widget.py`
- Modify: `src/main.py`

**Step 1: Create queue_item_widget.py**

```python
"""Widget for displaying a queue item."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.queue import QueueItem, QueueItemStatus
from src.ui.styles import COLORS


class QueueItemWidget(QWidget):
    """Widget representing a single download item."""

    cancel_clicked = pyqtSignal(str)  # item_id

    def __init__(self, item: QueueItem, parent=None):
        super().__init__(parent)
        self.item = item
        self._setup_ui()
        self.update_from_item(item)

    def _setup_ui(self):
        """Setup widget UI."""
        self.setStyleSheet(f"""
            QueueItemWidget {{
                background-color: {COLORS["bg_card"]};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        self.setMinimumHeight(80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Top row: title and cancel button
        top_row = QHBoxLayout()

        self.title_label = QLabel("Loading...")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.title_label)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        top_row.addWidget(self.status_label)

        self.cancel_btn = QPushButton("×")
        self.cancel_btn.setObjectName("iconButton")
        self.cancel_btn.setFixedSize(32, 32)
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.item.id))
        top_row.addWidget(self.cancel_btn)

        layout.addLayout(top_row)

        # Bottom row: progress bar and speed
        bottom_row = QHBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        bottom_row.addWidget(self.progress_bar, stretch=1)

        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet(f"color: {COLORS['text_secondary']}; min-width: 100px;")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        bottom_row.addWidget(self.speed_label)

        layout.addLayout(bottom_row)

    def update_from_item(self, item: QueueItem):
        """Update widget from item data."""
        self.item = item

        # Title
        if item.info:
            title = item.info.title
            if len(title) > 50:
                title = title[:47] + "..."
            self.title_label.setText(title)
        else:
            self.title_label.setText("Getting video info...")

        # Progress
        self.progress_bar.setValue(item.progress)

        # Status and speed
        if item.status == QueueItemStatus.PENDING:
            self.status_label.setText("Waiting")
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
        elif item.status == QueueItemStatus.DOWNLOADING:
            self.status_label.setText(f"{item.progress}%")
            self.speed_label.setText(f"{item.speed:.1f} MB/s" if item.speed > 0 else "")
            self.progress_bar.setVisible(True)
        elif item.status == QueueItemStatus.PROCESSING:
            self.status_label.setText("Processing...")
            self.speed_label.setText("")
            self.progress_bar.setVisible(True)
        elif item.status == QueueItemStatus.COMPLETED:
            self.status_label.setText("Done")
            self.status_label.setStyleSheet(f"color: {COLORS['success']};")
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.cancel_btn.setVisible(False)
        elif item.status == QueueItemStatus.FAILED:
            self.status_label.setText("Failed")
            self.status_label.setStyleSheet(f"color: {COLORS['error']};")
            self.speed_label.setText(item.error or "")
            self.progress_bar.setVisible(False)
        elif item.status == QueueItemStatus.CANCELLED:
            self.status_label.setText("Cancelled")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.cancel_btn.setVisible(False)
```

**Step 2: Create main_window.py**

```python
"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel,
    QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from src.core.queue import DownloadQueue, QueueItem
from src.ui.widgets.queue_item_widget import QueueItemWidget
from src.ui.styles import COLORS
from src.utils.config import config_manager


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video Downloader 2")
        self.setMinimumSize(650, 500)

        self.queue = DownloadQueue()
        self.item_widgets: dict[str, QueueItemWidget] = {}

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup main window UI."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # URL input section
        url_section = QHBoxLayout()

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste video URL here...")
        self.url_input.returnPressed.connect(self._on_add_clicked)
        url_section.addWidget(self.url_input, stretch=1)

        self.add_btn = QPushButton("+")
        self.add_btn.setObjectName("iconButton")
        self.add_btn.setFixedSize(44, 44)
        self.add_btn.clicked.connect(self._on_add_clicked)
        url_section.addWidget(self.add_btn)

        layout.addLayout(url_section)

        # Options section
        options_section = QHBoxLayout()

        # Quality selector
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Quality:")
        quality_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        quality_layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Best", "1080p", "720p", "Audio only"])
        self.quality_combo.setCurrentText(self._get_quality_display(
            config_manager.get('default_quality', 'best')
        ))
        quality_layout.addWidget(self.quality_combo)
        options_section.addLayout(quality_layout)

        options_section.addStretch()

        # Output folder
        folder_layout = QHBoxLayout()
        folder_label = QLabel("Save to:")
        folder_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        folder_layout.addWidget(folder_label)

        self.folder_label = QLabel(self._shorten_path(config_manager.get('download_path')))
        self.folder_label.setStyleSheet("font-weight: bold;")
        folder_layout.addWidget(self.folder_label)

        self.folder_btn = QPushButton("Change")
        self.folder_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid """ + COLORS['border'] + """;
                padding: 6px 12px;
            }
            QPushButton:hover {
                border-color: """ + COLORS['accent_purple'] + """;
            }
        """)
        self.folder_btn.clicked.connect(self._on_folder_clicked)
        folder_layout.addWidget(self.folder_btn)

        options_section.addLayout(folder_layout)

        layout.addLayout(options_section)

        # Queue section
        queue_label = QLabel("QUEUE")
        queue_label.setObjectName("sectionTitle")
        layout.addWidget(queue_label)

        # Scroll area for queue items
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self.queue_container = QWidget()
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(0, 0, 0, 0)
        self.queue_layout.setSpacing(8)
        self.queue_layout.addStretch()

        scroll.setWidget(self.queue_container)
        layout.addWidget(scroll, stretch=1)

        # Empty state
        self.empty_label = QLabel("Paste a video URL and click + to start downloading")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"color: {COLORS['text_secondary']}; padding: 40px;")
        self.queue_layout.insertWidget(0, self.empty_label)

        # Bottom bar
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid """ + COLORS['border'] + """;
                padding: 8px 16px;
            }
            QPushButton:hover {
                border-color: """ + COLORS['accent_purple'] + """;
            }
        """)
        bottom_bar.addWidget(self.settings_btn)

        layout.addLayout(bottom_bar)

    def _connect_signals(self):
        """Connect queue signals."""
        self.queue.item_added.connect(self._on_item_added)
        self.queue.item_updated.connect(self._on_item_updated)
        self.queue.item_removed.connect(self._on_item_removed)

    def _on_add_clicked(self):
        """Handle add button click."""
        url = self.url_input.text().strip()
        if not url:
            return

        # Validate URL (basic check)
        if not url.startswith(('http://', 'https://')):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid URL")
            return

        quality = self._get_quality_key(self.quality_combo.currentText())
        output_path = config_manager.get('download_path')

        self.queue.add(url, quality, output_path)
        self.url_input.clear()
        self.empty_label.hide()

    def _on_folder_clicked(self):
        """Handle folder button click."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            config_manager.get('download_path')
        )
        if folder:
            config_manager.set('download_path', folder)
            self.folder_label.setText(self._shorten_path(folder))

    def _on_item_added(self, item: QueueItem):
        """Handle new item added to queue."""
        widget = QueueItemWidget(item)
        widget.cancel_clicked.connect(self._on_cancel_clicked)

        # Insert before the stretch
        self.queue_layout.insertWidget(self.queue_layout.count() - 1, widget)
        self.item_widgets[item.id] = widget

    def _on_item_updated(self, item: QueueItem):
        """Handle item update."""
        if item.id in self.item_widgets:
            self.item_widgets[item.id].update_from_item(item)

    def _on_item_removed(self, item_id: str):
        """Handle item removal."""
        if item_id in self.item_widgets:
            widget = self.item_widgets.pop(item_id)
            widget.deleteLater()

        if not self.item_widgets:
            self.empty_label.show()

    def _on_cancel_clicked(self, item_id: str):
        """Handle cancel button click."""
        self.queue.cancel(item_id)

    @staticmethod
    def _get_quality_key(display: str) -> str:
        """Convert display quality to key."""
        mapping = {
            "Best": "best",
            "1080p": "1080p",
            "720p": "720p",
            "Audio only": "audio",
        }
        return mapping.get(display, "best")

    @staticmethod
    def _get_quality_display(key: str) -> str:
        """Convert quality key to display."""
        mapping = {
            "best": "Best",
            "1080p": "1080p",
            "720p": "720p",
            "audio": "Audio only",
        }
        return mapping.get(key, "Best")

    @staticmethod
    def _shorten_path(path: str, max_len: int = 30) -> str:
        """Shorten path for display."""
        if len(path) <= max_len:
            return path
        return "..." + path[-(max_len - 3):]
```

**Step 3: Update main.py**

```python
import sys
from PyQt6.QtWidgets import QApplication

from ui.styles import STYLESHEET
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Step 4: Create __init__.py files**

```bash
# Create empty __init__.py files
echo. > src\__init__.py
echo. > src\ui\__init__.py
echo. > src\ui\widgets\__init__.py
echo. > src\core\__init__.py
echo. > src\utils\__init__.py
```

**Step 5: Run and test the UI**

```bash
cd D:\dev\video-downloader2
python src/main.py
```
Expected: Full UI with URL input, quality selector, queue area

**Step 6: Commit**

```bash
git add .
git commit -m "feat: add main window UI with queue display"
```

---

## Task 6: Notifications System

**Files:**
- Create: `src/utils/notifications.py`
- Create: `assets/sounds/complete.wav` (download/create)
- Modify: `src/core/queue.py`

**Step 1: Create notifications.py**

```python
"""System notifications and sounds."""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect

from src.utils.config import config_manager


def get_assets_path() -> Path:
    """Get assets directory path."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent
    return base_path / 'assets'


class NotificationManager:
    """Manages system notifications and sounds."""

    def __init__(self):
        self._sound: QSoundEffect | None = None
        self._init_sound()

    def _init_sound(self):
        """Initialize sound effect."""
        sound_path = get_assets_path() / 'sounds' / 'complete.wav'
        if sound_path.exists():
            self._sound = QSoundEffect()
            self._sound.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._sound.setVolume(0.5)

    def notify_complete(self, title: str):
        """Send completion notification."""
        if config_manager.get('notifications_enabled', True):
            self._show_toast(f"Download Complete", title)

        if config_manager.get('sound_enabled', True):
            self._play_sound()

    def notify_error(self, title: str, error: str):
        """Send error notification."""
        if config_manager.get('notifications_enabled', True):
            self._show_toast(f"Download Failed: {title}", error)

    def _play_sound(self):
        """Play completion sound."""
        if self._sound:
            self._sound.play()

    def _show_toast(self, title: str, message: str):
        """Show Windows toast notification."""
        try:
            # Use Windows toast notifications
            if sys.platform == 'win32':
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    duration=5,
                    threaded=True,
                )
        except ImportError:
            # Fallback: no toast notifications
            pass
        except Exception:
            pass


# Global instance
notification_manager = NotificationManager()
```

**Step 2: Add win10toast to requirements.txt**

```txt
PyQt6>=6.6.0
yt-dlp>=2024.01.01
pyinstaller>=6.0.0
win10toast>=0.9
```

**Step 3: Create assets/sounds directory**

```bash
mkdir -p assets/sounds
```

**Step 4: Download or create a notification sound**

You can download a free notification sound or create a simple beep. For now, create a placeholder:

```python
# Generate a simple beep sound (run once)
import wave
import struct
import math

def create_beep(filename, freq=880, duration=0.3, volume=0.3):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)

    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)

        for i in range(n_samples):
            value = int(volume * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            f.writeframes(struct.pack('<h', value))

create_beep('assets/sounds/complete.wav')
```

**Step 5: Update queue.py to emit notifications**

Add to DownloadQueue class:

```python
from src.utils.notifications import notification_manager

# In _on_finished method, add:
notification_manager.notify_complete(item.info.title if item.info else "Video")

# In _on_error method, add:
notification_manager.notify_error(
    item.info.title if item.info else "Video",
    error
)
```

**Step 6: Install new dependency and test**

```bash
pip install win10toast
python src/main.py
```

**Step 7: Commit**

```bash
git add .
git commit -m "feat: add notifications and sound on download complete"
```

---

## Task 7: Settings Dialog

**Files:**
- Create: `src/ui/settings_dialog.py`
- Modify: `src/ui/main_window.py`

**Step 1: Create settings_dialog.py**

```python
"""Settings dialog."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QComboBox, QCheckBox, QPushButton,
    QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt

from src.utils.config import config_manager
from src.ui.styles import COLORS


class SettingsDialog(QDialog):
    """Settings dialog window."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setModal(True)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # Downloads section
        downloads_group = QGroupBox("Downloads")
        downloads_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }}
        """)
        downloads_layout = QVBoxLayout(downloads_group)

        # Download path
        path_layout = QHBoxLayout()
        path_label = QLabel("Save to:")
        path_layout.addWidget(path_label)

        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input, stretch=1)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self._browse_folder)
        path_layout.addWidget(browse_btn)

        downloads_layout.addLayout(path_layout)

        # Default quality
        quality_layout = QHBoxLayout()
        quality_label = QLabel("Default quality:")
        quality_layout.addWidget(quality_label)
        quality_layout.addStretch()

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Best", "1080p", "720p", "Audio only"])
        quality_layout.addWidget(self.quality_combo)

        downloads_layout.addLayout(quality_layout)

        layout.addWidget(downloads_group)

        # Notifications section
        notif_group = QGroupBox("Notifications")
        notif_group.setStyleSheet(downloads_group.styleSheet())
        notif_layout = QVBoxLayout(notif_group)

        self.notif_checkbox = QCheckBox("Show system notifications")
        notif_layout.addWidget(self.notif_checkbox)

        self.sound_checkbox = QCheckBox("Play sound when complete")
        notif_layout.addWidget(self.sound_checkbox)

        layout.addWidget(notif_group)

        # Updates section
        updates_group = QGroupBox("Updates")
        updates_group.setStyleSheet(downloads_group.styleSheet())
        updates_layout = QVBoxLayout(updates_group)

        self.updates_checkbox = QCheckBox("Check for yt-dlp updates on startup")
        updates_layout.addWidget(self.updates_checkbox)

        # Version info
        version_layout = QHBoxLayout()
        version_label = QLabel("yt-dlp version:")
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        version_layout.addWidget(version_label)

        self.version_label = QLabel("checking...")
        version_layout.addWidget(self.version_label)
        version_layout.addStretch()

        self.update_btn = QPushButton("Check Now")
        self.update_btn.clicked.connect(self._check_updates)
        version_layout.addWidget(self.update_btn)

        updates_layout.addLayout(version_layout)

        layout.addWidget(updates_group)

        # Buttons
        layout.addStretch()

        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._save_and_close)
        buttons_layout.addWidget(save_btn)

        layout.addLayout(buttons_layout)

        # Get yt-dlp version
        self._get_ytdlp_version()

    def _load_settings(self):
        """Load current settings."""
        self.path_input.setText(config_manager.get('download_path', ''))

        quality_map = {
            'best': 'Best',
            '1080p': '1080p',
            '720p': '720p',
            'audio': 'Audio only',
        }
        quality = config_manager.get('default_quality', 'best')
        self.quality_combo.setCurrentText(quality_map.get(quality, 'Best'))

        self.notif_checkbox.setChecked(config_manager.get('notifications_enabled', True))
        self.sound_checkbox.setChecked(config_manager.get('sound_enabled', True))
        self.updates_checkbox.setChecked(config_manager.get('check_updates', True))

    def _browse_folder(self):
        """Open folder browser."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)

    def _save_and_close(self):
        """Save settings and close dialog."""
        quality_map = {
            'Best': 'best',
            '1080p': '1080p',
            '720p': '720p',
            'Audio only': 'audio',
        }

        config_manager.set('download_path', self.path_input.text())
        config_manager.set('default_quality', quality_map.get(self.quality_combo.currentText(), 'best'))
        config_manager.set('notifications_enabled', self.notif_checkbox.isChecked())
        config_manager.set('sound_enabled', self.sound_checkbox.isChecked())
        config_manager.set('check_updates', self.updates_checkbox.isChecked())

        self.accept()

    def _get_ytdlp_version(self):
        """Get current yt-dlp version."""
        try:
            import yt_dlp
            self.version_label.setText(yt_dlp.version.__version__)
        except Exception:
            self.version_label.setText("unknown")

    def _check_updates(self):
        """Check for yt-dlp updates."""
        # TODO: Implement update check
        self.version_label.setText("Update check not implemented yet")
```

**Step 2: Connect settings button in main_window.py**

Add to MainWindow._setup_ui():

```python
self.settings_btn.clicked.connect(self._on_settings_clicked)
```

Add method to MainWindow:

```python
def _on_settings_clicked(self):
    """Open settings dialog."""
    from src.ui.settings_dialog import SettingsDialog
    dialog = SettingsDialog(self)
    if dialog.exec():
        # Reload settings
        self.folder_label.setText(self._shorten_path(config_manager.get('download_path')))
        self.quality_combo.setCurrentText(self._get_quality_display(
            config_manager.get('default_quality', 'best')
        ))
```

**Step 3: Run and test settings**

```bash
python src/main.py
```
Expected: Settings button opens dialog, settings persist after save

**Step 4: Commit**

```bash
git add .
git commit -m "feat: add settings dialog with persistence"
```

---

## Task 8: yt-dlp Auto-Update

**Files:**
- Create: `src/core/updater.py`
- Modify: `src/main.py`
- Modify: `src/ui/settings_dialog.py`

**Step 1: Create updater.py**

```python
"""yt-dlp update management."""

import subprocess
import sys
from typing import Optional, Tuple

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class UpdaterSignals(QObject):
    """Signals for updater."""
    version_checked = pyqtSignal(str, str)  # current, latest
    update_complete = pyqtSignal(bool, str)  # success, message


class UpdateChecker(QRunnable):
    """Background worker for checking updates."""

    def __init__(self):
        super().__init__()
        self.signals = UpdaterSignals()

    @pyqtSlot()
    def run(self):
        """Check for updates."""
        try:
            import yt_dlp
            current = yt_dlp.version.__version__

            # Check PyPI for latest version
            import urllib.request
            import json

            url = "https://pypi.org/pypi/yt-dlp/json"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                latest = data['info']['version']

            self.signals.version_checked.emit(current, latest)

        except Exception as e:
            self.signals.version_checked.emit("error", str(e))


class UpdateInstaller(QRunnable):
    """Background worker for installing updates."""

    def __init__(self):
        super().__init__()
        self.signals = UpdaterSignals()

    @pyqtSlot()
    def run(self):
        """Install yt-dlp update."""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
                capture_output=True,
                text=True,
                timeout=120,
            )

            if result.returncode == 0:
                self.signals.update_complete.emit(True, "Update successful! Restart to apply.")
            else:
                self.signals.update_complete.emit(False, f"Update failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.signals.update_complete.emit(False, "Update timed out")
        except Exception as e:
            self.signals.update_complete.emit(False, str(e))


class Updater(QObject):
    """Manages yt-dlp updates."""

    update_available = pyqtSignal(str, str)  # current, latest
    update_result = pyqtSignal(bool, str)  # success, message

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()

    def check_for_updates(self):
        """Check for available updates."""
        checker = UpdateChecker()
        checker.signals.version_checked.connect(self._on_version_checked)
        self.thread_pool.start(checker)

    def install_update(self):
        """Install yt-dlp update."""
        installer = UpdateInstaller()
        installer.signals.update_complete.connect(self._on_update_complete)
        self.thread_pool.start(installer)

    def _on_version_checked(self, current: str, latest: str):
        """Handle version check result."""
        if current != "error" and current != latest:
            self.update_available.emit(current, latest)

    def _on_update_complete(self, success: bool, message: str):
        """Handle update result."""
        self.update_result.emit(success, message)


def compare_versions(v1: str, v2: str) -> int:
    """Compare version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2."""
    parts1 = [int(x) for x in v1.split('.')]
    parts2 = [int(x) for x in v2.split('.')]

    for p1, p2 in zip(parts1, parts2):
        if p1 < p2:
            return -1
        elif p1 > p2:
            return 1

    return len(parts1) - len(parts2)
```

**Step 2: Add startup update check in main.py**

```python
import sys
from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.styles import STYLESHEET
from ui.main_window import MainWindow
from core.updater import Updater
from utils.config import config_manager


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    # Check for updates on startup
    if config_manager.get('check_updates', True):
        updater = Updater()

        def on_update_available(current: str, latest: str):
            reply = QMessageBox.question(
                window,
                "Update Available",
                f"yt-dlp {latest} is available (current: {current}).\n\nUpdate now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                updater.install_update()

        def on_update_result(success: bool, message: str):
            if success:
                QMessageBox.information(window, "Update Complete", message)
            else:
                QMessageBox.warning(window, "Update Failed", message)

        updater.update_available.connect(on_update_available)
        updater.update_result.connect(on_update_result)
        updater.check_for_updates()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
```

**Step 3: Update settings dialog to use Updater**

In settings_dialog.py, update _check_updates method:

```python
def _check_updates(self):
    """Check for yt-dlp updates."""
    from src.core.updater import Updater

    self.update_btn.setEnabled(False)
    self.update_btn.setText("Checking...")

    self._updater = Updater()
    self._updater.update_available.connect(self._on_update_available)
    self._updater.update_result.connect(self._on_update_result)
    self._updater.check_for_updates()

def _on_update_available(self, current: str, latest: str):
    """Handle update available."""
    from PyQt6.QtWidgets import QMessageBox

    reply = QMessageBox.question(
        self,
        "Update Available",
        f"yt-dlp {latest} is available (current: {current}).\n\nUpdate now?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    )

    if reply == QMessageBox.StandardButton.Yes:
        self.update_btn.setText("Updating...")
        self._updater.install_update()
    else:
        self.update_btn.setEnabled(True)
        self.update_btn.setText("Check Now")

def _on_update_result(self, success: bool, message: str):
    """Handle update result."""
    from PyQt6.QtWidgets import QMessageBox

    self.update_btn.setEnabled(True)
    self.update_btn.setText("Check Now")

    if success:
        QMessageBox.information(self, "Update Complete", message)
        self._get_ytdlp_version()
    else:
        QMessageBox.warning(self, "Update Failed", message)
```

**Step 4: Run and test update check**

```bash
python src/main.py
```
Expected: On startup, checks for updates. Settings dialog can also trigger check.

**Step 5: Commit**

```bash
git add .
git commit -m "feat: add yt-dlp auto-update system"
```

---

## Task 9: PyInstaller Build Configuration

**Files:**
- Create: `build.spec`
- Create: `scripts/build.py`
- Modify: `requirements.txt`

**Step 1: Create build.spec**

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[
        # Add ffmpeg binaries here when available
        # ('ffmpeg.exe', '.'),
        # ('ffprobe.exe', '.'),
    ],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'yt_dlp',
        'win10toast',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoDownloader2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',  # Add icon when available
)
```

**Step 2: Create build script**

```python
#!/usr/bin/env python
"""Build script for VideoDownloader2."""

import subprocess
import sys
import shutil
from pathlib import Path


def main():
    root = Path(__file__).parent.parent

    # Clean previous builds
    for folder in ['build', 'dist']:
        path = root / folder
        if path.exists():
            shutil.rmtree(path)

    # Run PyInstaller
    result = subprocess.run([
        sys.executable, '-m', 'PyInstaller',
        '--clean',
        str(root / 'build.spec'),
    ], cwd=root)

    if result.returncode == 0:
        print("\n✓ Build successful!")
        print(f"  Output: {root / 'dist' / 'VideoDownloader2.exe'}")
    else:
        print("\n✗ Build failed!")
        sys.exit(1)


if __name__ == '__main__':
    main()
```

**Step 3: Test build**

```bash
python scripts/build.py
```
Expected: Creates dist/VideoDownloader2.exe

**Step 4: Commit**

```bash
git add .
git commit -m "chore: add PyInstaller build configuration"
```

---

## Final Task: Integration Testing

**Step 1: Manual test checklist**

Run the application and verify:

- [ ] Dark theme displays correctly
- [ ] Can paste YouTube URL and add to queue
- [ ] Video info loads (title appears)
- [ ] Download progresses with percentage and speed
- [ ] Notification appears on completion
- [ ] Sound plays on completion
- [ ] Can cancel download
- [ ] Settings dialog opens
- [ ] Settings persist after restart
- [ ] Quality presets work (Best, 1080p, 720p, Audio)
- [ ] Can change download folder

**Step 2: Test with different sources**

- [ ] YouTube video
- [ ] YouTube playlist (first video)
- [ ] Vimeo video
- [ ] Twitter/X video

**Step 3: Final commit**

```bash
git add .
git commit -m "chore: complete MVP implementation"
git tag v0.1.0
```

---

## Summary

| Task | Description | Estimated Steps |
|------|-------------|-----------------|
| 0 | Project setup | 6 |
| 1 | Dark theme | 4 |
| 2 | Config system | 3 |
| 3 | Downloader core | 3 |
| 4 | Queue system | 3 |
| 5 | Main window UI | 6 |
| 6 | Notifications | 7 |
| 7 | Settings dialog | 4 |
| 8 | Auto-update | 5 |
| 9 | PyInstaller build | 4 |

**Total: ~45 bite-sized steps**

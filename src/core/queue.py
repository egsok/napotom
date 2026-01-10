"""Download queue management with Qt signals."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from uuid import uuid4

from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool, pyqtSlot

from .downloader import Downloader, VideoInfo, DownloaderError
from utils.notifications import notification_manager


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

    def retry(self, item_id: str) -> None:
        """Retry failed download."""
        for item in self.items:
            if item.id == item_id and item.status == QueueItemStatus.FAILED:
                item.status = QueueItemStatus.PENDING
                item.progress = 0
                item.speed = 0.0
                item.error = None
                self.item_updated.emit(item)
                self._process_next()
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
                notification_manager.notify_complete(item.info.title if item.info else "Video")
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
                notification_manager.notify_error(item.info.title if item.info else "Video", error)
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

"""Widget for displaying a queue item."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

from core.queue import QueueItem, QueueItemStatus
from ui.styles import COLORS


class QueueItemWidget(QWidget):
    """Widget representing a single download item."""

    cancel_clicked = pyqtSignal(str)  # item_id
    retry_clicked = pyqtSignal(str)  # item_id

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

        self.retry_btn = QPushButton("↻")
        self.retry_btn.setObjectName("iconButton")
        self.retry_btn.setFixedSize(32, 32)
        self.retry_btn.setToolTip("Retry download")
        self.retry_btn.clicked.connect(lambda: self.retry_clicked.emit(self.item.id))
        self.retry_btn.setVisible(False)
        top_row.addWidget(self.retry_btn)

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

        # Reset buttons and styles
        self.retry_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")

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
            self.retry_btn.setVisible(True)
        elif item.status == QueueItemStatus.CANCELLED:
            self.status_label.setText("Cancelled")
            self.status_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.cancel_btn.setVisible(False)

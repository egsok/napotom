"""Widget for displaying a queue item as a numbered print on the kraft sheet."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from core.queue import QueueItem, QueueItemStatus
from ui.styles import COLORS
from ui.common import display_font, ink_offset, mono_font
from utils.helpers import open_folder
from utils.i18n import tr


class QueueItemWidget(QWidget):
    """A single download shown as a numbered print run on the sheet."""

    cancel_clicked = pyqtSignal(str)  # item_id
    retry_clicked = pyqtSignal(str)  # item_id

    def __init__(self, item: QueueItem, run_no: int = 0, parent=None):
        super().__init__(parent)
        self.item = item
        self.run_no = run_no
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._setup_ui()
        self.update_from_item(item)

    def _setup_ui(self):
        """Setup widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 10, 2, 12)
        layout.setSpacing(7)

        # Top row: run number, title, status, action buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.no_label = QLabel(f"{self.run_no:02d}")
        self.no_label.setFont(display_font(11, QFont.Weight.ExtraBold))
        self.no_label.setStyleSheet(f"color: {COLORS['violet']};")
        top_row.addWidget(self.no_label)

        self.title_label = QLabel("...")
        title_font = QFont("IBM Plex Sans")
        title_font.setPixelSize(13)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS['violet']};")
        self.title_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.title_label)

        self.status_label = QLabel("")
        self.status_label.setFont(mono_font(10, QFont.Weight.DemiBold, 1.4))
        top_row.addWidget(self.status_label)

        self.retry_btn = QPushButton()
        self.retry_btn.setObjectName("kraftActionMag")
        self.retry_btn.setFont(mono_font(9, QFont.Weight.DemiBold, 1.0))
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.setToolTip(tr("retry_tooltip"))
        self.retry_btn.clicked.connect(lambda: self.retry_clicked.emit(self.item.id))
        self.retry_btn.setVisible(False)
        top_row.addWidget(self.retry_btn)

        self.folder_btn = QPushButton()
        self.folder_btn.setObjectName("kraftAction")
        self.folder_btn.setFont(mono_font(9, QFont.Weight.DemiBold, 1.0))
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.setToolTip(tr("open_folder_tooltip"))
        self.folder_btn.clicked.connect(self._on_folder_clicked)
        self.folder_btn.setVisible(False)
        top_row.addWidget(self.folder_btn)

        self.cancel_btn = QPushButton("✕")
        self.cancel_btn.setObjectName("kraftCancel")
        self.cancel_btn.setFixedSize(22, 22)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.item.id))
        top_row.addWidget(self.cancel_btn)

        layout.addLayout(top_row)

        # Bottom row: progress bar and speed
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        bottom_row.addWidget(self.progress_bar, stretch=1)

        self.speed_label = QLabel("")
        self.speed_label.setFont(mono_font(9, QFont.Weight.Medium, 0.8))
        self.speed_label.setStyleSheet(f"color: {COLORS['accent']}; min-width: 90px;")
        self.speed_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        bottom_row.addWidget(self.speed_label)

        layout.addLayout(bottom_row)

        self._retranslate_buttons()

    def _retranslate_buttons(self):
        """Set localized uppercase captions on the mono action buttons."""
        self.retry_btn.setText("↻ " + tr("item_retry").upper())
        self.folder_btn.setText("▸ " + tr("item_folder").upper())

    def _set_stamp(self, on: bool):
        """Style the status label as the 'done' rubber stamp (violet + magenta dot)."""
        if on:
            self.status_label.setTextFormat(Qt.TextFormat.RichText)
            self.status_label.setText(
                f"{tr('status_done').upper()} <span style='color:{COLORS['accent']};'>·</span>"
            )
            self.status_label.setStyleSheet(
                f"color: {COLORS['violet']};"
                f"border: 2px solid {COLORS['violet']};"
                "border-radius: 2px; padding: 1px 7px;"
            )
        else:
            self.status_label.setTextFormat(Qt.TextFormat.PlainText)
            self.status_label.setStyleSheet(f"color: {COLORS['violet_ink']}; border: none;")

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
            self.title_label.setText(tr("getting_video_info"))

        # Progress
        self.progress_bar.setValue(item.progress)

        # Reset to base state
        self.retry_btn.setVisible(False)
        self.folder_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self._set_stamp(False)
        self.no_label.setStyleSheet(f"color: {COLORS['violet']};")
        self.no_label.setGraphicsEffect(None)

        # Status and speed
        if item.status == QueueItemStatus.PENDING:
            self.status_label.setText(tr("status_waiting").upper())
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
        elif item.status == QueueItemStatus.DOWNLOADING:
            # Active run: magenta number with violet misregistration
            self.no_label.setStyleSheet(f"color: {COLORS['accent']};")
            ink_offset(self.no_label, 1.2, 1.2, COLORS["violet_2"])
            self.status_label.setText(f"{item.progress}%")
            self.status_label.setStyleSheet(f"color: {COLORS['accent']}; border: none;")
            self.speed_label.setText(f"{item.speed:.1f} MB/S" if item.speed > 0 else "")
            self.progress_bar.setVisible(True)
        elif item.status == QueueItemStatus.PROCESSING:
            self.status_label.setText(tr("status_processing").upper())
            self.status_label.setStyleSheet(f"color: {COLORS['violet']}; border: none;")
            self.speed_label.setText("")
            self.progress_bar.setVisible(True)
        elif item.status == QueueItemStatus.COMPLETED:
            self._set_stamp(True)
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.folder_btn.setVisible(True)
            self.cancel_btn.setVisible(False)
        elif item.status == QueueItemStatus.FAILED:
            self.status_label.setText(tr("status_failed").upper())
            self.status_label.setStyleSheet(
                f"color: {COLORS['accent']}; border: none; font-weight: 600;"
            )
            self.speed_label.setText(item.error or "")
            self.speed_label.setStyleSheet(f"color: {COLORS['violet_ink']};")
            self.progress_bar.setVisible(False)
            self.retry_btn.setVisible(True)
        elif item.status == QueueItemStatus.CANCELLED:
            self.status_label.setText(tr("status_cancelled").upper())
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.cancel_btn.setVisible(False)

        if item.status == QueueItemStatus.DOWNLOADING:
            self.speed_label.setStyleSheet(f"color: {COLORS['accent']}; min-width: 90px;")

    def _on_folder_clicked(self):
        """Open folder containing the downloaded file."""
        open_folder(self.item.output_path)

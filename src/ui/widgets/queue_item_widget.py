"""Widget for displaying a queue item as a numbered print on the kraft sheet."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy
)
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QFontMetrics

from core.queue import QueueItem, QueueItemStatus
from ui.styles import (
    CANCEL_BTN, COLORS, FONT_BODY, FS_BODY, FS_DISPLAY, FS_META, FS_MONO,
)
from ui.common import TaktDots, display_font, folder_icon, ink_offset, mono_font
from utils.helpers import open_folder
from utils.i18n import tr


class QueueItemWidget(QWidget):
    """A single download shown as a numbered print run on the sheet."""

    cancel_clicked = pyqtSignal(str)  # item_id
    retry_clicked = pyqtSignal(str)  # item_id

    CANCEL_SIZE = CANCEL_BTN  # the actions column is reserved from this, not sizeHint

    def __init__(self, item: QueueItem, run_no: int = 0, parent=None):
        super().__init__(parent)
        self.item = item
        self.run_no = run_no
        self._title_text = ""
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._setup_ui()
        self.update_from_item(item)

    def _setup_ui(self):
        """Setup widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 11, 2, 13)
        layout.setSpacing(8)

        # Top row: run number, title, status, action buttons
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.no_label = QLabel(f"{self.run_no:02d}")
        self.no_label.setFont(display_font(FS_DISPLAY, QFont.Weight.ExtraBold))
        self.no_label.setStyleSheet(f"color: {COLORS['violet']};")
        top_row.addWidget(self.no_label)

        self.title_label = QLabel("...")
        title_font = QFont(FONT_BODY)
        title_font.setPixelSize(FS_BODY)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet(f"color: {COLORS['violet']};")
        # Ignored (not Expanding): the label takes the width the row can spare
        # instead of demanding the width of its text, which would push the
        # status and action buttons past the right edge of a narrow window
        self.title_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        top_row.addWidget(self.title_label, stretch=1)

        # Statuses print on a common right edge: a reserved column, so "ЖДЁТ"
        # and "37%" do not wander with the width of their own text.
        self.status_label = QLabel("")
        self.status_label.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.4))
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        top_row.addWidget(self.status_label)

        # ...and the buttons keep a column of their own, so the status edge is
        # not pushed around by which actions this state happens to offer.
        self.actions = QWidget()
        actions_row = QHBoxLayout(self.actions)
        actions_row.setContentsMargins(0, 0, 0, 0)
        actions_row.setSpacing(7)
        actions_row.addStretch()

        self.retry_btn = QPushButton()
        self.retry_btn.setObjectName("kraftActionMag")
        self.retry_btn.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.0))
        self.retry_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.retry_btn.setToolTip(tr("retry_tooltip"))
        self.retry_btn.clicked.connect(lambda: self.retry_clicked.emit(self.item.id))
        self.retry_btn.setVisible(False)
        actions_row.addWidget(self.retry_btn)

        self.folder_btn = QPushButton()
        self.folder_btn.setObjectName("kraftAction")
        self.folder_btn.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.0))
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.setIcon(folder_icon())
        self.folder_btn.setIconSize(QSize(15, 12))
        self.folder_btn.setToolTip(tr("open_folder_tooltip"))
        self.folder_btn.clicked.connect(self._on_folder_clicked)
        self.folder_btn.setVisible(False)
        actions_row.addWidget(self.folder_btn)

        # U+00D7, not U+2715: the bundled Plex faces have no heavy multiply
        # glyph, and the OS fallback prints a tofu box instead
        self.cancel_btn = QPushButton("×")
        self.cancel_btn.setObjectName("kraftCancel")
        # The glyph fills its box: a small multiply sign rattling around inside
        # a square frame reads as a rendering slip, not as a button.
        self.cancel_btn.setFont(mono_font(17, QFont.Weight.Bold, 0))
        self.cancel_btn.setFixedSize(self.CANCEL_SIZE, self.CANCEL_SIZE)
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(lambda: self.cancel_clicked.emit(self.item.id))
        actions_row.addWidget(self.cancel_btn)

        top_row.addWidget(self.actions)

        layout.addLayout(top_row)

        # Bottom row: progress bar (or the takt dots) and speed
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(6)
        bottom_row.addWidget(self.progress_bar, stretch=1)

        # While ffmpeg merges there is no percentage to tell the truth with:
        # the dots print in takts instead of parking the bar at the last value.
        self.takt_dots = TaktDots()
        self.takt_dots.setVisible(False)
        bottom_row.addWidget(self.takt_dots)

        self.speed_label = QLabel("")
        self.speed_label.setFont(mono_font(FS_MONO, QFont.Weight.Medium, 0.8))
        self.speed_label.setStyleSheet(f"color: {COLORS['mag_text']}; min-width: 96px;")
        self.speed_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        bottom_row.addWidget(self.speed_label)

        layout.addLayout(bottom_row)

        # Failure detail on its own line: prose, not a caption. Wraps to the
        # sheet width instead of stretching the card past the window edge
        error_font = QFont(FONT_BODY)
        error_font.setPixelSize(FS_META)
        self.error_label = QLabel("")
        self.error_label.setWordWrap(True)
        self.error_label.setFont(error_font)
        self.error_label.setStyleSheet(f"color: {COLORS['violet_ink']};")
        # Ignored width for the same reason as the title: a wrapping label still
        # demands the width of its longest word, which an error message with a
        # long unbroken token (a path, a token, a URL) would blow up
        self.error_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum)
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        self._retranslate_buttons()

    def _set_title(self, text: str):
        """Store the full title and show it elided to the label's actual width."""
        self._title_text = text
        self.title_label.setToolTip(text)
        self._apply_title_elide()

    def _apply_title_elide(self):
        """Re-elide the stored title for the current label width."""
        metrics = QFontMetrics(self.title_label.font())
        width = max(self.title_label.width(), 40)
        self.title_label.setText(
            metrics.elidedText(self._title_text, Qt.TextElideMode.ElideRight, width)
        )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_title_elide()
        self._fit_error_height()

    def _fit_error_height(self):
        """Reserve the height the wrapped error text needs at the current width.

        The label's width policy is Ignored, so the layout no longer asks it how
        tall it wants to be — we have to tell it.
        """
        if not self.error_label.isVisible():
            return
        self.error_label.setMinimumHeight(
            self.error_label.heightForWidth(self.error_label.width())
        )

    def _retranslate_buttons(self):
        """Set localized uppercase captions on the mono action buttons."""
        self.retry_btn.setText("↻ " + tr("item_retry").upper())
        self.folder_btn.setText(tr("item_folder").upper())
        self._measure_columns()

    def _measure_columns(self):
        """Reserve the status and action columns for the widest state.

        Measured per language: a caption longer than the reserved width would
        push its own row's status out of the column and break the alignment.
        """
        metrics = QFontMetrics(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.4))
        status = max(metrics.horizontalAdvance(tr(key).upper()) for key in (
            "status_waiting", "status_processing", "status_failed", "status_cancelled",
        ))
        # the stamp carries a 2px rule box and 8px side padding on top of its text
        stamp = QFontMetrics(display_font(FS_MONO, QFont.Weight.Bold)).horizontalAdvance(
            tr("status_done").upper() + " ·") + 22
        self.status_label.setMinimumWidth(max(status, stamp))

        # Reserve from the cancel button's REAL size, not its sizeHint: the QSS
        # zeroes its padding and min-width, so the hint came out at 11px and the
        # layout squeezed the 28px square into a sliver of a frame.
        buttons = max(self.retry_btn.sizeHint().width(), self.folder_btn.sizeHint().width())
        self.actions.setFixedWidth(buttons + 7 + self.CANCEL_SIZE)

    def _set_stamp(self, on: bool):
        """Style the status label as the 'done' rubber stamp (violet + magenta dot)."""
        if on:
            self.status_label.setFont(display_font(FS_MONO, QFont.Weight.Bold))
            self.status_label.setTextFormat(Qt.TextFormat.RichText)
            # the rule box spans the reserved column, so the type centres in it
            self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.status_label.setText(
                f"{tr('status_done').upper()} <span style='color:{COLORS['accent']};'>·</span>"
            )
            self.status_label.setStyleSheet(
                f"color: {COLORS['violet']};"
                f"border: 2px solid {COLORS['violet']};"
                "border-radius: 2px; padding: 2px 8px;"
            )
        else:
            self.status_label.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.4))
            self.status_label.setTextFormat(Qt.TextFormat.PlainText)
            self.status_label.setAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.status_label.setStyleSheet(f"color: {COLORS['violet_ink']}; border: none;")

    def update_from_item(self, item: QueueItem):
        """Update widget from item data."""
        self.item = item

        # Title
        self._set_title(item.info.title if item.info else tr("getting_video_info"))

        # Progress
        self.progress_bar.setValue(item.progress)

        # Reset to base state
        self.retry_btn.setVisible(False)
        self.folder_btn.setVisible(False)
        self.cancel_btn.setVisible(True)
        self.error_label.setVisible(False)
        self.takt_dots.setVisible(False)
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
            ink_offset(self.no_label, 1, 1, COLORS["violet_2"])
            self.status_label.setText(f"{item.progress}%")
            self.status_label.setStyleSheet(f"color: {COLORS['mag_text']}; border: none;")
            self.speed_label.setText(f"{item.speed:.1f} MB/S" if item.speed > 0 else "")
            self.progress_bar.setVisible(True)
        elif item.status == QueueItemStatus.PROCESSING:
            self.status_label.setText(tr("status_processing").upper())
            self.status_label.setStyleSheet(f"color: {COLORS['violet']}; border: none;")
            self.speed_label.setText("")
            # No percentage exists here — hide the bar, print takts instead
            self.progress_bar.setVisible(False)
            self.takt_dots.setVisible(True)
        elif item.status == QueueItemStatus.COMPLETED:
            self._set_stamp(True)
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.folder_btn.setVisible(True)
            self.cancel_btn.setVisible(False)
        elif item.status == QueueItemStatus.FAILED:
            self.status_label.setText(tr("status_failed").upper())
            self.status_label.setStyleSheet(
                f"color: {COLORS['mag_text']}; border: none; font-weight: 600;"
            )
            self.speed_label.setText("")
            self.error_label.setText(item.error or "")
            self.error_label.setToolTip(item.error or "")
            self.error_label.setVisible(bool(item.error))
            self._fit_error_height()
            self.progress_bar.setVisible(False)
            self.retry_btn.setVisible(True)
        elif item.status == QueueItemStatus.CANCELLED:
            self.status_label.setText(tr("status_cancelled").upper())
            self.speed_label.setText("")
            self.progress_bar.setVisible(False)
            self.cancel_btn.setVisible(False)

    def _on_folder_clicked(self):
        """Open folder containing the downloaded file."""
        open_folder(self.item.output_path)

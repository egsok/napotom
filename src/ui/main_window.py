"""Main application window: one sheet of kraft paper, two inks."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel,
    QScrollArea, QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import QEvent, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont, QFontMetrics

from core.queue import DownloadQueue, QueueItem, QueueItemStatus
from ui.widgets.queue_item_widget import QueueItemWidget
from ui.styles import COLORS, FS_BODY, FS_DISPLAY, FS_META, FS_MONO
from ui.common import (
    InkComboBox, KraftSheet, RegMark, apply_brand_titlebar, apply_optical_center,
    display_font, ink_offset, mono_font, populate_quality_combo,
)
from utils.config import config_manager
from utils.helpers import open_folder
from utils.i18n import tr


# Statuses a "clear done" sweep is allowed to take off the sheet.
_DONE_STATUSES = (QueueItemStatus.COMPLETED, QueueItemStatus.CANCELLED)


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(650, 500)
        # The 650x500 minimum dates back to the first UI commit and still works,
        # but opening AT the minimum left no width for the download path. Start
        # at a size where the whole path and a few queue rows are readable.
        self.resize(900, 700)

        self.queue = DownloadQueue()
        self.item_widgets: dict[str, QueueItemWidget] = {}
        self._run_no = 0  # sequential print-run number for queue items
        self._folder_path = config_manager.get('download_path')

        self._setup_ui()
        self._connect_signals()
        apply_brand_titlebar(self)

    # --- construction -----------------------------------------------------
    def _setup_ui(self):
        """Setup main window UI."""
        # The window IS the sheet: kraft + fixed-seed grain behind everything.
        central = KraftSheet()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(22, 20, 22, 14)
        layout.setSpacing(14)

        layout.addLayout(self._build_url_row())
        layout.addLayout(self._build_options_row())
        layout.addLayout(self._build_queue_header())
        layout.addWidget(self._build_queue_scroll(), stretch=1)

        queue_foot = QFrame()
        queue_foot.setObjectName("ruleSoft")
        queue_foot.setFixedHeight(1)
        layout.addWidget(queue_foot)

        layout.addLayout(self._build_actions_row())
        layout.addWidget(self._build_colophon())

    def _build_url_row(self) -> QHBoxLayout:
        """The primary action: paste a link, print it."""
        row = QHBoxLayout()
        row.setSpacing(10)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(tr("url_placeholder"))
        self.url_input.returnPressed.connect(self._on_add_clicked)
        row.addWidget(self.url_input, stretch=1)

        # The screen's primary action carries a word, not a bare glyph: a fixed
        # 44x44 square could not hold "+ ДОБАВИТЬ" in either language.
        self.add_btn = QPushButton(self._add_caption())
        self.add_btn.setFont(mono_font(FS_MONO))
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._on_add_clicked)
        row.addWidget(self.add_btn)

        return row

    def _build_options_row(self) -> QHBoxLayout:
        """Quality on the left, destination path taking all the room it can."""
        row = QHBoxLayout()
        row.setSpacing(9)

        self.quality_label = QLabel(tr("quality_label").rstrip(':').upper())
        self.quality_label.setFont(mono_font(FS_MONO))
        self.quality_label.setStyleSheet(f"color: {COLORS['violet_ink']};")
        row.addWidget(self.quality_label)

        self.quality_combo = InkComboBox()
        populate_quality_combo(self.quality_combo, config_manager.get('default_quality', 'best'))
        row.addWidget(self.quality_combo)

        row.addSpacing(14)

        self.save_to_label = QLabel(tr("save_to_label").rstrip(':').upper())
        self.save_to_label.setFont(mono_font(FS_MONO))
        self.save_to_label.setStyleSheet(f"color: {COLORS['violet_ink']};")
        row.addWidget(self.save_to_label)

        self.folder_label = QLabel("")
        self.folder_label.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 0.4))
        self.folder_label.setStyleSheet(f"color: {COLORS['prose']};")
        # Ignored width for the same reason as the queue title: the label takes
        # the width the row can spare and elides, instead of demanding the width
        # of a long path and pushing the CHANGE button off the sheet.
        self.folder_label.setSizePolicy(QSizePolicy.Policy.Ignored,
                                        QSizePolicy.Policy.Preferred)
        # Re-elide from the label's OWN resize, not the window's: the window
        # event fires a layout pass early, so the path would be elided against
        # a stale width and then clipped without an ellipsis.
        self.folder_label.installEventFilter(self)
        row.addWidget(self.folder_label, stretch=1)

        self.folder_btn = QPushButton(tr("change_btn").upper())
        self.folder_btn.setObjectName("secondaryButton")
        self.folder_btn.setFont(mono_font(FS_MONO))
        self.folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.folder_btn.clicked.connect(self._on_folder_clicked)
        row.addWidget(self.folder_btn)

        self._set_folder_path(self._folder_path)
        return row

    def _build_queue_header(self) -> QHBoxLayout:
        """Registration mark, title, run count, rule — then the bulk action."""
        row = QHBoxLayout()
        row.setSpacing(8)
        row.addWidget(RegMark(13))

        self.queue_label = QLabel(tr("queue_title").upper())
        self.queue_label.setObjectName("sectionTitle")
        self.queue_label.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 2.2))
        row.addWidget(self.queue_label)

        self.queue_count_label = QLabel("")
        self.queue_count_label.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 2.2))
        self.queue_count_label.setStyleSheet(f"color: {COLORS['mag_text']};")
        row.addWidget(self.queue_count_label)

        rule = QFrame()
        rule.setObjectName("rule")
        rule.setFixedHeight(1)
        row.addWidget(rule, stretch=1)

        self.clear_done_btn = QPushButton(tr("clear_done_btn").upper())
        self.clear_done_btn.setObjectName("linkButton")
        self.clear_done_btn.setFont(mono_font(FS_MONO, QFont.Weight.Medium, 0.8))
        self.clear_done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_done_btn.clicked.connect(self._on_clear_done_clicked)
        self.clear_done_btn.setVisible(False)
        row.addWidget(self.clear_done_btn)

        return row

    def _build_queue_scroll(self) -> QScrollArea:
        """The list prints straight onto the page — no island, no second fill."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # The viewport and the scrolled widget must BOTH be transparent, or the
        # list prints on a paler rectangle — the island this repaint removes.
        scroll.setStyleSheet(
            "QScrollArea { border: none; background: transparent; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )
        scroll.viewport().setAutoFillBackground(False)

        self.queue_container = QWidget()
        self.queue_container.setAutoFillBackground(False)
        self.queue_layout = QVBoxLayout(self.queue_container)
        self.queue_layout.setContentsMargins(2, 8, 8, 10)
        self.queue_layout.setSpacing(0)
        self.queue_layout.addStretch()

        self.queue_layout.insertWidget(0, self._build_empty_state())

        scroll.setWidget(self.queue_container)
        return scroll

    def _build_empty_state(self) -> QWidget:
        """A blank sheet, not a rendering gap: reg mark over one line of prose."""
        self.empty_state = QWidget()
        box = QVBoxLayout(self.empty_state)
        box.setContentsMargins(20, 48, 20, 48)
        box.setSpacing(14)

        mark = RegMark(17)
        box.addWidget(mark, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.empty_label = QLabel(tr("empty_queue"))
        self.empty_label.setWordWrap(True)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(
            f"color: {COLORS['prose']}; font-size: {FS_BODY}px;"
        )
        box.addWidget(self.empty_label)

        return self.empty_state

    def _build_actions_row(self) -> QHBoxLayout:
        """Secondary actions keep their own right-aligned row above the rule."""
        row = QHBoxLayout()
        row.setSpacing(9)
        row.addStretch()

        self.open_folder_btn = QPushButton(tr("open_folder_btn").upper())
        self.open_folder_btn.setObjectName("secondaryButton")
        self.open_folder_btn.setFont(mono_font(FS_MONO))
        self.open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_folder_btn.clicked.connect(self._on_open_folder_clicked)
        row.addWidget(self.open_folder_btn)

        self.settings_btn = QPushButton(tr("settings_btn").upper())
        self.settings_btn.setObjectName("secondaryButton")
        self.settings_btn.setFont(mono_font(FS_MONO))
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        row.addWidget(self.settings_btn)

        return row

    def _build_colophon(self) -> QWidget:
        """Colophon: hairline, then ONE row — mark + credits left, chip right."""
        foot = QWidget()
        box = QVBoxLayout(foot)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(10)

        rule = QFrame()
        rule.setObjectName("rule")
        rule.setFixedHeight(1)
        box.addWidget(rule)

        row = QHBoxLayout()
        row.setSpacing(0)

        # "ннв" has no ascenders or descenders, so its em box centres it low:
        # lift both the word and the registration dot by their measured ink box.
        # The mark is a stamp, not a caption: it carries the sheet's signature
        # and has to read as one at a glance, so it prints above body size.
        self.stamp_glyph = QLabel("ннв")
        glyph_font = display_font(19, QFont.Weight.Black)
        glyph_font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, -1.5)
        self.stamp_glyph.setFont(glyph_font)
        self.stamp_glyph.setStyleSheet(f"color: {COLORS['violet']};")
        ink_offset(self.stamp_glyph, 1, 1)
        apply_optical_center(self.stamp_glyph)
        row.addWidget(self.stamp_glyph)

        self.stamp_dot = QLabel("·")
        self.stamp_dot.setFont(display_font(19, QFont.Weight.Black))
        self.stamp_dot.setStyleSheet(f"color: {COLORS['accent']};")
        apply_optical_center(self.stamp_dot)
        row.addWidget(self.stamp_dot)

        row.addSpacing(12)

        self.credits_label = QLabel(tr("credits_text"))
        self.credits_label.setStyleSheet(
            f"color: {COLORS['violet_ink']}; font-size: {FS_META}px;"
        )
        row.addWidget(self.credits_label)

        row.addStretch()

        self.subscribe_btn = QPushButton(tr("credits_subscribe"))
        self.subscribe_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.subscribe_btn.setFont(mono_font(FS_MONO, QFont.Weight.Medium, 0.4))
        self.subscribe_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid rgba(225, 27, 118, 50%);
                border-radius: 3px;
                color: {COLORS['mag_text']};
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent']};
                border-color: {COLORS['accent']};
                color: {COLORS['on_ink']};
            }}
        """)
        self.subscribe_btn.clicked.connect(self._on_subscribe_clicked)
        row.addWidget(self.subscribe_btn)

        box.addLayout(row)
        return foot

    def _connect_signals(self):
        """Connect queue signals."""
        self.queue.item_added.connect(self._on_item_added)
        self.queue.item_updated.connect(self._on_item_updated)
        self.queue.item_removed.connect(self._on_item_removed)
        self.settings_btn.clicked.connect(self._on_settings_clicked)

    # --- path display -----------------------------------------------------
    def _set_folder_path(self, path: str) -> None:
        """Store the full download path and show it elided to the real width."""
        self._folder_path = path or ""
        self.folder_label.setToolTip(self._folder_path)
        self._apply_path_elide()

    def _apply_path_elide(self) -> None:
        """Elide in the MIDDLE: the drive and the last folder stay readable."""
        metrics = QFontMetrics(self.folder_label.font())
        width = max(self.folder_label.width(), 90)
        self.folder_label.setText(
            metrics.elidedText(self._folder_path, Qt.TextElideMode.ElideMiddle, width)
        )

    def eventFilter(self, obj, event):
        if obj is self.folder_label and event.type() == QEvent.Type.Resize:
            self._apply_path_elide()
        return super().eventFilter(obj, event)

    # --- actions ----------------------------------------------------------
    @staticmethod
    def _add_caption() -> str:
        return "+ " + tr("add_btn").upper()

    def _on_add_clicked(self):
        """Handle add button click."""
        url = self.url_input.text().strip()
        if not url:
            return

        # Validate URL (basic check)
        if not url.startswith(('http://', 'https://')):
            QMessageBox.warning(self, tr("invalid_url_title"), tr("invalid_url_message"))
            return

        quality = self.quality_combo.currentData()
        output_path = config_manager.get('download_path')

        self.queue.add(url, quality, output_path)
        self.url_input.clear()
        self.empty_state.hide()

    def _on_folder_clicked(self):
        """Handle folder button click."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("select_download_folder"),
            config_manager.get('download_path')
        )
        if folder:
            config_manager.set('download_path', folder)
            self._set_folder_path(folder)

    def _on_clear_done_clicked(self):
        """Sweep every finished print off the sheet (queue + widget map)."""
        for item_id in [item.id for item in self.queue.items
                        if item.status in _DONE_STATUSES]:
            self.queue.remove(item_id)  # emits item_removed -> drops the widget

    def _on_item_added(self, item: QueueItem):
        """Handle new item added to queue."""
        self._run_no += 1
        widget = QueueItemWidget(item, run_no=self._run_no)
        widget.cancel_clicked.connect(self._on_cancel_clicked)
        widget.retry_clicked.connect(self._on_retry_clicked)

        # Insert before the stretch
        self.queue_layout.insertWidget(self.queue_layout.count() - 1, widget)
        self.item_widgets[item.id] = widget
        self.empty_state.hide()  # here, not at the click: every path adds items
        self._update_queue_count()

    def _on_item_updated(self, item: QueueItem):
        """Handle item update."""
        if item.id in self.item_widgets:
            self.item_widgets[item.id].update_from_item(item)
        self._update_clear_done()

    def _on_item_removed(self, item_id: str):
        """Handle item removal."""
        if item_id in self.item_widgets:
            widget = self.item_widgets.pop(item_id)
            widget.setParent(None)
            widget.deleteLater()

        if not self.item_widgets:
            self.empty_state.show()
        self._update_queue_count()

    def _update_queue_count(self):
        """Refresh the run counter next to the queue title."""
        count = len(self.item_widgets)
        self.queue_count_label.setText(f"— {count:02d}" if count else "")
        self._update_clear_done()

    def _update_clear_done(self):
        """The bulk action only exists while there is something to clear."""
        done = any(item.status in _DONE_STATUSES for item in self.queue.items)
        self.clear_done_btn.setVisible(done)

    def _on_cancel_clicked(self, item_id: str):
        """Handle cancel button click."""
        self.queue.cancel(item_id)

    def _on_retry_clicked(self, item_id: str):
        """Handle retry button click."""
        self.queue.retry(item_id)

    def _on_subscribe_clicked(self):
        """Open Telegram channel link."""
        QDesktopServices.openUrl(QUrl(tr("credits_url")))

    def _on_settings_clicked(self):
        """Handle settings button click."""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload settings
            self._set_folder_path(config_manager.get('download_path'))

            # Update quality combo from config
            quality_key = config_manager.get('default_quality', 'best')
            for i in range(self.quality_combo.count()):
                if self.quality_combo.itemData(i) == quality_key:
                    self.quality_combo.setCurrentIndex(i)
                    break

            # Update queue parallel limit
            self.queue._update_max_parallel()

            # Update UI text for new language
            self._retranslate_ui()

    def _retranslate_ui(self):
        """Update all UI text to current language (hot reload)."""
        self.setWindowTitle(tr("app_title"))
        self.url_input.setPlaceholderText(tr("url_placeholder"))
        self.add_btn.setText(self._add_caption())
        self.quality_label.setText(tr("quality_label").rstrip(':').upper())
        self.save_to_label.setText(tr("save_to_label").rstrip(':').upper())
        self.folder_btn.setText(tr("change_btn").upper())
        self.queue_label.setText(tr("queue_title").upper())
        self.clear_done_btn.setText(tr("clear_done_btn").upper())
        self.empty_label.setText(tr("empty_queue"))
        self.open_folder_btn.setText(tr("open_folder_btn").upper())
        self.settings_btn.setText(tr("settings_btn").upper())

        self.credits_label.setText(tr("credits_text"))
        self.subscribe_btn.setText(tr("credits_subscribe"))

        self._apply_path_elide()

        for widget in self.item_widgets.values():
            widget._retranslate_buttons()

        # Update quality combo (preserve selection)
        populate_quality_combo(self.quality_combo, self.quality_combo.currentData())

    def _on_open_folder_clicked(self):
        """Handle open folder button click."""
        open_folder(config_manager.get('download_path'))

    def closeEvent(self, event):
        """Confirm exit while downloads are active; cancel them on confirm."""
        if self.queue.has_active_downloads():
            reply = QMessageBox.question(
                self,
                tr("exit_confirm_title"),
                tr("exit_confirm_message"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
            self.queue.cancel_all()
            self.queue.thread_pool.waitForDone(5000)
        event.accept()

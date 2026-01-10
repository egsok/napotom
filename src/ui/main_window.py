"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QComboBox, QLabel,
    QScrollArea, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt

from core.queue import DownloadQueue, QueueItem
from ui.widgets.queue_item_widget import QueueItemWidget
from ui.styles import COLORS
from utils.config import config_manager


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
        self.settings_btn.clicked.connect(self._on_settings_clicked)

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
        widget.retry_clicked.connect(self._on_retry_clicked)

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

    def _on_retry_clicked(self, item_id: str):
        """Handle retry button click."""
        self.queue.retry(item_id)

    def _on_settings_clicked(self):
        """Handle settings button click."""
        from ui.settings_dialog import SettingsDialog
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload settings
            self.folder_label.setText(self._shorten_path(config_manager.get('download_path')))
            self.quality_combo.setCurrentText(self._get_quality_display(
                config_manager.get('default_quality', 'best')
            ))

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

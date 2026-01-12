"""Settings dialog window."""

import subprocess
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QLabel,
    QFileDialog, QGroupBox, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt

from ui.styles import COLORS
from utils.config import config_manager
from core.updater import Updater


class SettingsDialog(QDialog):
    """Settings dialog for application configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(450)
        self.setModal(True)

        # Initialize updater
        self._updater = Updater()
        self._updater.update_available.connect(self._on_update_available)
        self._updater.already_up_to_date.connect(self._on_already_up_to_date)
        self._updater.check_failed.connect(self._on_check_failed)
        self._updater.update_result.connect(self._on_update_result)

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Download section
        download_group = QGroupBox("Download Settings")
        download_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {COLORS['text_primary']};
            }}
        """)
        download_layout = QFormLayout(download_group)
        download_layout.setSpacing(12)
        download_layout.setContentsMargins(16, 20, 16, 16)

        # Download path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        self.browse_btn.clicked.connect(self._browse_folder)
        path_layout.addWidget(self.browse_btn)

        download_layout.addRow("Download Path:", path_layout)

        # Default quality
        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["Best", "1080p", "720p", "Audio only"])
        download_layout.addRow("Default Quality:", self.quality_combo)

        # Parallel downloads
        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 5)
        self.parallel_spin.setValue(2)
        self.parallel_spin.setToolTip("Number of videos to download simultaneously")
        download_layout.addRow("Parallel Downloads:", self.parallel_spin)

        layout.addWidget(download_group)

        # Preferences section
        prefs_group = QGroupBox("Preferences")
        prefs_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {COLORS['text_primary']};
            }}
        """)
        prefs_layout = QVBoxLayout(prefs_group)
        prefs_layout.setSpacing(12)
        prefs_layout.setContentsMargins(16, 20, 16, 16)

        self.notifications_check = QCheckBox("Enable notifications")
        prefs_layout.addWidget(self.notifications_check)

        self.sound_check = QCheckBox("Enable sound")
        prefs_layout.addWidget(self.sound_check)

        self.updates_check = QCheckBox("Check for updates on startup")
        prefs_layout.addWidget(self.updates_check)

        layout.addWidget(prefs_group)

        # yt-dlp section
        ytdlp_group = QGroupBox("yt-dlp")
        ytdlp_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {COLORS['text_primary']};
            }}
        """)
        ytdlp_layout = QHBoxLayout(ytdlp_group)
        ytdlp_layout.setContentsMargins(16, 20, 16, 16)

        version_label = QLabel("Version:")
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        ytdlp_layout.addWidget(version_label)

        self.version_label = QLabel(self._get_ytdlp_version())
        self.version_label.setStyleSheet("font-weight: bold;")
        ytdlp_layout.addWidget(self.version_label)

        ytdlp_layout.addStretch()

        self.check_updates_btn = QPushButton("Check Now")
        self.check_updates_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        self.check_updates_btn.clicked.connect(self._check_updates)
        ytdlp_layout.addWidget(self.check_updates_btn)

        layout.addWidget(ytdlp_group)

        # Spacer
        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 10px 24px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load current settings into UI."""
        self.path_input.setText(config_manager.get('download_path'))
        self.quality_combo.setCurrentText(
            self._get_quality_display(config_manager.get('default_quality', 'best'))
        )
        self.parallel_spin.setValue(config_manager.get('max_parallel_downloads', 2))
        self.notifications_check.setChecked(config_manager.get('notifications_enabled', True))
        self.sound_check.setChecked(config_manager.get('sound_enabled', True))
        self.updates_check.setChecked(config_manager.get('check_updates', True))

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)

    def _save_and_close(self):
        """Save settings and close dialog."""
        config_manager.set('download_path', self.path_input.text())
        config_manager.set('default_quality', self._get_quality_key(self.quality_combo.currentText()))
        config_manager.set('max_parallel_downloads', self.parallel_spin.value())
        config_manager.set('notifications_enabled', self.notifications_check.isChecked())
        config_manager.set('sound_enabled', self.sound_check.isChecked())
        config_manager.set('check_updates', self.updates_check.isChecked())
        self.accept()

    def _get_ytdlp_version(self) -> str:
        """Get installed yt-dlp version."""
        try:
            import yt_dlp
            return yt_dlp.version.__version__
        except (ImportError, AttributeError):
            pass
        return "Not installed"

    def _check_updates(self):
        """Check for yt-dlp updates."""
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText("Checking...")
        self._updater.check_for_updates()

    def _on_update_available(self, current: str, latest: str):
        """Handle update available signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("Check Now")

        reply = QMessageBox.question(
            self,
            "Update Available",
            f"yt-dlp {latest} is available (current: {current}).\n\nUpdate now?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.check_updates_btn.setEnabled(False)
            self.check_updates_btn.setText("Updating...")
            self._updater.install_update()

    def _on_already_up_to_date(self, version: str):
        """Handle already up to date signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("Check Now")
        QMessageBox.information(
            self,
            "Up to Date",
            f"yt-dlp {version} is the latest version."
        )

    def _on_check_failed(self, error: str):
        """Handle check failed signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("Check Now")
        QMessageBox.warning(
            self,
            "Update Check Failed",
            f"Could not check for updates:\n{error}"
        )

    def _on_update_result(self, success: bool, message: str):
        """Handle update result signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText("Check Now")

        if success:
            QMessageBox.information(self, "Update Complete", message)
            # Refresh the version display
            self.version_label.setText(self._get_ytdlp_version())
        else:
            QMessageBox.warning(self, "Update Failed", message)

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

"""Settings dialog window."""

import subprocess
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QLabel,
    QFileDialog, QGroupBox
)
from PyQt6.QtCore import Qt

from ui.styles import COLORS
from utils.config import config_manager


class SettingsDialog(QDialog):
    """Settings dialog for application configuration."""

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
        config_manager.set('notifications_enabled', self.notifications_check.isChecked())
        config_manager.set('sound_enabled', self.sound_check.isChecked())
        config_manager.set('check_updates', self.updates_check.isChecked())
        self.accept()

    def _get_ytdlp_version(self) -> str:
        """Get installed yt-dlp version."""
        try:
            result = subprocess.run(
                ['yt-dlp', '--version'],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            pass
        return "Not installed"

    def _check_updates(self):
        """Placeholder for checking yt-dlp updates."""
        # TODO: Implement yt-dlp update check
        pass

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

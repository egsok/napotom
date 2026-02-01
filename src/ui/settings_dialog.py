"""Settings dialog window."""

import os
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
from utils.logger import get_log_file_path
from core.updater import Updater
from yt_dlp.cookies import extract_cookies_from_browser


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

        # Cookies section (FEAT-01)
        cookie_group = QGroupBox("Cookies (for age-restricted videos)")
        cookie_group.setStyleSheet(f"""
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
        cookie_layout = QVBoxLayout(cookie_group)
        cookie_layout.setContentsMargins(16, 20, 16, 16)
        cookie_layout.setSpacing(12)

        # Description
        cookie_desc = QLabel("Required for age-restricted or members-only videos. Use cookies.txt file (recommended) or browser import.")
        cookie_desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        cookie_desc.setWordWrap(True)
        cookie_layout.addWidget(cookie_desc)

        # Cookies.txt file row (recommended)
        file_row = QHBoxLayout()
        
        file_label = QLabel("Cookies file:")
        file_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        file_row.addWidget(file_label)

        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setReadOnly(True)
        self.cookie_file_input.setPlaceholderText("No file selected")
        file_row.addWidget(self.cookie_file_input, 1)

        self.browse_cookies_btn = QPushButton("Browse...")
        self.browse_cookies_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        self.browse_cookies_btn.clicked.connect(self._browse_cookie_file)
        file_row.addWidget(self.browse_cookies_btn)

        self.clear_cookies_btn = QPushButton("Clear")
        self.clear_cookies_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['error']};
            }}
        """)
        self.clear_cookies_btn.clicked.connect(self._clear_cookie_file)
        file_row.addWidget(self.clear_cookies_btn)

        cookie_layout.addLayout(file_row)

        # Help link for cookies.txt
        self.help_cookies_btn = QPushButton("How to export cookies?")
        self.help_cookies_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {COLORS['accent_purple']};
                text-decoration: underline;
                padding: 0;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {COLORS['accent_magenta']};
            }}
        """)
        self.help_cookies_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_cookies_btn.clicked.connect(self._show_cookie_help)
        cookie_layout.addWidget(self.help_cookies_btn)

        # Separator
        separator = QLabel("— or use browser import (may not work on Windows) —")
        separator.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cookie_layout.addWidget(separator)

        # Browser selection row (fallback)
        browser_row = QHBoxLayout()
        
        browser_label = QLabel("Browser:")
        browser_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        browser_row.addWidget(browser_label)

        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["None", "Chrome", "Edge", "Firefox", "Brave", "Opera"])
        self.browser_combo.setMinimumWidth(120)
        browser_row.addWidget(self.browser_combo)

        browser_row.addStretch()

        self.test_cookies_btn = QPushButton("Test Import")
        self.test_cookies_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        self.test_cookies_btn.clicked.connect(self._test_cookie_import)
        browser_row.addWidget(self.test_cookies_btn)

        cookie_layout.addLayout(browser_row)

        # Status label for feedback
        self.cookie_status = QLabel("")
        self.cookie_status.setWordWrap(True)
        cookie_layout.addWidget(self.cookie_status)

        layout.addWidget(cookie_group)

        # Logging section
        log_group = QGroupBox("Logging")
        log_group.setStyleSheet(f"""
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
        log_layout = QHBoxLayout(log_group)
        log_layout.setContentsMargins(16, 20, 16, 16)

        log_path_label = QLabel("Log file:")
        log_path_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        log_layout.addWidget(log_path_label)

        log_file = get_log_file_path()
        self.log_path_value = QLabel(str(log_file) if log_file else "Not configured")
        self.log_path_value.setStyleSheet("font-size: 11px;")
        self.log_path_value.setWordWrap(True)
        log_layout.addWidget(self.log_path_value, 1)  # stretch factor 1

        self.open_log_folder_btn = QPushButton("Open Folder")
        self.open_log_folder_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 8px 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        self.open_log_folder_btn.clicked.connect(self._open_log_folder)
        log_layout.addWidget(self.open_log_folder_btn)

        layout.addWidget(log_group)

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
        
        # Load cookie settings
        cookie_file = config_manager.get('cookie_file_path', '')
        self.cookie_file_input.setText(cookie_file)
        
        cookie_browser = config_manager.get('cookie_browser', '')
        browser_display = cookie_browser.title() if cookie_browser else "None"
        self.browser_combo.setCurrentText(browser_display)

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)

    def _open_log_folder(self):
        """Open the log file folder in file explorer."""
        log_file = get_log_file_path()
        if log_file and log_file.parent.exists():
            # Windows: use os.startfile to open folder
            os.startfile(str(log_file.parent))

    def _save_and_close(self):
        """Save settings and close dialog."""
        config_manager.set('download_path', self.path_input.text())
        config_manager.set('default_quality', self._get_quality_key(self.quality_combo.currentText()))
        config_manager.set('max_parallel_downloads', self.parallel_spin.value())
        config_manager.set('notifications_enabled', self.notifications_check.isChecked())
        config_manager.set('sound_enabled', self.sound_check.isChecked())
        config_manager.set('check_updates', self.updates_check.isChecked())
        
        # Save cookie settings
        config_manager.set('cookie_file_path', self.cookie_file_input.text())
        
        browser_text = self.browser_combo.currentText()
        cookie_browser = browser_text.lower() if browser_text != "None" else ""
        config_manager.set('cookie_browser', cookie_browser)
        
        self.accept()

    def _get_ytdlp_version(self) -> str:
        """Get installed yt-dlp version with fallback strategies."""
        # Strategy 1: Direct attribute access (fastest, works in most cases)
        try:
            import yt_dlp
            version = getattr(yt_dlp, 'version', None)
            if version:
                v = getattr(version, '__version__', None)
                if v:
                    return v
        except Exception:
            pass

        # Strategy 2: Direct module import (handles some bundled app edge cases)
        try:
            from yt_dlp import version
            return version.__version__
        except Exception:
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

    def _show_cookie_help(self):
        """Show cookie export instructions dialog."""
        import webbrowser
        
        dialog = QDialog(self)
        dialog.setWindowTitle("How to Export Cookies")
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel("Export Cookies from Chrome")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Steps
        steps_text = """
<b>Step 1:</b> Install the browser extension<br><br>

<b>Step 2:</b> Go to <b>youtube.com</b> and make sure you're logged in<br><br>

<b>Step 3:</b> Click the extension icon and select <b>"Export"</b> or <b>"Current Site"</b><br><br>

<b>Step 4:</b> Save the file (e.g., <code>cookies.txt</code>)<br><br>

<b>Step 5:</b> In this app, click <b>"Browse..."</b> and select the saved file
        """
        steps = QLabel(steps_text)
        steps.setWordWrap(True)
        steps.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.5;")
        layout.addWidget(steps)
        
        # Extension link button
        ext_btn = QPushButton("Open Extension Page (Chrome Web Store)")
        ext_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_purple']};
                border: none;
                padding: 12px 24px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_magenta']};
            }}
        """)
        ext_btn.clicked.connect(lambda: webbrowser.open(
            "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
        ))
        layout.addWidget(ext_btn)
        
        # Note for other browsers
        note = QLabel("For Firefox: Use 'cookies.txt' extension from Firefox Add-ons")
        note.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(note)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                padding: 10px 24px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_purple']};
            }}
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        dialog.exec()

    def _browse_cookie_file(self):
        """Open file browser to select cookies.txt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Cookies File",
            "",
            "Cookie files (*.txt);;All files (*.*)"
        )
        if file_path:
            # Validate it looks like a Netscape cookie file
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = f.read(500)
                    # Netscape cookie files start with this comment or have tab-separated values
                    if '# Netscape HTTP Cookie File' in first_lines or '\t' in first_lines:
                        self.cookie_file_input.setText(file_path)
                        self.cookie_status.setText("Cookie file loaded successfully.")
                        self.cookie_status.setStyleSheet(f"color: {COLORS['success']};")
                    else:
                        self.cookie_status.setText("Invalid format. Use Netscape/Mozilla cookie format.")
                        self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
            except Exception as e:
                self.cookie_status.setText(f"Could not read file: {e}")
                self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")

    def _clear_cookie_file(self):
        """Clear the selected cookie file."""
        self.cookie_file_input.setText("")
        self.cookie_status.setText("Cookie file cleared.")
        self.cookie_status.setStyleSheet(f"color: {COLORS['text_secondary']};")

    def _test_cookie_import(self):
        """Test cookie import from selected browser."""
        browser_text = self.browser_combo.currentText()
        if browser_text == "None":
            self.cookie_status.setText("Select a browser first.")
            self.cookie_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
            return

        browser = browser_text.lower()
        self.test_cookies_btn.setEnabled(False)
        self.test_cookies_btn.setText("Testing...")
        self.cookie_status.setText("")

        try:
            # Use yt-dlp's built-in cookie extraction
            cookie_jar = extract_cookies_from_browser(
                browser_name=browser,
                profile=None,  # Default profile
                logger=None,   # Silent
            )
            
            # Count cookies to verify extraction worked
            cookie_count = len(list(cookie_jar))
            
            if cookie_count > 0:
                self.cookie_status.setText(f"Found {cookie_count} cookies from {browser_text}")
                self.cookie_status.setStyleSheet(f"color: {COLORS['success']};")
            else:
                self.cookie_status.setText(f"No cookies found in {browser_text}. Make sure you're logged into YouTube.")
                self.cookie_status.setStyleSheet("color: #FF9800;")  # Warning orange
                
        except PermissionError:
            self.cookie_status.setText(f"Permission denied. Close {browser_text} and try again.")
            self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            self.cookie_status.setText(f"Import failed: {error_msg}")
            self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
        finally:
            self.test_cookies_btn.setEnabled(True)
            self.test_cookies_btn.setText("Test Import")

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

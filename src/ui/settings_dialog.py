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
from utils.i18n import tr, get_current_language, set_language
from core.updater import Updater
from yt_dlp.cookies import extract_cookies_from_browser


class SettingsDialog(QDialog):
    """Settings dialog for application configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumSize(550, 700)
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

        # Language section (FIRST - before all other settings)
        lang_group = QGroupBox(tr("language_section"))
        lang_group.setStyleSheet(f"""
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
        lang_layout = QVBoxLayout(lang_group)
        lang_layout.setSpacing(12)
        lang_layout.setContentsMargins(20, 24, 20, 20)

        # Language selector row
        lang_row = QHBoxLayout()
        lang_label = QLabel(tr("language_label"))
        lang_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        lang_row.addWidget(lang_label)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.setMinimumWidth(150)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.language_combo)
        lang_row.addStretch()

        lang_layout.addLayout(lang_row)

        # Restart hint (hidden by default)
        self.restart_hint = QLabel(tr("language_restart_hint"))
        self.restart_hint.setStyleSheet(f"color: {COLORS['accent_purple']}; font-style: italic;")
        self.restart_hint.setVisible(False)
        lang_layout.addWidget(self.restart_hint)

        layout.addWidget(lang_group)

        # Download section
        download_group = QGroupBox(tr("download_settings"))
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
        download_layout.setSpacing(16)
        download_layout.setContentsMargins(20, 24, 20, 20)

        # Download path
        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input)

        self.browse_btn = QPushButton(tr("browse_btn"))
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

        download_layout.addRow(tr("download_path_label"), path_layout)

        # Default quality
        self.quality_combo = QComboBox()
        self.quality_combo.addItem(tr("quality_best"), "best")
        self.quality_combo.addItem(tr("quality_1080p"), "1080p")
        self.quality_combo.addItem(tr("quality_720p"), "720p")
        self.quality_combo.addItem(tr("quality_audio"), "audio")
        download_layout.addRow(tr("default_quality_label"), self.quality_combo)

        # Parallel downloads
        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 5)
        self.parallel_spin.setValue(2)
        self.parallel_spin.setToolTip(tr("parallel_downloads_tooltip"))
        download_layout.addRow(tr("parallel_downloads_label"), self.parallel_spin)

        layout.addWidget(download_group)

        # Preferences section
        prefs_group = QGroupBox(tr("preferences_section"))
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
        prefs_layout.setContentsMargins(20, 24, 20, 20)

        self.notifications_check = QCheckBox(tr("enable_notifications"))
        prefs_layout.addWidget(self.notifications_check)

        self.sound_check = QCheckBox(tr("enable_sound"))
        prefs_layout.addWidget(self.sound_check)

        self.updates_check = QCheckBox(tr("check_updates_startup"))
        prefs_layout.addWidget(self.updates_check)

        layout.addWidget(prefs_group)

        # yt-dlp section
        ytdlp_group = QGroupBox(tr("ytdlp_section"))
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
        ytdlp_layout.setContentsMargins(20, 24, 20, 20)

        version_label = QLabel(tr("version_label"))
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        ytdlp_layout.addWidget(version_label)

        self.version_label = QLabel(self._get_ytdlp_version())
        self.version_label.setStyleSheet("font-weight: bold;")
        ytdlp_layout.addWidget(self.version_label)

        ytdlp_layout.addStretch()

        self.check_updates_btn = QPushButton(tr("check_now_btn"))
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
        cookie_group = QGroupBox(tr("cookies_section"))
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
        cookie_layout.setContentsMargins(20, 24, 20, 20)
        cookie_layout.setSpacing(12)

        # Description
        cookie_desc = QLabel(tr("cookies_description"))
        cookie_desc.setStyleSheet(f"color: {COLORS['text_secondary']};")
        cookie_desc.setWordWrap(True)
        cookie_layout.addWidget(cookie_desc)

        # Cookies.txt file row (recommended)
        file_row = QHBoxLayout()
        
        file_label = QLabel(tr("cookies_file_label"))
        file_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        file_row.addWidget(file_label)

        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setReadOnly(True)
        self.cookie_file_input.setPlaceholderText(tr("no_file_selected"))
        file_row.addWidget(self.cookie_file_input, 1)

        self.browse_cookies_btn = QPushButton(tr("browse_btn"))
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

        self.clear_cookies_btn = QPushButton(tr("clear_btn"))
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
        self.help_cookies_btn = QPushButton(tr("how_to_export_cookies"))
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
        separator = QLabel(tr("or_use_browser"))
        separator.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cookie_layout.addWidget(separator)

        # Browser selection row (fallback)
        browser_row = QHBoxLayout()
        
        browser_label = QLabel(tr("browser_label"))
        browser_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        browser_row.addWidget(browser_label)

        self.browser_combo = QComboBox()
        self.browser_combo.addItem(tr("browser_none"), "")
        self.browser_combo.addItem("Chrome", "chrome")
        self.browser_combo.addItem("Edge", "edge")
        self.browser_combo.addItem("Firefox", "firefox")
        self.browser_combo.addItem("Brave", "brave")
        self.browser_combo.addItem("Opera", "opera")
        self.browser_combo.setMinimumWidth(120)
        browser_row.addWidget(self.browser_combo)

        browser_row.addStretch()

        self.test_cookies_btn = QPushButton(tr("test_import_btn"))
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
        log_group = QGroupBox(tr("logging_section"))
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
        log_layout.setContentsMargins(20, 24, 20, 20)

        log_path_label = QLabel(tr("log_file_label"))
        log_path_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        log_layout.addWidget(log_path_label)

        log_file = get_log_file_path()
        self.log_path_value = QLabel(str(log_file) if log_file else tr("not_configured"))
        self.log_path_value.setStyleSheet("font-size: 11px;")
        self.log_path_value.setWordWrap(True)
        log_layout.addWidget(self.log_path_value, 1)  # stretch factor 1

        self.open_log_folder_btn = QPushButton(tr("open_folder_btn"))
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

        self.cancel_btn = QPushButton(tr("cancel_btn"))
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

        self.save_btn = QPushButton(tr("save_btn"))
        self.save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _load_settings(self):
        """Load current settings into UI."""
        self.path_input.setText(config_manager.get('download_path'))
        
        # Quality combo uses data instead of display text
        quality_key = config_manager.get('default_quality', 'best')
        for i in range(self.quality_combo.count()):
            if self.quality_combo.itemData(i) == quality_key:
                self.quality_combo.setCurrentIndex(i)
                break
        
        self.parallel_spin.setValue(config_manager.get('max_parallel_downloads', 2))
        self.notifications_check.setChecked(config_manager.get('notifications_enabled', True))
        self.sound_check.setChecked(config_manager.get('sound_enabled', True))
        self.updates_check.setChecked(config_manager.get('check_updates', True))
        
        # Load language setting
        current_lang = config_manager.get('language', 'en')
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
        
        # Load cookie settings
        cookie_file = config_manager.get('cookie_file_path', '')
        self.cookie_file_input.setText(cookie_file)
        
        # Browser combo uses data instead of display text
        cookie_browser = config_manager.get('cookie_browser', '')
        for i in range(self.browser_combo.count()):
            if self.browser_combo.itemData(i) == cookie_browser:
                self.browser_combo.setCurrentIndex(i)
                break

    def _on_language_changed(self, index):
        """Handle language selection change."""
        new_lang = self.language_combo.itemData(index)
        current_lang = config_manager.get('language', 'en')
        
        # Show restart hint if language changed from current saved value
        if new_lang != current_lang:
            self.restart_hint.setVisible(True)
        else:
            self.restart_hint.setVisible(False)

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("select_download_folder"),
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
        config_manager.set('default_quality', self.quality_combo.currentData())
        config_manager.set('max_parallel_downloads', self.parallel_spin.value())
        config_manager.set('notifications_enabled', self.notifications_check.isChecked())
        config_manager.set('sound_enabled', self.sound_check.isChecked())
        config_manager.set('check_updates', self.updates_check.isChecked())
        
        # Save language setting
        set_language(self.language_combo.currentData())
        
        # Save cookie settings
        config_manager.set('cookie_file_path', self.cookie_file_input.text())
        config_manager.set('cookie_browser', self.browser_combo.currentData())
        
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
        self.check_updates_btn.setText(tr("checking_btn"))
        self._updater.check_for_updates()

    def _on_update_available(self, current: str, latest: str):
        """Handle update available signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn"))

        reply = QMessageBox.question(
            self,
            tr("update_available_title"),
            tr("update_available_message", latest=latest, current=current),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.check_updates_btn.setEnabled(False)
            self.check_updates_btn.setText(tr("updating_btn"))
            self._updater.install_update()

    def _on_already_up_to_date(self, version: str):
        """Handle already up to date signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn"))
        QMessageBox.information(
            self,
            tr("up_to_date_title"),
            tr("up_to_date_message", version=version)
        )

    def _on_check_failed(self, error: str):
        """Handle check failed signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn"))
        QMessageBox.warning(
            self,
            tr("update_check_failed_title"),
            tr("update_check_failed_message", error=error)
        )

    def _on_update_result(self, success: bool, message: str):
        """Handle update result signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn"))

        if success:
            QMessageBox.information(self, tr("update_complete_title"), message)
            # Refresh the version display
            self.version_label.setText(self._get_ytdlp_version())
        else:
            QMessageBox.warning(self, tr("update_failed_title"), message)

    def _show_cookie_help(self):
        """Show cookie export instructions dialog."""
        import webbrowser
        
        dialog = QDialog(self)
        dialog.setWindowTitle(tr("cookie_help_title"))
        dialog.setMinimumWidth(450)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Title
        title = QLabel(tr("export_from_chrome"))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # Steps
        steps_text = (
            tr("cookie_step_1") +
            tr("cookie_step_2") +
            tr("cookie_step_3") +
            tr("cookie_step_4") +
            tr("cookie_step_5")
        )
        steps = QLabel(steps_text)
        steps.setWordWrap(True)
        steps.setStyleSheet(f"color: {COLORS['text_secondary']}; line-height: 1.5;")
        layout.addWidget(steps)
        
        # Extension link button
        ext_btn = QPushButton(tr("open_extension_page"))
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
        note = QLabel(tr("firefox_note"))
        note.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(note)
        
        # Close button
        close_btn = QPushButton(tr("close_btn"))
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
            tr("select_cookies_file"),
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
                        self.cookie_status.setText(tr("cookie_file_loaded"))
                        self.cookie_status.setStyleSheet(f"color: {COLORS['success']};")
                    else:
                        self.cookie_status.setText(tr("cookie_file_invalid"))
                        self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
            except Exception as e:
                self.cookie_status.setText(tr("cookie_file_error", error=str(e)))
                self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")

    def _clear_cookie_file(self):
        """Clear the selected cookie file."""
        self.cookie_file_input.setText("")
        self.cookie_status.setText(tr("cookie_file_cleared"))
        self.cookie_status.setStyleSheet(f"color: {COLORS['text_secondary']};")

    def _test_cookie_import(self):
        """Test cookie import from selected browser."""
        browser_key = self.browser_combo.currentData()
        if not browser_key:
            self.cookie_status.setText(tr("select_browser_first"))
            self.cookie_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
            return

        browser_text = self.browser_combo.currentText()
        self.test_cookies_btn.setEnabled(False)
        self.test_cookies_btn.setText(tr("testing_btn"))
        self.cookie_status.setText("")

        try:
            # Use yt-dlp's built-in cookie extraction
            cookie_jar = extract_cookies_from_browser(
                browser_name=browser_key,
                profile=None,  # Default profile
                logger=None,   # Silent
            )
            
            # Count cookies to verify extraction worked
            cookie_count = len(list(cookie_jar))
            
            if cookie_count > 0:
                self.cookie_status.setText(tr("cookies_found", count=cookie_count, browser=browser_text))
                self.cookie_status.setStyleSheet(f"color: {COLORS['success']};")
            else:
                self.cookie_status.setText(tr("no_cookies_found", browser=browser_text))
                self.cookie_status.setStyleSheet("color: #FF9800;")  # Warning orange
                
        except PermissionError:
            self.cookie_status.setText(tr("permission_denied", browser=browser_text))
            self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
        except Exception as e:
            error_msg = str(e)
            if len(error_msg) > 100:
                error_msg = error_msg[:97] + "..."
            self.cookie_status.setText(tr("import_failed", error=error_msg))
            self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
        finally:
            self.test_cookies_btn.setEnabled(True)
            self.test_cookies_btn.setText(tr("test_import_btn"))

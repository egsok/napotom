"""Settings dialog window."""

import os
import subprocess
import sys

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QCheckBox, QLabel,
    QFileDialog, QGroupBox, QMessageBox, QSpinBox, QFrame
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
        self.setMinimumWidth(680)
        self.setMaximumHeight(620)
        self.setModal(True)

        # Initialize updater
        self._updater = Updater()
        self._updater.update_available.connect(self._on_update_available)
        self._updater.already_up_to_date.connect(self._on_already_up_to_date)
        self._updater.check_failed.connect(self._on_check_failed)
        self._updater.update_result.connect(self._on_update_result)

        self._setup_ui()
        self._load_settings()

    def _create_group_style(self):
        """Return common group box stylesheet."""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {COLORS['text_primary']};
            }}
        """

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        group_style = self._create_group_style()

        # === ROW 1: Language + Preferences side by side ===
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Language section (compact)
        lang_group = QGroupBox(tr("language_section"))
        lang_group.setStyleSheet(group_style)
        lang_layout = QVBoxLayout(lang_group)
        lang_layout.setSpacing(8)
        lang_layout.setContentsMargins(12, 16, 12, 12)

        lang_row = QHBoxLayout()
        lang_label = QLabel(tr("language_label"))
        lang_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        lang_row.addWidget(lang_label)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.setMinimumWidth(120)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_row.addWidget(self.language_combo)
        lang_row.addStretch()
        lang_layout.addLayout(lang_row)

        self.restart_hint = QLabel(tr("language_restart_hint"))
        self.restart_hint.setStyleSheet(f"color: {COLORS['accent_purple']}; font-style: italic; font-size: 11px;")
        self.restart_hint.setVisible(False)
        lang_layout.addWidget(self.restart_hint)

        row1.addWidget(lang_group)

        # Preferences section (compact)
        prefs_group = QGroupBox(tr("preferences_section"))
        prefs_group.setStyleSheet(group_style)
        prefs_layout = QVBoxLayout(prefs_group)
        prefs_layout.setSpacing(6)
        prefs_layout.setContentsMargins(12, 16, 12, 12)

        self.notifications_check = QCheckBox(tr("enable_notifications"))
        prefs_layout.addWidget(self.notifications_check)
        self.sound_check = QCheckBox(tr("enable_sound"))
        prefs_layout.addWidget(self.sound_check)
        self.updates_check = QCheckBox(tr("check_updates_startup"))
        prefs_layout.addWidget(self.updates_check)

        row1.addWidget(prefs_group)
        layout.addLayout(row1)

        # === ROW 2: Download Settings (full width) ===
        download_group = QGroupBox(tr("download_settings"))
        download_group.setStyleSheet(group_style)
        download_layout = QHBoxLayout(download_group)
        download_layout.setSpacing(16)
        download_layout.setContentsMargins(12, 16, 12, 12)

        # Path
        path_label = QLabel(tr("download_path_label"))
        path_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        download_layout.addWidget(path_label)
        
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        download_layout.addWidget(self.path_input, 1)

        self.browse_btn = QPushButton(tr("browse_btn"))
        self.browse_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 6px 10px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        self.browse_btn.clicked.connect(self._browse_folder)
        download_layout.addWidget(self.browse_btn)

        # Separator
        download_layout.addWidget(self._create_separator())

        # Quality
        quality_label = QLabel(tr("default_quality_label"))
        quality_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        download_layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItem(tr("quality_best"), "best")
        self.quality_combo.addItem(tr("quality_1080p"), "1080p")
        self.quality_combo.addItem(tr("quality_720p"), "720p")
        self.quality_combo.addItem(tr("quality_audio"), "audio")
        self.quality_combo.setMinimumWidth(100)
        download_layout.addWidget(self.quality_combo)

        # Separator
        download_layout.addWidget(self._create_separator())

        # Parallel
        parallel_label = QLabel(tr("parallel_downloads_label"))
        parallel_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        download_layout.addWidget(parallel_label)

        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 5)
        self.parallel_spin.setValue(2)
        self.parallel_spin.setToolTip(tr("parallel_downloads_tooltip"))
        self.parallel_spin.setMaximumWidth(60)
        download_layout.addWidget(self.parallel_spin)

        layout.addWidget(download_group)

        # === ROW 3: yt-dlp + Logging side by side ===
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        # yt-dlp section
        ytdlp_group = QGroupBox(tr("ytdlp_section"))
        ytdlp_group.setStyleSheet(group_style)
        ytdlp_layout = QHBoxLayout(ytdlp_group)
        ytdlp_layout.setContentsMargins(12, 16, 12, 12)

        version_label = QLabel(tr("version_label"))
        version_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        ytdlp_layout.addWidget(version_label)

        self.version_label = QLabel(self._get_ytdlp_version())
        self.version_label.setStyleSheet("font-weight: bold;")
        ytdlp_layout.addWidget(self.version_label)
        ytdlp_layout.addStretch()

        self.check_updates_btn = QPushButton(tr("check_now_btn"))
        self.check_updates_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 6px 10px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        self.check_updates_btn.clicked.connect(self._check_updates)
        ytdlp_layout.addWidget(self.check_updates_btn)

        row3.addWidget(ytdlp_group)

        # Logging section
        log_group = QGroupBox(tr("logging_section"))
        log_group.setStyleSheet(group_style)
        log_layout = QHBoxLayout(log_group)
        log_layout.setContentsMargins(12, 16, 12, 12)

        log_path_label = QLabel(tr("log_file_label"))
        log_path_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        log_layout.addWidget(log_path_label)

        log_file = get_log_file_path()
        log_display = str(log_file.name) if log_file else tr("not_configured")
        self.log_path_value = QLabel(log_display)
        self.log_path_value.setStyleSheet("font-size: 11px;")
        self.log_path_value.setToolTip(str(log_file) if log_file else "")
        log_layout.addWidget(self.log_path_value)
        log_layout.addStretch()

        self.open_log_folder_btn = QPushButton(tr("open_folder_btn"))
        self.open_log_folder_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 6px 10px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        self.open_log_folder_btn.clicked.connect(self._open_log_folder)
        log_layout.addWidget(self.open_log_folder_btn)

        row3.addWidget(log_group)
        layout.addLayout(row3)

        # === ROW 4: Cookies section (full width, compact) ===
        cookie_group = QGroupBox(tr("cookies_section"))
        cookie_group.setStyleSheet(group_style)
        cookie_layout = QVBoxLayout(cookie_group)
        cookie_layout.setContentsMargins(12, 16, 12, 12)
        cookie_layout.setSpacing(8)

        # Description (shorter)
        cookie_desc = QLabel(tr("cookies_description"))
        cookie_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        cookie_desc.setWordWrap(True)
        cookie_layout.addWidget(cookie_desc)

        # Two columns: cookies.txt on left, browser on right
        cookie_row = QHBoxLayout()
        cookie_row.setSpacing(16)

        # Left: Cookies file
        file_col = QVBoxLayout()
        file_col.setSpacing(4)

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
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 5px 8px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        self.browse_cookies_btn.clicked.connect(self._browse_cookie_file)
        file_row.addWidget(self.browse_cookies_btn)

        self.clear_cookies_btn = QPushButton(tr("clear_btn"))
        self.clear_cookies_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 5px 8px; }}
            QPushButton:hover {{ border-color: {COLORS['error']}; }}
        """)
        self.clear_cookies_btn.clicked.connect(self._clear_cookie_file)
        file_row.addWidget(self.clear_cookies_btn)

        file_col.addLayout(file_row)

        # Help link
        self.help_cookies_btn = QPushButton(tr("how_to_export_cookies"))
        self.help_cookies_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: none; color: {COLORS['accent_purple']}; text-decoration: underline; padding: 0; font-size: 11px; text-align: left; }}
            QPushButton:hover {{ color: {COLORS['accent_magenta']}; }}
        """)
        self.help_cookies_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_cookies_btn.clicked.connect(self._show_cookie_help)
        file_col.addWidget(self.help_cookies_btn)

        cookie_row.addLayout(file_col, 2)

        # Vertical separator
        cookie_row.addWidget(self._create_separator(vertical=True))

        # Right: Browser fallback
        browser_col = QVBoxLayout()
        browser_col.setSpacing(4)

        browser_header = QLabel(tr("or_use_browser"))
        browser_header.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        browser_col.addWidget(browser_header)

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
        self.browser_combo.setMinimumWidth(100)
        browser_row.addWidget(self.browser_combo)

        self.test_cookies_btn = QPushButton(tr("test_import_btn"))
        self.test_cookies_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 5px 8px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        self.test_cookies_btn.clicked.connect(self._test_cookie_import)
        browser_row.addWidget(self.test_cookies_btn)

        browser_col.addLayout(browser_row)
        cookie_row.addLayout(browser_col, 1)

        cookie_layout.addLayout(cookie_row)

        # Status label
        self.cookie_status = QLabel("")
        self.cookie_status.setWordWrap(True)
        self.cookie_status.setStyleSheet("font-size: 11px;")
        cookie_layout.addWidget(self.cookie_status)

        layout.addWidget(cookie_group)

        # === Spacer ===
        layout.addStretch()

        # === Buttons ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_btn = QPushButton(tr("cancel_btn"))
        self.cancel_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 8px 20px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(tr("save_btn"))
        self.save_btn.clicked.connect(self._save_and_close)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _create_separator(self, vertical=False):
        """Create a visual separator line."""
        sep = QFrame()
        if vertical:
            sep.setFrameShape(QFrame.Shape.VLine)
        else:
            sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {COLORS['border']};")
        return sep

    def _load_settings(self):
        """Load current settings into UI."""
        self.path_input.setText(config_manager.get('download_path'))
        
        quality_key = config_manager.get('default_quality', 'best')
        for i in range(self.quality_combo.count()):
            if self.quality_combo.itemData(i) == quality_key:
                self.quality_combo.setCurrentIndex(i)
                break
        
        self.parallel_spin.setValue(config_manager.get('max_parallel_downloads', 2))
        self.notifications_check.setChecked(config_manager.get('notifications_enabled', True))
        self.sound_check.setChecked(config_manager.get('sound_enabled', True))
        self.updates_check.setChecked(config_manager.get('check_updates', True))
        
        current_lang = config_manager.get('language', 'en')
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
        
        cookie_file = config_manager.get('cookie_file_path', '')
        self.cookie_file_input.setText(cookie_file)
        
        cookie_browser = config_manager.get('cookie_browser', '')
        for i in range(self.browser_combo.count()):
            if self.browser_combo.itemData(i) == cookie_browser:
                self.browser_combo.setCurrentIndex(i)
                break

    def _on_language_changed(self, index):
        """Handle language selection change."""
        new_lang = self.language_combo.itemData(index)
        current_lang = config_manager.get('language', 'en')
        self.restart_hint.setVisible(new_lang != current_lang)

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, tr("select_download_folder"), self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)

    def _open_log_folder(self):
        """Open the log file folder in file explorer."""
        log_file = get_log_file_path()
        if log_file and log_file.parent.exists():
            os.startfile(str(log_file.parent))

    def _save_and_close(self):
        """Save settings and close dialog."""
        config_manager.set('download_path', self.path_input.text())
        config_manager.set('default_quality', self.quality_combo.currentData())
        config_manager.set('max_parallel_downloads', self.parallel_spin.value())
        config_manager.set('notifications_enabled', self.notifications_check.isChecked())
        config_manager.set('sound_enabled', self.sound_check.isChecked())
        config_manager.set('check_updates', self.updates_check.isChecked())
        set_language(self.language_combo.currentData())
        config_manager.set('cookie_file_path', self.cookie_file_input.text())
        config_manager.set('cookie_browser', self.browser_combo.currentData())
        self.accept()

    def _get_ytdlp_version(self) -> str:
        """Get installed yt-dlp version with fallback strategies."""
        try:
            import yt_dlp
            version = getattr(yt_dlp, 'version', None)
            if version:
                v = getattr(version, '__version__', None)
                if v:
                    return v
        except Exception:
            pass
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
            self, tr("update_available_title"),
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
        QMessageBox.information(self, tr("up_to_date_title"), tr("up_to_date_message", version=version))

    def _on_check_failed(self, error: str):
        """Handle check failed signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn"))
        QMessageBox.warning(self, tr("update_check_failed_title"), tr("update_check_failed_message", error=error))

    def _on_update_result(self, success: bool, message: str):
        """Handle update result signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn"))
        if success:
            QMessageBox.information(self, tr("update_complete_title"), message)
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
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel(tr("export_from_chrome"))
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        steps_text = (
            tr("cookie_step_1") + tr("cookie_step_2") + tr("cookie_step_3") +
            tr("cookie_step_4") + tr("cookie_step_5")
        )
        steps = QLabel(steps_text)
        steps.setWordWrap(True)
        steps.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(steps)
        
        ext_btn = QPushButton(tr("open_extension_page"))
        ext_btn.setStyleSheet(f"""
            QPushButton {{ background-color: {COLORS['accent_purple']}; border: none; padding: 10px 20px; font-weight: bold; }}
            QPushButton:hover {{ background-color: {COLORS['accent_magenta']}; }}
        """)
        ext_btn.clicked.connect(lambda: webbrowser.open(
            "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
        ))
        layout.addWidget(ext_btn)
        
        note = QLabel(tr("firefox_note"))
        note.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(note)
        
        close_btn = QPushButton(tr("close_btn"))
        close_btn.setStyleSheet(f"""
            QPushButton {{ background-color: transparent; border: 1px solid {COLORS['border']}; padding: 8px 20px; }}
            QPushButton:hover {{ border-color: {COLORS['accent_purple']}; }}
        """)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        dialog.exec()

    def _browse_cookie_file(self):
        """Open file browser to select cookies.txt file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, tr("select_cookies_file"), "",
            "Cookie files (*.txt);;All files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_lines = f.read(500)
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
            self.cookie_status.setStyleSheet(f"color: {COLORS['warning']};")
            return

        self.cookie_status.setText(tr("testing_cookies"))
        self.cookie_status.setStyleSheet(f"color: {COLORS['text_secondary']};")
        self.test_cookies_btn.setEnabled(False)

        try:
            jar = extract_cookies_from_browser(browser_key)
            count = len(list(jar))
            if count > 0:
                self.cookie_status.setText(tr("cookie_import_success", count=count, browser=browser_key.title()))
                self.cookie_status.setStyleSheet(f"color: {COLORS['success']};")
            else:
                self.cookie_status.setText(tr("cookie_import_empty", browser=browser_key.title()))
                self.cookie_status.setStyleSheet(f"color: {COLORS['warning']};")
        except Exception as e:
            error_msg = str(e)
            if 'DPAPI' in error_msg or 'decrypt' in error_msg.lower():
                self.cookie_status.setText(tr("cookie_import_dpapi_error"))
            elif 'Permission' in error_msg or 'access' in error_msg.lower():
                self.cookie_status.setText(tr("cookie_import_permission_error", browser=browser_key.title()))
            else:
                self.cookie_status.setText(tr("cookie_import_error", error=error_msg[:100]))
            self.cookie_status.setStyleSheet(f"color: {COLORS['error']};")
        finally:
            self.test_cookies_btn.setEnabled(True)

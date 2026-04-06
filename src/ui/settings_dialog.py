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
        self._initial_lang = get_current_language()
        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(600)
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
                margin-top: 8px;
                padding-top: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 4px;
                color: {COLORS['text_primary']};
            }}
        """

    def _create_button_style(self, hover_color='accent_purple'):
        """Return common button stylesheet."""
        return f"""
            QPushButton {{ 
                background-color: transparent; 
                border: 1px solid {COLORS['border']}; 
                padding: 6px 12px; 
            }}
            QPushButton:hover {{ 
                border-color: {COLORS[hover_color]}; 
            }}
        """

    def _setup_ui(self):
        """Setup dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(16, 16, 16, 16)

        group_style = self._create_group_style()
        btn_style = self._create_button_style()

        # === ROW 1: Language (inline, compact) + Preferences ===
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        # Language - compact inline
        lang_group = QGroupBox(tr("language_section"))
        lang_group.setStyleSheet(group_style)
        lang_layout = QHBoxLayout(lang_group)
        lang_layout.setContentsMargins(12, 12, 12, 8)

        self.lang_label = QLabel(tr("language_label"))
        self.lang_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        lang_layout.addWidget(self.lang_label)

        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.setMinimumWidth(110)
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(self.language_combo)

        row1.addWidget(lang_group, 0)  # Don't stretch

        # Preferences - compact checkboxes in a row
        prefs_group = QGroupBox(tr("preferences_section"))
        prefs_group.setStyleSheet(group_style)
        prefs_layout = QHBoxLayout(prefs_group)
        prefs_layout.setContentsMargins(12, 12, 12, 8)
        prefs_layout.setSpacing(16)

        self.notifications_check = QCheckBox(tr("enable_notifications"))
        prefs_layout.addWidget(self.notifications_check)
        self.sound_check = QCheckBox(tr("enable_sound"))
        prefs_layout.addWidget(self.sound_check)
        self.updates_check = QCheckBox(tr("check_updates_startup"))
        prefs_layout.addWidget(self.updates_check)
        prefs_layout.addStretch()

        row1.addWidget(prefs_group, 1)  # Stretch to fill
        layout.addLayout(row1)

        # === ROW 2: Download Path (full width) ===
        path_group = QGroupBox(tr("download_path_label").rstrip(':'))
        path_group.setStyleSheet(group_style)
        path_layout = QHBoxLayout(path_group)
        path_layout.setContentsMargins(12, 12, 12, 8)

        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        path_layout.addWidget(self.path_input, 1)

        self.browse_btn = QPushButton(tr("browse_btn"))
        self.browse_btn.setStyleSheet(btn_style)
        self.browse_btn.clicked.connect(self._browse_folder)
        path_layout.addWidget(self.browse_btn)

        layout.addWidget(path_group)

        # === ROW 3: Quality + Parallel + yt-dlp + Logging ===
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        # Quality
        quality_group = QGroupBox(tr("default_quality_label").rstrip(':'))
        quality_group.setStyleSheet(group_style)
        quality_layout = QHBoxLayout(quality_group)
        quality_layout.setContentsMargins(12, 12, 12, 8)

        self.quality_combo = QComboBox()
        self.quality_combo.addItem(tr("quality_best"), "best")
        self.quality_combo.addItem(tr("quality_1080p"), "1080p")
        self.quality_combo.addItem(tr("quality_720p"), "720p")
        self.quality_combo.addItem(tr("quality_audio"), "audio")
        self.quality_combo.setMinimumWidth(100)
        quality_layout.addWidget(self.quality_combo)

        row3.addWidget(quality_group)

        # Parallel downloads
        parallel_group = QGroupBox(tr("parallel_downloads_label").rstrip(':'))
        parallel_group.setStyleSheet(group_style)
        parallel_layout = QHBoxLayout(parallel_group)
        parallel_layout.setContentsMargins(12, 12, 12, 8)

        self.parallel_spin = QSpinBox()
        self.parallel_spin.setRange(1, 5)
        self.parallel_spin.setValue(2)
        self.parallel_spin.setToolTip(tr("parallel_downloads_tooltip"))
        parallel_layout.addWidget(self.parallel_spin)

        row3.addWidget(parallel_group)

        # yt-dlp version
        ytdlp_group = QGroupBox(tr("ytdlp_section"))
        ytdlp_group.setStyleSheet(group_style)
        ytdlp_layout = QHBoxLayout(ytdlp_group)
        ytdlp_layout.setContentsMargins(12, 12, 12, 8)

        self.version_text_label = QLabel(tr("version_label"))
        self.version_text_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        ytdlp_layout.addWidget(self.version_text_label)

        self.version_label = QLabel(self._get_ytdlp_version())
        self.version_label.setStyleSheet("font-weight: bold;")
        ytdlp_layout.addWidget(self.version_label)

        self.check_updates_btn = QPushButton(tr("check_now_btn"))
        self.check_updates_btn.setStyleSheet(btn_style)
        self.check_updates_btn.clicked.connect(self._check_updates)
        ytdlp_layout.addWidget(self.check_updates_btn)

        row3.addWidget(ytdlp_group)

        # Logging
        log_group = QGroupBox(tr("logging_section"))
        log_group.setStyleSheet(group_style)
        log_layout = QHBoxLayout(log_group)
        log_layout.setContentsMargins(12, 12, 12, 8)

        log_file = get_log_file_path()
        log_display = str(log_file.name) if log_file else tr("not_configured")
        self.log_path_value = QLabel(log_display)
        self.log_path_value.setStyleSheet("font-size: 11px;")
        self.log_path_value.setToolTip(str(log_file) if log_file else "")
        log_layout.addWidget(self.log_path_value)

        self.open_log_folder_btn = QPushButton(tr("open_folder_btn"))
        self.open_log_folder_btn.setStyleSheet(btn_style)
        self.open_log_folder_btn.clicked.connect(self._open_log_folder)
        log_layout.addWidget(self.open_log_folder_btn)

        row3.addWidget(log_group)
        layout.addLayout(row3)

        # === ROW 4: Cookies section ===
        cookie_group = QGroupBox(tr("cookies_section"))
        cookie_group.setStyleSheet(group_style)
        cookie_layout = QVBoxLayout(cookie_group)
        cookie_layout.setContentsMargins(12, 12, 12, 8)
        cookie_layout.setSpacing(8)

        # Description
        self.cookie_desc = QLabel(tr("cookies_description"))
        self.cookie_desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        self.cookie_desc.setWordWrap(True)
        cookie_layout.addWidget(self.cookie_desc)

        # Cookies file row
        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.cookies_file_label = QLabel(tr("cookies_file_label"))
        self.cookies_file_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        file_row.addWidget(self.cookies_file_label)

        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setReadOnly(True)
        self.cookie_file_input.setPlaceholderText(tr("no_file_selected"))
        file_row.addWidget(self.cookie_file_input, 1)

        self.browse_cookies_btn = QPushButton(tr("browse_btn"))
        self.browse_cookies_btn.setStyleSheet(btn_style)
        self.browse_cookies_btn.clicked.connect(self._browse_cookie_file)
        file_row.addWidget(self.browse_cookies_btn)

        self.clear_cookies_btn = QPushButton(tr("clear_btn"))
        self.clear_cookies_btn.setStyleSheet(self._create_button_style('error'))
        self.clear_cookies_btn.clicked.connect(self._clear_cookie_file)
        file_row.addWidget(self.clear_cookies_btn)

        self.help_cookies_btn = QPushButton(tr("how_to_export_cookies"))
        self.help_cookies_btn.setStyleSheet(f"""
            QPushButton {{ 
                background-color: transparent; 
                border: none; 
                color: {COLORS['accent_purple']}; 
                text-decoration: underline; 
                padding: 6px 0; 
            }}
            QPushButton:hover {{ color: {COLORS['accent_magenta']}; }}
        """)
        self.help_cookies_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_cookies_btn.clicked.connect(self._show_cookie_help)
        file_row.addWidget(self.help_cookies_btn)

        cookie_layout.addLayout(file_row)

        # Browser import row
        browser_row = QHBoxLayout()
        browser_row.setSpacing(8)

        self.or_browser_label = QLabel(tr("or_use_browser"))
        self.or_browser_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        browser_row.addWidget(self.or_browser_label)

        self.browser_label = QLabel(tr("browser_label"))
        self.browser_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        browser_row.addWidget(self.browser_label)

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
        self.test_cookies_btn.setStyleSheet(btn_style)
        self.test_cookies_btn.clicked.connect(self._test_cookie_import)
        browser_row.addWidget(self.test_cookies_btn)

        browser_row.addStretch()
        cookie_layout.addLayout(browser_row)

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

    def _retranslate_ui(self):
        """Update all UI text to current language (hot reload)."""
        self.setWindowTitle(tr("settings_title"))
        
        # Find group boxes and update their titles
        for group in self.findChildren(QGroupBox):
            name = group.objectName()
            # We'll update titles based on known patterns
        
        # Update labels
        self.lang_label.setText(tr("language_label"))
        self.notifications_check.setText(tr("enable_notifications"))
        self.sound_check.setText(tr("enable_sound"))
        self.updates_check.setText(tr("check_updates_startup"))
        self.browse_btn.setText(tr("browse_btn"))
        self.version_text_label.setText(tr("version_label"))
        self.check_updates_btn.setText(tr("check_now_btn"))
        self.open_log_folder_btn.setText(tr("open_folder_btn"))
        self.cookie_desc.setText(tr("cookies_description"))
        self.cookies_file_label.setText(tr("cookies_file_label"))
        self.cookie_file_input.setPlaceholderText(tr("no_file_selected"))
        self.browse_cookies_btn.setText(tr("browse_btn"))
        self.clear_cookies_btn.setText(tr("clear_btn"))
        self.help_cookies_btn.setText(tr("how_to_export_cookies"))
        self.or_browser_label.setText(tr("or_use_browser"))
        self.browser_label.setText(tr("browser_label"))
        self.test_cookies_btn.setText(tr("test_import_btn"))
        self.cancel_btn.setText(tr("cancel_btn"))
        self.save_btn.setText(tr("save_btn"))
        
        # Update quality combo items (preserve selection)
        current_quality = self.quality_combo.currentData()
        self.quality_combo.clear()
        self.quality_combo.addItem(tr("quality_best"), "best")
        self.quality_combo.addItem(tr("quality_1080p"), "1080p")
        self.quality_combo.addItem(tr("quality_720p"), "720p")
        self.quality_combo.addItem(tr("quality_audio"), "audio")
        for i in range(self.quality_combo.count()):
            if self.quality_combo.itemData(i) == current_quality:
                self.quality_combo.setCurrentIndex(i)
                break
        
        # Update browser combo (preserve selection)
        current_browser = self.browser_combo.currentData()
        self.browser_combo.setItemText(0, tr("browser_none"))
        for i in range(self.browser_combo.count()):
            if self.browser_combo.itemData(i) == current_browser:
                self.browser_combo.setCurrentIndex(i)
                break

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
        """Handle language selection change - hot reload UI."""
        new_lang = self.language_combo.itemData(index)
        # Temporarily set language to see preview
        set_language(new_lang)
        # Update all UI text
        self._retranslate_ui()

    def _browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self, tr("select_download_folder"), self.path_input.text()
        )
        if folder:
            self.path_input.setText(folder)

    def _open_log_folder(self):
        """Open the log file folder in file explorer."""
        from utils.helpers import open_folder
        log_file = get_log_file_path()
        if log_file and log_file.parent.exists():
            open_folder(str(log_file.parent))

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

    def reject(self):
        """Handle cancel - restore original language."""
        set_language(self._initial_lang)
        super().reject()

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
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # When needed info
        when_needed = QLabel(tr("cookie_help_when_needed"))
        when_needed.setWordWrap(True)
        when_needed.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(when_needed)
        
        # Warning about cookie rotation
        warning = QLabel(tr("cookie_help_warning"))
        warning.setWordWrap(True)
        warning.setStyleSheet(f"""
            background-color: {COLORS['bg_input']};
            border: 1px solid {COLORS['border']};
            border-radius: 6px;
            padding: 10px;
            color: {COLORS['text_primary']};
        """)
        layout.addWidget(warning)
        
        title = QLabel(tr("export_from_chrome"))
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        steps_text = (
            tr("cookie_step_1") + tr("cookie_step_2") + tr("cookie_step_3") +
            tr("cookie_step_4") + tr("cookie_step_5") + tr("cookie_step_6")
        )
        steps = QLabel(steps_text)
        steps.setWordWrap(True)
        steps.setOpenExternalLinks(True)
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

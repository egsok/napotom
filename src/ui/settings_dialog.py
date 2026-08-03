"""Settings dialog window."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QWidget, QScrollArea,
    QLineEdit, QPushButton, QComboBox, QLabel,
    QFileDialog, QMessageBox, QFrame, QApplication, QStyle, QStyleOption
)
from PyQt6.QtCore import Qt, QObject, QRunnable, QSize, QThreadPool, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QFont, QPainter

from ui.styles import COLORS, FS_DISPLAY, FS_META, FS_MONO
from ui.common import (
    InfoMark, InkCheckBox, InkComboBox, KraftSheet, SegmentedControl, apply_brand_titlebar,
    mono_font, populate_quality_combo, update_prompt_text,
)
from utils.config import config_manager
from utils.logger import get_log_file_path
from utils.i18n import tr, get_current_language, set_language
from core.updater import Updater, get_ytdlp_version
from yt_dlp.cookies import extract_cookies_from_browser


def _row_text(key: str) -> str:
    """Row title from a key that may carry a form label's trailing colon."""
    return tr(key).rstrip(':')


class CookieTestSignals(QObject):
    """Signals for cookie test worker."""
    success = pyqtSignal(int)  # cookie count
    error = pyqtSignal(str)  # error message


class CookieTestWorker(QRunnable):
    """Background worker for testing browser cookie extraction."""

    def __init__(self, browser_key: str):
        super().__init__()
        self.browser_key = browser_key
        self.signals = CookieTestSignals()

    @pyqtSlot()
    def run(self):
        try:
            jar = extract_cookies_from_browser(self.browser_key)
            self.signals.success.emit(len(list(jar)))
        except Exception as e:
            self.signals.error.emit(str(e))


class SettingRow(QWidget):
    """One printed line of settings: what it is (and why) left, its control right.

    Heights are not set per row; they fall out of one floor and the content, so
    the sheet prints in a handful of regular steps: a bare title line sits at
    the floor, a segmented control or a field pushes its own row up, and a row
    that explains itself is one line taller.
    """

    PAD_X = 14
    PAD_Y = 8
    FLOOR = 38  # one title line (14px/600) with the padding around it

    def __init__(self, title_key: str = "", desc_key: str = "",
                 stretch_control: bool = False, parent=None):
        super().__init__(parent)
        self.title_key = title_key
        self.desc_key = desc_key
        self.separator = None  # the dashed rule above it, set by SettingsSection
        self.setMinimumHeight(self.FLOOR)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(self.PAD_X, self.PAD_Y, self.PAD_X, self.PAD_Y)
        layout.setSpacing(14)

        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 0)
        left.setSpacing(2)

        self._head = QHBoxLayout()
        self._head.setContentsMargins(0, 0, 0, 0)
        self._head.setSpacing(7)
        self.title_label = None
        if title_key:
            self.title_label = QLabel(_row_text(title_key))
            self.title_label.setObjectName("rowTitle")
            self._head.addWidget(self.title_label)
        self._head.addStretch()
        left.addLayout(self._head)

        self.desc_label = None
        if desc_key:
            self.desc_label = QLabel(tr(desc_key))
            self.desc_label.setObjectName("rowDesc")
            self.desc_label.setWordWrap(True)
            left.addWidget(self.desc_label)

        self._controls = QHBoxLayout()
        self._controls.setContentsMargins(0, 0, 0, 0)
        self._controls.setSpacing(8)

        # A stretching control (a path field) splits the row with a caption that
        # has an explanation to fit, and takes the rest of the width when it has
        # not; everything else parks flush against the right margin.
        layout.addLayout(left, 1 if (desc_key or not stretch_control) else 0)
        layout.addLayout(self._controls, 1 if stretch_control else 0)

    def add_control(self, widget: QWidget, stretch: int = 0) -> QWidget:
        """Append a control to the right-hand end of the row."""
        self._controls.addWidget(widget, stretch)
        return widget

    def add_mark(self, widget: QWidget) -> QWidget:
        """Put a mark (the "?" affordance) right after the row title."""
        self._head.insertWidget(self._head.count() - 1, widget)
        return widget

    def set_shown(self, visible: bool) -> None:
        """Show/hide the row together with the rule that fences it off."""
        if self.separator is not None:
            self.separator.setVisible(visible)
        self.setVisible(visible)

    def retranslate(self) -> None:
        """Re-print the row's own text in the current language."""
        if self.title_label is not None:
            self.title_label.setText(_row_text(self.title_key))
        if self.desc_label is not None:
            self.desc_label.setText(tr(self.desc_key))


class SettingsSection(QWidget):
    """Rows fenced by one hairline and divided by perforation — not an island card."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("section")
        self._rows = QVBoxLayout(self)
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(0)

    def paintEvent(self, event):
        # A QWidget *subclass* ignores the stylesheet's border unless it draws
        # PE_Widget itself — without this the fence around the rows is missing.
        option = QStyleOption()
        option.initFrom(self)
        painter = QPainter(self)
        self.style().drawPrimitive(QStyle.PrimitiveElement.PE_Widget, option,
                                   painter, self)

    def add_row(self, row: SettingRow) -> SettingRow:
        if self._rows.count():
            separator = QFrame()
            separator.setObjectName("rowSep")
            separator.setFixedHeight(1)
            self._rows.addWidget(separator)
            row.separator = separator
        self._rows.addWidget(row)
        return row


class _SheetScroll(QScrollArea):
    """Scroll area that asks for the full height of what it holds.

    A plain QScrollArea hints at a small viewport, which would open the dialog
    as a peephole onto the sheet. Here it scrolls only when the settings are
    taller than the screen they open on.
    """

    def sizeHint(self):
        content = self.widget()
        if content is None:
            return super().sizeHint()
        hint = content.sizeHint()
        return QSize(hint.width(), hint.height())


class SettingsDialog(QDialog):
    """Settings dialog for application configuration."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._initial_lang = get_current_language()
        self._initial_nightly = config_manager.get('ytdlp_nightly', False)
        self._updating = False  # an update install is in flight
        self._sections = []  # (label, translation key) for the hot reload
        self._rows = []
        self.setWindowTitle(tr("settings_title"))
        # Two columns per row: this is the width at which every explanation
        # still prints on one line in both languages. Narrower and the rows
        # wrap, and the sheet grows a scrollbar it does not need.
        self.setMinimumWidth(720)
        self.setModal(True)

        # Initialize updater
        self._updater = Updater()
        self._updater.update_available.connect(self._on_update_available)
        self._updater.already_up_to_date.connect(self._on_already_up_to_date)
        self._updater.check_failed.connect(self._on_check_failed)
        self._updater.update_result.connect(self._on_update_result)
        self._updater.check_skipped.connect(self._on_check_skipped)

        self._setup_ui()
        self._load_settings()
        apply_brand_titlebar(self)

    # --- construction --------------------------------------------------
    def _setup_ui(self):
        """Setup dialog UI: one kraft sheet, sectioned rows printed on it."""
        outer = QVBoxLayout(self)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        self._sheet = KraftSheet()
        sheet_layout = QVBoxLayout(self._sheet)
        sheet_layout.setSpacing(0)
        sheet_layout.setContentsMargins(0, 0, 0, 0)

        self._body = QWidget()
        self._body.setAutoFillBackground(False)
        body_layout = QVBoxLayout(self._body)
        body_layout.setContentsMargins(22, 14, 22, 10)
        body_layout.setSpacing(6)

        self._build_general(body_layout)
        self._build_downloads(body_layout)
        self._build_ytdlp(body_layout)
        self._build_cookies(body_layout)
        self._build_logging(body_layout)
        body_layout.addStretch()

        scroll = _SheetScroll()
        scroll.setWidget(self._body)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.viewport().setAutoFillBackground(False)  # let the kraft grain through
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sheet_layout.addWidget(scroll, 1)

        sheet_layout.addWidget(self._build_footer())
        outer.addWidget(self._sheet)

        self._fit_update_button()

    def _add_section(self, body_layout: QVBoxLayout, title_key: str) -> SettingsSection:
        """Print a mono uppercase section title and the rows it heads."""
        if body_layout.count():
            body_layout.addSpacing(6)
        title = QLabel(tr(title_key).upper())
        title.setObjectName("sectionTitle")
        title.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.6))
        title.setWordWrap(True)
        body_layout.addWidget(title)
        self._sections.append((title, title_key))

        section = SettingsSection()
        body_layout.addWidget(section)
        return section

    def _add_row(self, section: SettingsSection, title_key: str = "",
                 desc_key: str = "", stretch_control: bool = False) -> SettingRow:
        row = section.add_row(SettingRow(title_key, desc_key, stretch_control))
        self._rows.append(row)
        return row

    def _mono_button(self, text_key: str, object_name: str = "secondaryButton") -> QPushButton:
        button = QPushButton(tr(text_key).upper())
        if object_name:
            button.setObjectName(object_name)
        button.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.0))
        return button

    def _build_general(self, body_layout: QVBoxLayout):
        section = self._add_section(body_layout, "general_section")

        row = self._add_row(section, "language_row", "language_row_desc")
        self.language_combo = InkComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        row.add_control(self.language_combo)

        # These three say all there is to say in their own titles — a second
        # line under them only restated it and cost the sheet a line each
        row = self._add_row(section, "enable_notifications")
        self.notifications_check = InkCheckBox()  # the name lives in the row title
        row.add_control(self.notifications_check)

        row = self._add_row(section, "enable_sound")
        self.sound_check = InkCheckBox()
        row.add_control(self.sound_check)

        row = self._add_row(section, "check_updates_startup")
        self.updates_check = InkCheckBox()
        row.add_control(self.updates_check)

    def _build_downloads(self, body_layout: QVBoxLayout):
        section = self._add_section(body_layout, "downloads_section")

        row = self._add_row(section, "download_path_row", "download_path_row_desc",
                            stretch_control=True)
        self.path_input = QLineEdit()
        self.path_input.setReadOnly(True)
        row.add_control(self.path_input, 1)
        self.browse_btn = self._mono_button("browse_btn")
        self.browse_btn.clicked.connect(self._browse_folder)
        row.add_control(self.browse_btn)

        row = self._add_row(section, "default_quality_row", "default_quality_row_desc")
        self.quality_combo = InkComboBox()
        populate_quality_combo(self.quality_combo)
        row.add_control(self.quality_combo)

        # Five values are one click in a segmented control; a spin box hides
        # them behind two specks of arrow
        row = self._add_row(section, "parallel_downloads_label",
                            "parallel_downloads_row_desc")
        self.parallel_control = SegmentedControl([(str(n), n) for n in range(1, 6)])
        row.add_control(self.parallel_control)

    def _build_ytdlp(self, body_layout: QVBoxLayout):
        section = self._add_section(body_layout, "ytdlp_section")

        row = self._add_row(section, "ytdlp_version_row", "ytdlp_version_row_desc")
        self.version_label = QLabel(self._get_ytdlp_version())
        self.version_label.setObjectName("value")
        self.version_label.setFont(mono_font(FS_META, QFont.Weight.Medium, 0.6))
        row.add_control(self.version_label)
        self.check_updates_btn = self._mono_button("check_now_btn")
        self.check_updates_btn.clicked.connect(self._check_updates)
        row.add_control(self.check_updates_btn)

        row = self._add_row(section, "ytdlp_channel_row")
        self.channel_info = InfoMark(tr("ytdlp_channel_help"))
        row.add_mark(self.channel_info)
        self.channel_control = SegmentedControl([
            (tr("ytdlp_channel_stable"), False),
            (tr("ytdlp_channel_nightly"), True),
        ])
        # Applied immediately (and rolled back on Cancel) so "Check Now" above
        # queries the channel the control currently shows
        self.channel_control.changed.connect(
            lambda _: config_manager.set(
                'ytdlp_nightly', bool(self.channel_control.currentData())
            )
        )
        row.add_control(self.channel_control)

    def _build_cookies(self, body_layout: QVBoxLayout):
        section = self._add_section(body_layout, "cookies_section")

        # The "how to export" link belongs with the explanation, not on a row
        # of its own — a whole line for one link is the sheet's cheapest cut
        row = self._add_row(section, desc_key="cookies_description")
        self.help_cookies_btn = QPushButton(tr("how_to_export_cookies"))
        self.help_cookies_btn.setObjectName("linkButton")
        self.help_cookies_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.help_cookies_btn.clicked.connect(self._show_cookie_help)
        row.add_control(self.help_cookies_btn)

        row = self._add_row(section, "cookies_method_row")
        self.cookie_method = SegmentedControl([
            (tr("cookies_method_file"), "file"),
            (tr("cookies_method_browser"), "browser"),
        ])
        self.cookie_method.changed.connect(lambda _: self._apply_cookie_method())
        row.add_control(self.cookie_method)

        self.cookie_file_row = self._add_row(section, "cookies_file_label",
                                             stretch_control=True)
        self.cookie_file_input = QLineEdit()
        self.cookie_file_input.setReadOnly(True)
        self.cookie_file_input.setPlaceholderText(tr("no_file_selected"))
        self.cookie_file_row.add_control(self.cookie_file_input, 1)
        self.browse_cookies_btn = self._mono_button("browse_btn")
        self.browse_cookies_btn.clicked.connect(self._browse_cookie_file)
        self.cookie_file_row.add_control(self.browse_cookies_btn)
        self.clear_cookies_btn = self._mono_button("clear_btn", "dangerButton")
        self.clear_cookies_btn.clicked.connect(self._clear_cookie_file)
        self.cookie_file_row.add_control(self.clear_cookies_btn)

        self.cookie_browser_row = self._add_row(section, "browser_label",
                                                "cookies_browser_warning")
        self.browser_combo = InkComboBox()
        self.browser_combo.addItem(tr("browser_none"), "")
        self.browser_combo.addItem("Chrome", "chrome")
        self.browser_combo.addItem("Edge", "edge")
        self.browser_combo.addItem("Firefox", "firefox")
        self.browser_combo.addItem("Brave", "brave")
        self.browser_combo.addItem("Opera", "opera")
        self.cookie_browser_row.add_control(self.browser_combo)
        self.test_cookies_btn = self._mono_button("test_import_btn")
        self.test_cookies_btn.clicked.connect(self._test_cookie_import)
        self.cookie_browser_row.add_control(self.test_cookies_btn)

        # Printed only while it has something to report
        self.cookie_status_row = self._add_row(section, stretch_control=True)
        self.cookie_status = QLabel("")
        self.cookie_status.setObjectName("value")
        self.cookie_status.setWordWrap(True)
        self.cookie_status_row.add_control(self.cookie_status, 1)
        self.cookie_status_row.set_shown(False)

    def _build_logging(self, body_layout: QVBoxLayout):
        section = self._add_section(body_layout, "logging_section")

        row = self._add_row(section, "log_row", "log_row_desc")
        log_file = get_log_file_path()
        self.log_path_value = QLabel(str(log_file.name) if log_file else tr("not_configured"))
        self.log_path_value.setObjectName("value")
        self.log_path_value.setFont(mono_font(FS_META, QFont.Weight.Medium, 0.6))
        self.log_path_value.setToolTip(str(log_file) if log_file else "")
        row.add_control(self.log_path_value)
        self.open_log_folder_btn = self._mono_button("open_folder_btn")
        self.open_log_folder_btn.clicked.connect(self._open_log_folder)
        row.add_control(self.open_log_folder_btn)

    def _build_footer(self) -> QWidget:
        """Cancel/Save sit ON the sheet — a dark shelf below it read as a bug."""
        footer = QWidget()
        footer.setAutoFillBackground(False)
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(22, 0, 22, 14)
        layout.setSpacing(12)

        rule = QFrame()
        rule.setObjectName("rule")
        rule.setFixedHeight(1)
        layout.addWidget(rule)

        buttons = QHBoxLayout()
        buttons.setSpacing(10)
        buttons.addStretch()

        self.cancel_btn = self._mono_button("cancel_btn")
        self.cancel_btn.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.2))
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(self.cancel_btn)

        self.save_btn = QPushButton(tr("save_btn").upper())
        self.save_btn.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.2))
        self.save_btn.clicked.connect(self._save_and_close)
        buttons.addWidget(self.save_btn)

        layout.addLayout(buttons)
        return footer

    def sizeHint(self):
        """Open as one whole page, but never taller than the screen it opens on."""
        hint = super().sizeHint()
        screen = self.screen() or QApplication.primaryScreen()
        if screen:
            hint.setHeight(min(hint.height(),
                               int(screen.availableGeometry().height() * 0.92)))
        return hint

    def _fit_update_button(self):
        """Reserve room for the widest caption the update button can show.

        It swaps between "Check Now", "Checking..." and "Updating..." — without
        a reserved width the longer captions clip and shove the version value
        out of the row.
        """
        button = self.check_updates_btn
        original = button.text()
        widest = 0
        for key in ('check_now_btn', 'checking_btn', 'updating_btn'):
            button.setText(tr(key).upper())
            # Ask the button itself: font metrics miss the QSS padding and the
            # per-character letter-spacing of the mono brand font
            widest = max(widest, button.sizeHint().width())
        button.setText(original)
        button.setMinimumWidth(widest)

    # --- state ---------------------------------------------------------
    def _retranslate_ui(self):
        """Update all UI text to current language (hot reload)."""
        self.setWindowTitle(tr("settings_title"))

        for label, key in self._sections:
            label.setText(tr(key).upper())
        for row in self._rows:
            row.retranslate()

        self.browse_btn.setText(tr("browse_btn").upper())
        self.check_updates_btn.setText(tr("check_now_btn").upper())
        self._fit_update_button()
        self.open_log_folder_btn.setText(tr("open_folder_btn").upper())
        if not get_log_file_path():
            self.log_path_value.setText(tr("not_configured"))
        self.cookie_file_input.setPlaceholderText(tr("no_file_selected"))
        self.browse_cookies_btn.setText(tr("browse_btn").upper())
        self.clear_cookies_btn.setText(tr("clear_btn").upper())
        self.help_cookies_btn.setText(tr("how_to_export_cookies"))
        self.test_cookies_btn.setText(tr("test_import_btn").upper())
        self.cancel_btn.setText(tr("cancel_btn").upper())
        self.save_btn.setText(tr("save_btn").upper())

        self.channel_info.setText(tr("ytdlp_channel_help"))
        self.channel_control.setOptions([
            (tr("ytdlp_channel_stable"), False),
            (tr("ytdlp_channel_nightly"), True),
        ])
        self.cookie_method.setOptions([
            (tr("cookies_method_file"), "file"),
            (tr("cookies_method_browser"), "browser"),
        ])

        # Update quality combo items (preserve selection)
        populate_quality_combo(self.quality_combo, self.quality_combo.currentData())

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
        self.path_input.setCursorPosition(0)  # show the start of a long path

        quality_key = config_manager.get('default_quality', 'best')
        for i in range(self.quality_combo.count()):
            if self.quality_combo.itemData(i) == quality_key:
                self.quality_combo.setCurrentIndex(i)
                break

        self.parallel_control.setCurrentData(
            config_manager.get('max_parallel_downloads', 2)
        )
        self.notifications_check.setChecked(config_manager.get('notifications_enabled', True))
        self.sound_check.setChecked(config_manager.get('sound_enabled', True))
        self.updates_check.setChecked(config_manager.get('check_updates', True))
        self.channel_control.setCurrentData(bool(config_manager.get('ytdlp_nightly', False)))

        current_lang = config_manager.get('language', 'en')
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break

        cookie_file = config_manager.get('cookie_file_path', '')
        self.cookie_file_input.setText(cookie_file)
        self.cookie_file_input.setCursorPosition(0)

        cookie_browser = config_manager.get('cookie_browser', '')
        for i in range(self.browser_combo.count()):
            if self.browser_combo.itemData(i) == cookie_browser:
                self.browser_combo.setCurrentIndex(i)
                break

        # The fork shows whichever source is actually populated; the file wins
        # when both are, because that is the order the downloader tries them in
        self.cookie_method.setCurrentData(
            "browser" if not cookie_file and cookie_browser else "file"
        )
        self._apply_cookie_method()

    def _apply_cookie_method(self):
        """Show only the branch the segmented control points at."""
        browser = self.cookie_method.currentData() == "browser"
        self.cookie_file_row.set_shown(not browser)
        self.cookie_browser_row.set_shown(browser)

    def _set_cookie_status(self, text: str, color: str, strong: bool = False):
        """Print a cookie status line — the row exists only while there is one."""
        self.cookie_status.setText(text)
        self.cookie_status.setStyleSheet(
            f"color: {color};" + (" font-weight: 600;" if strong else "")
        )
        self.cookie_status_row.set_shown(bool(text))

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
        if self._updating:
            return  # the disabled button can still be triggered by Enter
        config_manager.set('download_path', self.path_input.text())
        config_manager.set('default_quality', self.quality_combo.currentData())
        config_manager.set('max_parallel_downloads', self.parallel_control.currentData())
        config_manager.set('notifications_enabled', self.notifications_check.isChecked())
        config_manager.set('sound_enabled', self.sound_check.isChecked())
        config_manager.set('check_updates', self.updates_check.isChecked())
        config_manager.set('ytdlp_nightly', bool(self.channel_control.currentData()))
        set_language(self.language_combo.currentData())
        # Only the chosen branch is stored: a leftover file path would silently
        # win over the browser the fork says it is using
        use_browser = self.cookie_method.currentData() == "browser"
        config_manager.set('cookie_file_path',
                           "" if use_browser else self.cookie_file_input.text())
        config_manager.set('cookie_browser',
                           self.browser_combo.currentData() if use_browser else "")
        self.accept()

    def reject(self):
        """Handle cancel - restore original language and update channel."""
        if self._updating:
            return  # see _set_updating()
        set_language(self._initial_lang)
        config_manager.set('ytdlp_nightly', self._initial_nightly)
        super().reject()

    def closeEvent(self, event):
        """Keep the dialog open while an update is installing."""
        if self._updating:
            event.ignore()
            return
        super().closeEvent(event)

    def _set_updating(self, updating: bool):
        """Lock the dialog for the duration of an update install.

        The result arrives on this dialog, and an application-modal message box
        owned by a dialog the user already closed blocks the main window while
        being effectively invisible — so the dialog has to outlive the install.
        """
        self._updating = updating
        self.check_updates_btn.setEnabled(not updating)
        self.check_updates_btn.setText(
            tr("updating_btn" if updating else "check_now_btn").upper()
        )
        self.save_btn.setEnabled(not updating)
        self.cancel_btn.setEnabled(not updating)

    def _get_ytdlp_version(self) -> str:
        """Get installed yt-dlp version for display."""
        return get_ytdlp_version() or "Not installed"

    def _check_updates(self):
        """Check for yt-dlp updates."""
        self.check_updates_btn.setEnabled(False)
        self.check_updates_btn.setText(tr("checking_btn").upper())
        self._updater.check_for_updates()

    def _on_update_available(self, current: str, latest: str):
        """Handle update available signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn").upper())
        reply = QMessageBox.question(
            self, tr("update_available_title"),
            update_prompt_text(self._updater, current, latest),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._set_updating(True)
            self._updater.install_update()

    def _on_already_up_to_date(self, version: str):
        """Handle already up to date signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn").upper())
        QMessageBox.information(self, tr("up_to_date_title"), tr("up_to_date_message", version=version))

    def _on_check_skipped(self):
        """Handle check skipped signal (update already installed, pending restart)."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn").upper())
        QMessageBox.information(
            self, tr("update_complete_title"), tr("update_pending_restart_message")
        )

    def _on_check_failed(self, error: str):
        """Handle check failed signal."""
        self.check_updates_btn.setEnabled(True)
        self.check_updates_btn.setText(tr("check_now_btn").upper())
        QMessageBox.warning(self, tr("update_check_failed_title"), tr("update_check_failed_message", error=error))

    def _on_update_result(self, success: bool, message: str):
        """Handle update result signal."""
        self._set_updating(False)
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
        dialog.setMinimumWidth(560)
        apply_brand_titlebar(dialog)

        outer = QVBoxLayout(dialog)
        outer.setSpacing(0)
        outer.setContentsMargins(0, 0, 0, 0)

        sheet = KraftSheet()
        layout = QVBoxLayout(sheet)
        layout.setSpacing(12)
        layout.setContentsMargins(22, 20, 22, 18)

        # When needed info
        when_needed = QLabel(tr("cookie_help_when_needed"))
        when_needed.setWordWrap(True)
        when_needed.setStyleSheet(f"color: {COLORS['prose']};")
        layout.addWidget(when_needed)

        # Warning about cookie rotation
        warning = QLabel(tr("cookie_help_warning"))
        warning.setWordWrap(True)
        warning.setStyleSheet(f"""
            background-color: {COLORS['paper_2']};
            border: 1px solid {COLORS['line']};
            border-radius: 6px;
            padding: 12px;
            color: {COLORS['prose']};
        """)
        layout.addWidget(warning)

        title = QLabel(tr("export_from_chrome"))
        title.setWordWrap(True)
        title.setStyleSheet(
            f"color: {COLORS['violet']}; font-size: {FS_DISPLAY}px; font-weight: 700;"
        )
        layout.addWidget(title)

        steps_text = (
            tr("cookie_step_1") + tr("cookie_step_2") + tr("cookie_step_3") +
            tr("cookie_step_4") + tr("cookie_step_5") + tr("cookie_step_6")
        )
        # Neither the stylesheet nor the palette reaches a rich-text link on a
        # styled widget — it prints in the system's default blue unless the
        # ink is written into the markup itself
        steps_text = steps_text.replace(
            '<a href=', f'<a style="color: {COLORS["mag_text"]};" href='
        )
        steps = QLabel(steps_text)
        steps.setWordWrap(True)
        steps.setOpenExternalLinks(True)
        steps.setStyleSheet(f"color: {COLORS['prose']};")
        layout.addWidget(steps)

        ext_btn = QPushButton(tr("open_extension_page").upper())
        ext_btn.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.0))
        ext_btn.clicked.connect(lambda: webbrowser.open(
            "https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc"
        ))
        layout.addWidget(ext_btn)

        note = QLabel(tr("firefox_note"))
        note.setObjectName("rowDesc")
        note.setWordWrap(True)
        layout.addWidget(note)

        rule = QFrame()
        rule.setObjectName("ruleSoft")
        rule.setFixedHeight(1)
        layout.addWidget(rule)

        close_btn = QPushButton(tr("close_btn").upper())
        close_btn.setObjectName("secondaryButton")
        close_btn.setFont(mono_font(FS_MONO, QFont.Weight.DemiBold, 1.2))
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignRight)

        outer.addWidget(sheet)
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
                        self._set_cookie_status(tr("cookie_file_loaded"),
                                                COLORS['violet'], strong=True)
                    else:
                        self._set_cookie_status(tr("cookie_file_invalid"),
                                                COLORS['mag_text'])
            except Exception as e:
                self._set_cookie_status(tr("cookie_file_error", error=str(e)),
                                        COLORS['mag_text'])

    def _clear_cookie_file(self):
        """Clear the selected cookie file."""
        self.cookie_file_input.setText("")
        self._set_cookie_status(tr("cookie_file_cleared"), COLORS['violet_ink'])

    def _test_cookie_import(self):
        """Test cookie import from selected browser (in a background thread)."""
        browser_key = self.browser_combo.currentData()
        if not browser_key:
            self._set_cookie_status(tr("select_browser_first"), COLORS['violet_ink'])
            return

        self._set_cookie_status(tr("testing_cookies"), COLORS['violet_ink'])
        self.test_cookies_btn.setEnabled(False)

        worker = CookieTestWorker(browser_key)
        worker.signals.success.connect(
            lambda count, b=browser_key: self._on_cookie_test_success(count, b)
        )
        worker.signals.error.connect(
            lambda error, b=browser_key: self._on_cookie_test_error(error, b)
        )
        self._cookie_test_worker = worker  # Keep alive until signals delivered
        QThreadPool.globalInstance().start(worker)

    def _on_cookie_test_success(self, count: int, browser_key: str):
        """Handle cookie test result."""
        self.test_cookies_btn.setEnabled(True)
        if count > 0:
            self._set_cookie_status(
                tr("cookie_import_success", count=count, browser=browser_key.title()),
                COLORS['violet'], strong=True
            )
        else:
            self._set_cookie_status(
                tr("cookie_import_empty", browser=browser_key.title()),
                COLORS['violet_ink']
            )

    def _on_cookie_test_error(self, error_msg: str, browser_key: str):
        """Handle cookie test failure."""
        self.test_cookies_btn.setEnabled(True)
        if 'DPAPI' in error_msg or 'decrypt' in error_msg.lower():
            message = tr("cookie_import_dpapi_error")
        elif 'Permission' in error_msg or 'access' in error_msg.lower():
            message = tr("cookie_import_permission_error", browser=browser_key.title())
        else:
            message = tr("cookie_import_error", error=error_msg[:100])
        self._set_cookie_status(message, COLORS['mag_text'])

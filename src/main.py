"""Napotom - Main entry point."""

import logging
import os
import shutil
import sys
from pathlib import Path

from utils.config import get_app_data_dir


def _read_ytdlp_version_file(version_file: Path) -> "str | None":
    """Parse ``__version__`` from a yt_dlp ``version.py`` without importing it."""
    try:
        with open(version_file, 'r', encoding='utf-8') as fh:
            for line in fh:
                if line.startswith('__version__'):
                    # e.g. __version__ = '2025.03.31'
                    return line.split('=', 1)[1].strip().strip("'\"")
    except OSError:
        return None
    return None


def _get_bundled_ytdlp_version() -> "str | None":
    """Read the bundled yt-dlp version WITHOUT importing yt_dlp.

    In frozen builds the yt_dlp modules live inside the PyInstaller archive,
    so ``version.py`` is bundled separately as a data file (see build.spec,
    ``_bundled_meta``). In dev mode, locate version.py in the source tree via
    find_spec — the override dir is not on sys.path at this point, so this
    resolves to the .venv copy.
    """
    if getattr(sys, 'frozen', False):
        version_file = Path(sys._MEIPASS) / '_bundled_meta' / 'version.py'
    else:
        import importlib.util
        try:
            spec = importlib.util.find_spec('yt_dlp')
        except (ImportError, ValueError):
            return None
        if not spec or not spec.origin:
            return None
        version_file = Path(spec.origin).parent / 'version.py'

    if not version_file.is_file():
        return None
    return _read_ytdlp_version_file(version_file)


def _cleanup_stale_override() -> None:
    """Remove the yt-dlp override directory if the bundled version is already newer.

    Compares the override's ``yt_dlp/version.py`` against the bundled yt-dlp
    version, both read from files without importing yt_dlp. This MUST run
    BEFORE ``_apply_ytdlp_override()`` so a stale override never gets imported
    by the current process. Wrapped in a broad except so it never blocks
    startup; if the bundled version cannot be determined, the override is
    left in place (fail-safe).
    """
    logger = logging.getLogger(__name__)
    try:
        override_dir = get_app_data_dir() / 'yt_dlp_override'
        if not override_dir.exists():
            return

        version_file = override_dir / 'yt_dlp' / 'version.py'
        if not version_file.is_file():
            logger.warning("Override dir exists but missing yt_dlp/version.py — removing stale override")
            shutil.rmtree(override_dir, ignore_errors=True)
            return

        override_version = _read_ytdlp_version_file(version_file)
        if not override_version:
            logger.warning("Could not parse override yt_dlp version — leaving override in place")
            return

        bundled_version = _get_bundled_ytdlp_version()
        if not bundled_version:
            logger.info("Cannot determine bundled yt_dlp version — leaving override in place")
            return

        # --- Compare as tuples of ints (e.g. (2025, 3, 31)) ---
        # Local import: core.updater pulls in PyQt6, keep it out of the
        # minimal pre-override import surface at module top
        from core.updater import parse_version

        bundled_t = parse_version(bundled_version)
        override_t = parse_version(override_version)
        if bundled_t is None or override_t is None:
            logger.warning("Version comparison failed — leaving override in place")
            return

        if bundled_t >= override_t:
            logger.info(
                "Bundled yt-dlp %s >= override %s — removing stale override dir",
                bundled_version, override_version,
            )
            shutil.rmtree(override_dir, ignore_errors=True)
        else:
            logger.info(
                "Override yt-dlp %s is newer than bundled %s — keeping override",
                override_version, bundled_version,
            )

    except Exception:
        # Never block startup
        logger.debug("Stale-override cleanup failed", exc_info=True)


def _apply_ytdlp_override() -> None:
    """Prepend the yt-dlp override directory to sys.path if it exists.

    In frozen (PyInstaller) builds, an updated yt-dlp package may have been
    extracted to an AppData override directory. Prepending that directory to
    sys.path ensures the updated ``yt_dlp`` package is imported instead of the
    bundled one.

    This function MUST be called before any module that transitively imports
    ``yt_dlp`` (e.g. ``ui.main_window`` -> ``core.downloader`` -> ``yt_dlp``).
    """
    override_dir = get_app_data_dir() / 'yt_dlp_override'
    init_file = override_dir / 'yt_dlp' / '__init__.py'
    if init_file.is_file():
        path_str = str(override_dir)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
            # logger may not be configured yet, use print as fallback
            print(f"[yt-dlp override] Prepended {path_str} to sys.path")
    # If the override dir or init file doesn't exist, silently do nothing.


# --- Remove stale override, then apply it BEFORE importing modules that trigger yt_dlp ---
_cleanup_stale_override()
_apply_ytdlp_override()

from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402
from PyQt6.QtGui import QFont, QFontDatabase, QIcon  # noqa: E402

from utils.logger import setup_logging  # noqa: E402
from ui.styles import COLORS, FS_BODY, STYLESHEET  # noqa: E402
from ui.common import update_prompt_text  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402  (triggers yt_dlp import)
from core.updater import Updater  # noqa: E402
from utils.config import config_manager  # noqa: E402
from utils.i18n import tr  # noqa: E402


def get_asset_path(filename: str) -> str:
    """Get path to asset file, works for dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_path = sys._MEIPASS
    else:
        # Running in dev mode
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'assets', filename)


def _load_brand_fonts():
    """Register bundled brand fonts (Unbounded, IBM Plex) with Qt."""
    fonts_dir = get_asset_path('fonts')
    if not os.path.isdir(fonts_dir):
        logging.getLogger(__name__).warning('Fonts dir missing: %s', fonts_dir)
        return
    for name in os.listdir(fonts_dir):
        if name.lower().endswith('.ttf'):
            QFontDatabase.addApplicationFont(os.path.join(fonts_dir, name))


def _apply_paper_palette(app):
    """Put the bits QSS cannot reach into the paper register.

    Placeholder text has no QSS property (`QLineEdit::placeholder` is silently
    ignored), and tooltips/base colours leak the OS light theme's greys.
    """
    from PyQt6.QtGui import QColor, QPalette

    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['paper']))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['paper_2']))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['violet']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['violet']))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(58, 42, 122, 130))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS['on_ink']))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['paper_2']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['prose']))
    app.setPalette(palette)


def _setup_bundled_path():
    """Add PyInstaller bundle dir to PATH so bundled binaries (node, ffmpeg) are discoverable."""
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        current_path = os.environ.get('PATH', '')
        if bundle_dir not in current_path:
            os.environ['PATH'] = bundle_dir + os.pathsep + current_path


def main():
    # Ensure bundled binaries are on PATH before anything else
    _setup_bundled_path()

    # Initialize logging first, before any other operations
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info('Application starting')

    # Register graceful exit handler (BUG-03: helps with clean shutdown logging)
    import atexit
    def graceful_exit():
        logger.info('Application shutting down gracefully')
    atexit.register(graceful_exit)

    app = QApplication(sys.argv)
    _load_brand_fonts()
    body_font = QFont('IBM Plex Sans')
    body_font.setPixelSize(FS_BODY)
    body_font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(body_font)
    _apply_paper_palette(app)
    app.setStyleSheet(STYLESHEET)

    # Set application icon (for taskbar and window title)
    icon_path = get_asset_path('icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    updater = Updater()

    # Clear pending restart flag on fresh start (BUG-04) — unconditionally,
    # so a Settings-initiated update doesn't leave the flag stuck forever
    # when startup update checks are disabled
    updater.clear_update_pending()

    # Check for yt-dlp updates on startup if enabled
    if config_manager.get('check_updates', True):

        def on_update_available(current, latest):
            # Check if user already dismissed this version (BUG-04)
            if not updater.should_prompt_for_update(latest):
                return

            reply = QMessageBox.question(
                window,
                tr("update_available_title"),
                update_prompt_text(updater, current, latest),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                updater.install_update()
            else:
                # User dismissed - remember this version (BUG-04)
                updater.mark_update_dismissed(latest)

        def on_update_result(success, message):
            if success:
                # Pending-restart flag is set inside Updater._on_update_complete
                QMessageBox.information(
                    window,
                    tr("update_complete_title"),
                    tr("update_complete_message")
                )
            else:
                QMessageBox.warning(window, tr("update_failed_title"), message)

        updater.update_available.connect(on_update_available)
        updater.update_result.connect(on_update_result)
        updater.check_for_updates()

    # Keep updater alive by attaching to window
    window._startup_updater = updater

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

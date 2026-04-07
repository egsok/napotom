"""Video Downloader 2 - Main entry point."""

import logging
import os
import shutil
import sys

from utils.config import get_app_data_dir


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


# --- Apply yt-dlp override BEFORE importing modules that trigger yt_dlp ---
_apply_ytdlp_override()

from PyQt6.QtWidgets import QApplication, QMessageBox  # noqa: E402
from PyQt6.QtGui import QIcon  # noqa: E402

from utils.logger import setup_logging  # noqa: E402
from ui.styles import STYLESHEET  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402  (triggers yt_dlp import)
from core.updater import Updater  # noqa: E402
from utils.config import config_manager  # noqa: E402


def _cleanup_stale_override() -> None:
    """Remove the yt-dlp override directory if the bundled version is already newer.

    Compares the override's ``yt_dlp/version.py`` ``__version__`` against the
    currently importable yt_dlp version. If the bundled version is equal or
    newer, the override dir is deleted so the app uses the bundled package.

    This MUST be called after yt_dlp is importable (i.e. inside ``main()``),
    and is wrapped in a broad except so it never blocks startup.
    """
    logger = logging.getLogger(__name__)
    try:
        override_dir = get_app_data_dir() / 'yt_dlp_override'
        if not override_dir.exists():
            return

        # --- Read the override version by parsing version.py directly ---
        version_file = override_dir / 'yt_dlp' / 'version.py'
        if not version_file.is_file():
            logger.warning("Override dir exists but missing yt_dlp/version.py — removing stale override")
            shutil.rmtree(override_dir, ignore_errors=True)
            return

        override_version: str | None = None
        with open(version_file, 'r', encoding='utf-8') as fh:
            for line in fh:
                if line.startswith('__version__'):
                    # e.g. __version__ = '2025.03.31'
                    override_version = line.split('=', 1)[1].strip().strip("'\"")
                    break

        if not override_version:
            logger.warning("Could not parse override yt_dlp version — leaving override in place")
            return

        # --- Get the bundled (or currently loaded) yt_dlp version ---
        try:
            import yt_dlp.version as _ytver
            bundled_version = _ytver.__version__
        except Exception:
            logger.info("Cannot determine bundled yt_dlp version — leaving override in place")
            return

        # --- Compare as tuples of ints (e.g. (2025, 3, 31)) ---
        def _ver_tuple(v: str) -> tuple:
            return tuple(int(x) for x in v.split('.'))

        try:
            if _ver_tuple(bundled_version) >= _ver_tuple(override_version):
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
        except (ValueError, TypeError):
            logger.warning("Version comparison failed — leaving override in place")

    except Exception:
        # Never block startup
        logger.debug("Stale-override cleanup failed", exc_info=True)


def get_asset_path(filename: str) -> str:
    """Get path to asset file, works for dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_path = sys._MEIPASS
    else:
        # Running in dev mode
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'assets', filename)


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
    app.setStyleSheet(STYLESHEET)

    # Set application icon (for taskbar and window title)
    icon_path = get_asset_path('icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.show()

    # Remove stale yt-dlp override if bundled version is already up-to-date
    _cleanup_stale_override()

    # Check for yt-dlp updates on startup if enabled
    if config_manager.get('check_updates', True):
        updater = Updater()

        # Clear pending restart flag on fresh start (BUG-04)
        updater.clear_update_pending()

        def on_update_available(current, latest):
            # Check if user already dismissed this version (BUG-04)
            if not updater.should_prompt_for_update(latest):
                return

            reply = QMessageBox.question(
                window,
                "Update Available",
                f"yt-dlp {latest} is available (current: {current}).\n\nUpdate now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                updater.install_update()
            else:
                # User dismissed - remember this version (BUG-04)
                updater.mark_update_dismissed(latest)

        def on_update_result(success, message):
            if success:
                # Mark update as complete (pending restart) (BUG-04)
                updater.mark_update_complete()
                QMessageBox.information(
                    window,
                    "Update Complete",
                    "yt-dlp has been updated successfully.\n\n"
                    "Please restart the application to use the new version."
                )
            else:
                QMessageBox.warning(window, "Update Failed", message)

        updater.update_available.connect(on_update_available)
        updater.update_result.connect(on_update_result)
        updater.check_for_updates()

        # Keep updater alive by attaching to window
        window._startup_updater = updater

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

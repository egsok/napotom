"""Video Downloader 2 - Main entry point."""

import logging
import sys
import os

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon

from utils.logger import setup_logging
from ui.styles import STYLESHEET
from ui.main_window import MainWindow
from core.updater import Updater
from utils.config import config_manager


def get_asset_path(filename: str) -> str:
    """Get path to asset file, works for dev and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        # Running as compiled exe
        base_path = sys._MEIPASS
    else:
        # Running in dev mode
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, 'assets', filename)


def main():
    # Initialize logging first, before any other operations
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info('Application starting')
    logger.info('Python: %s, Platform: %s, Frozen: %s', sys.version, sys.platform, getattr(sys, 'frozen', False))
    if getattr(sys, 'frozen', False):
        logger.info('_MEIPASS: %s', sys._MEIPASS)
        logger.info('sys.executable: %s', sys.executable)
    
    # Log ffmpeg detection early
    from core.downloader import get_ffmpeg_path
    ffmpeg_path = get_ffmpeg_path()
    logger.info('FFmpeg location: %s', ffmpeg_path or 'NOT FOUND (will use system PATH)')

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

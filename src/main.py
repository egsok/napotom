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

        def on_update_available(current, latest):
            reply = QMessageBox.question(
                window,
                "Update Available",
                f"yt-dlp {latest} is available (current: {current}).\n\nUpdate now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                updater.install_update()

        def on_update_result(success, message):
            if success:
                QMessageBox.information(window, "Update Complete", message)
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

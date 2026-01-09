"""Video Downloader 2 - Main entry point."""

import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from ui.styles import STYLESHEET
from ui.main_window import MainWindow
from core.updater import Updater
from utils.config import config_manager


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)

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

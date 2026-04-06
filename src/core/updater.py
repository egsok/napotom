"""yt-dlp update management."""

import subprocess
import sys
from typing import Optional

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from utils.config import config_manager


class UpdaterSignals(QObject):
    """Signals for updater."""
    version_checked = pyqtSignal(str, str)  # current, latest
    update_complete = pyqtSignal(bool, str)  # success, message


class UpdateChecker(QRunnable):
    """Background worker for checking updates."""

    def __init__(self):
        super().__init__()
        self.signals = UpdaterSignals()

    def _get_current_version(self) -> str:
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

        return "Unknown"

    @pyqtSlot()
    def run(self):
        """Check for updates."""
        try:
            current = self._get_current_version()

            # Check PyPI for latest version
            import urllib.request
            import json

            url = "https://pypi.org/pypi/yt-dlp/json"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())
                latest = data['info']['version']

            self.signals.version_checked.emit(current, latest)

        except Exception as e:
            self.signals.version_checked.emit("error", str(e))


class UpdateInstaller(QRunnable):
    """Background worker for installing updates."""

    def __init__(self):
        super().__init__()
        self.signals = UpdaterSignals()

    @pyqtSlot()
    def run(self):
        """Install yt-dlp update."""
        try:
            # Use CREATE_NO_WINDOW on Windows to hide console
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
                capture_output=True,
                text=True,
                timeout=120,
                creationflags=creationflags,
            )

            if result.returncode == 0:
                self.signals.update_complete.emit(True, "Update successful! Restart to apply.")
            else:
                self.signals.update_complete.emit(False, f"Update failed: {result.stderr}")

        except subprocess.TimeoutExpired:
            self.signals.update_complete.emit(False, "Update timed out")
        except Exception as e:
            self.signals.update_complete.emit(False, str(e))


class Updater(QObject):
    """Manages yt-dlp updates."""

    update_available = pyqtSignal(str, str)  # current, latest
    already_up_to_date = pyqtSignal(str)  # current version
    check_failed = pyqtSignal(str)  # error message
    update_result = pyqtSignal(bool, str)  # success, message

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()

    def should_check_for_updates(self) -> bool:
        """Check if we should perform update check."""
        # Don't check if update is pending restart
        if config_manager.get('ytdlp_update_pending_restart', False):
            return False
        return True

    def should_prompt_for_update(self, latest: str) -> bool:
        """Check if we should prompt user about this update."""
        dismissed = config_manager.get('last_dismissed_ytdlp_version', '')
        if dismissed == latest:
            return False
        return True

    def mark_update_dismissed(self, version: str) -> None:
        """Record that user dismissed update for this version."""
        config_manager.set('last_dismissed_ytdlp_version', version)

    def mark_update_complete(self) -> None:
        """Record that update completed successfully."""
        config_manager.set('ytdlp_update_pending_restart', True)
        # Clear dismissed version since they accepted the update
        config_manager.set('last_dismissed_ytdlp_version', '')

    def clear_update_pending(self) -> None:
        """Clear pending restart flag (called on app start)."""
        config_manager.set('ytdlp_update_pending_restart', False)

    def check_for_updates(self):
        """Check for available updates."""
        if not self.should_check_for_updates():
            return  # Skip check if update pending restart
        
        checker = UpdateChecker()
        checker.signals.version_checked.connect(self._on_version_checked)
        self.thread_pool.start(checker)

    def install_update(self):
        """Install yt-dlp update."""
        installer = UpdateInstaller()
        installer.signals.update_complete.connect(self._on_update_complete)
        self.thread_pool.start(installer)

    def _normalize_version(self, version: str) -> tuple:
        """Normalize version string to comparable tuple."""
        # yt-dlp versions are like "2025.12.8" or "2025.12.08"
        # Convert to tuple of ints for proper comparison
        try:
            return tuple(int(x) for x in version.split('.'))
        except ValueError:
            return (0,)

    def _on_version_checked(self, current: str, latest: str):
        """Handle version check result."""
        if current == "error":
            self.check_failed.emit(latest)  # latest contains error message
        elif self._normalize_version(current) < self._normalize_version(latest):
            self.update_available.emit(current, latest)
        else:
            self.already_up_to_date.emit(current)

    def _on_update_complete(self, success: bool, message: str):
        """Handle update result."""
        self.update_result.emit(success, message)

"""yt-dlp update management."""

import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, urlretrieve

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from utils.config import config_manager, get_app_data_dir

logger = logging.getLogger(__name__)


def get_override_dir() -> Path:
    """Return the directory where updated yt-dlp packages are extracted.

    In frozen (PyInstaller) builds, yt-dlp wheels are extracted here so they
    can be prepended to sys.path and take precedence over the bundled version.
    """
    return get_app_data_dir() / 'yt_dlp_override'


def _download_and_extract_wheel() -> Tuple[bool, str]:
    """Download the latest yt-dlp universal wheel from PyPI and extract it.

    Returns:
        (True, version_string) on success, (False, error_message) on failure.
    """
    tmp_path: Optional[str] = None
    try:
        # 1. Query PyPI for latest yt-dlp metadata
        logger.info("Querying PyPI for latest yt-dlp version...")
        pypi_url = "https://pypi.org/pypi/yt-dlp/json"
        with urlopen(pypi_url, timeout=30) as resp:
            data = json.loads(resp.read())

        version = data['info']['version']
        logger.info("Latest yt-dlp version on PyPI: %s", version)

        # 2. Find the universal wheel in the release URLs
        wheel_url: Optional[str] = None
        for entry in data.get('urls', []):
            if entry.get('filename', '').endswith('-py3-none-any.whl'):
                wheel_url = entry['url']
                break

        if wheel_url is None:
            msg = f"No universal wheel found for yt-dlp {version} on PyPI"
            logger.error(msg)
            return False, msg

        logger.info("Downloading wheel from %s", wheel_url)

        # 3. Download to a temp file
        fd, tmp_path = tempfile.mkstemp(suffix='.whl')
        os.close(fd)
        urlretrieve(wheel_url, tmp_path)

        # 4. Validate the downloaded file is a valid zip
        if not zipfile.is_zipfile(tmp_path):
            msg = "Downloaded file is not a valid zip/wheel archive"
            logger.error(msg)
            return False, msg

        # 5. Extract yt_dlp/ entries to the override directory
        override = get_override_dir()

        with zipfile.ZipFile(tmp_path, 'r') as zf:
            yt_dlp_entries = [n for n in zf.namelist() if n.startswith('yt_dlp/')]
            if not yt_dlp_entries:
                msg = "Wheel does not contain a yt_dlp/ directory"
                logger.error(msg)
                return False, msg

            # Remove stale override if present
            if override.exists():
                logger.info("Removing stale override dir: %s", override)
                shutil.rmtree(override)

            override.mkdir(parents=True, exist_ok=True)
            logger.info("Extracting %d entries to %s", len(yt_dlp_entries), override)

            for entry in yt_dlp_entries:
                zf.extract(entry, override)

        logger.info("yt-dlp %s extracted successfully to %s", version, override)
        return True, version

    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON response from PyPI: {exc}"
        logger.error(msg)
        return False, msg
    except (OSError, IOError) as exc:
        msg = f"Filesystem or network error: {exc}"
        logger.error(msg)
        return False, msg
    except Exception as exc:
        msg = f"Unexpected error during wheel download: {exc}"
        logger.exception(msg)
        return False, msg
    finally:
        # Clean up temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


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
        """Install yt-dlp update.

        In frozen (PyInstaller) builds, downloads the wheel from PyPI and
        extracts it to an AppData override directory.  In dev mode, falls
        back to pip subprocess.
        """
        if getattr(sys, 'frozen', False):
            logger.info("Frozen build detected — using wheel download strategy")
            success, detail = _download_and_extract_wheel()
            if success:
                self.signals.update_complete.emit(
                    True,
                    f"Updated yt-dlp to {detail}. Restart to apply.",
                )
            else:
                self.signals.update_complete.emit(False, detail)
        else:
            # Dev mode — use pip subprocess
            logger.info("Dev mode — updating via pip")
            try:
                creationflags = (
                    subprocess.CREATE_NO_WINDOW
                    if sys.platform == 'win32'
                    else 0
                )

                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--upgrade', 'yt-dlp'],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    creationflags=creationflags,
                )

                if result.returncode == 0:
                    self.signals.update_complete.emit(
                        True, "Update successful! Restart to apply.",
                    )
                else:
                    self.signals.update_complete.emit(
                        False, f"Update failed: {result.stderr}",
                    )

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

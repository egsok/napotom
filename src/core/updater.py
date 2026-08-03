"""yt-dlp update management."""

import json
import logging
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple
from urllib.request import urlopen, urlretrieve

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot

from utils.config import config_manager, get_app_data_dir

logger = logging.getLogger(__name__)

PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
NIGHTLY_URL = "https://api.github.com/repos/yt-dlp/yt-dlp-nightly-builds/releases/latest"


def get_update_channel() -> str:
    """Return the yt-dlp channel the user selected: 'stable' or 'nightly'."""
    return 'nightly' if config_manager.get('ytdlp_nightly', False) else 'stable'


def get_ytdlp_version() -> Optional[str]:
    """Get the installed yt-dlp version, or None if it cannot be determined."""
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

    return None


def parse_version(v: str) -> Optional[tuple]:
    """Parse a dotted version string into an int tuple; None if invalid.

    Handles yt-dlp style versions like "2025.12.8" / "2025.12.08".
    """
    try:
        return tuple(int(x) for x in v.split('.'))
    except (ValueError, AttributeError):
        return None


def get_override_dir() -> Path:
    """Return the directory where updated yt-dlp packages are extracted.

    In frozen (PyInstaller) builds, yt-dlp wheels are extracted here so they
    can be prepended to sys.path and take precedence over the bundled version.
    """
    return get_app_data_dir() / 'yt_dlp_override'


def fetch_latest_release(channel: str) -> Tuple[str, str]:
    """Return (version, download_url) for the latest build on ``channel``.

    Stable builds come from PyPI as a universal wheel; nightly builds come from
    the yt-dlp nightly GitHub releases, which ship no wheel — only the sdist
    tarball carries the importable ``yt_dlp`` package.
    """
    if channel == 'nightly':
        logger.info("Querying GitHub for the latest yt-dlp nightly build...")
        with urlopen(NIGHTLY_URL, timeout=30) as resp:
            data = json.loads(resp.read())

        version = data['tag_name']
        for asset in data.get('assets', []):
            if asset.get('name') == 'yt-dlp.tar.gz':
                return version, asset['browser_download_url']
        raise ValueError(f"No yt-dlp.tar.gz asset in nightly release {version}")

    logger.info("Querying PyPI for latest yt-dlp version...")
    with urlopen(PYPI_URL, timeout=30) as resp:
        data = json.loads(resp.read())

    version = data['info']['version']
    for entry in data.get('urls', []):
        if entry.get('filename', '').endswith('-py3-none-any.whl'):
            return version, entry['url']
    raise ValueError(f"No universal wheel found for yt-dlp {version} on PyPI")


def _extract_package(archive_path: str, override: Path) -> int:
    """Extract the ``yt_dlp`` package from a wheel or sdist into ``override``.

    Returns the number of extracted entries; raises ValueError when the archive
    holds no yt_dlp package.
    """
    if zipfile.is_zipfile(archive_path):
        with zipfile.ZipFile(archive_path, 'r') as zf:
            entries = [n for n in zf.namelist() if n.startswith('yt_dlp/')]
            if not entries:
                raise ValueError("Wheel does not contain a yt_dlp/ directory")
            _reset_override(override)
            for entry in entries:
                zf.extract(entry, override)
            return len(entries)

    if tarfile.is_tarfile(archive_path):
        with tarfile.open(archive_path, 'r:*') as tf:
            # sdist layout is yt-dlp-<version>/yt_dlp/... — drop the top level
            members = [m for m in tf.getmembers() if '/yt_dlp/' in m.name]
            if not members:
                raise ValueError("Tarball does not contain a yt_dlp/ directory")
            _reset_override(override)
            for member in members:
                member.name = member.name.split('/', 1)[1]
                tf.extract(member, override, filter='data')
            return len(members)

    raise ValueError("Downloaded file is neither a wheel nor a tarball")


def _reset_override(override: Path) -> None:
    """Drop any previously extracted override and recreate the directory."""
    if override.exists():
        logger.info("Removing stale override dir: %s", override)
        shutil.rmtree(override)
    override.mkdir(parents=True, exist_ok=True)


def _download_and_install(channel: str) -> Tuple[bool, str]:
    """Download the latest yt-dlp build on ``channel`` and extract it.

    Returns:
        (True, version_string) on success, (False, error_message) on failure.
    """
    tmp_path: Optional[str] = None
    try:
        version, download_url = fetch_latest_release(channel)
        logger.info("Latest yt-dlp %s build: %s (%s)", channel, version, download_url)

        fd, tmp_path = tempfile.mkstemp(suffix='.ytdlp-download')
        os.close(fd)
        urlretrieve(download_url, tmp_path)

        override = get_override_dir()
        count = _extract_package(tmp_path, override)

        logger.info("yt-dlp %s (%s) extracted: %d entries to %s",
                    version, channel, count, override)
        return True, version

    except ValueError as exc:
        logger.error("yt-dlp %s update failed: %s", channel, exc)
        return False, str(exc)
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON response from the {channel} update source: {exc}"
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

    @pyqtSlot()
    def run(self):
        """Check for updates on the currently selected channel."""
        try:
            current = get_ytdlp_version() or "Unknown"
            latest, _ = fetch_latest_release(get_update_channel())
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

        In frozen (PyInstaller) builds, downloads the latest build of the
        selected channel and extracts it to an AppData override directory.
        In dev mode, falls back to pip subprocess — except for nightly builds,
        which are not published on PyPI and so also go through the override.
        """
        channel = get_update_channel()

        if getattr(sys, 'frozen', False) or channel == 'nightly':
            logger.info("Installing yt-dlp from the %s channel via override dir", channel)
            success, detail = _download_and_install(channel)
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
    check_skipped = pyqtSignal()  # update already installed, pending restart

    def __init__(self):
        super().__init__()
        self.thread_pool = QThreadPool()
        # True when the pending update installs a different channel rather than
        # a newer version; the UI words its prompt accordingly
        self.channel_switch = False
        self._checker = None
        self._installer = None

    def is_channel_switch_pending(self) -> bool:
        """True when the installed build came from a channel the user left."""
        return config_manager.get('ytdlp_installed_channel', 'stable') != get_update_channel()

    def should_check_for_updates(self) -> bool:
        """Check if we should perform update check."""
        # Don't check if update is pending restart
        if config_manager.get('ytdlp_update_pending_restart', False):
            return False
        return True

    def should_prompt_for_update(self, latest: str) -> bool:
        """Check if we should prompt user about this update."""
        # A channel switch is a different build, not the version the user
        # dismissed — always offer it
        if self.channel_switch:
            return True
        dismissed = config_manager.get('last_dismissed_ytdlp_version', '')
        if dismissed == latest:
            return False
        return True

    def mark_update_dismissed(self, version: str) -> None:
        """Record that user dismissed update for this version."""
        config_manager.set('last_dismissed_ytdlp_version', version)

    def mark_update_complete(self) -> None:
        """Record that update completed successfully."""
        logger.info("Marking yt-dlp update as installed, pending restart")
        config_manager.set('ytdlp_update_pending_restart', True)
        # Clear dismissed version since they accepted the update
        config_manager.set('last_dismissed_ytdlp_version', '')
        # Remember which channel the installed build came from
        config_manager.set('ytdlp_installed_channel', get_update_channel())
        self.channel_switch = False

    def clear_update_pending(self) -> None:
        """Clear pending restart flag (called on app start)."""
        config_manager.set('ytdlp_update_pending_restart', False)

    def check_for_updates(self):
        """Check for available updates."""
        if not self.should_check_for_updates():
            self.check_skipped.emit()  # Update pending restart
            return

        checker = UpdateChecker()
        checker.signals.version_checked.connect(self._on_version_checked)
        # Keep the worker alive until its signal is delivered: the thread pool
        # owns the C++ runnable, but nothing holds the Python object carrying
        # the signals, so a long-running job can lose its result to the GC
        self._checker = checker
        self.thread_pool.start(checker)

    def install_update(self):
        """Install yt-dlp update."""
        logger.info("Update install requested (channel: %s)", get_update_channel())
        installer = UpdateInstaller()
        installer.signals.update_complete.connect(self._on_update_complete)
        self._installer = installer  # keep alive — see check_for_updates()
        self.thread_pool.start(installer)

    def _normalize_version(self, version: str) -> tuple:
        """Normalize version string to comparable tuple."""
        return parse_version(version) or (0,)

    def _on_version_checked(self, current: str, latest: str):
        """Handle version check result."""
        self._checker = None
        if current == "error":
            self.channel_switch = False
            self.check_failed.emit(latest)  # latest contains error message
            return

        # After switching channels the installed build can be *newer* than the
        # selected channel's latest (nightly -> stable). Offer it anyway, or the
        # user silently keeps running the channel they just left.
        self.channel_switch = self.is_channel_switch_pending()

        if (self.channel_switch
                or self._normalize_version(current) < self._normalize_version(latest)):
            self.update_available.emit(current, latest)
        else:
            self.already_up_to_date.emit(current)

    def _on_update_complete(self, success: bool, message: str):
        """Handle update result."""
        logger.info("Update result received by the app: success=%s (%s)", success, message)
        self._installer = None
        if success:
            # Single owner of the pending-restart flag: set it here so updates
            # started from any place (startup dialog, Settings) record it
            self.mark_update_complete()
        self.update_result.emit(success, message)

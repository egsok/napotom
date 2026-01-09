"""System notifications and sounds."""

import sys
from pathlib import Path
from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QSoundEffect
from src.utils.config import config_manager


def get_assets_path() -> Path:
    """Get assets directory path."""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).parent.parent.parent
    return base_path / 'assets'


class NotificationManager:
    """Manages system notifications and sounds."""

    def __init__(self):
        self._sound: QSoundEffect | None = None
        self._init_sound()

    def _init_sound(self):
        """Initialize sound effect."""
        sound_path = get_assets_path() / 'sounds' / 'complete.wav'
        if sound_path.exists():
            self._sound = QSoundEffect()
            self._sound.setSource(QUrl.fromLocalFile(str(sound_path)))
            self._sound.setVolume(0.5)

    def notify_complete(self, title: str):
        """Send completion notification."""
        if config_manager.get('notifications_enabled', True):
            self._show_toast("Download Complete", title)
        if config_manager.get('sound_enabled', True):
            self._play_sound()

    def notify_error(self, title: str, error: str):
        """Send error notification."""
        if config_manager.get('notifications_enabled', True):
            self._show_toast(f"Download Failed: {title}", error)

    def _play_sound(self):
        """Play completion sound."""
        if self._sound:
            self._sound.play()

    def _show_toast(self, title: str, message: str):
        """Show Windows toast notification."""
        try:
            if sys.platform == 'win32':
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, threaded=True)
        except ImportError:
            pass
        except Exception:
            pass


# Global instance
notification_manager = NotificationManager()

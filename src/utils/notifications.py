"""System notifications and sounds — cross-platform (Windows + macOS)."""

import sys
from pathlib import Path
from utils.config import config_manager


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
        self._sound = None
        self._sound_initialized = False

    def _init_sound(self):
        """Initialize sound effect (lazy, Windows only)."""
        if self._sound_initialized:
            return
        self._sound_initialized = True
        if sys.platform == 'win32':
            sound_path = get_assets_path() / 'sounds' / 'complete.wav'
            if sound_path.exists():
                try:
                    from PyQt6.QtMultimedia import QSoundEffect
                    from PyQt6.QtCore import QUrl
                    self._sound = QSoundEffect()
                    self._sound.setSource(QUrl.fromLocalFile(str(sound_path)))
                    self._sound.setVolume(0.5)
                except Exception:
                    pass  # QApplication not ready yet

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
        if sys.platform == 'darwin':
            # macOS: pync handles sound via notification
            return
        self._init_sound()
        if self._sound:
            self._sound.play()

    def _show_toast(self, title: str, message: str):
        """Show system notification (cross-platform)."""
        try:
            if sys.platform == 'darwin':
                import pync
                sound = 'default' if config_manager.get('sound_enabled', True) else None
                pync.notify(message, title=title, sound=sound)
            elif sys.platform == 'win32':
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=5, threaded=True)
        except ImportError:
            pass
        except Exception:
            pass


# Global instance
notification_manager = NotificationManager()

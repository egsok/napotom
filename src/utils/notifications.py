"""System notifications and sounds for macOS."""

from utils.config import config_manager


class NotificationManager:
    """Manages system notifications using macOS Notification Center."""

    def notify_complete(self, title: str):
        """Send completion notification."""
        sound = config_manager.get('sound_enabled', True)
        if config_manager.get('notifications_enabled', True):
            self._show_notification("Download Complete", title, sound=sound)
        elif sound:
            # Play sound even if notifications disabled
            self._show_notification("", "", sound=True)

    def notify_error(self, title: str, error: str):
        """Send error notification."""
        if config_manager.get('notifications_enabled', True):
            self._show_notification(f"Download Failed: {title}", error, sound=False)

    def _show_notification(self, title: str, message: str, sound: bool = False):
        """Show macOS notification via pync."""
        try:
            import pync
            pync.notify(
                message,
                title=title,
                sound='default' if sound else None
            )
        except ImportError:
            pass
        except Exception:
            pass  # notifications not critical


# Global instance
notification_manager = NotificationManager()

"""Configuration management with JSON persistence."""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


def get_app_data_dir() -> Path:
    """Get application data directory."""
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:  # Linux/Mac
        base = Path.home() / '.config'

    app_dir = base / 'VideoDownloader2'
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


def get_default_download_dir() -> str:
    """Get default download directory."""
    downloads = Path.home() / 'Downloads' / 'Videos'
    downloads.mkdir(parents=True, exist_ok=True)
    return str(downloads)


@dataclass
class Config:
    """Application configuration."""
    download_path: str = ""
    default_quality: str = "best"
    notifications_enabled: bool = True
    sound_enabled: bool = True
    check_updates: bool = True
    max_parallel_downloads: int = 2
    language: str = "en"  # Interface language: 'en' or 'ru'
    # Update loop prevention (BUG-04)
    last_dismissed_ytdlp_version: str = ""  # Version user dismissed
    ytdlp_update_pending_restart: bool = False  # True after successful update
    # Browser cookie import (FEAT-01)
    cookie_browser: str = ""  # Browser for cookie import: chrome, edge, firefox, brave, opera, or empty
    cookie_file_path: str = ""  # Path to cookies.txt file (Netscape format) - more reliable than browser extraction

    def __post_init__(self):
        if not self.download_path:
            self.download_path = get_default_download_dir()


class ConfigManager:
    """Manages loading and saving configuration."""

    def __init__(self):
        self.config_path = get_app_data_dir() / 'config.json'
        self.config = self._load()

    def _load(self) -> Config:
        """Load config from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return Config(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return Config()

    def save(self) -> None:
        """Save config to file."""
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)

    def get(self, key: str, default=None):
        """Get config value."""
        return getattr(self.config, key, default)

    def set(self, key: str, value) -> None:
        """Set config value and save."""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
            self.save()


# Global config instance
config_manager = ConfigManager()

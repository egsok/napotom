"""Configuration management with JSON persistence."""

import json
import os
from dataclasses import dataclass, asdict, fields
from pathlib import Path
from typing import Optional


def get_app_data_dir() -> Path:
    """Get application data directory.

    Migrates the legacy VideoDownloader2 directory (pre-Napotom rename) so
    existing settings, cookies and the yt-dlp override survive the rebrand.
    """
    if os.name == 'nt':  # Windows
        base = Path(os.environ.get('APPDATA', Path.home()))
    else:  # Linux/Mac
        base = Path.home() / '.config'

    app_dir = base / 'Napotom'
    legacy_dir = base / 'VideoDownloader2'
    if not app_dir.exists() and legacy_dir.is_dir():
        try:
            legacy_dir.rename(app_dir)
        except OSError:
            pass  # e.g. old app still running — start fresh, keep legacy dir
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
    # yt-dlp update channel: nightly builds carry site fixes weeks before releases
    ytdlp_nightly: bool = False  # True = pull nightly builds instead of PyPI releases
    ytdlp_installed_channel: str = "stable"  # Channel the installed override came from
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
        """Load config from file or create default.

        Unknown keys are dropped rather than fatal: a config written by a newer
        build used to raise TypeError here, fall back to defaults, and get
        overwritten by the next set() — losing everything on a downgrade.
        A file we genuinely cannot parse is kept aside instead of vanishing.
        """
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                known = {f.name for f in fields(Config)}
                return Config(**{k: v for k, v in data.items() if k in known})
            except (json.JSONDecodeError, TypeError, OSError, ValueError):
                try:
                    os.replace(self.config_path,
                               self.config_path.with_suffix('.json.corrupt'))
                except OSError:
                    pass
        return Config()

    def save(self) -> None:
        """Save config to file, atomically.

        Every set() rewrites the whole file, so a crash or a second process
        writing at the same moment used to leave a truncated config — which
        _load() then failed to parse and silently replaced with defaults,
        losing every setting at once. Write beside the target and rename:
        os.replace is atomic, so a reader sees either the old file or the new.
        """
        tmp_path = self.config_path.with_suffix('.json.tmp')
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(self.config), f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.config_path)

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

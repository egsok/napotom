# Technology Stack

**Analysis Date:** 2026-02-01

## Languages

**Primary:**
- Python 3.12+ (3.14.0 in dev environment) - All application code

**Secondary:**
- Qt Stylesheet (CSS-like) - UI styling in `src/ui/styles.py`

## Runtime

**Environment:**
- Python 3.12+ (CI uses 3.12, dev uses 3.14.0)
- Windows primary target, macOS secondary

**Package Manager:**
- pip
- Lockfile: Not present (uses `requirements.txt` with minimum versions)

**Virtual Environment:**
- `.venv/` directory with Python venv
- Config: `.venv/pyvenv.cfg`

## Frameworks

**Core:**
- PyQt6 6.10.2 - Desktop GUI framework
  - Uses QMainWindow, QDialog, QWidget patterns
  - Signal/slot communication between components
  - QThreadPool for background tasks

**Downloader:**
- yt-dlp 2025.12.8 - Video extraction and download
  - Supports 1000+ video sites
  - Handles video/audio format selection
  - Progress hooks for download tracking

**Build/Packaging:**
- PyInstaller 6.17.0 - Creates standalone Windows executable
  - Spec file: `build.spec`
  - Bundles FFmpeg binaries
  - Single-file executable output

## Key Dependencies

**Critical:**
- `PyQt6>=6.6.0` - GUI framework, entire UI depends on this
- `yt-dlp>=2024.01.01` - Core download functionality
- `pyinstaller>=6.0.0` - Build system for distribution

**Infrastructure:**
- `win10toast>=0.9` - Windows toast notifications
- FFmpeg (external binary) - Video/audio merging and conversion

**Installed (dev environment):**
- PyQt6-sip 13.10.3 - Qt Python bindings
- pywin32 311 - Windows API access
- python-dotenv 1.2.1 - Environment variable loading

## Configuration

**Application Config:**
- Location: `%APPDATA%/VideoDownloader2/config.json` (Windows)
- Location: `~/.config/VideoDownloader2/config.json` (Linux/Mac)
- Manager: `src/utils/config.py` - ConfigManager singleton

**Config Options:**
```python
@dataclass
class Config:
    download_path: str          # Default: ~/Downloads/Videos
    default_quality: str        # best, 1080p, 720p, audio
    notifications_enabled: bool # Windows toast notifications
    sound_enabled: bool         # Completion sound
    check_updates: bool         # yt-dlp update check on startup
    max_parallel_downloads: int # 1-5, default: 2
```

**Environment:**
- No `.env` files required
- No environment variables required for operation

**Build Configuration:**
- `build.spec` - PyInstaller build configuration
- `scripts/build.py` - Build automation script

## Platform Requirements

**Development:**
- Python 3.12+
- pip
- FFmpeg binaries in project root (for video merging)
- Windows for win10toast notifications

**Production:**
- Windows 10+ (primary target)
- macOS (secondary, via `mac` branch)
- FFmpeg bundled in executable

**CI/CD:**
- GitHub Actions
- Windows and macOS runners
- Python 3.12
- FFmpeg downloaded during build

## Assets

**Location:** `assets/`
- `icon.ico` - Application icon
- `sounds/complete.wav` - Download completion sound

**Bundling:**
- Assets included via PyInstaller datas
- Path resolution handles both dev and bundled modes

## Quality Presets

Defined in `src/core/downloader.py`:
```python
QUALITY_PRESETS = {
    "best": "bestvideo+bestaudio/best",
    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "audio": "bestaudio/best",  # Extracts to MP3
}
```

---

*Stack analysis: 2026-02-01*

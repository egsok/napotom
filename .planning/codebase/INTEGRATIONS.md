# External Integrations

**Analysis Date:** 2026-02-01

## APIs & External Services

**PyPI (yt-dlp version check):**
- Purpose: Check for yt-dlp updates
- Endpoint: `https://pypi.org/pypi/yt-dlp/json`
- Implementation: `src/core/updater.py`
- Auth: None required
- Usage: On startup (if `check_updates` enabled) and manual check in Settings

**Video Platforms (via yt-dlp):**
- YouTube, Vimeo, VK, and 1000+ sites
- Handled entirely by yt-dlp library
- No direct API keys required
- Some sites may require authentication (not currently implemented)

**GitHub (FFmpeg download):**
- Purpose: Download FFmpeg binaries during CI build
- URL: `https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip`
- Only used in `.github/workflows/release.yml`

## Data Storage

**Databases:**
- None - No database used

**File Storage:**
- Local filesystem only
- Download path: Configurable, default `~/Downloads/Videos`
- Config file: `%APPDATA%/VideoDownloader2/config.json`

**Caching:**
- None - No caching layer

## Authentication & Identity

**Auth Provider:**
- None - No user authentication
- Video site authentication not currently supported

**Potential future:**
- Cookies support for authenticated video downloads
- OAuth for specific platforms

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service

**Logs:**
- Console output only (suppressed in production via PyInstaller)
- yt-dlp configured with `quiet: True, no_warnings: True`

## CI/CD & Deployment

**Hosting:**
- GitHub Releases
- Single executable distribution

**CI Pipeline:**
- GitHub Actions (`.github/workflows/release.yml`)
- Triggered by: Git tags matching `v*` or manual dispatch
- Builds: Windows (windows-latest), macOS (macos-latest)
- Outputs: 
  - `VideoDownloader2-Windows.zip`
  - `VideoDownloader2-macOS.dmg`

**Build Steps:**
1. Set up Python 3.12
2. Install dependencies via pip
3. Download FFmpeg binaries
4. Run PyInstaller with `build.spec`
5. Create distribution archive
6. Upload as GitHub Release

## Environment Configuration

**Required env vars:**
- None - Application works without any environment variables

**Optional env vars:**
- Standard Python/pip environment variables

**Secrets location:**
- No secrets required for operation
- GitHub Actions uses default GITHUB_TOKEN for releases

## External Binaries

**FFmpeg:**
- Required for: Video/audio merging, audio extraction
- Location (dev): Project root (`ffmpeg.exe`, `ffprobe.exe`)
- Location (bundled): Alongside executable (via PyInstaller)
- Detection: `src/core/downloader.py::get_ffmpeg_path()`
- Fallback: System PATH

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## Windows Integration

**win10toast:**
- Purpose: System tray notifications on download complete/error
- Implementation: `src/utils/notifications.py`
- Triggered by: `notification_manager.notify_complete()` and `notify_error()`

**Qt Multimedia:**
- Purpose: Play completion sound
- Implementation: `src/utils/notifications.py::NotificationManager`
- Sound file: `assets/sounds/complete.wav`

## Update Mechanism

**yt-dlp Updates:**
- Check: Compares installed version against PyPI latest
- Install: Runs `pip install --upgrade yt-dlp` via subprocess
- Location: `src/core/updater.py`
- Threading: Uses QThreadPool for background execution

**Flow:**
1. `UpdateChecker.run()` - Fetches PyPI JSON, compares versions
2. Signals emitted: `update_available`, `already_up_to_date`, `check_failed`
3. `UpdateInstaller.run()` - Executes pip upgrade
4. Signal emitted: `update_complete` with success/failure

## Network Configuration

**yt-dlp settings (from `src/core/downloader.py`):**
```python
opts = {
    'socket_timeout': 30,
    'retries': 10,
    'fragment_retries': 10,
    'concurrent_fragment_downloads': 4,
}
```

**No proxy support currently implemented.**

---

*Integration audit: 2026-02-01*

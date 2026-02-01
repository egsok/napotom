# Video Downloader 2 — Bug Fix & Stabilization

## What This Is

Desktop video downloader for Windows (PyQt6 + yt-dlp) that downloads videos from YouTube and 1000+ sites. Currently has several bugs breaking core functionality — this milestone fixes them and adds stability improvements.

## Core Value

Downloads must work reliably — users paste a URL, it downloads. No cryptic errors, no broken version detection, no temp file warnings.

## Requirements

### Validated

- ✓ User can paste URL and download video — existing
- ✓ User can choose quality preset (best, 1080p, 720p, audio) — existing
- ✓ User can see download progress in queue — existing
- ✓ User can change download folder — existing
- ✓ User can configure parallel downloads (1-5) — existing
- ✓ User gets notifications on completion — existing
- ✓ App bundles as single Windows executable — existing

### Active

- [ ] Fix Errno 22: Invalid argument when getting video info
- [ ] Fix yt-dlp version detection showing "Not installed"
- [ ] Fix PyInstaller temp directory cleanup warning (MEI folder)
- [ ] Add browser cookie import for age-restricted/login-required videos
- [ ] Improve error messages — translate yt-dlp errors to user-friendly text
- [ ] Add proper logging for debugging future issues

### Out of Scope

- New features beyond bug fixes — focus on stability first
- Linux/macOS support — Windows only for now
- Auto-update mechanism — manual updates acceptable

## Context

**Current bugs:**
1. Errno 22 appears when trying to get video info — possibly path or encoding issue on Windows
2. yt-dlp version check returns "Not installed" even when working — version detection broken
3. PyInstaller shows "Failed to remove temporary directory" on exit — MEI cleanup issue
4. yt-dlp cookie errors show raw wiki links — need user-friendly cookie import

**Codebase state:**
- Clean layered architecture (UI → Core → Utils)
- PyQt6 signals/slots for communication
- QThreadPool for background downloads
- ConfigManager singleton for settings
- No logging currently — console output only

## Constraints

- **Stack**: Python 3.12+, PyQt6, yt-dlp — existing stack, no changes
- **Platform**: Windows 10+ primary target
- **Distribution**: PyInstaller single-file executable

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Add cookie import (not just friendly messages) | Users need to access age-restricted content | — Pending |
| Add logging system | Need visibility into errors for debugging | — Pending |

---
*Last updated: 2026-02-01 after initialization*

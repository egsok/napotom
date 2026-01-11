# Mac Version Design

## Overview

Port Video Downloader 2 to macOS with minimal changes. The app uses cross-platform stack (Python + PyQt6 + yt-dlp), so most code works as-is.

## Approach

Separate branch (`mac`) with independent development. No changes to Windows version.

## Changes Required

| Component | Windows | Mac | Effort |
|-----------|---------|-----|--------|
| GUI (PyQt6) | ✓ | ✓ no changes | 0 |
| Downloader (yt-dlp) | ✓ | ✓ no changes | 0 |
| Queue, config | ✓ | ✓ no changes | 0 |
| Notifications | win10toast | pync | ~10 lines |
| Icon | .ico | .icns | convert |
| Build | PyInstaller .exe | PyInstaller .app | new spec |
| CI/CD | none | GitHub Actions | new workflow |

## Notifications (src/utils/notifications.py)

Replace `win10toast` with `pync` for native macOS Notification Center:

```python
import pync

class NotificationManager:
    def show(self, title: str, message: str, sound: bool = True):
        try:
            pync.notify(message, title=title, sound='default' if sound else None)
        except Exception:
            pass  # notifications not critical
```

Key differences:
- No custom icons in notifications (macOS limitation)
- Sound via `sound='default'` parameter
- No separate `playsound` dependency needed

## Build Configuration (build_mac.spec)

```python
a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    datas=[('assets', 'assets')],
    hiddenimports=[
        'yt_dlp', 'pync',
        'ui', 'ui.main_window', 'ui.settings_dialog', 'ui.styles',
        'ui.widgets', 'ui.widgets.queue_item_widget',
        'core', 'core.downloader', 'core.queue', 'core.updater',
        'utils', 'utils.config', 'utils.notifications',
    ],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name='VideoDownloader2',
    console=False,
)

coll = COLLECT(exe, a.binaries, a.datas, name='VideoDownloader2')

app = BUNDLE(
    coll,
    name='VideoDownloader2.app',
    icon='assets/icon.icns',
    bundle_identifier='com.egsok.videodownloader2',
    version='1.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
    },
)
```

## GitHub Actions (.github/workflows/build-mac.yml)

```yaml
name: Build macOS App

on:
  push:
    branches: [mac]
  workflow_dispatch:

jobs:
  build:
    runs-on: macos-latest
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install pyqt6 yt-dlp pync pyinstaller
      
      - name: Build app
        run: pyinstaller build_mac.spec --noconfirm
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: VideoDownloader2-macOS
          path: dist/VideoDownloader2.app
```

## Dependencies (requirements.txt for Mac)

```
PyQt6
yt-dlp
pync
pyinstaller
```

## Implementation Tasks

1. Create branch `mac` from `main`
2. Replace `src/utils/notifications.py` with pync version
3. Convert `assets/icon.ico` to `assets/icon.icns`
4. Create `build_mac.spec`
5. Create `.github/workflows/build-mac.yml`
6. Update `requirements.txt` (pync instead of win10toast, remove playsound)
7. Test on Mac manually

## Complexity

Low. ~1-2 hours of work. Most code remains unchanged.

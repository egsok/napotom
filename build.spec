# -*- mode: python ; coding: utf-8 -*-
import sys

block_cipher = None

ffmpeg_bin = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'
ffprobe_bin = 'ffprobe.exe' if sys.platform == 'win32' else 'ffprobe'

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[
        (ffmpeg_bin, '.'),
        (ffprobe_bin, '.'),
    ],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'yt_dlp',
        'win10toast',
        'ui',
        'ui.main_window',
        'ui.settings_dialog',
        'ui.styles',
        'ui.widgets',
        'ui.widgets.queue_item_widget',
        'core',
        'core.downloader',
        'core.queue',
        'core.updater',
        'utils',
        'utils.config',
        'utils.notifications',
        'utils.helpers',
        'utils.logger',
        'utils.i18n',
        'utils.translations',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VideoDownloader2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    # BUG-03: Let OS handle MEI temp cleanup (avoids "Failed to remove" warnings)
    # Setting to None is the recommended approach - OS cleans up on reboot
    runtime_tmpdir=None,
    # No console window - MEI warnings aren't user-visible anyway
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

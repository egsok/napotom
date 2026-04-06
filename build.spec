# -*- mode: python ; coding: utf-8 -*-
import os
import sys

import yt_dlp

block_cipher = None

ffmpeg_bin = 'ffmpeg.exe' if sys.platform == 'win32' else 'ffmpeg'
ffprobe_bin = 'ffprobe.exe' if sys.platform == 'win32' else 'ffprobe'

# yt-dlp JS solver files needed for YouTube challenge solving
yt_dlp_dir = os.path.dirname(yt_dlp.__file__)
jsc_vendor_dir = os.path.join(yt_dlp_dir, 'extractor', 'youtube', 'jsc', '_builtin', 'vendor')

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[
        (ffmpeg_bin, '.'),
        (ffprobe_bin, '.'),
    ],
    datas=[
        ('assets', 'assets'),
        (jsc_vendor_dir, os.path.join('yt_dlp', 'extractor', 'youtube', 'jsc', '_builtin', 'vendor')),
    ],
    hiddenimports=[
        'yt_dlp',
        'yt_dlp.extractor.youtube',
        'yt_dlp.extractor.youtube.pot',
        'yt_dlp.extractor.youtube.pot._builtin',
        'yt_dlp.extractor.youtube.pot._builtin.memory_cache',
        'yt_dlp.extractor.youtube.pot._builtin.webpo_cachespec',
        'yt_dlp.extractor.youtube.jsc',
        'yt_dlp.extractor.youtube.jsc._builtin',
        'yt_dlp.extractor.youtube.jsc._builtin.bun',
        'yt_dlp.extractor.youtube.jsc._builtin.deno',
        'yt_dlp.extractor.youtube.jsc._builtin.ejs',
        'yt_dlp.extractor.youtube.jsc._builtin.node',
        'yt_dlp.extractor.youtube.jsc._builtin.quickjs',
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

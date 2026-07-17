# -*- mode: python ; coding: utf-8 -*-
import os

import yt_dlp

block_cipher = None

# yt-dlp JS solver files needed for YouTube challenge solving
yt_dlp_dir = os.path.dirname(yt_dlp.__file__)
jsc_vendor_dir = os.path.join(yt_dlp_dir, 'extractor', 'youtube', 'jsc', '_builtin', 'vendor')

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[
        ('bin/ffmpeg', '.'),
        ('bin/ffprobe', '.'),
        ('bin/node', '.'),
    ],
    datas=[
        ('assets', 'assets'),
        (jsc_vendor_dir, os.path.join('yt_dlp', 'extractor', 'youtube', 'jsc', '_builtin', 'vendor')),
        # Bundled yt-dlp version metadata for stale-override cleanup.
        # Must be a neutral dir (NOT yt_dlp/) so it doesn't shadow the archived package.
        (os.path.join(yt_dlp_dir, 'version.py'), '_bundled_meta'),
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
        'pync',
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
    exclude_binaries=True,
    name='VideoDownloader2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='VideoDownloader2',
)

app = BUNDLE(
    coll,
    name='VideoDownloader2.app',
    icon='assets/icon.icns',
    bundle_identifier='com.egsok.videodownloader2',
    version='1.5.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.5.0',
    },
)

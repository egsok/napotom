# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=['src'],
    binaries=[
        ('bin/ffmpeg', '.'),
        ('bin/ffprobe', '.'),
    ],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'yt_dlp',
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
    version='1.0.0',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
    },
)

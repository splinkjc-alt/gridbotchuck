# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../../main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../../config', 'config'),
        ('../../strategies', 'strategies'),
        ('../../web', 'web'),
        ('../../setup_wizard', 'setup_wizard'),
    ],
    hiddenimports=[
        'ccxt',
        'aiosqlite',
        'apprise',
        'pandas',
        'numpy',
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
    [],
    exclude_binaries=True,
    name='GridBotChuck',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='../../desktop/assets/icon.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GridBotChuck',
)

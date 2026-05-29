# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for XENONnT Event Viewer."""

import glob
import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

_PROJ = SPECPATH

block_cipher = None

# Collect matplotlib data
mpl_data = collect_data_files("matplotlib", subdir="mpl-data")
bundle_data = []
for pattern in (
    os.path.join(_PROJ, "scripts", "output", "*.npz"),
    os.path.join(_PROJ, "dali_probe", "*.npz"),
):
    for path in sorted(glob.glob(pattern)):
        bundle_data.append((path, "."))

# Collect hidden imports
hiddenimports = [
    # PySide6
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtNetwork",
    # matplotlib backends
    "matplotlib.backends.backend_qtagg",
    "matplotlib.backends.backend_pdf",
    "matplotlib.backends.backend_agg",
    # numpy (collect all submodules for numpy 2.x compat)
    *collect_submodules("numpy"),
]

a = Analysis(
    [os.path.join(_PROJ, "run_app.py")],
    pathex=[_PROJ],
    binaries=[],
    datas=mpl_data + bundle_data,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide2",
        "wx",
        "IPython",
        "jupyter",
        "notebook",
        "scipy",
        "pandas",
    ],
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
    name="XENONnT-EventViewer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app bundle for double-click launch
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="XENONnT-EventViewer.app",
        icon=None,
        bundle_identifier="org.xenon.eventviewer",
        info_plist={
            "NSHighResolutionCapable": True,
            "CFBundleName": "XENONnT Event Viewer",
            "CFBundleShortVersionString": "2.0.6",
            "CFBundleVersion": "2.0.6",
            "CFBundleInfoDictionaryVersion": "6.0",
            "CFBundlePackageType": "APPL",
            "LSEnvironment": {
                "LC_ALL": "en_US.UTF-8",
            },
        },
    )

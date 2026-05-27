# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for XENONnT Event Viewer."""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

_PROJ = SPECPATH

block_cipher = None

# Collect matplotlib data
mpl_data = collect_data_files("matplotlib", subdir="mpl-data")

# Collect hidden imports
hiddenimports = [
    # PySide2
    "PySide2.QtCore",
    "PySide2.QtGui",
    "PySide2.QtWidgets",
    "PySide2.QtNetwork",
    # matplotlib backends
    "matplotlib.backends.backend_qt5agg",
    # numpy
    "numpy.core._methods",
    "numpy.lib.format",
    # strax
    "strax",
]

a = Analysis(
    [os.path.join(_PROJ, "run_app.py")],
    pathex=[_PROJ],
    binaries=[],
    datas=mpl_data,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "PyQt5",
        "PyQt6",
        "PySide6",
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

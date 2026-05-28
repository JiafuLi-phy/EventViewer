#!/bin/bash
# Build standalone executables for XENONnT Event Viewer
#
# Prerequisites:
#   pip install pyinstaller
#   pip install pyside6 matplotlib numpy strax
#
# Output:
#   dist/linux/XENONnT-EventViewer       (Linux)
#   dist/windows/XENONnT-EventViewer.exe (Windows, cross-compile)
#   dist/mac/XENONnT-EventViewer.app     (macOS, built on Mac)

set -e

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"

PLATFORM="${1:-linux}"

case "$PLATFORM" in
    linux)
        echo "=== Building Linux executable ==="
        pyinstaller EventViewer.spec \
            --distpath dist/linux \
            --workpath /tmp/pyinstaller_build_linux \
            --clean
        echo ""
        echo "Done: dist/linux/XENONnT-EventViewer"
        ls -lh dist/linux/XENONnT-EventViewer
        ;;

    windows)
        echo "=== Building Windows executable (cross-compile) ==="
        echo "Requires: wine + Python for Windows, or build on Windows directly."
        echo "On Windows, run:"
        echo "  pyinstaller EventViewer.spec --distpath dist\\windows --workpath %TEMP%\\pyinstaller_build_win"
        ;;

    mac)
        echo "=== Building macOS app (ARM64 native) ==="
        pyinstaller \
            --onedir --windowed \
            --name "XENONnT-EventViewer" \
            --add-data "scripts/output/events_run_023756.npz:." \
            --add-data "dali_probe/events_run_043864_real_peaks_200ev.npz:." \
            --hidden-import PySide6.QtCore \
            --hidden-import PySide6.QtGui \
            --hidden-import PySide6.QtWidgets \
            --hidden-import matplotlib.backends.backend_qtagg \
            --hidden-import matplotlib.backends.backend_pdf \
            --hidden-import matplotlib.backends.backend_agg \
            --collect-submodules numpy \
            --collect-data matplotlib \
            --exclude-module tkinter \
            --exclude-module PyQt5 \
            --exclude-module scipy \
            --exclude-module pandas \
            --distpath dist \
            --workpath /tmp/pyinstaller_mac \
            run_app.py
        echo ""
        echo "=== Creating DMG ==="
        mkdir -p pkg/XENONnT-EventViewer-macos
        cp -R dist/XENONnT-EventViewer.app pkg/XENONnT-EventViewer-macos/
        cp scripts/output/events_run_023756.npz pkg/XENONnT-EventViewer-macos/ 2>/dev/null || true
        cp dali_probe/events_run_043864_real_peaks_200ev.npz pkg/XENONnT-EventViewer-macos/ 2>/dev/null || true
        cp README.md pkg/XENONnT-EventViewer-macos/ 2>/dev/null || true
        hdiutil create -volname "XENONnT-EventViewer" \
            -srcfolder pkg/XENONnT-EventViewer-macos \
            -ov -format UDZO \
            pkg/XENONnT-EventViewer-macos-arm64.dmg
        echo ""
        echo "Done: pkg/XENONnT-EventViewer-macos-arm64.dmg"
        ls -lh pkg/XENONnT-EventViewer-macos-arm64.dmg
        rm -rf pkg/XENONnT-EventViewer-macos
        ;;
esac

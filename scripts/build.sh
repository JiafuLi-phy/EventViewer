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
        echo "=== Building macOS app ==="
        echo "On macOS, run:"
        echo "  pyinstaller EventViewer.spec --distpath dist/mac --workpath /tmp/pyinstaller_build_mac"
        ;;
esac

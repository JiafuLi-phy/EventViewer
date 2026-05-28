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

copy_bundles() {
    local dest="$1"
    mkdir -p "$dest"
    for bundle in scripts/output/*.npz dali_probe/*.npz; do
        if [ -f "$bundle" ]; then
            cp "$bundle" "$dest/"
        fi
    done
}

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
        pyinstaller EventViewer.spec \
            --distpath dist \
            --workpath /tmp/pyinstaller_mac \
            --clean
        echo ""
        echo "=== Creating DMG ==="
        mkdir -p pkg/XENONnT-EventViewer-macos
        cp -R dist/XENONnT-EventViewer.app pkg/XENONnT-EventViewer-macos/
        copy_bundles pkg/XENONnT-EventViewer-macos
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

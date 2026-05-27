#!/bin/bash
# Build macOS .app bundle for XENONnT Event Viewer
set -e
cd "$(dirname "$0")/.."

echo "=== Cleaning ==="
rm -rf dist/XENONnT-EventViewer dist/XENONnT-EventViewer.app

echo "=== Building ==="
~/Library/Python/3.9/bin/pyinstaller \
  --onedir \
  --windowed \
  --name XENONnT-EventViewer \
  --add-data "scripts/output/events_run_023756.npz:." \
  --hidden-import PySide6.QtCore \
  --hidden-import PySide6.QtGui \
  --hidden-import PySide6.QtWidgets \
  --hidden-import matplotlib.backends.backend_qtagg \
  --collect-submodules numpy \
  --collect-data matplotlib \
  --exclude-module tkinter \
  --exclude-module PyQt5 \
  --exclude-module scipy \
  --exclude-module pandas \
  --distpath dist \
  --workpath /tmp/pyinstaller_mac \
  run_app.py

echo "=== Deploying ==="
rm -rf "/Applications/XENONnT-EventViewer.app"
cp -R dist/XENONnT-EventViewer.app /Applications/
xattr -cr "/Applications/XENONnT-EventViewer.app"

echo "=== Done ==="
ls -ld "/Applications/XENONnT-EventViewer.app"
echo "Run: open /Applications/XENONnT-EventViewer.app"

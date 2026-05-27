#!/usr/bin/env python3
"""Launch the XENONnT Event Viewer desktop application.

Usage::

    XENONnT-EventViewer                                    # GUI, File→Open
    XENONnT-EventViewer events.npz                         # open a bundle
    XENONnT-EventViewer --npz /path/to/events.npz          # same
"""

import argparse
import os
import sys

# ── resolve paths (PyInstaller vs source) ──
if getattr(sys, "frozen", False):
    _APP_DIR = os.path.dirname(sys.executable)
else:
    _APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

from event_viewer_app.qt_compat import QApplication
from event_viewer_app.qt_compat import Qt


def main():
    parser = argparse.ArgumentParser(description="XENONnT Event Viewer")
    parser.add_argument("npz", nargs="?", help=".npz event bundle file or directory")
    parser.add_argument("--npz", dest="npz_opt", help="Open a .npz event bundle file or directory")
    parser.add_argument("--bundle", dest="bundle_opt", help="Alias for --npz")
    args = parser.parse_args()

    # High-DPI support
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("XENONnT Event Viewer")
    app.setOrganizationName("XENON")

    from event_viewer_app.main_window import MainWindow

    window = MainWindow()
    window.show()

    # ── auto-detect sample bundle ──
    npz_path = args.npz or args.npz_opt or args.bundle_opt
    if not npz_path:
        # Look for *.npz next to the executable / in cwd
        candidates = []
        for d in (_APP_DIR, os.getcwd()):
            try:
                for f in sorted(os.listdir(d)):
                    if f.endswith(".npz"):
                        candidates.append(os.path.join(d, f))
                        break
            except OSError:
                pass
        if candidates:
            npz_path = candidates[0]

    if npz_path:
        if os.path.isfile(npz_path):
            n = window._dm.open_npz_bundle(npz_path)
        elif os.path.isdir(npz_path):
            n = window._dm.open_npz_directory(npz_path)
        else:
            print(f"Path not found: {npz_path}")
            n = 0
        if n:
            window._browser._on_data_loaded(n, f"Data: {npz_path}")

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

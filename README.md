# XENONnT Event Viewer

Cross-platform desktop application for browsing XENONnT event waveforms, PMT hit patterns, and signal properties.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

## Download

Go to [Releases](https://github.com/JiafuLi-phy/EventViewer/releases) and download the package for your platform:

| Platform | File | 
|---|---|
| **Linux** (x86_64) | `XENONnT-EventViewer-linux.tar.gz` |
| **Windows** (x86_64) | `XENONnT-EventViewer-windows.zip` |
| **macOS** (Apple Silicon) | `XENONnT-EventViewer-macos-arm64.tar.gz` |
| **macOS** (Intel) | `XENONnT-EventViewer-macos-x64.tar.gz` |

## Quick Start

1. Download and extract the package for your platform
2. Run the executable (no installation required):
   - **Linux**: `./XENONnT-EventViewer`
   - **Windows**: Double-click `XENONnT-EventViewer.exe`
   - **macOS**: `./XENONnT-EventViewer` (may need `xattr -cr` first)
3. **File → Open Event Bundle** (Ctrl+O) to load a `.npz` file
4. Browse events in the left panel, click to view waveforms

A sample bundle with 50 events from run 023756 is included in each package (`events_run_023756.npz`).

## Keyboard Shortcuts

| Key | Action |
|---|---|
| `Ctrl+O` | Open event bundle (.npz) |
| `Ctrl+R` | Open strax run directly |
| `Ctrl+S` | Export current event as PDF |
| `↑` / `↓` | Previous / Next event |

## Features

- Browse events by event number, S1/S2 area filters
- Interactive zoom/pan on waveform panels (matplotlib toolbar)
- **Main S1 / S2** — zoomed waveform with area, width, amplitude annotations
- **PMT hit patterns** — top/bottom arrays for S1, S2, and full event (linear plasma colormap)
- **Full event waveform** — linear and log-scale views
- Export to PDF / PNG

## Building from Source

### Prerequisites

- Python 3.11+ 
- Git

### All platforms

```bash
# 1. Clone
git clone https://github.com/JiafuLi-phy/EventViewer.git
cd EventViewer

# 2. Install dependencies
pip install pyside6 matplotlib numpy pyinstaller
# Optional: pip install strax (for direct run access)

# 3. Build
pyinstaller EventViewer.spec

# 4. Output
# Linux/macOS: dist/XENONnT-EventViewer
# Windows:     dist\XENONnT-EventViewer.exe
```

### Platform-specific notes

**Linux**: If the binary fails to start, install system dependencies:
```bash
sudo apt-get install libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0 \
  libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-xinerama0 \
  libxcb-xfixes0 libegl1 libgl1
```

**macOS**: If Gatekeeper blocks the app, run:
```bash
xattr -cr dist/XENONnT-EventViewer
```

**Windows**: Build on Windows directly (PyInstaller cannot cross-compile to Windows from Linux/macOS).

### Package for distribution

```bash
# Linux
mkdir -p pkg/XENONnT-EventViewer-linux
cp dist/XENONnT-EventViewer pkg/XENONnT-EventViewer-linux/
cp scripts/output/events_run_023756.npz pkg/XENONnT-EventViewer-linux/
cd pkg && tar czf XENONnT-EventViewer-linux.tar.gz XENONnT-EventViewer-linux/

# Windows (PowerShell)
New-Item -ItemType Directory -Path pkg\XENONnT-EventViewer-windows -Force
Copy-Item dist\XENONnT-EventViewer.exe pkg\XENONnT-EventViewer-windows\
Copy-Item scripts\output\events_run_023756.npz pkg\XENONnT-EventViewer-windows\
Compress-Archive -Path pkg\XENONnT-EventViewer-windows\* -DestinationPath pkg\XENONnT-EventViewer-windows.zip

# macOS
mkdir -p pkg/XENONnT-EventViewer-macos
cp dist/XENONnT-EventViewer pkg/XENONnT-EventViewer-macos/
cp scripts/output/events_run_023756.npz pkg/XENONnT-EventViewer-macos/
cd pkg && tar czf XENONnT-EventViewer-macos.tar.gz XENONnT-EventViewer-macos/
```

## Data Formats

### Pre-extracted `.npz` bundle (recommended)

```bash
python scripts/extract_event_bundle.py --run 023756 --n 50 --s1-min 1000 --s2-min 100000
# Output: scripts/output/events_run_023756.npz
```

Open in the viewer: **File → Open Event Bundle**.

### Direct strax run access (requires data access)

```bash
python run_app.py --run 023756
```

## Creating a Release

1. Build on each target platform (see Building from Source)
2. Package each build (see Package for distribution)
3. Go to [Releases](https://github.com/JiafuLi-phy/EventViewer/releases) → "Draft a new release"
4. Upload all platform packages
5. Publish

## License

MIT

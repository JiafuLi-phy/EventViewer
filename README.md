# XENONnT Event Viewer

Cross-platform desktop application for browsing XENONnT event waveforms, PMT hit patterns, and signal properties.

![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Download & Install

Go to [Releases](https://github.com/JiafuLi-phy/EventViewer/releases) and download the package for your platform:

| Platform | File | Instructions |
|---|---|---|
| **Linux** | `XENONnT-EventViewer-linux.tar.gz` | Extract → double-click `XENONnT-EventViewer` |
| **Windows** | `XENONnT-EventViewer-windows.zip` | Extract → double-click `XENONnT-EventViewer.exe` |
| **macOS** | `XENONnT-EventViewer-macos.tar.gz` | Extract → double-click `XENONnT-EventViewer` |

No installation required — just extract and run.

## Quick Start

1. Download and extract the package for your platform
2. Run the executable
3. **File → Open Event Bundle** (Ctrl+O) → select a `.npz` file
4. Browse events in the left panel, click to view waveforms on the right

A sample bundle with 50 events from run 023756 is included in the package (`events_run_023756.npz`).

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
- **PMT hit patterns** — top/bottom arrays for S1, S2, and full event (linear color scale)
- **Full event waveform** — linear and log-scale views
- Export to PDF / PNG

## Data Formats

The viewer supports two data sources:

### 1. Pre-extracted `.npz` bundle (recommended for offline use)

```bash
# Extract a bundle from any strax run:
python scripts/extract_event_bundle.py --run 023756 --n 50 --s1-min 1000 --s2-min 100000
# Output: scripts/output/events_run_023756.npz
```

Then open in the viewer: **File → Open Event Bundle**.

### 2. Direct strax run access

On a system with access to processed XENONnT data:
```bash
# File → Open Strax Run → enter "023756"
# or from command line:
python run_app.py --run 023756
```

## Building from Source

```bash
# Install dependencies
pip install pyside6 matplotlib numpy strax pyinstaller

# Build executable
bash scripts/build.sh linux

# Run
./dist/linux/XENONnT-EventViewer
```

For Windows / macOS, build on the target platform:
```bash
# Windows
pyinstaller EventViewer.spec --distpath dist\windows

# macOS
pyinstaller EventViewer.spec --distpath dist/macos
```

## Creating a Release (maintainers)

1. Tag a version: `git tag v1.0.0 && git push --tags`
2. GitHub Actions builds all platforms automatically
3. Download artifacts or publish the draft release

## License

MIT

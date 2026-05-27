# XENONnT Event Viewer

Cross-platform desktop application for browsing XENONnT event waveforms and PMT hit patterns.

## Quick Start

1. Download and extract the package for your platform from [Releases](https://github.com/JiafuLi-phy/EventViewer/releases)
2. Run the executable:
   - **macOS**: Open `.dmg` → drag `XENONnT-EventViewer.app` to Applications → double-click
   - **Windows**: Unzip → double-click `.exe`
   - **Linux**: `tar xzf` → `./XENONnT-EventViewer`
3. **File → Open Event Bundle** (Ctrl+O) to load a `.npz` file
4. Browse events in the left panel, click to view waveforms

A sample bundle with 50 events from run 023756 is included (`events_run_023756.npz`).

## Architecture

```
run_app.py                     # Entry point, auto-loads bundled NPZ
├── event_viewer_app/          # Qt GUI layer
│   ├── main_window.py         # MainWindow + PeakListWidget
│   ├── event_browser.py       # Event list, search, filters
│   ├── event_canvas.py        # Matplotlib canvas + mouse/keyboard events
│   ├── data_manager.py        # Data loading (NPZ bundle / strax)
│   └── qt_compat.py           # PySide6 / PySide2 compatibility
├── event_plotter/             # Plotting engine
│   ├── plotter.py             # Waveform + PMT hit pattern rendering
│   ├── io.py                  # Strax/NPZ data I/O, PMT geometry
│   └── style.py               # Nature-journal color palette + fonts
└── scripts/                   # CLI tools
    ├── extract_event_bundle.py # Extract events from strax into portable .npz
    ├── plot_events.py          # Batch plot events to PDF/PNG
    └── build_mac.sh            # macOS PyInstaller build script
```

## UI Layout

```
┌──────────────┬─────────────────────────────────────┐
│  Event List   │  Matplotlib Toolbar (zoom/pan/home) │
│  (50 events)  │                                     │
│               │  ┌─────────────────────────────────┐ │
│  Filters      │  │  Event Waveform                  │ │
│  S1/S2 min    │  │  (all peaks, color-coded type)   │ │
│               │  │                                  │ │
│  Search       │  ├────────────────┬────────────────┤ │
│               │  │  Top PMT       │  Bottom PMT    │ │
│  Peak List    │  │  Hit Pattern   │  Hit Pattern   │ │
│  Type Area    │  └────────────────┴────────────────┘ │
│  Width Rise   │                                     │
│  *main S1/S2  │                                     │
└──────────────┴─────────────────────────────────────┘
```

## Data Flow

```
NPZ file → DataManager.open_npz_bundle()
         → events[], peaks_list[], eac_list[], pmt_positions, to_pe
         → EventBrowser displays event list
         → User clicks event → MainWindow._on_event_selected()
           → plot_event_full() → rendered to EventCanvas

Peak click → EventCanvas hit-test → peak_clicked Signal
           → MainWindow._on_peak_clicked()
           → plot_peak_zoom() → 3-layer waveform + PMT patterns
```

## Features

| Feature | How | Location |
|---------|-----|----------|
| Event navigation | ← → arrow keys | `main_window.py:_setup_shortcuts` |
| Event waveform | Full event waveform + Top/Bot PMT patterns | `plotter.py:plot_event_full` |
| Peak list | Table: Type, Area, Width, Rise, Time | `main_window.py:PeakListWidget` |
| Main S1/S2 markers | Bold `*` in peak list | `PeakListWidget.populate()` |
| Click peak → zoom | Click waveform or list → 3-panel zoom view | `plotter.py:plot_peak_zoom` |
| 3-layer waveform | Top PMT (violet) + Bottom (orange) + Total (blue/green) in overview and peak zoom | `plotter.py` |
| Legend toggle | Click legend text to show/hide layers | `event_canvas.py:_on_click` |
| Scroll zoom | Mouse wheel on waveform and PMT panels | `event_canvas.py:_on_scroll` |
| Toolbar | Zoom rect / Pan / Home / Save | matplotlib NavigationToolbar2QT |
| PMT ID hover | Hover over PMT dot shows channel ID | `event_canvas.py:_on_hover` |
| Escape | Return to overview from peak zoom | `main_window.py:_clear_peak_selection` |
| Export PDF/PNG | Ctrl+S / File menu | `main_window.py:_on_export_*` |
| Open other NPZ | Ctrl+O / File → Open Event Bundle | `main_window.py:_on_open_bundle` |

## Peak Zoom Layout

```
┌───────────────────────────────────────┐
│  Peak Waveform                        │
│  ── Top PMT  (violet, area*frac_top)  │  ← click legend to toggle
│  ── Bot PMT  (orange, area*(1-frac))  │
│  ── Total    (blue/S1 or green/S2)    │
├──────────────────┬────────────────────┤
│  Top PMT         │  Bottom PMT        │
│  Hit Pattern     │  Hit Pattern       │  ← scaled to peak area
└──────────────────┴────────────────────┘
```

## Data Formats

### NPZ Bundle (recommended)

Pre-extracted portable format. Contains events, peaks, PMT positions, gains, and optional EAC data.

```bash
python scripts/extract_event_bundle.py --run 023756 --n 50 --s1-min 1000 --s2-min 100000
# Output: scripts/output/events_run_023756.npz
```

### Direct Strax Access (requires cluster data)

```bash
python run_app.py
# File → Open Strax Run → enter run ID
```

For real XENONnT data on Midway3, the viewer now tries the recommended
`cutax.contexts.xenonnt_offline(xedocs_version="global_v20")` context first
and falls back to direct strax chunk loading from Midway-accessible processed
directories. It requests `peaks` first so real peak waveforms and
`area_per_channel` are used when available; if that is unavailable it falls
back to `peak_basics`, which displays model pulses from peak metadata.

To build a portable bundle with true peak-level data when the source run has
it:

```bash
python scripts/extract_event_bundle.py --run 023756 --peak-data-type peaks
```

To also include raw-record windows for true event-level top/bottom/total
waveforms:

```bash
python scripts/extract_event_bundle.py --run 023756 --peak-data-type peaks --include-raw-records
```

On DALI, where TPC `raw_records` are mounted under
`/dali/lgrandi/xenonnt/raw`, a quick smoke test can be run with:

```bash
source /cvmfs/xenon.opensciencegrid.org/releases/nT/el7.2025.07.2/setup.sh
python scripts/raw_records_probe.py --run 043572 --window-us 500 --max-chunks 1
```

This writes a small `.npz` plus `.png` waveform probe without loading a full
run.

If a bundle contains only `peak_basics`, waveforms are explicitly model-based
and single-peak PMT patterns are estimated from event-level S1/S2
per-channel maps. If `peaks.area_per_channel` is present, the single-peak PMT
pattern is the true peak distribution.

## Build & Distribution

### macOS

```bash
bash scripts/build_mac.sh
# Output: dist/XENONnT-EventViewer.app → /Applications

# Create DMG:
mkdir -p pkg/XENONnT-EventViewer-macos
cp -R dist/XENONnT-EventViewer.app pkg/XENONnT-EventViewer-macos/
cp scripts/output/events_run_023756.npz pkg/XENONnT-EventViewer-macos/
hdiutil create -volname "XENONnT-EventViewer" \
  -srcfolder pkg/XENONnT-EventViewer-macos \
  -ov -format UDZO XENONnT-EventViewer-macos-arm64.dmg
```

### CI (GitHub Actions)

Push a `v*` tag to trigger multi-platform builds:

| Platform | Artifact |
|----------|----------|
| macOS ARM64 | `.dmg` |
| macOS x64 | `.dmg` |
| Windows x64 | `.zip` (`.exe`) |
| Linux x64 | `.tar.gz` |

CI config: `.github/workflows/build.yml`

## Dependencies

```
Python 3.9+
├── numpy >= 1.21        # Array operations
├── matplotlib >= 3.5     # Scientific plotting
├── PySide6 >= 6.3        # Qt GUI toolkit
├── strax >= 0.17 (optional)   # Direct XENON data access
└── straxen >= 0.17 (optional) # PMT geometry from XENON context
```

Install for development:
```bash
pip install -e .
pip install -e ".[strax]"   # with strax support
pip install -e ".[build]"   # with PyInstaller
```

## Bug Fixes Applied

| Bug | Fix |
|-----|-----|
| PMT dots outside circle | Circle radius computed from actual PMT positions |
| PMT hit patterns blank | EAC data loaded for NPZ mode (not just strax) |
| Event waveform title overlap | Increased GridSpec `hspace`, tight_layout `rect` |
| Edge colored-dot artifacts | `fig.clf()` instead of `fig.clear()` |
| Arrow keys not working | QShortcut with WindowShortcut context |
| .app opens Terminal | `--onedir --windowed` build |
| `no module named strax` | Removed strax from PyInstaller hidden imports |
| Peak zoom PMT pattern wrong scale | Scaled EAC pattern to match individual peak area |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+O | Open Event Bundle |
| Ctrl+R | Open Strax Run |
| Ctrl+S | Export PDF |
| ← | Previous Event |
| → | Next Event |
| Escape | Return to overview |
| o | Zoom mode (toolbar) |
| p | Pan mode (toolbar) |
| h | Home / reset view (toolbar) |
| s | Save figure (toolbar) |

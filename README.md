# XENONnT Event Viewer

Cross-platform desktop application for interactive browsing of XENONnT event waveforms and PMT hit patterns.

## Quick Start

1. Download the package for your platform from [Releases](https://github.com/JiafuLi-phy/EventViewer/releases)
2. **macOS**: Open `.dmg` → drag to Applications → double-click. First launch: right-click → Open.
3. **Windows**: Unzip → double-click `.exe`
4. **Linux**: `tar xzf` → `./XENONnT-EventViewer`
5. App auto-loads bundled sample data. Use **Run Selector** dropdown to switch runs.

## Features

| Feature | How |
|---------|-----|
| Event browsing | Left panel event list, ← → arrow keys |
| Peak list | Sortable table: Type, Area, Width, Rise, Time |
| Main S1/S2 | Bold **Main S1**/**Main S2** in peak list |
| Waveform display | Full event waveform + Top/Bot PMT patterns |
| 3-layer waveform | Top PMT (blue) + Bottom (green) + Total (red) |
| Peak zoom | Click waveform or peak list → 3-panel zoom view |
| Legend toggle | Click legend text to show/hide waveform layers |
| Scroll zoom | Mouse wheel on waveform panels |
| Page zoom | +/- buttons or Ctrl+scroll |
| PMT ID hover | Hover over PMT dot shows channel ID |
| PDF/PNG export | Ctrl+S or toolbar save icon |
| Run Selector | Dropdown to switch between bundled NPZ files |
| Escape | Return to overview from peak zoom |
| Strax loading | Background worker keeps UI responsive while opening runs |

## Architecture

```
run_app.py                     # Entry point
├── event_viewer_app/          # Qt GUI layer (PySide6)
│   ├── main_window.py         # MainWindow + PeakListWidget + Run Selector
│   ├── event_browser.py       # Event list, search, S1/S2 filters
│   ├── event_canvas.py        # Matplotlib canvas + mouse/keyboard events
│   ├── data_manager.py        # Data loading (NPZ bundle / strax)
│   └── qt_compat.py           # PySide6/PySide2 compatibility
├── event_plotter/             # Plotting engine
│   ├── plotter.py             # Waveform + PMT hit pattern rendering
│   ├── io.py                  # Strax/NPZ data I/O, PMT geometry
│   └── style.py               # Color palette, fonts, matplotlib rcParams
└── scripts/                   # CLI tools + build
    ├── extract_event_bundle.py # Extract events from strax into .npz
    ├── plot_events.py          # Batch plot to PDF/PNG
    └── build_mac.sh            # macOS PyInstaller build
```

## Data Flow

```
NPZ file → DataManager.open_npz_bundle()
         → events[], peaks_list[], eac_list[], pmt_positions, to_pe
         → EventBrowser displays event list
         → User clicks event → MainWindow._on_event_selected()
           → plot_event_full() → EventCanvas

Peak click → EventCanvas hit-test → peak_clicked Signal
           → MainWindow._on_peak_clicked()
           → plot_peak_zoom() → 3-layer waveform + PMT patterns
```

## Data Types

| Source | Waveform | PMT Pattern |
|--------|:--------:|:-----------:|
| NPZ (peak_basics) | Model pulse (area+rise+width) | EAC scaled |
| NPZ (real peaks) | Real `data` + `data_top` from DALI | Real `area_per_channel` |

Real peaks bundles are extracted from DALI using `dali_probe/extract_peaks_bundle.py`.

## Dependencies

```
Python 3.9+
├── numpy >= 1.21
├── matplotlib >= 3.5
├── PySide6 >= 6.3
├── strax >= 0.17 (optional)
└── straxen >= 0.17 (optional)
```

## Build & Distribution

### macOS
```bash
bash scripts/build_mac.sh
# Output: dist/XENONnT-EventViewer.app → /Applications
```

### DMG
```bash
mkdir -p pkg && cp -R dist/XENONnT-EventViewer.app pkg/
cp scripts/output/events_run_023756.npz pkg/
hdiutil create -volname "XENONnT-EventViewer" -srcfolder pkg -ov -format UDZO XENONnT-EventViewer-macos-arm64.dmg
```

### CI (GitHub Actions)
Push `v*` tag → multi-platform: macOS .dmg, Windows .zip, Linux .tar.gz

## Key Bug Fixes

| Bug | Fix |
|-----|-----|
| PMT dots outside circle | Circle radius from actual PMT positions |
| PMT patterns blank | EAC loaded for NPZ mode |
| Edge colored-dot artifacts | Full figure+canvas replacement on clear() |
| Waveform ghosting | New Figure + Canvas each render |
| Arrow keys not working | QShortcut with WindowShortcut context |
| .app opens Terminal | --onedir --windowed build |
| PDF export missing module | backend_pdf in PyInstaller hidden imports |
| Toolbar save broken | Update toolbar.canvas after clear() |
| Peak index misalignment | NumericItem + UserRole for original index |

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Ctrl+O | Open Event Bundle |
| Ctrl+S | Export PDF to Desktop |
| ← | Previous Event |
| → | Next Event |
| Escape | Return to overview |

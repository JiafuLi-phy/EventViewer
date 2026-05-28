# Handoff to Codex — Final State

## Current Status

**App**: `/Applications/XENONnT-EventViewer.app` (v2.0.0, working)
**Git**: main branch, pushed to GitHub

## What's Done

### UI & Layout
- 3-row event display: linear waveform + log waveform + PMT patterns
- Figure 18in tall, PMT row 1.4x height
- Legend 16pt, no border, positioned (1.04, 1.10)
- Interactive legend: click layer → show only that layer
- PMT markers 40 (event) / 80 (zoom)
- 4-sided spines on all axes
- Y-axis: Amplitude [PE/μs], X-axis: Time [μs]
- Peak list: Type/Area/Width/Rise/X/Y columns
- Peak sort: Main S1 → Main S2 → S1s → S2s → unknown
- Run Selector dropdown + Browse button
- Log y-scale: symlog, bottom=1e-3, top=15x max peak
- Adaptive linear y-limit from data

### Features
- 3-layer waveform: Top (blue) + Bottom (green) + Total (red)
- Peak click → zoom with per-peak position markers
- PMT pattern click → standalone zoomed window with colorbar
- PMT ID hover (both main and zoomed windows)
- Numeric peak search: area>1000, width<50, etc.
- Event info above peaks: drift time, S2 position
- Export Ctrl+S → Desktop (no dialog)
- Toolbar save button works

### Data Pipeline
- Unified extraction: `dali_probe/extract_bundle.py`
  - Auto-detects DALI/Midway3 server
  - Auto-selects real peaks or peak_basics
  - Always loads CNN positions if available
- 7 bundled runs (all with positions):
  ```bash
  # DALI (real waveforms + positions)
  python extract_bundle.py --batch 043864,044116,044165,044225,044311,044834 --n 30
  # Midway3 (model waveforms + positions)  
  python extract_bundle.py --run 023756 --n 50
  ```

### Rendering Fixes
- Full Figure+Canvas replacement on clear() (ghosting)
- 3-pass drawing: all Top → all Bottom → all Total
- numpy void copy: p.copy() not np.array(p, copy=True)
- ns→μs: /1000 conversion everywhere
- S1/S2 position markers on PMT patterns
- Per-peak CNN positions in peak list X/Y columns
- Event overview always shows S1+S2 markers

## Remaining Issues

### High Priority
- [ ] QScrollArea stability (edge artifacts risk, not fully verified)
- [ ] macOS Gatekeeper warning on first launch
- [ ] Windows/Linux CI build (push v* tag)

### Medium Priority
- [ ] Event overview 3-layer dense/cluttered for many-peak events
- [ ] No loading indicator when switching runs
- [ ] Data source panel is redundant (Run Selector + Browse covers it)
- [ ] Export QFileDialog may not open in PyInstaller .app

### Low Priority
- [ ] print() debug leftovers in scripts/
- [ ] TeX docs need updating (describe new features)
- [ ] Old LaTeX PDFs should be removed from git tracking

## Files Structure

```
EventViewer/
├── event_viewer_app/     # Qt GUI
│   ├── main_window.py    # PeakListWidget, RunSelector, Browse
│   ├── event_browser.py  # Event list, search, filters
│   ├── event_canvas.py   # Canvas + events + PMT zoom
│   ├── data_manager.py   # NPZ/strax loading + positions
│   └── qt_compat.py      # PySide6/2 compat
├── event_plotter/        # Plotting engine
│   ├── plotter.py        # plot_event_full, plot_peak_zoom, markers
│   ├── io.py             # Data I/O
│   └── style.py          # Colors, fonts, spines
├── dali_probe/
│   ├── extract_bundle.py # UNIFIED extraction (DALI+Midway3)
│   ├── extract_peaks_bundle.py  # Legacy DALI extractor
│   ├── extract_with_positions.py # Legacy Midway3 extractor
│   └── events_*_bundle.npz     # 7 NPZ bundles with positions
├── scripts/
│   ├── build_mac.sh      # macOS PyInstaller build
│   └── output/events_run_023756.npz  # Original 50ev bundle
├── docs/                 # LaTeX docs (CN + EN)
├── debug_reports/        # Test suite
└── README.md
```

## Quick Commands

```bash
# Build
bash scripts/build_mac.sh

# Extract data
python dali_probe/extract_bundle.py --run 023756 --n 50    # Midway3
python dali_probe/extract_bundle.py --batch 043864,044116 --n 30  # DALI
```

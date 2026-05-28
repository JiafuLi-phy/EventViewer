# Handoff to Codex — 2026-05-28 Final

## Current State

**App**: `/Applications/XENONnT-EventViewer.app` v2.0.0 — working, deployed  
**Git**: main branch, pushed to GitHub  
**Data**: 7 unified bundles in `dali_probe/` (all with CNN positions)

## Architecture

```
run_app.py → MainWindow(QSplitter)
  ├── Left Panel
  │   ├── Run Selector (QComboBox + Browse)
  │   ├── EventBrowser (list, filter, search)
  │   └── PeakListWidget (search, sort, X/Y)
  └── Right Panel
      └── EventCanvas (full canvas replacement, scroll/click/hover)

Data: NPZ → DataManager → plot_event_full / plot_peak_zoom → EventCanvas
```

## Completed Features

### UI
- [x] 3-row layout: linear waveform + log(symlog) waveform + PMT patterns
- [x] Figure 18in tall, PMT row 1.4x
- [x] Legend 16pt, no border, upper-right (1.04, 1.10)
- [x] Interactive legend: click layer → exclusive show, click again → all
- [x] PMT markers: 40 (event) / 80 (zoom)
- [x] 4-sided spines on all plot panels
- [x] X-axis: Time [μs], Y-axis: Amplitude [PE/μs]
- [x] Log y-scale: symlog, bottom=1e-3, top=15x max peak
- [x] Peak list columns: Type, Area, Width, Rise, X, Y
- [x] Peak sort: Main S1 → Main S2 → S1s → S2s → unknown
- [x] Numeric peak search: area>1000, width<50, etc.
- [x] Run Selector dropdown (auto-scan) + Browse button
- [x] Event info line above peaks: drift time, S2 position

### Rendering
- [x] Full Figure+Canvas replacement on clear() (eliminates ghosting)
- [x] 3-pass drawing: all Top → all Bottom → all Total (z-order)
- [x] numpy void deep copy: p.copy() not np.array(p, copy=True)
- [x] ns→μs: /1000 conversion everywhere
- [x] Total=red (#F44336), Top=blue (#2196F3), Bottom=green (#4CAF50)
- [x] Total alpha 0.30, Top/Bottom alpha 0.08
- [x] Line widths 3x thicker across all paths
- [x] adaptative y-limit from data (tighten_ylim checks collections too)

### Interaction
- [x] Peak click → zoom with per-peak CNN position markers (gold star)
- [x] PMT pattern click → standalone zoomed figure with colorbar
- [x] PMT ID hover (both main and zoomed windows)
- [x] Scroll zoom on waveform panels
- [x] Page zoom (+/- buttons, Ctrl+scroll)
- [x] Arrow keys: ←→ for event navigation
- [x] Escape: return to overview

### Position Markers
- [x] Event overview: S1 green star + S2 red star with labels
- [x] Peak zoom: per-peak gold star with "Pk{id}" label
- [x] All annotations: dark colors + white semi-transparent background
- [x] S1 text positioned below star (no overlap with S2)

### Data Pipeline
- [x] Unified extraction: `dali_probe/extract_bundle.py`
  - Auto-detects DALI vs Midway3 server
  - Auto-selects real peaks or peak_basics
  - Always loads CNN positions if available
  - Single command: `python extract_bundle.py --run ID --n N`
- [x] 7 bundles with positions (023756 model + 6 DALI real-data runs)
- [x] Old NPZ without positions deleted

### Export
- [x] Ctrl+S → PDF to Desktop (no dialog)
- [x] Toolbar save button works (toolbar.canvas updated after clear())
- [x] backend_pdf, backend_agg in PyInstaller hidden imports

### Build
- [x] build_mac.sh: PyInstaller --onedir --windowed
- [x] Info.plist version 2.0.0 (PlistBuddy)
- [x] Old versions cleaned from Desktop and Applications
- [x] App pinned to Dock

## Unresolved Issues

### High
- [ ] QScrollArea edge artifacts (not fully verified — canvas replacement workaround)
- [ ] macOS Gatekeeper "unidentified developer" on first launch
- [ ] Windows/Linux need CI build (push v* tag)

### Medium
- [ ] Event overview 3-layer dense for 50+ peak events
- [ ] No progress/loading indicator when switching runs
- [ ] Data Source panel in sidebar is redundant (Run Selector covers it)
- [ ] Export QFileDialog may not open in PyInstaller .app (macOS z-order)
- [ ] Strax mode on main thread (Codex added StraxLoadWorker but not tested)

### Low
- [ ] print() statements in scripts/ (cosmetic)
- [ ] TeX docs need content update
- [ ] 200ev bundle for 043864 not available with positions

## File Summary

```
dali_probe/events_*_bundle.npz   ← 7 unified bundles (all with CNN positions)
dali_probe/extract_bundle.py     ← OFFICIAL extraction script (DALI+Midway3)
scripts/build_mac.sh             ← macOS build script
scripts/output/events_run_023756.npz  ← Original 50ev bundle
HANDOFF_TO_CODEX.md              ← This file
README.md                        ← Project README
```

## Quick Commands

```bash
# Build macOS app
bash scripts/build_mac.sh

# Extract data (from Midway3)
python dali_probe/extract_bundle.py --run 023756 --n 50

# Extract data (from DALI)
python dali_probe/extract_bundle.py --batch 043864,044116,044165,044225,044311,044834 --n 30
```

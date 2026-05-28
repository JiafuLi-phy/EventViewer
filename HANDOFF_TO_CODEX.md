# Handoff to Codex — Final State 2026-05-28

## Current State

**App**: `/Applications/XENONnT-EventViewer.app` v2.0.0 — working, deployed, Dock pinned  
**Git**: main branch, pushed to GitHub  
**Desktop**: clean (old versions removed)

## Architecture

```
run_app.py → MainWindow(QSplitter)
  ├── Left Panel
  │   ├── Run Selector (QComboBox + Browse button)
  │   ├── EventBrowser (list, filter, search)
  │   └── PeakListWidget (search bar, sort, 7 columns)
  └── Right Panel
      └── EventCanvas (full canvas replacement on clear)
```

## Data Pipeline

### Two official sources:
1. **DALI** — real peaks (data, data_top, area_per_channel) + CNN positions
2. **Midway3** — peak_basics (model pulses) + CNN positions

### Single extraction script:
```bash
python dali_probe/extract_bundle.py --run 023756 --n 50        # Midway3
python dali_probe/extract_bundle.py --run 043864 --n 30        # DALI
python dali_probe/extract_bundle.py --batch 044116,044165 --n 30  # DALI batch
```

### 7 bundled NPZ files in `dali_probe/` (all with CNN positions):
| Run | Events | Waveform | Server |
|-----|--------|:--------:|:------:|
| 023756 | 50 | Model | Midway3 |
| 043864 | 30 | Real | DALI |
| 044116 | 30 | Real | DALI |
| 044165 | 30 | Real | DALI |
| 044225 | 30 | Real | DALI |
| 044311 | 30 | Real | DALI |
| 044834 | 30 | Real | DALI |

## Completed Features (~55 items)

### Layout
- 3-row: linear waveform + symlog waveform + PMT patterns (18in tall, PMT 1.4x height)
- Legend: horizontal 1-row, centered below title, 16pt, no border, wide spacing
- 4-sided spines, Peak list 7 columns, PMT markers 40/80

### Rendering
- 3-layer waveform: Top(blue) + Bottom(green) + Total(red), linewidth 3x
- 3-pass drawing, full canvas replacement (no ghosting)
- ns→μs conversion, adaptive y-limits, symlog with data-driven top
- numpy void deep copy fix

### Interaction
- Peak click → zoom with per-peak position markers
- PMT click → standalone zoomed window with colorbar + hover
- Interactive legend (exclusive layer toggle)
- Scroll zoom, page zoom, arrow key navigation
- Numeric peak search (area>1000, width<50, etc.)

### Position Markers
- Event overview: S1(green star, below) + S2(red star, above) with labels
- Peak zoom: per-peak gold star "Pk{id}"
- All dark colors + white semi-transparent background boxes

### Export & Build
- Ctrl+S → PDF to Desktop, toolbar save works
- build_mac.sh (PyInstaller --onedir --windowed), version 2.0.0
- backend_pdf/backend_agg in hidden imports

## Unresolved

### High (3)
- QScrollArea edge artifacts (workaround: canvas replacement)
- macOS Gatekeeper warning
- Windows/Linux CI build (push v* tag)

### Medium (4)
- 3-layer dense for many-peak events
- No loading indicator
- Redundant Data Source panel
- Export QFileDialog may not open in .app

### Low (3)
- print() statements in scripts/
- TeX docs outdated
- 043864 200ev bundle lost positions during migration

## Quick Commands
```bash
bash scripts/build_mac.sh                    # Build
python dali_probe/extract_bundle.py --run X --n N  # Extract data
```

# Handoff to Codex — 2026-05-28 Final

## App: `/Applications/XENONnT-EventViewer.app` v2.0.0 — working

## Completed (~55 items)

### UI
- 3-row layout: linear + symlog + PMT patterns (18in, PMT 1.4x)
- Legend: horizontal 1-row, centered, 16pt, no border, wide spacing
- 4-sided spines, PMT markers 40/80, all units in μs/PE
- Peak list: Type/Area/Width/Rise/Height/X/Y (7 cols)
- Peak sort: Main S1→Main S2→S1s→S2s→unknown
- Numeric peak search (area>1000, width<50, etc.)
- Run Selector dropdown + Browse button
- Event info line: drift time, S2 position

### Rendering
- 3-layer waveform: Top(blue)+Bottom(green)+Total(red), linewidth 3x
- Full canvas replacement (no ghosting)
- 3-pass drawing (Total always on top)
- ns→μs /1000, adaptive y-limits, symlog top=15x max
- numpy void p.copy() fix

### Interaction
- Peak click → zoom + per-peak CNN position (gold star "Pk{id}")
- PMT pattern click → standalone zoom + colorbar + hover
- Interactive legend (exclusive layer toggle)
- S1/S2 markers: green/red star + label (white bg, S1 below)

### Data
- Unified extraction: `dali_probe/extract_bundle.py` (DALI+Midway3)
- 7 NPZ bundles with CNN positions (023756 model + 6 DALI real-data)

### Build
- build_mac.sh (PyInstaller --onedir --windowed, v2.0.0)
- Export Ctrl+S, toolbar save, backend_pdf/agg

## Unresolved (10 items)

### High
- [ ] **CI broken** — workflow "Startup failure" on tag push. Need YAML debug or manual trigger at https://github.com/JiafuLi-phy/EventViewer/actions/workflows/build.yml
- [ ] macOS Gatekeeper warning on first launch
- [ ] QScrollArea edge artifacts risk

### Medium
- [ ] 3-layer dense for many-peak events
- [ ] No loading progress indicator
- [ ] Data Source panel is redundant
- [ ] Export dialog may not open in .app

### Low
- [ ] print() in scripts/
- [ ] TeX docs outdated
- [ ] 043864 200ev bundle lost positions

## Clean Slate
- Old tags (v1.0.0, v2.0.1-3) deleted from GitHub
- Old NPZ files removed from dali_probe/
- Old app versions removed from computer
- Only `/Applications/XENONnT-EventViewer.app` remains

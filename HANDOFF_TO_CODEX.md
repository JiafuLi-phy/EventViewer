# Handoff to Codex — 2026-05-28

## Completed Changes (today)

### UI / Layout
- [x] Figure height 12→18in, 3-row GridSpec (linear + log + PMT)
- [x] Log-scale event waveform (symlog, bottom=1e-3, below linear)
- [x] PMT marker sizes: event overview 40, peak zoom 80, zoom window 100
- [x] Legend font 16pt, positioned (1.04, 1.10), uses rcParams correctly
- [x] Legend border removed
- [x] Interactive legend: click layer name → show only that layer, click again → show all
- [x] Left panel max width 500, stretch factor 1:3, draggable
- [x] Peak list sort: Main S1 → Main S2 → S1s → S2s → unknown (within group by area)
- [x] Peak list units: ns→μs (Width, Rise, Time)
- [x] Main S1/S2 displayed as bold "Main S1"/"Main S2"
- [x] Run Selector dropdown + Browse button
- [x] Run Selector auto-scans dali_probe/, scripts/output/, ~/Desktop/EventViewer/dali_probe
- [x] Run Selector refreshes on File→Open

### Rendering
- [x] 3-pass drawing: all Top first → all Bottom → all Total (z-order fix)
- [x] Total color = red (#F44336) everywhere (model + real data paths)
- [x] `p.copy()` instead of `np.array(p, copy=True)` for numpy void scalars (shared memory bug)
- [x] `fig.clf()` → full Figure+Canvas replacement (ghosting fix)
- [x] `tighten_ylim` checks both lines and collections (fix_between data)
- [x] y-axis pad_frac 0.05→0.10
- [x] Total alpha 0.55→0.30 (lighter fill)
- [x] Top/Bottom alpha 0.20→0.08 (very faint background)
- [x] Total linewidth 1.5x (boldest)
- [x] 3-layer legend now works for model pulse path (was missing _legend_state)
- [x] x-axis: seconds→μs, correct ns/1000 conversion
- [x] xlabel "Time [μs]" on all waveform axes
- [x] MAX_CLICK_DIST 0.0005s→500μs for μs x-axis

### Features
- [x] PMT pattern click → standalone zoomed figure (larger dots, hover shows PMT ID)
- [x] PMT ID hover on zoomed figure (standalone canvas with motion_notify_event)

### Data
- [x] 023756 (50ev, model) — original bundle
- [x] 043864 (200ev, real peaks, 9MB) — from DALI
- [x] 043864 (30ev, real peaks) — new extraction
- [x] 044116 (20ev + 30ev, real peaks) — new extraction
- [x] 044165 (20ev, real peaks) — new extraction
- [x] 044225 (20ev, real peaks) — new extraction
- [x] 044311 (20ev, real peaks) — new extraction
- [x] 044834 (20ev, real peaks) — new extraction
- [x] DALI batch extraction script (dali_probe/batch_extract.sh)
- [x] Total: 6 runs, 430 events, all with real waveform data

### Build
- [x] Info.plist version 2.0.1 (PlistBuddy injection in build_mac.sh)
- [x] backend_pdf, backend_agg added to PyInstaller hidden imports
- [x] Export Ctrl+S → Desktop (no dialog)
- [x] Toolbar save button fixed (toolbar.canvas updated after clear())
- [x] Old versions cleaned from Desktop and Applications

### Bugs Fixed (today, ~40 commits)
1. numpy void scalar copy bug (shared memory)
2. Total=red missing in real data event overview
3. Interactive legend missing for model pulse path
4. ns→μs wrong conversion (/1e6→/1000)
5. MAX_CLICK_DIST not updated for μs units
6. PMT marker too large for taller figure
7. Syntax errors from inline comments in replace_all
8. Legend fontsize overridden by explicit fontsize parameter

## Unresolved Issues

### High Priority
- [ ] QScrollArea stability not fully verified — colored edge artifacts risk
- [ ] Strax mode UI freeze (synchronous loading, no progress bar)
- [ ] Run Selector in .app only finds bundled NPZ, not external files
- [ ] macOS Gatekeeper "unidentified developer" warning on first launch

### Medium Priority
- [ ] Event overview 3-layer is dense/cluttered for runs with many peaks
- [ ] Peak zoom PMT pattern shows scaled EAC for model data (no real per-peak apc)
- [ ] No loading indicator when switching runs/events
- [ ] Export QFileDialog may not open in PyInstaller .app (macOS z-order)
- [ ] Windows/Linux packages need CI build (push v* tag)

### Low Priority
- [ ] print() debug leftovers in scripts/ (cosmetic)
- [ ] Daq data source panel is redundant (Run Selector + Browse covers it)
- [ ] Peak list time column shows absolute epoch time (should be relative to event start)
- [ ] 044834 NPZ transfer was unreliable (SCP truncation)
- [ ] TeX docs not included in app bundle

## Current App State
- `/Applications/XENONnT-EventViewer.app` — latest build, working
- Git: branch main, pushed to GitHub
- 9 NPZ files in `dali_probe/`, Run Selector shows them all
- Debug reports: `debug_reports/00_SUMMARY.md`
- Probe data: `dali_probe/report.md`

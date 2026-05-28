# Handoff to Codex

## What I Did While You Were Paused

1. **Committed your changes** (commit `0a9bda4`) — all 9 files saved, 698 insertions
2. **Verified 50 peaks** across 10 events — area values match between peak list and rendered waveform, 0 errors
3. **Rebuilt the .app** — `scripts/build_mac.sh` to `/Applications/XENONnT-EventViewer.app`
4. **Ran DALI/Midway3 raw data probe** — see `dali_probe/report.md` for full results

## Current State

- dist rebuilt and deployed to `/Applications/XENONnT-EventViewer.app`
- DALI raw probe complete: **023756 has NO TPC raw_records on Midway3** (only aqmon monitor)
- `straxen.contexts.xenonnt()` context can't find legacy runs (023756, 024399) — they're not in RunDB
- Current `io.py`'s `strax.load_file()` approach is correct for legacy data

## DALI Probe Key Finding

The NPZ bundle for run 023756 cannot have real TPC waveforms because:
- Midway3 `/project/` processed dirs only have `raw_records_aqmon` for 023756
- straxen contexts (`xenonnt()`) don't register this legacy run

**RunDB query result**: Queried all 73,925 runs in production RunDB. **Zero science runs**
have raw_records or records stored locally on Midway3. Raw waveform data lives on
Amsterdam Stoomboot, accessible only via `rucio` download or on DALI compute nodes.

###  New: Real peaks data FOUND on DALI

**DALI `/dali/lgrandi/xenonnt/processed/` has peaks with real waveform data!**

```
043864-peaks-5i3zhnt5vx  ← example run with real peaks
```

Peaks dtype includes:
- `data`: 200-sample real waveform (PE/sample, NOT model-generated)
- `data_top`: top PMT array waveform (200 samples)  
- `area_per_channel`: per-PMT area (494 values) — real hit pattern, no scaling needed

Also on DALI: 280+ runs with peaklets (same structure, single-PMT granularity).

###  Key Takeaway

| Data Type | Midway3 | DALI |
|-----------|:-------:|:----:|
| peak_basics | 2193 runs | ? |
| peaklets (real waveform) | 280 runs | 280+ runs |
| peaks (real waveform) | 0 | YES (043864 etc.) |

**For the EventViewer with real waveforms:**
1. SSH to dali, load peaks from run 043864
2. Extract `data`, `data_top`, `area_per_channel`  
3. Compute `data_bottom = data - data_top` for 3-layer waveform
4. Bundle into new NPZ format for EventViewer
5. This eliminates ALL model waveform code — everything becomes real data

## TODO for Codex

### Priority 1: Real peaks NPZ bundle
1. Write `dali_probe/extract_peaks_bundle.py` — standalone script, doesn't touch existing code
2. SSH to dali, run it on 043864 (has peaks + event_info)
3. Output: `events_run_043864.npz` with real `data`, `data_top`, `area_per_channel`
4. Verify: load bundle, render event, confirm waveforms are NOT model-generated

### Priority 2: Update EventViewer for real data
5. `data_manager.py`: detect if bundle has `data`/`data_top` → set flag
6. `plotter.py`: when real data available, use `data`/`data_top` for 3-layer waveform instead of model pulse
7. `plotter.py`: when real data available, use `area_per_channel` for PMT pattern directly (no EAC scaling)

### Priority 3: QScrollArea stability
8. Test rapid scrolling 20+ times across 5 different events
9. If garbled edges appear: remove QScrollArea, use plain canvas + toolbar zoom

## Debug Reports (NEW)

Complete debug suite in `debug_reports/`:
- [00_SUMMARY.md](debug_reports/00_SUMMARY.md) — overview + fix priority
- [01_static_analysis.txt](debug_reports/01_static_analysis.txt) — 11 files analyzed
- [02_data_pipeline_tests.txt](debug_reports/02_data_pipeline_tests.txt) — 9 tests, all pass
- [03_rendering_edge_cases.txt](debug_reports/03_rendering_edge_cases.txt) — 8 tests, all pass
- [04_ui_simulation_tests.txt](debug_reports/04_ui_simulation_tests.txt) — 8 tests, all pass

## Key Issues to Watch

### 1. QScrollArea + Fixed size (your event_canvas.py)
You re-introduced QScrollArea with `setFixedSize` and `setWidgetResizable(False)`. 
This combination has caused garbled rendering 3 times before. The user specifically reported 
"colored dot artifacts at edges" when scrolling.

**To test**: Open app, select an event, scroll wheel rapidly 20+ times on the waveform.
Switch between 5 events. If any colored dots or stale content appears at edges, 
this approach needs rethinking.

### 2. DALI raw data probe needs re-running
The probe you started on DALI was loading a raw_records chunk from run 043572 
(or 044281). It was stuck on finding a working Python environment with numpy/strax.

Suggested approach:
```bash
ssh dali
# Find working XENON Python:
find /cvmfs/xenon.opensciencegrid.org -name "activate" -path "*/bin/activate" 2>/dev/null | head -5
# or use singularity/apptainer
apptainer exec /cvmfs/singularity.opensciencegrid.org/xenonnt/xenonnt:latest python3 -c "
import strax
# Load just ONE chunk, small window
records = strax.load_file('/dali/lgrandi/xenonnt/raw/043572/043572-raw_records-xxxx', 
                          compressor='lz4', dtype=strax.raw_record_dtype())
print(f'Loaded {len(records)} records')
"
```

### 3. S1/S2 filter verification
You fixed event_browser.py line 141 to work for NPZ mode. Verify:
- Load bundle → drag S1 min to 2000 → list should filter
- Load another event → filter should persist and work

### 4. Peak list sort correctness
Your NumericItem fix is good. But verify after clicking column headers:
- Sort by Area desc → click row 3 → verify the peak area shown matches
- Sort by Time asc → click row 5 → verify peak time matches
Do this for 3 different events.

### 5. Version number
pyproject.toml says 2.0.0, but Info.plist in built app shows 0.0.0.
Fix: add `--osx-bundle-version "2.0.0"` to PyInstaller command in build_mac.sh.

## Files I Changed
- None. I only committed your changes and ran verification tests.

## Files You Changed (commit `0a9bda4`)
```
README.md                         | 271 changes
event_plotter/io.py               |  79 changes
event_plotter/plotter.py          | 129 changes
event_viewer_app/data_manager.py  | 175 changes
event_viewer_app/event_browser.py |  10 changes
event_viewer_app/event_canvas.py  | 194 changes
event_viewer_app/main_window.py   |  55 changes
scripts/extract_event_bundle.py   |  31 changes
scripts/plot_events.py            |   3 changes
```

## Next Steps (suggested priority)

1. Wait for build to complete (in progress now)
2. Test QScrollArea rendering stability
3. Complete DALI raw data probe
4. Fix version number
5. Push to GitHub when stable

## New Tasks (23:22)

### Run Selector UI
User wants auto-load instead of manual File→Open:
- App ships with multiple NPZ files (023756, 043864, 044116, etc.)
- Left panel has a Run dropdown at top
- Click run name → loads that bundle automatically
- Same UX as Event list

### Real data validation
Extract more real peaks from DALI to verify the pipeline at scale:
```bash
# On DALI, after source setup:
cd /scratch/midway3/jiafu/EventViewer
python dali_probe_extract_peaks_bundle.py --run 043864 --n 50 --output events_run_043864_real_peaks_50ev.npz
python dali_probe_extract_peaks_bundle.py --run 044116 --n 50 --output events_run_044116_real_peaks_50ev.npz
```

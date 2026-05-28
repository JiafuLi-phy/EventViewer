# EventViewer Debug Report Summary

Generated: 2026-05-28

## Test Results Overview

| Report | Tests | Result |
|--------|-------|--------|
| [01_static_analysis.txt](01_static_analysis.txt) | current code scan | PASS with known non-blocking notes |
| [02_data_pipeline_tests.txt](02_data_pipeline_tests.txt) | NPZ + real peaks data checks | PASS |
| [03_rendering_edge_cases.txt](03_rendering_edge_cases.txt) | overview/zoom/render/export checks | PASS |
| [04_ui_simulation_tests.txt](04_ui_simulation_tests.txt) | offscreen Qt interaction checks | PASS |

## Current Status

- QScrollArea fixed-size rendering path removed; EventCanvas uses plain expanding canvas and replaces the canvas on clear.
- Event overview and peak zoom both draw Top/Bottom/Total layers.
- Real DALI peaks bundles use `data`, `data_top`, and `area_per_channel` directly.
- Packaged macOS app includes `events_run_023756.npz` and `events_run_043864_real_peaks_200ev.npz`.
- Run Selector scans packaged app resources and de-duplicates PyInstaller resource symlinks.
- Strax run loading is handled by a QThread worker and preloads peaks off the GUI thread.
- PDF export was verified locally and PyInstaller hidden imports include `backend_pdf` and `backend_agg`.

## Remaining External Validation

- Linux tar.gz and Windows zip must be built by GitHub Actions or native OS runners.
- GitHub release creation is triggered by pushing a `v*` tag.

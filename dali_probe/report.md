# DALI/Midway3 Raw Data Probe Report

**Date**: 2026-05-27  
**Purpose**: Determine if real TPC raw_records are accessible for EventViewer waveform rendering.

## Findings

### 1. DALI Raw Data

**DALI `/dali/lgrandi/xenonnt/raw/`** only contains `raw_records_aqmon` (acquisition monitor)
runs, NOT full TPC raw_records. These are small monitor data, not physics waveforms.

```
025164-raw_records_aqmon-rfzvpzj4mf
025903-raw_records_aqmon-rfzvpzj4mf
...
```

No TPC raw_records found on DALI for physics runs.

### 2. Midway3 Processed Data

**Midway3 `/project/lgrandi/xenonnt/processed/`** has processed data for many runs including 023756.
But for run 023756, the raw data types are:
- `023756-raw_records_aqmon` — monitor only, NOT TPC waveforms
- `023756-raw_records_aux_mv` — auxiliary, NOT TPC waveforms
- `023756-event_info` — available
- `023756-peak_basics` — available
- `023756-event_area_per_channel` — available

**No TPC raw_records for run 023756 on Midway3** — this is why the NPZ bundle 
only contains peak_basics (metadata), not waveform samples.

### 3. straxen Context Availability

The `straxen.contexts.xenonnt()` (production RunDB context) cannot find runs 023756
or 024399. These old calibration/commissioning runs are stored as flat files in 
the processed directories, not registered in the production RunDB.

**Available contexts on Midway3**:
- `xenonnt()` — production RunDB
- `xenonnt_online()` — online RunDB  
- `xenonnt_led()` — LED calibration
- `xenonnt_simulation()` — simulation
- No `xenonnt_offline()` in this straxen version

### 4. Current Data Access Pattern (correct)

The current `io.py` uses `strax.load_file()` to directly read chunk files from 
processed directories. This is the CORRECT approach for legacy data like 023756:

```python
# io.py load_strax_chunks() — works for peak_basics, event_info, etc.
data_dir = find_data_dir(run_id, dtype_prefix)
chunks = [strax.load_file(f, compressor=compressor, dtype=dtype) for f in files]
return np.concatenate(chunks)
```

But this only works for data types that EXIST as chunk files. raw_records chunk
files do not exist for 023756 (only aqmon).

## Conclusion

| Data Type | 023756 on Midway3 | Real TPC raw_records |
|-----------|-------------------|---------------------|
| peak_basics | Available | N/A |
| event_info | Available | N/A |
| event_area_per_channel | Available | N/A |
| TPC raw_records | NOT available (only aqmon) | Need RunDB-registered run |
| records | NOT available | Need RunDB-registered run |

### For EventViewer with real waveforms:

**Option A**: Use a RunDB-registered run (SR1/SR2) that has raw_records.
Load via `straxen.contexts.xenonnt().get_array(run_id, "raw_records", seconds_range=(0,1))`.
A 1-second window is ~2 GB of raw data.

**Option B**: Pre-extract raw_records on Midway3 and bundle into NPZ.
Run `scripts/extract_event_bundle.py --include-raw-records` on Midway3
for a run with raw_records available.

**Option C**: Accept that model waveforms (from peak_basics metadata) 
are the primary display mode. Real waveforms require the user to have
strax/straxen data access on a Midway3 compute node.

## Recommendation for Codex

1. Keep the current `strax.load_file()` approach for NPZ extraction (works for 023756)
2. Add `straxen.contexts.xenonnt()` as an ALTERNATIVE data source for recent runs
3. Test with a RunDB run (e.g., 044000+) that has raw_records
4. For the `.app` distribution, continue using model waveforms from peak_basics
5. Document clearly that real TPC waveforms require accessing a Midway3/DALI compute node

#!/bin/bash
# Batch extract real peaks from DALI runs
# Usage: run on DALI after sourcing XENON environment

SCRIPT="dali_probe_extract_peaks_bundle.py"
OUTDIR="/scratch/midway3/jiafu/EventViewer"
source /cvmfs/xenon.opensciencegrid.org/releases/nT/el7.2025.07.2/setup.sh 2>/dev/null

for RUN in 043864 044116 044165 044225 044311 044834; do
    echo "=== Extracting run $RUN (30 events) ==="
    python3 "$OUTDIR/$SCRIPT" --run "$RUN" --n 30 --output "$OUTDIR/events_${RUN}_peaks_30ev.npz" 2>&1 | tail -3
done

echo "=== Done ==="
ls -lh "$OUTDIR"/events_*_peaks_30ev.npz

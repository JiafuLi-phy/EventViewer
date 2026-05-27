#!/usr/bin/env python3
"""Extract full peak data (with waveforms) for offline viewing.

This script MUST run on a compute node with CVMFS access (midway3
compute or dali).  It computes the ``peaks`` data type for each
event and saves per-event .npz bundles that the event viewer can
read offline.

Usage on compute node::

    source /cvmfs/xenon.opensciencegrid.org/releases/nT/development/setup.sh
    python extract_peak_data.py --run 023756 --n-events 20  \\
        --s1-min 1000 --s2-min 100000  \\
        --out /scratch/midway3/jiafu/EventViewer/data/

Output per event::

    data/event_<number>_run_<run_id>.npz
        peaks       - all peaks in event (with data, area_per_channel)
        event       - event_info row
        to_pe       - gain factors
        pmt_pos     - PMT geometry
"""

import argparse
import os
import sys
import warnings

import numpy as np

# Ensure we're on a node with CVMFS
try:
    import cutax
except ImportError:
    print("ERROR: cutax not found.  This script must run with CVMFS.")
    print("Source the environment first:")
    print("  source /cvmfs/xenon.opensciencegrid.org/releases/nT/development/setup.sh el8.2026.02.2")
    sys.exit(1)


def main():
    args = parse_args()

    # Context
    st = cutax.contexts.xenonnt_offline(xedocs_version="global_v20")
    print(f"Context ready, backends: {len(st.context_config)}")

    run_id = args.run

    # Load event_info
    print(f"Loading event_info for run {run_id} ...")
    events = st.get_df(run_id, "event_info")
    print(f"  {len(events)} events")

    # Filter
    mask = np.ones(len(events), dtype=bool)
    if "s1_area" in events.columns:
        mask &= events["s1_area"] > args.s1_min
    if "s2_area" in events.columns:
        mask &= events["s2_area"] > args.s2_min
    events = events[mask].copy()
    print(f"  {len(events)} pass S1>{args.s1_min}, S2>{args.s2_min}")

    if len(events) == 0:
        print("No events match.  Lower thresholds.")
        return

    # Sort by S2 descending, take top N
    events = events.sort_values("s2_area", ascending=False)
    events = events.head(args.n_events)
    # Convert to numpy structured array for saving
    ev_arr = events.to_records(index=False)

    # Get gains and PMT positions
    to_pe = st.get_array(run_id, "to_pe")
    import straxen
    pmt_pos = straxen.pmt_positions()

    os.makedirs(args.out, exist_ok=True)

    # Compute peaks per event
    for i, (_, event) in enumerate(events.iterrows()):
        ev_num = int(event["event_number"])
        print(f"\n[{i+1}/{len(events)}] Event {ev_num} ...")

        t_range = (int(event["time"]), int(event["endtime"]))

        # Compute peaks for this event
        try:
            peaks = st.get_array(run_id, "peaks", time_range=t_range, progress_bar=False)
        except Exception as e:
            print(f"  ERROR computing peaks: {e}")
            continue

        if len(peaks) == 0:
            print(f"  No peaks found")
            continue

        print(f"  {len(peaks)} peaks (S1: {(peaks['type']==1).sum()}, "
              f"S2: {(peaks['type']==2).sum()})")

        # Save bundle
        out_path = os.path.join(args.out, f"event_{ev_num}_run_{run_id}.npz")
        np.savez_compressed(
            out_path,
            peaks=peaks,
            event=np.array(event.to_records(index=False)),
            to_pe=to_pe,
            pmt_pos=pmt_pos,
            run_id=np.array([run_id]),
        )
        print(f"  saved → {out_path}")

    print(f"\nDone.  {len(events)} event bundles saved to {args.out}/")


def parse_args():
    p = argparse.ArgumentParser(description="Extract peak data for offline event viewing")
    p.add_argument("--run", required=True, help="Run ID")
    p.add_argument("--n-events", type=int, default=20, help="Max events to export")
    p.add_argument("--s1-min", type=float, default=1000)
    p.add_argument("--s2-min", type=float, default=100000)
    p.add_argument("--out", default="/scratch/midway3/jiafu/EventViewer/data/")
    return p.parse_args()


if __name__ == "__main__":
    main()

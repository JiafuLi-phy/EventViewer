#!/usr/bin/env python3
"""Extract N events into a single portable .npz bundle for the Event Viewer.

Usage:
    python extract_event_bundle.py                          # 50 events from run 023756
    python extract_event_bundle.py --run 023756 --n 100     # 100 events
    python extract_event_bundle.py --run 023756 --n 20 --s1-min 500 --s2-min 50000
    python extract_event_bundle.py --run 023756 --events 42,100,38991  # specific events

Output: scripts/output/events_run_023756.npz
"""

import argparse
import os
import sys
import warnings

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from event_plotter import io

OUTPUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT, exist_ok=True)
DEFAULT_RUN = "023756"


def main():
    args = parse_args()
    run_id = args.run or DEFAULT_RUN

    print(f"Loading run {run_id} ...")
    events = io.load_strax_chunks(run_id, "event_info")
    print(f"  {len(events)} events")

    # Selection
    mask = np.ones(len(events), dtype=bool)
    if args.events is not None:
        wanted = set(args.events)
        mask = np.array([e in wanted for e in events["event_number"]], dtype=bool)
    else:
        if "s1_area" in events.dtype.names:
            mask &= events["s1_area"] > args.s1_min
        if "s2_area" in events.dtype.names:
            mask &= events["s2_area"] > args.s2_min

    selected = events[mask]
    if len(selected) == 0:
        print("No events match selection.")
        return

    order = np.argsort(selected["s2_area"])[::-1]
    selected = selected[order]
    selected = selected[: args.n]
    # Sort by time for fully_contained_in
    selected = selected[np.argsort(selected["time"])]
    n_events = len(selected)
    print(f"  Selected {n_events} events")

    # Load shared data
    pmt_positions = io.load_pmt_geometry()
    to_pe = io.load_to_pe(n_channels=len(pmt_positions))
    print(f"  PMT positions: {len(pmt_positions)}")

    # Load peaks. Use "peaks" for true waveform + area_per_channel when
    # available, or "peak_basics" for compact metadata-only bundles.
    print(f"Loading {args.peak_data_type} ...")
    peaks_all = io.load_strax_chunks(run_id, args.peak_data_type)
    print(f"  {len(peaks_all)} peaks total")

    # Load event_area_per_channel if available
    eac_all = None
    eac_dir = io.find_data_dir(run_id, "event_area_per_channel")
    if eac_dir:
        print("Loading event_area_per_channel ...")
        eac_all = io.load_strax_chunks(run_id, "event_area_per_channel")
        print(f"  {len(eac_all)} eac rows")

    # Extract per-event data
    from strax import fully_contained_in

    fci_peaks = fully_contained_in(peaks_all, selected)
    fci_eac = fully_contained_in(eac_all, selected) if eac_all is not None else None

    peaks_list = []
    eac_list = []
    raw_records_list = []
    event_numbers = []

    for i in range(n_events):
        ev = selected[i]
        ev_num = int(ev["event_number"])
        event_numbers.append(ev_num)

        # Peaks for this event
        ev_peaks = peaks_all[fci_peaks == i]
        peaks_list.append(ev_peaks)

        # EAC for this event
        if eac_all is not None and fci_eac is not None:
            eac_idx = np.where(fci_eac == i)[0]
            if len(eac_idx):
                eac_list.append(eac_all[eac_idx[0]])
            else:
                eac_list.append(None)

        if args.include_raw_records:
            try:
                raw = io.load_raw_records_window(
                    run_id, int(ev["time"]) - args.raw_margin_ns,
                    int(ev["endtime"]) + args.raw_margin_ns,
                )
            except Exception as e:
                print(f"    raw_records unavailable: {e}")
                raw = None
            raw_records_list.append(raw)

        s1_str = f"  S1={ev['s1_area']:.0f}" if "s1_area" in ev.dtype.names else ""
        s2_str = f"  S2={ev['s2_area']:.0f}" if "s2_area" in ev.dtype.names else ""
        print(f"  [{i+1}/{n_events}] event {ev_num}: {len(ev_peaks)} peaks{s1_str}{s2_str}")

    # Build bundle
    # Save PMT positions as separate arrays to preserve structured dtype roundtrip
    bundle = {
        "events": selected,
        "peaks_list": np.array(peaks_list, dtype=object),
        "event_numbers": np.array(event_numbers, dtype=np.int32),
        "pmt_x": pmt_positions["x"],
        "pmt_y": pmt_positions["y"],
        "pmt_array": pmt_positions["array"].astype(str),
        "pmt_i": pmt_positions["i"],
        "to_pe": to_pe,
        "run_id": run_id,
    }

    if eac_list:
        bundle["eac_list"] = np.array(eac_list, dtype=object)
    if raw_records_list:
        bundle["raw_records_list"] = np.array(raw_records_list, dtype=object)

    out_path = os.path.join(OUTPUT, f"events_run_{run_id}.npz")
    print(f"\nSaving {n_events} events to {out_path} ...")
    np.savez_compressed(out_path, **bundle)

    # Verify
    _check = np.load(out_path, allow_pickle=True)
    print(f"  File size: {os.path.getsize(out_path) / 1024 / 1024:.1f} MB")
    print(f"  Keys: {list(_check.keys())}")
    print(f"  Events: {len(_check['events'])}")
    print("Done.")


def parse_args():
    p = argparse.ArgumentParser(description="Extract events into portable .npz bundle")
    p.add_argument("--run", help=f"Run ID (default: {DEFAULT_RUN})")
    p.add_argument("--n", type=int, default=50, help="Number of events to extract")
    p.add_argument("--events", help="Comma-separated event numbers (overrides --n)")
    p.add_argument("--s1-min", type=float, default=1000, help="Minimum S1 area [PE]")
    p.add_argument("--s2-min", type=float, default=100000, help="Minimum S2 area [PE]")
    p.add_argument(
        "--peak-data-type", default="peak_basics", choices=("peak_basics", "peaks"),
        help="'peaks' preserves waveform and per-channel peak maps when available; "
             "'peak_basics' creates smaller metadata-only bundles",
    )
    p.add_argument(
        "--include-raw-records", action="store_true",
        help="Include raw_records windows for true event waveforms when accessible",
    )
    p.add_argument("--raw-margin-ns", type=int, default=50000, help="raw_records margin around each event")
    return p.parse_args()


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    main()

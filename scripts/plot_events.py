#!/usr/bin/env python3
"""Plot event waveform displays for XENONnT events.

Usage:
    python plot_events.py                    # auto: use run 023756, first large event
    python plot_events.py --run 023756       # specific run
    python plot_events.py --event 42         # specific event_number (needs --run)
    python plot_events.py --n-events 5       # plot N events
    python plot_events.py --stack            # also produce S1/S2 stacking plots

Requirements:
    - strax, straxen, numpy, matplotlib
    - Access to /project/lgrandi/xenonnt/processed/
"""

import argparse
import os
import sys
import warnings

import numpy as np

# Ensure the package is importable
_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from event_plotter import style, plotter, io

# Output directory
OUTPUT = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT, exist_ok=True)

# Default run (has event_info + peak_basics + event_area_per_channel)
DEFAULT_RUN = "023756"


def main():
    args = parse_args()

    # ── apply publication style ──
    style.apply_style(font_size=9)

    run_id = args.run or DEFAULT_RUN

    # ── load data ──
    print(f"Loading data for run {run_id} ...")
    events = io.load_strax_chunks(run_id, "event_info")
    peaks = io.load_strax_chunks(run_id, "peak_basics")
    pmt_positions = io.load_pmt_geometry()
    to_pe = io.load_to_pe(n_channels=len(pmt_positions))

    # Load event area per channel if available
    eac = None
    eac_dir = io.find_data_dir(run_id, "event_area_per_channel")
    if eac_dir:
        print("Loading event_area_per_channel ...")
        eac = io.load_strax_chunks(run_id, "event_area_per_channel")

    print(f"Events: {len(events)}  |  Peaks: {len(peaks)}")

    # ── select events ──
    mask = np.ones(len(events), dtype=bool)
    if "s1_area" in events.dtype.names:
        mask &= events["s1_area"] > args.s1_min
    if "s2_area" in events.dtype.names:
        mask &= events["s2_area"] > args.s2_min

    selected = events[mask]
    print(f"Events with S1>{args.s1_min}, S2>{args.s2_min}: {len(selected)}")

    if len(selected) == 0:
        print("No events match selection. Try lowering --s1-min / --s2-min.")
        return

    # order by S2 area descending
    order = np.argsort(selected["s2_area"])[::-1]
    selected = selected[order]

    # specific event_number?
    if args.event is not None:
        match = selected[selected["event_number"] == args.event]
        if len(match) == 0:
            print(f"Event {args.event} not found in selection.")
            return
        selected = match

    n_events = min(args.n_events, len(selected))
    selected = selected[:n_events]

    # Check for real raw_records (not aqmon monitor subset)
    has_raw_records = False
    for base in ["/project/lgrandi/xenonnt/processed/",
                 "/project2/lgrandi/xenonnt/processed/"]:
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            # Match "023756-raw_records-SUFFIX" but NOT "raw_records_aqmon"
            if d.startswith(run_id.zfill(6) + "-raw_records-"):
                has_raw_records = True
                break
        if has_raw_records:
            break
    if has_raw_records:
        print("raw_records available – will build waveforms from records")

    # ── plot each event ──
    for i, event in enumerate(selected):
        ev_num = event["event_number"]
        print(f"\nPlotting event {ev_num} ({i+1}/{n_events}) ...")

        # get peaks for this event
        from strax import fully_contained_in
        fci = fully_contained_in(peaks, np.array([event]))
        ev_peaks = peaks[fci == 0]

        eac_row = None
        if eac is not None:
            eac_fci = fully_contained_in(eac, np.array([event]))
            eac_idx = np.where(eac_fci == 0)[0]
            if len(eac_idx):
                eac_row = eac[eac_idx[0]]

        # Load raw_records for this event's time range
        ev_rr = None
        if has_raw_records:
            t_ev = int(event["time"]) - 50000
            t_ev_end = int(event["endtime"]) + 50000
            try:
                ev_rr = io.load_raw_records_window(run_id, t_ev, t_ev_end)
                if len(ev_rr):
                    print(f"  {len(ev_rr)} raw_records in event window")
            except Exception as e:
                print(f"  Warning: could not load raw_records: {e}")

        fig = plotter.plot_event_full(
            event,
            ev_peaks,
            to_pe,
            pmt_positions,
            event_area_per_channel=eac_row,
            show_largest=200,
            raw_records=ev_rr,
            run_id=run_id,
        )

        out_path = os.path.join(OUTPUT, f"event_{ev_num}_run_{run_id}")
        style.save_figure(fig, out_path, formats=("pdf", "png"), dpi=300)
        plt.close(fig)

    # ── stacking plots ──
    if args.stack and n_events > 1:
        print("\nProducing stacking plots ...")
        _make_stacking_plots(events, peaks, run_id, to_pe, pmt_positions)

    print(f"\nDone.  Output in {OUTPUT}/")


def _make_stacking_plots(events, peaks, run_id, to_pe, pmt_positions):
    """Produce S1 and S2 stacking plots from the selected events."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from strax import fully_contained_in

    # Pick large events
    mask = np.ones(len(events), dtype=bool)
    if "s1_area" in events.dtype.names:
        mask &= events["s1_area"] > 500
    if "s2_area" in events.dtype.names:
        mask &= events["s2_area"] > 50000
    sel = events[mask]
    sel = sel[np.argsort(sel["s2_area"])[::-1][:500]]

    fci = fully_contained_in(peaks, sel)
    ev_peaks = peaks[np.isin(fci, np.arange(len(sel)))]

    # Only do stacking if peaks have 'data' field
    if not plotter.has_waveform(ev_peaks):
        print("Peaks have no waveform data — skipping stacking plots.")
        return

    for ptype, pt_label in [(1, "S1"), (2, "S2")]:
        subset = ev_peaks[ev_peaks["type"] == ptype]
        if len(subset) < 10:
            print(f"Not enough {pt_label} peaks for stacking ({len(subset)})")
            continue

        # split into list of per-event peaks
        peaks_by_event = []
        uq_fci = np.unique(fci[fci != -1])
        for idx in uq_fci[:200]:
            ev_p = ev_peaks[fci == idx]
            ev_p_type = ev_p[ev_p["type"] == ptype]
            if len(ev_p_type):
                peaks_by_event.append(ev_p_type)

        t_range = (-2000, 4000) if ptype == 1 else (-5000, 10000)

        fig = plotter.plot_peak_stack(
            peaks_by_event,
            peak_type=ptype,
            align="center_time",
            t_range=t_range,
            n_bootstrap=200,
            title=f"{len(peaks_by_event)} {pt_label} peaks from {len(sel)} events  |  run {run_id}",
        )
        out_path = os.path.join(OUTPUT, f"stack_{pt_label.lower()}_run_{run_id}")
        style.save_figure(fig, out_path, formats=("pdf", "png"), dpi=300)
        plt.close(fig)


def parse_args():
    p = argparse.ArgumentParser(description="XENONnT event waveform plotter")
    p.add_argument("--run", help="Run ID (default: %(default)s)")
    p.add_argument("--event", type=int, help="Specific event_number")
    p.add_argument("--n-events", type=int, default=3, help="Number of events to plot")
    p.add_argument("--s1-min", type=float, default=1000, help="Minimum S1 area [PE]")
    p.add_argument("--s2-min", type=float, default=100000, help="Minimum S2 area [PE]")
    p.add_argument("--stack", action="store_true", help="Also produce stacking plots")
    return p.parse_args()


if __name__ == "__main__":
    # Allow running without a full straxen context
    warnings.filterwarnings("ignore")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    main()

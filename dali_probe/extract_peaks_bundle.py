#!/usr/bin/env python3
"""Extract a small EventViewer NPZ from DALI real `peaks` chunks.

Run on DALI (or another XENON environment with DALI mounted), e.g.:

    source /cvmfs/xenon.opensciencegrid.org/releases/nT/el7.2025.07.2/setup.sh
    python extract_peaks_bundle.py --run 043864 --n 10

This script intentionally avoids GUI dependencies and reads only chunked strax
arrays needed for a compact real-waveform bundle.
"""

import argparse
import glob
import json
import os
from pathlib import Path

import numpy as np


DEFAULT_STORAGE_DIRS = [
    "/dali/lgrandi/xenonnt/processed",
    "/project/lgrandi/xenonnt/processed",
    "/project2/lgrandi/xenonnt/processed",
]


def main():
    args = parse_args()
    run_id = str(args.run).zfill(6)
    storage_dirs = args.storage_dir or DEFAULT_STORAGE_DIRS
    output = Path(args.output or f"events_run_{run_id}_real_peaks.npz")

    import strax

    print(f"Run {run_id}")
    try:
        events = load_strax_chunks(run_id, "event_info", storage_dirs)
        event_type = "event_info"
    except FileNotFoundError:
        events = load_strax_chunks(run_id, "event_basics", storage_dirs)
        event_type = "event_basics"
    peaks = load_strax_chunks(run_id, "peaks", storage_dirs)
    print(f"  {event_type}: {len(events)} rows")
    print(f"  peaks: {len(peaks)} rows; fields={peaks.dtype.names}")
    if "data" not in peaks.dtype.names:
        raise RuntimeError("Loaded peaks do not contain waveform field 'data'")

    selected = select_events(events, args)
    if len(selected) == 0:
        raise RuntimeError("No events matched selection")
    selected = selected[np.argsort(selected["time"])]
    print(f"  selected events: {len(selected)}")

    fci = strax.fully_contained_in(peaks, selected)
    peaks_list = []
    event_numbers = []
    keep = []
    for i, ev in enumerate(selected):
        ev_peaks = peaks[fci == i]
        if len(ev_peaks) == 0:
            continue
        peaks_list.append(ev_peaks)
        event_numbers.append(int(ev["event_number"]))
        keep.append(i)
        print(f"    event {int(ev['event_number'])}: {len(ev_peaks)} peaks")

    selected = selected[np.array(keep, dtype=int)]

    eac_list = []
    try:
        eac = load_strax_chunks(run_id, "event_area_per_channel", storage_dirs)
        fci_eac = strax.fully_contained_in(eac, selected)
        for i in range(len(selected)):
            idx = np.where(fci_eac == i)[0]
            eac_list.append(eac[idx[0]] if len(idx) else None)
        print(f"  event_area_per_channel: {len(eac)} rows")
    except Exception as e:
        print(f"  event_area_per_channel unavailable: {e}")

    pmt_positions = load_pmt_positions()
    to_pe = load_to_pe(run_id, len(pmt_positions))

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
        "waveform_source": np.array("peaks"),
    }
    if eac_list:
        bundle["eac_list"] = np.array(eac_list, dtype=object)

    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, **bundle)
    print(f"Saved {len(selected)} events to {output}")
    print(f"Size: {output.stat().st_size / 1024 / 1024:.1f} MB")


def select_events(events, args):
    mask = np.ones(len(events), dtype=bool)
    if args.events:
        wanted = {int(x) for x in args.events.split(",") if x.strip()}
        mask &= np.array([int(e) in wanted for e in events["event_number"]])
    else:
        if "s1_area" in events.dtype.names:
            mask &= events["s1_area"] >= args.s1_min
        if "s2_area" in events.dtype.names:
            mask &= events["s2_area"] >= args.s2_min
    selected = events[mask]
    if "s2_area" in selected.dtype.names:
        selected = selected[np.argsort(selected["s2_area"])[::-1]]
    return selected[: args.n]


def find_data_dir(run_id, data_type, storage_dirs):
    for base in storage_dirs:
        if not os.path.isdir(base):
            continue
        prefix = f"{run_id}-{data_type}-"
        matches = [x for x in glob.glob(os.path.join(base, prefix + "*")) if os.path.isdir(x)]
        if matches:
            return sorted(matches)[0]
    raise FileNotFoundError(f"No {data_type} chunks found for run {run_id}")


def load_strax_chunks(run_id, data_type, storage_dirs):
    import strax

    data_dir = find_data_dir(run_id, data_type, storage_dirs)
    meta_files = [f for f in os.listdir(data_dir) if f.endswith(".json")]
    if not meta_files:
        raise FileNotFoundError(f"No metadata JSON in {data_dir}")
    with open(os.path.join(data_dir, meta_files[0])) as f:
        meta = json.load(f)
    dtype = eval(meta["dtype"])
    compressor = meta.get("compressor", "zstd")
    chunks = []
    for chunk in meta["chunks"]:
        chunks.append(strax.load_file(
            os.path.join(data_dir, chunk["filename"]),
            compressor=compressor,
            dtype=dtype,
        ))
    return np.concatenate(chunks)


def load_pmt_positions():
    try:
        import straxen
        return straxen.pmt_positions()
    except Exception:
        return make_fallback_pmt_positions()


def load_to_pe(run_id, n_channels):
    try:
        import straxen
        ctx = straxen.contexts.xenonnt()
        return ctx.get_array(run_id, "to_pe")
    except Exception:
        return np.ones(n_channels, dtype=float)


def make_fallback_pmt_positions():
    n_top = 253
    n_total = 494
    dtype = np.dtype([("x", np.float64), ("y", np.float64), ("array", "U10"), ("i", np.int32)])
    pos = np.zeros(n_total, dtype=dtype)
    for start, n, label in [(0, n_top, "top"), (n_top, n_total - n_top, "bottom")]:
        rings = max(1, int(np.sqrt(n)))
        idx = 0
        for ring in range(rings):
            n_ring = int(n / rings) if ring < rings - 1 else n - idx
            radius = 42.0 * (ring + 0.5) / rings
            for k in range(n_ring):
                j = start + idx
                angle = 2 * np.pi * k / max(n_ring, 1)
                pos[j]["x"] = radius * np.cos(angle)
                pos[j]["y"] = radius * np.sin(angle)
                pos[j]["array"] = label
                pos[j]["i"] = j
                idx += 1
    return pos


def parse_args():
    p = argparse.ArgumentParser(description="Extract EventViewer bundle from real DALI peaks")
    p.add_argument("--run", default="043864")
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--events", help="Comma-separated event numbers")
    p.add_argument("--s1-min", type=float, default=0)
    p.add_argument("--s2-min", type=float, default=0)
    p.add_argument("--storage-dir", action="append", help="Storage dirs to search; can repeat")
    p.add_argument("--output", help="Output .npz path")
    return p.parse_args()


if __name__ == "__main__":
    main()

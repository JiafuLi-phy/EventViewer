#!/usr/bin/env python3
"""Load a small raw_records window and save a waveform probe.

This is meant for DALI or a node/container where raw_records are mounted.
It intentionally reads only a small number of chunks/records.
"""

import argparse
import os
import sys

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from event_plotter import io


def main():
    args = parse_args()
    raw_dir = io.find_data_dir(args.run, "raw_records", args.storage_dir)
    if raw_dir is None:
        raise FileNotFoundError(f"No raw_records directory found for run {args.run}")

    records = load_probe_records(raw_dir, args.max_chunks, args.max_records)
    if len(records) == 0:
        raise RuntimeError(f"No records loaded from {raw_dir}")

    t0 = int(records["time"].min()) if args.start_ns is None else args.start_ns
    t1 = t0 + args.window_us * 1000
    window = records[(records["time"] >= t0) & (records["time"] < t1)]

    if len(window) < args.min_records:
        # Pick the densest short window among loaded records.
        times = np.sort(records["time"].astype(np.int64))
        span = args.window_us * 1000
        best_i, best_n = 0, 0
        j = 0
        for i, t in enumerate(times):
            while j < len(times) and times[j] < t + span:
                j += 1
            if j - i > best_n:
                best_i, best_n = i, j - i
        t0 = int(times[best_i])
        t1 = t0 + span
        window = records[(records["time"] >= t0) & (records["time"] < t1)]

    x, y = sum_waveform(window, dt_out=args.dt)
    base = args.output or os.path.join(
        os.getcwd(), f"raw_probe_run_{str(args.run).zfill(6)}"
    )
    np.savez_compressed(
        base + ".npz",
        records=window,
        x_us=x,
        sum_adc_per_ns=y,
        run_id=str(args.run).zfill(6),
        raw_dir=raw_dir,
    )
    save_plot(base + ".png", x, y, args.run, len(window))
    print(f"raw_dir: {raw_dir}")
    print(f"records_loaded: {len(records)}")
    print(f"records_in_window: {len(window)}")
    print(f"time_window_ns: {t0} {t1}")
    print(f"saved: {base}.npz")
    print(f"saved: {base}.png")


def load_probe_records(raw_dir, max_chunks, max_records):
    import json
    import strax

    meta_file = [f for f in os.listdir(raw_dir) if f.endswith(".json")][0]
    with open(os.path.join(raw_dir, meta_file)) as f:
        meta = json.load(f)
    dtype = eval(meta["dtype"])
    compressor = meta.get("compressor", "zstd")

    chunks = []
    for ci in meta["chunks"][:max_chunks]:
        data = strax.load_file(
            os.path.join(raw_dir, ci["filename"]),
            compressor=compressor,
            dtype=dtype,
        )
        if max_records and len(data) > max_records:
            data = data[:max_records]
        chunks.append(data)
        if max_records and sum(len(x) for x in chunks) >= max_records:
            break
    if not chunks:
        return np.array([], dtype=dtype)
    out = np.concatenate(chunks)
    return out[:max_records] if max_records else out


def sum_waveform(records, dt_out=10):
    if len(records) == 0:
        return np.array([]), np.array([])
    t_start = int(records["time"].min())
    t_end = int(np.max(records["time"] + records["length"] * records["dt"]))
    n_bins = int((t_end - t_start) / dt_out) + 1
    amp = np.zeros(n_bins + 1)
    for rec in records:
        rec_len = int(rec["length"])
        rec_dt = int(rec["dt"])
        ts = int(rec["time"]) + np.arange(rec_len) * rec_dt
        bins = ((ts - t_start) / dt_out).astype(int)
        valid = (bins >= 0) & (bins < n_bins)
        if valid.any():
            data = rec["data"][:rec_len].astype(float) / rec_dt
            np.add.at(amp, bins[valid], data[valid])
    x_us = np.arange(n_bins) * dt_out / 1000.0
    return x_us, amp[:n_bins]


def save_plot(path, x_us, y, run_id, n_records):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x_us, y, lw=0.8)
    ax.set_xlabel("Time from window start [us]")
    ax.set_ylabel("ADC/ns")
    ax.set_title(f"Run {str(run_id).zfill(6)} raw_records sum waveform, {n_records} records")
    fig.tight_layout()
    fig.savefig(path, dpi=180)


def parse_args():
    p = argparse.ArgumentParser(description="Small raw_records waveform probe")
    p.add_argument("--run", default="043572", help="Run ID with raw_records available")
    p.add_argument("--storage-dir", action="append", help="Storage dir to search; can repeat")
    p.add_argument("--start-ns", type=int, help="Window start time in ns")
    p.add_argument("--window-us", type=int, default=200, help="Window width in microseconds")
    p.add_argument("--dt", type=int, default=10, help="Output bin width in ns")
    p.add_argument("--max-chunks", type=int, default=1)
    p.add_argument("--max-records", type=int, default=20000)
    p.add_argument("--min-records", type=int, default=50)
    p.add_argument("--output", help="Output base path without extension")
    return p.parse_args()


if __name__ == "__main__":
    main()

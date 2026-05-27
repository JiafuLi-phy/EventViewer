"""Data I/O helpers – load event & peak data.

Three loading strategies (in order of preference):
1.  ``strax.load_file`` direct chunk access (no CVMFS needed, Section 3.4)
2.  straxen context (requires proper environment on compute nodes)
3.  Pre-extracted .npz bundles (fully offline)
"""

import os
import json
import warnings
from typing import List, Optional, Tuple

import numpy as np


# ── strax.load_file – direct chunk access (Section 3.4) ────────


def find_data_dir(
    run_id: str,
    dtype_prefix: str,
    storage_dirs: Optional[List[str]] = None,
) -> Optional[str]:
    """Return the first data directory matching *run_id* and *dtype_prefix*."""
    if storage_dirs is None:
        storage_dirs = [
            "/project/lgrandi/xenonnt/processed/",
            "/project2/lgrandi/xenonnt/processed/",
        ]
    run_str = str(run_id).zfill(6)
    for base in storage_dirs:
        if not os.path.isdir(base):
            continue
        for d in sorted(os.listdir(base)):
            if d.startswith(run_str) and dtype_prefix in d:
                return os.path.join(base, d)
    return None


def load_strax_chunks(
    run_id: str,
    dtype_prefix: str,
    storage_dirs: Optional[List[str]] = None,
    max_chunks: Optional[int] = None,
) -> np.ndarray:
    """Load strax chunk data directly via ``strax.load_file``.

    This bypasses the need for a straxen context or CVMFS.  It works
    wherever the processed data directories are mounted.

    Parameters
    ----------
    run_id : str
        e.g. "023756"
    dtype_prefix : str
        e.g. "event_info", "peak_basics"
    storage_dirs : list of str, optional
        Directories to search for chunk directories.
    max_chunks : int, optional
        If set, load at most this many chunks (for large data types).

    Returns
    -------
    data : numpy structured array
    """
    import strax

    data_dir = find_data_dir(run_id, dtype_prefix, storage_dirs)
    if data_dir is None:
        raise FileNotFoundError(
            f"No directory matching run={run_id}, dtype={dtype_prefix}"
        )

    meta_file = [f for f in os.listdir(data_dir) if f.endswith(".json")][0]
    with open(os.path.join(data_dir, meta_file)) as f:
        meta = json.load(f)

    dtype = eval(meta["dtype"])
    compressor = meta.get("compressor", "zstd")

    chunks_info = meta["chunks"]
    if max_chunks is not None:
        chunks_info = chunks_info[:max_chunks]

    chunks = []
    for chunk_info in chunks_info:
        data = strax.load_file(
            os.path.join(data_dir, chunk_info["filename"]),
            compressor=compressor,
            dtype=dtype,
        )
        chunks.append(data)

    return np.concatenate(chunks)


# ── PMT geometry ────────────────────────────────────────────────


def load_pmt_geometry(context=None) -> np.ndarray:
    """Return PMT positions as a structured array with 'x','y','array','i'."""
    if context is not None:
        try:
            import straxen
            return straxen.pmt_positions()
        except Exception:
            pass
    try:
        import straxen
        return straxen.pmt_positions()
    except Exception:
        pass
    _here = os.path.dirname(__file__)
    _cached = os.path.join(_here, "..", "data", "pmt_positions.npy")
    if os.path.exists(_cached):
        return np.load(_cached, allow_pickle=True)
    # Last resort: built-in XENONnT positions
    return _make_xenonnt_pmt_positions()


def _make_xenonnt_pmt_positions() -> np.ndarray:
    """Build minimal XENONnT PMT geometry (top + bottom, 494 channels)."""
    import straxen
    try:
        return straxen.pmt_positions()
    except Exception:
        pass

    # Hard-coded fallback
    n_top = straxen.n_top_pmts if hasattr(straxen, "n_top_pmts") else 253
    n_total = 494
    tpc_r = 47.9

    dt = np.dtype([
        ("x", np.float64),
        ("y", np.float64),
        ("array", "U10"),
        ("i", np.int32),
    ])
    pos = np.zeros(n_total, dtype=dt)

    # approximate positions (concentric rings)
    rings_top = _concentric_rings(n_top, tpc_r * 0.85)
    rings_bot = _concentric_rings(n_total - n_top, tpc_r * 0.85)

    for i in range(n_top):
        pos[i]["x"] = rings_top[i][0]
        pos[i]["y"] = rings_top[i][1]
        pos[i]["array"] = "top"
        pos[i]["i"] = i

    for i in range(n_total - n_top):
        j = n_top + i
        pos[j]["x"] = rings_bot[i][0]
        pos[j]["y"] = rings_bot[i][1]
        pos[j]["array"] = "bottom"
        pos[j]["i"] = j

    return pos


def _concentric_rings(n: int, r: float) -> np.ndarray:
    """Distribute *n* points in concentric rings within radius *r*."""
    positions = []
    n_rings = max(1, int(np.sqrt(n)))
    for ring in range(n_rings):
        n_in_ring = int(n / n_rings)
        if ring == n_rings - 1:
            n_in_ring = n - len(positions)
        ring_r = r * (ring + 0.5) / n_rings
        for k in range(n_in_ring):
            angle = 2 * np.pi * k / n_in_ring
            positions.append((ring_r * np.cos(angle), ring_r * np.sin(angle)))
    return np.array(positions)


# ── to_pe (gains) ──────────────────────────────────────────────


def load_to_pe(context=None, n_channels: int = 494) -> np.ndarray:
    """Return PMT gain factors (to_pe).  Dead PMTs have gain=0."""
    if context is not None:
        try:
            return context.get_array(context.run_id, "to_pe")
        except Exception:
            pass
    try:
        import straxen
        ctx = straxen.contexts.xenonnt()
        # Try a known run
        return ctx.get_array("023756", "to_pe")
    except Exception:
        pass
    # Fallback: assume all PMTs active
    return np.ones(n_channels, dtype=float)


# ── raw_records → sum waveform builder ────────────────────────

def load_raw_records_window(
    run_id: str,
    t_start: int,
    t_end: int,
    storage_dirs: Optional[List[str]] = None,
) -> np.ndarray:
    """Load raw_records overlapping [*t_start*, *t_end*] (both in ns).

    Only loads chunks whose time range intersects the window, avoiding
    the cost of reading the full run.
    """
    import strax

    if storage_dirs is None:
        storage_dirs = [
            "/project/lgrandi/xenonnt/processed/",
            "/project2/lgrandi/xenonnt/processed/",
        ]

    # find the raw_records directory
    data_dir = find_data_dir(run_id, "raw_records", storage_dirs)
    if data_dir is None:
        raise FileNotFoundError(f"No raw_records for run {run_id}")

    meta_file = [f for f in os.listdir(data_dir) if f.endswith(".json")][0]
    with open(os.path.join(data_dir, meta_file)) as f:
        meta = json.load(f)

    dtype = eval(meta["dtype"])
    compressor = meta.get("compressor", "zstd")

    # select overlapping chunks
    chunks_to_load = []
    for ci in meta["chunks"]:
        if ci["end"] > t_start and ci["start"] < t_end:
            chunks_to_load.append(ci)

    if not chunks_to_load:
        return np.array([], dtype=dtype)

    records = []
    for ci in chunks_to_load:
        data = strax.load_file(
            os.path.join(data_dir, ci["filename"]),
            compressor=compressor,
            dtype=dtype,
        )
        mask = (data["time"] >= t_start) & (data["time"] < t_end)
        records.append(data[mask])

    if not records:
        return np.array([], dtype=dtype)
    return np.concatenate(records)


def build_sum_waveform(
    records: np.ndarray,
    t_start: int,
    t_end: int,
    t0: int = 0,
    dt_out: int = 10,
    to_pe: Optional[np.ndarray] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Build a sum waveform from raw_records.

    Parameters
    ----------
    records : raw_records array
    t_start, t_end : time range of interest in ns
    t0 : reference time for output x-axis
    dt_out : output sample width in ns
    to_pe : optional per-channel gain factors (n_pmts,). If provided,
        waveform is in PE/ns; otherwise in ADC/ns.

    Returns
    -------
    t_edges : (n_bins+1,) float – time in seconds relative to t0
    amplitude : (n_bins,) float – sum amplitude in PE/ns or ADC/ns
    """
    n_bins = int((t_end - t_start) / dt_out) + 1
    t_edges = np.linspace(t_start, t_start + n_bins * dt_out, n_bins + 1)

    # histogram accumulator
    amp_sum = np.zeros(n_bins + 1)  # +1 for edge safety

    for rec in records:
        ch = int(rec["channel"])
        rec_dt = int(rec["dt"])
        rec_len = int(rec["length"])
        rec_t0 = int(rec["time"])

        # Time of each sample in this record
        t_samples = rec_t0 + np.arange(rec_len) * rec_dt

        # Which output bins?
        bin_idx = ((t_samples - t_start) / dt_out).astype(int)
        valid = (bin_idx >= 0) & (bin_idx < n_bins)

        if not valid.any():
            continue

        data = rec["data"][:rec_len].astype(np.float64)
        if to_pe is not None and ch < len(to_pe) and to_pe[ch] > 0:
            data = data / rec_dt * to_pe[ch]
        else:
            data = data / rec_dt

        np.add.at(amp_sum, bin_idx[valid], data[valid])

    amp = amp_sum[:n_bins]
    t_out = (t_edges - t0) / 1e9  # seconds
    return t_out, amp


# ── .npz bundle save / load ────────────────────────────────────


def save_event_bundle(data: dict, path: str) -> None:
    """Save extracted event data to a compressed .npz file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    save = {}
    for k, v in data.items():
        if isinstance(v, np.ndarray):
            save[k] = v
        elif isinstance(v, str):
            save[k] = np.array([v])
    np.savez_compressed(path, **save)
    print(f"Saved {len(data.get('events', []))} events to {path}")


def load_event_bundle(path: str) -> dict:
    """Load event data from a .npz file created by save_event_bundle."""
    with np.load(path, allow_pickle=True) as f:
        data = {k: f[k] for k in f.files}
    for k in ("run_id",):
        if k in data and data[k].ndim == 1:
            data[k] = str(data[k][0])
    return data

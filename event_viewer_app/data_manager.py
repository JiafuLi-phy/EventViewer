"""Data loading and caching for the event viewer app.

Supports two backends:
1.  Pre-extracted .npz bundle directory
2.  Direct strax chunk access (event_info + peak_basics + event_area_per_channel)
"""

import os
import sys
from typing import Optional, List

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from event_plotter import io


class DataManager:
    """Loads and caches event data for the viewer."""

    def __init__(self):
        self._mode = None          # 'npz' or 'strax'
        self._npz_dir = None
        self._run_id = None
        self._events = None        # array of event_info rows
        self._peaks_cache = {}     # event_number → peaks array
        self._pmt_positions = None
        self._to_pe = None
        self._eac = None           # event_area_per_channel

    # ── open data source ─────────────────────────────────────────

    def open_npz_bundle(self, path: str) -> int:
        """Open a single .npz bundle file containing all events.

        The bundle must have keys: events, peaks_list, event_numbers,
        pmt_positions, to_pe, run_id.  Optional: eac_list.
        """
        self._mode = "npz"
        self._peaks_cache.clear()

        bundle = np.load(path, allow_pickle=True)

        self._events = bundle["events"]
        self._to_pe = bundle["to_pe"]
        self._run_id = str(bundle["run_id"])

        # Reconstruct PMT positions structured array
        if "pmt_positions" in bundle and bundle["pmt_positions"].dtype.names is not None:
            self._pmt_positions = bundle["pmt_positions"]
        elif "pmt_x" in bundle:
            dt = np.dtype([
                ("x", np.float64),
                ("y", np.float64),
                ("array", "U10"),
                ("i", np.int32),
            ])
            pos = np.zeros(len(bundle["pmt_x"]), dtype=dt)
            pos["x"] = bundle["pmt_x"]
            pos["y"] = bundle["pmt_y"]
            pos["array"] = bundle["pmt_array"].astype("U10")
            pos["i"] = bundle["pmt_i"]
            self._pmt_positions = pos
        else:
            self._pmt_positions = bundle.get("pmt_positions")

        # Cache peaks and eac by index
        self._peaks_by_idx = list(bundle["peaks_list"])
        self._eac_by_idx = list(bundle.get("eac_list", [None] * len(self._events)))
        self._event_to_idx = {}
        for i, ev in enumerate(self._events):
            ev_num = int(ev["event_number"])
            self._event_to_idx[ev_num] = i

        return len(self._events)

    def open_npz_directory(self, path: str) -> int:
        """Open a directory of per-event .npz files. Returns number of events found."""
        self._mode = "npz"
        self._npz_dir = path
        self._peaks_cache.clear()

        # scan for .npz files named event_*_run_*.npz
        bundles = []
        for fname in sorted(os.listdir(path)):
            if not fname.endswith(".npz"):
                continue
            if fname.startswith("event_") and "_run_" in fname:
                bundles.append(os.path.join(path, fname))

        # parse event info from filenames
        records = []
        for bpath in bundles:
            try:
                bname = os.path.basename(bpath)
                parts = bname.replace(".npz", "").split("_")
                ev_num = int(parts[1])
                run_id = parts[3] if len(parts) > 3 else "?"
                records.append((ev_num, run_id, bpath))
            except (ValueError, IndexError):
                continue

        if not records:
            self._events = np.array([])
            return 0

        dt = np.dtype([
            ("event_number", np.int32),
            ("run_id", "U20"),
            ("file_path", "U500"),
        ])
        self._events = np.array(records, dtype=dt)
        self._events.sort(order="event_number")

        # load shared data from first bundle
        if records:
            self._load_shared_from_bundle(records[0][2])

        return len(self._events)

    def open_strax_run(self, run_id: str, storage_dirs=None) -> int:
        """Open a run via direct strax chunk access. Returns number of events."""
        self._mode = "strax"
        self._run_id = run_id
        self._peaks_cache.clear()

        self._events = io.load_strax_chunks(run_id, "event_info", storage_dirs)
        self._pmt_positions = io.load_pmt_geometry()
        self._to_pe = io.load_to_pe(n_channels=len(self._pmt_positions))

        # try loading event_area_per_channel
        eac_dir = io.find_data_dir(run_id, "event_area_per_channel", storage_dirs)
        if eac_dir:
            self._eac = io.load_strax_chunks(run_id, "event_area_per_channel", storage_dirs)

        return len(self._events)

    def _load_shared_from_bundle(self, bundle_path: str):
        """Load pmt_positions and to_pe from a bundle."""
        data = io.load_event_bundle(bundle_path)
        self._pmt_positions = data.get("pmt_pos")
        self._to_pe = data.get("to_pe")
        self._run_id = str(data.get("run_id", "?"))

    # ── accessors ────────────────────────────────────────────────

    @property
    def mode(self) -> Optional[str]:
        return self._mode

    @property
    def events(self) -> np.ndarray:
        return self._events if self._events is not None else np.array([])

    @property
    def run_id(self) -> Optional[str]:
        return self._run_id

    def get_event(self, event_number: int) -> Optional[np.ndarray]:
        """Return the event_info row for *event_number*."""
        if self._events is None or len(self._events) == 0:
            return None
        mask = self._events["event_number"] == event_number
        idx = np.where(mask)[0]
        if len(idx) == 0:
            return None
        return self._events[idx[0]]

    def get_peaks(self, event_number: int) -> Optional[np.ndarray]:
        """Return peaks for *event_number*, caching after first load."""
        if event_number in self._peaks_cache:
            return self._peaks_cache[event_number]

        if self._mode == "npz":
            # Bundle format: peaks pre-loaded by index
            if hasattr(self, "_peaks_by_idx") and self._peaks_by_idx is not None:
                idx = self._event_to_idx.get(event_number)
                if idx is not None and idx < len(self._peaks_by_idx):
                    peaks = self._peaks_by_idx[idx]
                    self._peaks_cache[event_number] = peaks
                    return peaks
            # Directory format: load from per-event .npz
            ev = self.get_event(event_number)
            if ev is None:
                return None
            data = io.load_event_bundle(str(ev["file_path"]))
            peaks = data.get("peaks")
            self._peaks_cache[event_number] = peaks
            return peaks

        elif self._mode == "strax":
            ev = self.get_event(event_number)
            if ev is None:
                return None
            import strax
            peaks = io.load_strax_chunks(
                self._run_id, "peak_basics",
            )
            fci = strax.fully_contained_in(peaks, np.array([ev]))
            ev_peaks = peaks[fci == 0]
            self._peaks_cache[event_number] = ev_peaks
            return ev_peaks

        return None

    def get_pmt_positions(self) -> Optional[np.ndarray]:
        return self._pmt_positions

    def get_to_pe(self) -> Optional[np.ndarray]:
        return self._to_pe

    def get_event_area_per_channel(self, event_number: int) -> Optional[np.ndarray]:
        """Return eac row for *event_number*."""
        if self._mode == "npz":
            if hasattr(self, "_eac_by_idx") and self._eac_by_idx is not None:
                idx = self._event_to_idx.get(event_number)
                if idx is not None and idx < len(self._eac_by_idx):
                    eac = self._eac_by_idx[idx]
                    return eac if eac is not None and (isinstance(eac, np.ndarray) or isinstance(eac, np.void)) else None
            return None

        if self._mode != "strax" or self._eac is None:
            return None
        ev = self.get_event(event_number)
        if ev is None:
            return None
        import strax
        fci = strax.fully_contained_in(self._eac, np.array([ev]))
        idx = np.where(fci == 0)[0]
        if len(idx):
            return self._eac[idx[0]]
        return None

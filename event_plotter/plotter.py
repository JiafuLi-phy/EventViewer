"""Core plotting functions for XENONnT event waveforms.

All functions accept numpy structured arrays (peaks, events, to_pe)
so they work independently of how data was loaded.

Two data modes are supported:
- **full peaks** with ``data`` and ``area_per_channel`` fields (draws
  actual step-waveforms)
- **peak_basics** with only metadata (draws coloured time-span markers)
"""

from typing import Dict, List, Optional, Tuple

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np

from . import style

# ── data detection ──────────────────────────────────────────────


def has_waveform(peaks: np.ndarray) -> bool:
    """Return True if *peaks* has a ``data`` field suitable for waveform drawing."""
    names = getattr(getattr(peaks, "dtype", None), "names", None) or ()
    return "data" in names


def has_per_channel(peaks: np.ndarray) -> bool:
    """Return True if *peaks* has ``area_per_channel``."""
    names = getattr(getattr(peaks, "dtype", None), "names", None) or ()
    return "area_per_channel" in names


def has_top_waveform(peaks: np.ndarray) -> bool:
    """Return True if *peaks* has top-array waveform samples."""
    names = getattr(getattr(peaks, "dtype", None), "names", None) or ()
    return "data_top" in names


# ── low-level waveform helpers ─────────────────────────────────


def time_and_samples(
    peak: np.ndarray,
    t0: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (x_seconds, y_pe_per_ns) for a step-plot of *peak*.

    Parameters
    ----------
    peak : single element of a peaks array
    t0 : int, optional
        Reference time in ns.  Defaults to ``peak['time']``.

    Returns
    -------
    x : (N+1,) float – time in seconds relative to *t0*
    y : (N+1,) float – amplitude in PE/ns
    """
    n = int(peak["length"])
    if t0 is None:
        t0 = int(peak["time"])
    x = (int(peak["time"]) - t0 + np.arange(n + 1) * peak["dt"]) / 1000
    y = peak["data"][:n] / peak["dt"]
    return x, np.concatenate([[y[0]], y])


def time_and_component_samples(
    peak: np.ndarray,
    component: str = "total",
    t0: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return step x/y arrays for total, top, or bottom peak waveform."""
    n = int(peak["length"])
    dt = int(peak["dt"])
    if t0 is None:
        t0 = int(peak["time"])
    total = peak["data"][:n].astype(float)
    if component == "top" and "data_top" in peak.dtype.names:
        data = peak["data_top"][:n].astype(float)
    elif component == "bottom" and "data_top" in peak.dtype.names:
        data = total - peak["data_top"][:n].astype(float)
    else:
        data = total
    x = (int(peak["time"]) - t0 + np.arange(n + 1) * dt) / 1000
    y = data / dt
    return x, np.concatenate([[y[0]], y])


def plot_peak_component_waveform(
    peak: np.ndarray,
    component: str,
    t0: int,
    ax: plt.Axes,
    color: str,
    alpha_fill: float = 0.18,
    linewidth: float = 0.6,
    label: Optional[str] = None,
):
    """Draw one component from real peak waveform samples."""
    x, y = time_and_component_samples(peak, component=component, t0=t0)
    line = ax.plot(x, y, drawstyle="steps-pre", color=color,
                   linewidth=linewidth, label=label)
    fill = ax.fill_between(x, 0, y, step="pre", color=color,
                           alpha=alpha_fill, linewidth=0)
    return [*line, fill]


def _step_patch_coords(
    peak: np.ndarray,
    t0: int = 0,
    time_scaler: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray]:
    """Return (x, y) for a matplotlib fill_between step-patch.

    *time_scaler* converts ns → other units (e.g. 1e3 → μs).
    """
    n = int(peak["length"])
    xx = np.arange(n + 1) * peak["dt"] + (int(peak["time"]) - t0)
    xx = xx / time_scaler
    yy = peak["data"][:n] / peak["dt"]
    # duplicate for steps-pre
    xp = np.zeros(2 * n + 2)
    yp = np.zeros(2 * n + 2)
    xp[0], yp[0] = xx[0], 0.0
    xp[1:-1:2] = xx[:-1]
    xp[2::2] = xx[1:]
    yp[1:-1:2] = yy
    yp[2::2] = yy
    xp[-1], yp[-1] = xx[-1], 0.0
    return xp, yp


# ── peak-level plotting ────────────────────────────────────────


def plot_peak_waveform(
    peak: np.ndarray,
    t0: Optional[int] = None,
    ax: Optional[plt.Axes] = None,
    color: Optional[str] = None,
    alpha_fill: float = 0.25,
    linewidth: float = 0.6,
    center_time: bool = False,
    label: Optional[str] = None,
) -> plt.Axes:
    """Draw a single peak as a filled step-waveform.

    Parameters
    ----------
    peak : single peak element
    t0 : reference time in ns (default: peak['time'])
    ax : matplotlib Axes (creates one if None)
    color : line & fill colour. Defaults to ``PEAK_COLORS[peak['type']]``
    alpha_fill : transparency of the filled area
    linewidth : line width
    center_time : if True, mark center_time with a dashed vertical line
    label : legend label
    """
    if ax is None:
        ax = plt.gca()
    if color is None:
        ptype = int(peak["type"])
        color = style.PEAK_COLORS.get(ptype, style.NEUTRAL_MID)

    x, y = time_and_samples(peak, t0=t0)

    ax.plot(x, y, drawstyle="steps-pre", color=color, linewidth=linewidth, label=label)
    ax.fill_between(x, 0, y, step="pre", color=color, alpha=alpha_fill, linewidth=0)

    # extent marker
    ax.plot(
        [x[0], x[-1]], [y.max(), y.max()],
        color="k", alpha=0.25, linewidth=0.5,
    )

    if center_time:
        if t0 is None:
            t0 = int(peak["time"])
        ct = (int(peak["center_time"]) - t0) / 1000
        ax.axvline(ct, color="k", alpha=0.35, linewidth=0.6, linestyle="--")

    return ax


def _model_pulse_waveform(peak: np.ndarray, n_samples: int = 200) -> Tuple[np.ndarray, np.ndarray]:
    """Build a model pulse (double-exponential) from peak_basics metadata.

    Uses rise_time and range_90p_area to construct a realistic
    fast-rise / slow-decay pulse shape when real waveform data is
    unavailable.

    Returns (t_rel_ns, amplitude) arrays.
    """
    area = float(peak["area"])
    dt = int(peak["dt"]) if "dt" in peak.dtype.names else 10
    if "endtime" in peak.dtype.names:
        duration = int(peak["endtime"]) - int(peak["time"])
    elif "length" in peak.dtype.names:
        duration = int(peak["length"]) * dt
    else:
        duration = n_samples * dt
    duration = max(duration, dt)

    # Rise time: time from 10% to 50% of cumulative integral
    rise = float(peak["rise_time"]) if "rise_time" in peak.dtype.names else 10.0
    if rise <= 0:
        rise = 20.0

    # Range containing 90% of area — use as width constraint
    if "range_90p_area" in peak.dtype.names:
        w90 = float(peak["range_90p_area"])
    else:
        w90 = duration
    if w90 <= 0:
        w90 = duration

    # Build a skewed pulse: fast rise, slow decay
    tau_rise = max(rise / 3.0, dt * 0.5)
    tau_fall = max((w90 - rise) / 3.0, tau_rise * 2)

    t = np.linspace(0, duration, n_samples)
    # Difference of exponentials convolved with step gives smooth pulse
    y = np.exp(-t / tau_fall) - np.exp(-t / tau_rise)
    y = np.maximum(y, 0)

    # Normalize to preserve area
    if y.sum() > 0:
        y = y * area / (y.sum() * duration / n_samples)

    return t, y


def plot_peak_waveform_model(
    peak: np.ndarray,
    t0: Optional[int] = None,
    ax: Optional[plt.Axes] = None,
    color: Optional[str] = None,
    alpha_fill: float = 0.3,
    linewidth: float = 0.6,
    label: Optional[str] = None,
) -> plt.Axes:
    """Draw a model pulse for a peak that lacks waveform data.

    Uses _model_pulse_waveform to construct a realistic pulse shape
    from rise_time and area metadata.  Much more informative than
    the plain rectangle fallback.
    """
    if ax is None:
        ax = plt.gca()
    if color is None:
        ptype = int(peak["type"])
        color = style.PEAK_COLORS.get(ptype, style.NEUTRAL_MID)
    if t0 is None:
        t0 = int(peak["time"])

    t_rel, y = _model_pulse_waveform(peak)
    t_abs = int(peak["time"]) - t0 + t_rel  # ns
    x = t_abs / 1000  # seconds

    ax.plot(x, y, color=color, linewidth=linewidth, label=label)
    ax.fill_between(x, 0, y, color=color, alpha=alpha_fill, linewidth=0)

    return ax


def _plot_step_arrays(ax, x, series, colors, labels, linewidths=None, alphas=None):
    """Draw one or more already-binned waveforms as filled step arrays."""
    artists = {}
    if linewidths is None:
        linewidths = [2.4] * len(series)
    if alphas is None:
        alphas = [0.25] * len(series)
    for y, color, label, lw, alpha in zip(series, colors, labels, linewidths, alphas):
        line = ax.plot(x[:-1], y, drawstyle="steps-post", color=color, linewidth=lw, label=label)
        fill = ax.fill_between(x[:-1], 0, y, step="post", color=color, alpha=alpha, linewidth=0)
        artists[label.lower()] = [*line, fill]
    return artists


def plot_peak_markers(
    peaks: np.ndarray,
    t0: Optional[int] = None,
    ax: Optional[plt.Axes] = None,
    colors: Optional[Dict[int, str]] = None,
    alpha: float = 0.35,
    height_scale: float = 0.85,
    legend: bool = True,
) -> plt.Axes:
    """Draw coloured time-span rectangles for peaks (no waveform required).

    Use this when peaks only have time/endtime/type/area metadata
    (e.g. peak_basics).  The rectangle height is proportional to
    log10(area).
    """
    if ax is None:
        ax = plt.gca()
    if colors is None:
        colors = style.PEAK_COLORS
    if t0 is None and len(peaks):
        t0 = int(peaks[0]["time"])

    peaks = peaks[np.argsort(peaks["time"])]
    areas = peaks["area"].astype(float)
    with np.errstate(divide="ignore"):
        log_areas = np.log10(areas)
        log_areas[~np.isfinite(log_areas)] = 0.0
    if log_areas.max() > 0:
        h = log_areas / log_areas.max() * height_scale
    else:
        h = np.full_like(log_areas, height_scale * 0.5)

    plotted_types = set()
    for i, p in enumerate(peaks):
        ptype = int(p["type"])
        c = colors.get(ptype, style.NEUTRAL_MID)
        lbl = style.PEAK_LABELS.get(ptype, f"type={ptype}")
        if ptype in plotted_types:
            lbl = None
        plotted_types.add(ptype)

        x_start = (int(p["time"]) - t0) / 1000
        length = int(p["length"]) if "length" in p.dtype.names else 1
        dt = int(p["dt"]) if "dt" in p.dtype.names else 10
        x_end = x_start + length * dt / 1000
        # if endtime available, use it (more accurate)
        if "endtime" in p.dtype.names:
            x_end = (int(p["endtime"]) - t0) / 1000

        ax.axvspan(x_start, x_end, ymin=0, ymax=float(h[i]),
                   color=c, alpha=alpha, linewidth=0, label=lbl)

    ax.set_ylim(0, 1.05)
    ax.set_ylabel("log₁₀(area) / max")
    ax.set_xlabel("Time [μs]")
    if legend:
        ax.legend(loc="upper right", fontsize=style.plt.rcParams["legend.fontsize"])
    return ax


def _plot_peak_from_records(
    peak: np.ndarray,
    raw_records: np.ndarray,
    t0: int = 0,
    ax: Optional[plt.Axes] = None,
    color: Optional[str] = None,
    alpha_fill: float = 0.25,
    linewidth: float = 0.6,
    label: Optional[str] = None,
    to_pe: Optional[np.ndarray] = None,
    margin_ns: int = 200,
) -> None:
    """Draw a single peak waveform built from raw_records.

    Loads raw_records within the peak's time range, builds a sum
    waveform, and plots as a filled step-plot.
    """
    from . import io as _io

    if ax is None:
        ax = plt.gca()
    if color is None:
        ptype = int(peak["type"])
        color = style.PEAK_COLORS.get(ptype, style.NEUTRAL_MID)

    t_start = int(peak["time"]) - margin_ns
    t_end = int(peak["endtime"]) + margin_ns
    dt = int(peak["dt"]) if "dt" in peak.dtype.names else 10

    # filter raw_records to the peak's time window
    rr_mask = (raw_records["time"] >= t_start) & (raw_records["time"] < t_end)
    recs = raw_records[rr_mask]

    if len(recs) == 0:
        return

    t_edges, amp = _io.build_sum_waveform(
        recs, t_start, t_end, t0=t0, dt_out=dt, to_pe=to_pe,
    )

    if len(amp) == 0:
        return

    # step-plot
    x = np.repeat(t_edges, 2)[1:-1]
    y = np.repeat(amp, 2)

    ax.plot(x, y, color=color, linewidth=linewidth, label=label)
    ax.fill_between(x, 0, y, color=color, alpha=alpha_fill, linewidth=0)


def plot_peaks(
    peaks: np.ndarray,
    t0: Optional[int] = None,
    ax: Optional[plt.Axes] = None,
    show_largest: int = 200,
    colors: Optional[Dict[int, str]] = None,
    alpha_fill: float = 0.2,
    linewidth: float = 0.5,
    legend: bool = True,
    raw_records: Optional[np.ndarray] = None,
    to_pe: Optional[np.ndarray] = None,
    highlight_idx: Optional[int] = None,
) -> plt.Axes:
    """Draw all peaks overlaid on one axes.

    If peaks have ``data`` field, draws full step-waveforms.
    If *raw_records* is provided, builds sum waveforms from raw records
    for each peak (much better than the marker fallback).
    Otherwise falls back to coloured time-span markers.

    Peaks are coloured by type (S1=blue, S2=green, unknown=gray).

    Stores ``ax._peak_regions`` for hit-testing on click events.
    """
    if ax is None:
        ax = plt.gca()
    if colors is None:
        colors = style.PEAK_COLORS
    if t0 is None and len(peaks):
        t0 = int(peaks[0]["time"])

    # keep the largest N by area (track original indices)
    original_indices = np.arange(len(peaks))
    if len(peaks) > show_largest:
        order = np.argsort(peaks["area"])[::-1][:show_largest]
        peaks = peaks[order]
        original_indices = original_indices[order]
    time_order = np.argsort(peaks["time"])
    peaks = peaks[time_order]
    original_indices = original_indices[time_order]

    # Store peak hit regions on the axes for interactive clicking
    # Ensure minimum clickable width for narrow peaks
    MIN_CLICK_WIDTH = 1e-4  # 100 microseconds in seconds
    ax._peak_regions = []

    if has_waveform(peaks):
        plotted_types = set()
        for i, p in enumerate(peaks):
            ptype = int(p["type"])
            c = colors.get(ptype, style.NEUTRAL_MID)
            lbl = style.PEAK_LABELS.get(ptype, f"type={ptype}")
            if ptype in plotted_types:
                lbl = None
            plotted_types.add(ptype)
            _af = alpha_fill * 3 if highlight_idx is not None and original_indices[i] == highlight_idx else alpha_fill
            _lw = linewidth * 4 if highlight_idx is not None and original_indices[i] == highlight_idx else linewidth
            plot_peak_waveform(
                p, t0=t0, ax=ax, color=c, alpha_fill=_af,
                linewidth=_lw, label=lbl,
            )
            # record hit region
            x_start = (int(p["time"]) - t0) / 1000
            n = int(p["length"])
            dt = int(p["dt"]) if "dt" in p.dtype.names else 10
            x_end = x_start + n * dt / 1000
            ax._peak_regions.append({
                "x_start": x_start, "x_end": x_end,
                "center_x": (x_start + x_end) / 2,
                "index": int(original_indices[i]),
                "type": ptype, "area": float(p["area"]),
                "time": int(p["time"]), "endtime": int(p["time"]) + n * dt,
            })
        ax.set_ylabel("Intensity [PE/ns]")
        style.tighten_ylim(ax)
    elif raw_records is not None and len(raw_records):
        from . import io as _io
        plotted_types = set()
        for i, p in enumerate(peaks):
            ptype = int(p["type"])
            c = colors.get(ptype, style.NEUTRAL_MID)
            lbl = style.PEAK_LABELS.get(ptype, f"type={ptype}")
            if ptype in plotted_types:
                lbl = None
            plotted_types.add(ptype)
            _af = alpha_fill * 3 if highlight_idx is not None and original_indices[i] == highlight_idx else alpha_fill
            _lw = linewidth * 4 if highlight_idx is not None and original_indices[i] == highlight_idx else linewidth
            _plot_peak_from_records(
                p, raw_records, t0=t0, ax=ax, color=c,
                alpha_fill=_af, linewidth=_lw,
                label=lbl, to_pe=to_pe,
            )
            x_start = (int(p["time"]) - t0) / 1000
            x_end = (int(p["endtime"]) - t0) / 1000 if "endtime" in p.dtype.names else x_start + 1e-8
            ax._peak_regions.append({
                "x_start": x_start, "x_end": x_end,
                "center_x": (x_start + x_end) / 2,
                "index": int(original_indices[i]),
                "type": ptype, "area": float(p["area"]),
                "time": int(p["time"]),
                "endtime": int(p["endtime"]) if "endtime" in p.dtype.names else int(p["time"]) + int(p["length"]) * int(p["dt"]),
            })
        ax.set_ylabel("Amplitude [ADC/ns]" if to_pe is None else "Intensity [PE/ns]")
        style.tighten_ylim(ax)
    else:
        # Use model pulse shapes (fast rise / slow decay) from metadata
        plotted_types = set()
        for i, p in enumerate(peaks):
            ptype = int(p["type"])
            c = colors.get(ptype, style.NEUTRAL_MID)
            lbl = style.PEAK_LABELS.get(ptype, f"type={ptype}")
            if ptype in plotted_types:
                lbl = None
            plotted_types.add(ptype)
            _af = alpha_fill * 3 if highlight_idx is not None and original_indices[i] == highlight_idx else alpha_fill
            _lw = linewidth * 4 if highlight_idx is not None and original_indices[i] == highlight_idx else linewidth
            plot_peak_waveform_model(
                p, t0=t0, ax=ax, color=c, alpha_fill=_af,
                linewidth=_lw, label=lbl,
            )
            x_start = (int(p["time"]) - t0) / 1000
            end_ns = int(p["endtime"]) if "endtime" in p.dtype.names else int(p["time"]) + int(p["length"]) * int(p["dt"])
            x_end = (end_ns - t0) / 1000
            ax._peak_regions.append({
                "x_start": x_start, "x_end": x_end,
                "center_x": (x_start + x_end) / 2,
                "index": int(original_indices[i]),
                "type": ptype, "area": float(p["area"]),
                "time": int(p["time"]),
                "endtime": end_ns,
            })
        ax.set_ylabel("Model pulse [PE/ns]")
        style.tighten_ylim(ax)

    ax.axhline(0, color="k", alpha=0.15, linewidth=0.4)
    ax.set_xlabel("Time [μs]", fontsize=style.plt.rcParams["font.size"] + 1, fontweight="bold")
    if legend:
        ax.legend(loc="upper right", fontsize=style.plt.rcParams["legend.fontsize"])
    return ax


# ── PMT hit-pattern plotting ───────────────────────────────────


def plot_pmt_hit_pattern(
    area_per_channel: np.ndarray,
    pmt_positions: np.ndarray,
    to_pe: np.ndarray,
    array_name: str = "top",
    ax: Optional[plt.Axes] = None,
    log_scale: bool = False,
    vmin: Optional[float] = None,
    vmax: Optional[float] = None,
    cmap: str = "Blues",
    dead_pmt_color: str = "#D0D0D0",
    marker_size: float = 80,
    show_colorbar: bool = True,
    label: Optional[str] = None,
) -> plt.Axes:
    """Plot one PMT array coloured by per-channel area.

    Parameters
    ----------
    area_per_channel : (n_tpc_pmts,) float – area per PMT in PE
    pmt_positions : structured array with 'x','y','array','i' fields
    to_pe : (n_tpc_pmts,) float – gain factor, zero for dead PMTs
    array_name : 'top' or 'bottom'
    ax : matplotlib Axes
    log_scale : use LogNorm for colour mapping
    vmin, vmax : colour-scale limits
    cmap : matplotlib colormap name
    dead_pmt_color : colour for PMTs with gain=0
    marker_size : scatter marker size
    show_colorbar : add a colour bar
    label : colour bar label text
    """
    if ax is None:
        ax = plt.gca()

    # select the correct array
    mask_arr = pmt_positions["array"] == array_name
    pos = pmt_positions[mask_arr]
    area = area_per_channel[pos["i"]]

    # dead PMTs (gain = 0)
    mask_dead = (to_pe[pos["i"]] == 0)

    # colour mapping
    if log_scale:
        # set zero / negative values above vmin
        _area_plot = np.where(area > 0, area, np.nan)
        norm = matplotlib.colors.LogNorm(
            vmin=vmin or np.nanmin(_area_plot),
            vmax=vmax or np.nanmax(_area_plot),
        )
    else:
        norm = matplotlib.colors.Normalize(
            vmin=vmin or np.nanmin(area),
            vmax=vmax or np.nanmax(area),
        )

    # plot active PMTs
    active = ~mask_dead
    # Store PMT IDs for hover display
    ax._pmt_ids = pos["i"].tolist()
    sc = ax.scatter(
        pos["x"][active], pos["y"][active],
        c=area[active], norm=norm, cmap=cmap,
        s=marker_size, edgecolors="white", linewidths=0.2,
        zorder=3,
    )

    # dead PMTs
    if mask_dead.any():
        ax.scatter(
            pos["x"][mask_dead], pos["y"][mask_dead],
            c=dead_pmt_color, s=marker_size,
            edgecolors="white", linewidths=0.5,
            zorder=2,
        )

    # PMT array boundary circle
    # Compute from PMT positions to match actual detector geometry
    pmt_r = np.sqrt(pmt_positions["x"]**2 + pmt_positions["y"]**2).max()
    r_bound = pmt_r * 1.02
    ax.add_artist(
        plt.Circle(
            (0, 0), r_bound,
            edgecolor="k", facecolor="none",
            linewidth=1.2, zorder=1,
        )
    )

    ax.set_xlabel("x [cm]")
    ax.set_ylabel("y [cm]")
    ax.set_title(array_name.capitalize(), fontsize=style.plt.rcParams["font.size"])

    if show_colorbar:
        cbar = ax.figure.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(label or "Area [PE]", fontsize=style.plt.rcParams["legend.fontsize"])

    # Set aspect and limits AFTER colorbar to avoid distortion
    ax.set_aspect("equal")
    ax.set_xlim(-r_bound * 1.06, r_bound * 1.06)
    ax.set_ylim(-r_bound * 1.06, r_bound * 1.06)

    return ax


def plot_pmt_pattern_both(
    area_per_channel: np.ndarray,
    pmt_positions: np.ndarray,
    to_pe: np.ndarray,
    figsize: Tuple[float, float] = (8, 3.5),
    **kwargs,
) -> Tuple[plt.Figure, Tuple[plt.Axes, plt.Axes]]:
    """Plot both top and bottom PMT arrays side by side.

    Returns (fig, (ax_top, ax_bottom)).
    """
    fig, (ax_t, ax_b) = plt.subplots(1, 2, figsize=figsize)
    plot_pmt_hit_pattern(
        area_per_channel, pmt_positions, to_pe,
        array_name="top", ax=ax_t, **kwargs,
    )
    plot_pmt_hit_pattern(
        area_per_channel, pmt_positions, to_pe,
        array_name="bottom", ax=ax_b, **kwargs,
    )
    plt.subplots_adjust(wspace=0.35)
    return fig, (ax_t, ax_b)


# ── full event display figure ──────────────────────────────────


def plot_event_full(
    event: np.ndarray,
    peaks: np.ndarray,
    to_pe: np.ndarray,
    pmt_positions: np.ndarray,
    event_area_per_channel: Optional[np.ndarray] = None,
    s1_hp_kwargs: Optional[dict] = None,
    s2_hp_kwargs: Optional[dict] = None,
    figsize: Tuple[float, float] = (14, 12),
    show_largest: int = 200,
    title: Optional[str] = None,
    fig: Optional[plt.Figure] = None,
    raw_records: Optional[np.ndarray] = None,
    run_id: Optional[str] = None,
    highlight_peak_idx: Optional[int] = None,
) -> plt.Figure:
    """Event display — vertical pages: waveform then PMT patterns.

    Layout::

        ┌───────────────────────────────────────┐
        │   Event waveform                      │
        │   (top + bottom = total, 3 layers)    │
        ├──────────────────┬────────────────────┤
        │   PMT Top        │   PMT Bottom       │
        └──────────────────┴────────────────────┘

    Parameters
    ----------
    event : single event element from events array
    peaks : peaks within this event
    to_pe : (n_tpc_pmts,) gain array
    pmt_positions : PMT geometry structured array
    event_area_per_channel : optional structured array with
        s1_area_per_channel / s2_area_per_channel fields
    s1_hp_kwargs, s2_hp_kwargs : extra kwargs for hit-pattern panels
    figsize : figure size in inches
    show_largest : max peaks to draw in the full-event panel

    Returns
    -------
    fig : matplotlib Figure
    """
    if s1_hp_kwargs is None:
        s1_hp_kwargs = {}
    if s2_hp_kwargs is None:
        s2_hp_kwargs = {}

    if s1_hp_kwargs is None:
        s1_hp_kwargs = {}
    if s2_hp_kwargs is None:
        s2_hp_kwargs = {}

    if fig is None:
        fig = plt.figure(figsize=figsize, facecolor="white")
    else:
        fig.set_size_inches(figsize)
        fig.clf()

    _rsize = style.plt.rcParams["font.size"]

    # ── Row 1: Event waveform (3-layer: top+bottom=total) ──
    gs = gridspec.GridSpec(2, 2, figure=fig,
                           height_ratios=[1.0, 1.0],
                           hspace=0.5, wspace=0.4)

    ax_wf = fig.add_subplot(gs[0, :])  # full width waveform
    ax_pmt_top = fig.add_subplot(gs[1, 0])
    ax_pmt_bot = fig.add_subplot(gs[1, 1])

    fig._peak_axes = [ax_wf]

    t0_ev = int(event["time"])
    if len(peaks):
        _draw_3layer_waveform(
            peaks, t0=t0_ev, ax=ax_wf, show_largest=show_largest,
            raw_records=raw_records, to_pe=to_pe, pmt_positions=pmt_positions,
            highlight_idx=highlight_peak_idx,
        )
    ax_wf.set_title("Event waveform: top + bottom + total",
                    fontsize=_rsize + 3, fontweight="bold")

    # ── Row 2: PMT patterns (event total) ──
    if event_area_per_channel is not None:
        ev_area = np.zeros(len(to_pe))
        for key in ("s1_area_per_channel", "s2_area_per_channel",
                     "alt_s1_area_per_channel", "alt_s2_area_per_channel"):
            if key in event_area_per_channel.dtype.names:
                ev_area += event_area_per_channel[key]
    else:
        ev_area = np.zeros(len(to_pe))

    for ax_pmt, arr_name in [(ax_pmt_top, "top"), (ax_pmt_bot, "bottom")]:
        plot_pmt_hit_pattern(ev_area, pmt_positions, to_pe,
                             array_name=arr_name, ax=ax_pmt, cmap="plasma",
                             vmin=0, marker_size=120,
                             show_colorbar=True, label="Area [PE]")
        ax_pmt.set_title(f"Event {arr_name.capitalize()} PMT", fontweight="bold")

    if title is None:
        title = _make_event_title(event, run_id=run_id)
    fig.suptitle(title, fontsize=_rsize + 4, fontweight="bold", y=0.97)

    return fig


def _draw_3layer_waveform(
    peaks, t0, ax, show_largest=200, raw_records=None, to_pe=None,
    pmt_positions=None, highlight_idx=None,
):
    """Draw all peaks as model pulses with top/bottom/total layers.
    Stores _peak_regions with original indices for click handling."""
    original_idx = np.arange(len(peaks))
    if len(peaks) > show_largest:
        order = np.argsort(peaks["area"])[::-1][:show_largest]
        peaks = peaks[order]
        original_idx = original_idx[order]
    time_order = np.argsort(peaks["time"])
    peaks = peaks[time_order]
    original_idx = original_idx[time_order]

    plotted_types = set()
    ax._peak_regions = []

    if has_waveform(peaks):
        legend_artists = {"top": [], "bottom": [], "total": []}
        for i, p in enumerate(peaks):
            orig_i = original_idx[i]
            ptype = int(p["type"])
            total_color = "#F44336"  # bright red
            top_lbl = "Top" if "top" not in plotted_types else None
            bot_lbl = "Bottom" if "bottom" not in plotted_types else None
            total_lbl = "Total" if "total" not in plotted_types else None
            plotted_types.update({"top", "bottom", "total"})
            lw_scale = 3 if highlight_idx is not None and orig_i == highlight_idx else 1

            if has_top_waveform(np.array([p])):
                legend_artists["top"].extend(plot_peak_component_waveform(
                    p, "top", t0, ax, "#2196F3",
                    alpha_fill=0.16, linewidth=0.75 * lw_scale, label=top_lbl,
                ))
                legend_artists["bottom"].extend(plot_peak_component_waveform(
                    p, "bottom", t0, ax, "#4CAF50",
                    alpha_fill=0.16, linewidth=0.75 * lw_scale, label=bot_lbl,
                ))
            legend_artists["total"].extend(plot_peak_component_waveform(
                p, "total", t0, ax, total_color,
                alpha_fill=0.22, linewidth=1.05 * lw_scale, label=total_lbl,
            ))

            x_start = (int(p["time"]) - t0) / 1000
            end_ns = int(p["endtime"]) if "endtime" in p.dtype.names else int(p["time"]) + int(p["length"]) * int(p["dt"])
            x_end = (end_ns - t0) / 1000
            ax._peak_regions.append({
                "x_start": x_start, "x_end": x_end,
                "center_x": (x_start + x_end) / 2,
                "index": int(orig_i), "type": ptype, "area": float(p["area"]),
            })

        ax.axhline(0, color="k", alpha=0.15, linewidth=0.4)
        ax.set_xlabel("Time [μs]", fontweight="bold")
        ax.set_ylabel("Real peak waveform [PE/ns]")
        style.tighten_ylim(ax)
        leg = ax.legend(loc="upper right", fontsize=style.plt.rcParams["legend.fontsize"])
        for txt in leg.get_texts():
            txt.set_picker(True)
        ax._legend_artists = {k: v for k, v in legend_artists.items() if v}
        ax._legend_state = {k: True for k in ax._legend_artists}
        return

    if raw_records is not None and len(raw_records) and pmt_positions is not None:
        from . import io as _io
        t_start = min(int(peaks["time"].min()), int(raw_records["time"].min()))
        t_end = max(
            int(peaks["endtime"].max()) if "endtime" in peaks.dtype.names else int(peaks["time"].max()),
            int(raw_records["time"].max()),
        )
        dt = int(np.median(raw_records["dt"])) if "dt" in raw_records.dtype.names else 10
        x, y_top, y_bot, y_total = _io.build_array_waveforms(
            raw_records, t_start, t_end, pmt_positions, t0=t0, dt_out=dt, to_pe=to_pe
        )
        artists = _plot_step_arrays(
            ax, x, [y_top, y_bot, y_total],
            ["#2196F3", "#4CAF50", "#F44336"],
            ["Top", "Bottom", "Total"],
            linewidths=[1.35, 1.35, 2.4],
            alphas=[0.18, 0.18, 0.12],
        )
        ax._legend_artists = {
            "top": artists["top"],
            "bottom": artists["bottom"],
            "total": artists["total"],
        }
        ax._legend_state = {"top": True, "bottom": True, "total": True}
        for i, p in enumerate(peaks):
            orig_i = original_idx[i]
            x_start = (int(p["time"]) - t0) / 1000
            end_ns = int(p["endtime"]) if "endtime" in p.dtype.names else int(p["time"]) + int(p["length"]) * int(p["dt"])
            x_end = (end_ns - t0) / 1000
            ax._peak_regions.append({
                "x_start": x_start, "x_end": x_end,
                "center_x": (x_start + x_end) / 2,
                "index": int(orig_i), "type": int(p["type"]), "area": float(p["area"]),
            })
        ax.set_xlabel("Time [μs]", fontweight="bold")
        ax.set_ylabel("Intensity [PE/ns]")
        style.tighten_ylim(ax)
        leg = ax.legend(loc="upper right", fontsize=style.plt.rcParams["legend.fontsize"])
        for txt in leg.get_texts():
            txt.set_picker(True)
        return

    # Pre-compute frac_top for all peaks
    peak_data = []
    for i, p in enumerate(peaks):
        orig_i = original_idx[i]
        ptype = int(p["type"])
        if "area_fraction_top" in p.dtype.names:
            frac_top = float(p["area_fraction_top"])
        elif "data_top" in p.dtype.names and "data" in p.dtype.names:
            dtop = p["data_top"][:int(p["length"])].sum()
            dtot = p["data"][:int(p["length"])].sum()
            frac_top = dtop / dtot if dtot > 0 else 0.5
        else:
            frac_top = 0.5
        area_tot = float(p["area"])
        peak_data.append((i, orig_i, p, ptype, frac_top, area_tot))

    # Pass 1: draw ALL Top layers first
    for i, orig_i, p, ptype, frac_top, area_tot in peak_data:
        if ptype == 1 and "top" not in plotted_types:
            top_lbl = "Top"; plotted_types.add("top")
        else: top_lbl = None
        p_top = p.copy()
        p_top["area"] = area_tot * frac_top
        lw_scale = 3 if highlight_idx is not None and orig_i == highlight_idx else 1
        plot_peak_waveform_model(p_top, t0=t0, ax=ax,
            color="#2196F3", alpha_fill=0.08, linewidth=0.9 * lw_scale,
            label=top_lbl)
    # Reset for pass 2
    if "top" in plotted_types: plotted_types.remove("top")

    # Pass 2: draw ALL Bottom layers
    for i, orig_i, p, ptype, frac_top, area_tot in peak_data:
        if ptype == 1 and "bottom" not in plotted_types:
            bot_lbl = "Bottom"; plotted_types.add("bottom")
        else: bot_lbl = None
        p_bot = p.copy()
        p_bot["area"] = area_tot * (1 - frac_top)
        lw_scale = 3 if highlight_idx is not None and orig_i == highlight_idx else 1
        plot_peak_waveform_model(p_bot, t0=t0, ax=ax,
            color="#4CAF50", alpha_fill=0.08, linewidth=0.9 * lw_scale,
            label=bot_lbl)
    if "bottom" in plotted_types: plotted_types.remove("bottom")

    # Pass 3: draw ALL Total layers LAST (always on top)
    for i, orig_i, p, ptype, frac_top, area_tot in peak_data:
        lbl = "Total" if "total" not in plotted_types else None
        plotted_types.add("total")
        lw_scale = 3 if highlight_idx is not None and orig_i == highlight_idx else 1
        plot_peak_waveform_model(p, t0=t0, ax=ax,
            color="#F44336", alpha_fill=0.30, linewidth=1.5 * lw_scale, label=lbl)

        x_start = (int(p["time"]) - t0) / 1000
        end_ns = int(p["endtime"]) if "endtime" in p.dtype.names else int(p["time"]) + int(p["length"]) * int(p["dt"])
        x_end = (end_ns - t0) / 1000
        ax._peak_regions.append({
            "x_start": x_start, "x_end": x_end,
            "center_x": (x_start + x_end) / 2,
            "index": int(orig_i), "type": ptype, "area": area_tot,
        })

    ax.axhline(0, color="k", alpha=0.15, linewidth=0.4)
    ax.set_xlabel("Time [μs]", fontweight="bold")
    ax.set_ylabel("Model pulse [PE/ns]")
    style.tighten_ylim(ax)
    leg = ax.legend(loc="upper right", fontsize=style.plt.rcParams["legend.fontsize"])
    for txt in leg.get_texts():
        txt.set_picker(True)
    # Collect all artists from the 3 passes
    all_artists = {"top": [], "bottom": [], "total": []}
    for line in ax.lines:
        c = line.get_color()
        if c == "#2196F3": all_artists["top"].append(line)
        elif c == "#4CAF50": all_artists["bottom"].append(line)
        elif c == "#F44336": all_artists["total"].append(line)
    for coll in ax.collections:
        fc = coll.get_facecolor()
        if len(fc) > 0:
            r, g, b = fc[0][:3]
            if r < 0.2 and b > 0.8: all_artists["top"].append(coll)
            elif g > 0.8: all_artists["bottom"].append(coll)
            elif r > 0.8: all_artists["total"].append(coll)
    ax._legend_artists = {k: v for k, v in all_artists.items() if v}
    ax._legend_state = {k: True for k in ax._legend_artists}


# ── peak stacking ──────────────────────────────────────────────


def plot_peak_stack(
    peaks_list: List[np.ndarray],
    peak_type: int = 1,
    align: str = "center_time",
    t_range: Tuple[float, float] = (-2000, 4000),
    ax: Optional[plt.Axes] = None,
    figsize: Tuple[float, float] = (8, 5),
    color: Optional[str] = None,
    n_bootstrap: int = 0,
    title: Optional[str] = None,
    normalize: bool = False,
) -> plt.Figure:
    """Overlay waveforms from many peaks of the same type.

    Parameters
    ----------
    peaks_list : list of peak arrays (can be length-1 arrays from different events)
    peak_type : 1 for S1, 2 for S2
    align : 'center_time' or 'time'
    t_range : (t_min_ns, t_max_ns) relative to alignment point
    ax : axes to draw on (creates new fig if None)
    figsize : figure size
    color : line colour for individual traces
    n_bootstrap : if > 0, also plot bootstrap median ± 1σ band
    title : plot title
    normalize : if True, normalise each peak to unit area

    Returns
    -------
    fig : matplotlib Figure
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    if color is None:
        color = style.PEAK_COLORS.get(peak_type, style.NEUTRAL_DARK)

    # flatten peaks_list into individual peaks
    all_peaks = []
    for pitem in peaks_list:
        if pitem.ndim == 0:
            all_peaks.append(pitem)
        else:
            for p in pitem:
                if p["type"] == peak_type:
                    all_peaks.append(p)

    if not all_peaks:
        ax.text(0.5, 0.5, "No peaks found", transform=ax.transAxes, ha="center", va="center")
        return fig

    t_min_ns, t_max_ns = t_range
    n_t = int((t_max_ns - t_min_ns) / 10)  # 10 ns bins
    t_edges = np.linspace(t_min_ns, t_max_ns, n_t + 1)
    t_centers = 0.5 * (t_edges[:-1] + t_edges[1:])

    waveforms = []
    for p in all_peaks:
        # get raw waveform
        n = int(p["length"])
        if n < 2:
            continue
        t_rel = np.arange(n) * p["dt"]  # ns relative to p['time']

        # align
        if align == "center_time":
            t_rel = t_rel + (int(p["time"]) - int(p["center_time"]))  # shift so center_time = 0
        else:
            t_rel = t_rel  # relative to 'time'

        y = p["data"][:n] / p["dt"]

        # rebin to common grid
        y_rebin, _ = np.histogram(t_rel, bins=t_edges, weights=y)
        cnt, _ = np.histogram(t_rel, bins=t_edges)
        with np.errstate(divide="ignore", invalid="ignore"):
            y_rebin = y_rebin / cnt
            y_rebin[cnt == 0] = 0.0

        if normalize and y_rebin.sum() > 0:
            y_rebin = y_rebin / y_rebin.sum()

        waveforms.append(y_rebin)

    if not waveforms:
        ax.text(0.5, 0.5, "No valid waveforms", transform=ax.transAxes, ha="center", va="center")
        return fig

    waveforms = np.array(waveforms)
    n_wf = waveforms.shape[0]

    # plot individual traces
    alpha_indiv = max(0.02, min(0.3, 50.0 / n_wf))
    for i in range(n_wf):
        ax.plot(
            t_centers / 1000, waveforms[i],
            color=color, alpha=alpha_indiv, linewidth=0.3,
        )

    # mean ± std
    mean_wf = waveforms.mean(axis=0)
    std_wf = waveforms.std(axis=0)
    ax.plot(t_centers / 1000, mean_wf, color=style.NEUTRAL_BLACK, linewidth=1.5, label="Mean")
    ax.fill_between(
        t_centers / 1000,
        mean_wf - std_wf, mean_wf + std_wf,
        color=style.NEUTRAL_BLACK, alpha=0.15, linewidth=0, label="±1σ",
    )

    # bootstrap median
    if n_bootstrap and n_wf >= 10:
        rng = np.random.default_rng(42)
        medians = []
        for _ in range(n_bootstrap):
            idx = rng.integers(0, n_wf, size=n_wf)
            medians.append(np.median(waveforms[idx], axis=0))
        medians = np.array(medians)
        med_lo = np.percentile(medians, 16, axis=0)
        med_hi = np.percentile(medians, 84, axis=0)
        ax.fill_between(
            t_centers / 1000, med_lo, med_hi,
            color=color, alpha=0.2, linewidth=0, label="Bootstrap 68%",
        )

    ax.axhline(0, color="k", alpha=0.15, linewidth=0.4)
    ax.set_xlabel(f"Time rel. to {align.replace('_', ' ')} [μs]")
    ax.set_ylabel("Amplitude [PE/ns]" if not normalize else "Norm. amplitude")
    ptype_label = style.PEAK_LABELS.get(peak_type, f"type={peak_type}")
    ax.set_title(title or f"{n_wf} {ptype_label} peaks stacked")
    ax.legend(loc="upper right", fontsize=style.plt.rcParams["legend.fontsize"])

    style.tighten_ylim(ax)
    return fig


# ── internal helpers ───────────────────────────────────────────


def _clean_zoom_ax(ax: plt.Axes) -> None:
    """Minimalist styling for zoomed-in peak detail axes."""
    ax.tick_params(labelsize=style.plt.rcParams["font.size"] - 1)
    ax.set_xlabel("Time [μs]", fontsize=style.plt.rcParams["font.size"])


def _annotate_peak_info(ax: plt.Axes, event: np.ndarray, prefix: str) -> None:
    """Annotate S1/S2 area, width, and peak amplitude on the axes."""
    area_key = f"{prefix}_area"
    width_key = f"{prefix}_range_90p_area"
    rise_key = f"{prefix}_rise_time"
    time_key = f"{prefix}_time"
    endtime_key = f"{prefix}_endtime"

    if area_key not in event.dtype.names:
        return

    area = float(event[area_key])
    width = float(event[width_key]) if width_key in event.dtype.names else 0.0
    rise = float(event[rise_key]) if rise_key in event.dtype.names else 20.0
    duration = float(event[endtime_key]) - float(event[time_key]) if time_key in event.dtype.names and endtime_key in event.dtype.names else max(width, 100)

    # Estimate peak amplitude from double-exponential model
    if width > 0 and rise > 0:
        tau_r = max(rise / 3.0, 1.0)
        tau_f = max((width - rise) / 3.0, tau_r * 2)
        t_peak = tau_r * tau_f / (tau_f - tau_r) * np.log(tau_f / tau_r)
        y_peak = np.exp(-t_peak / tau_f) - np.exp(-t_peak / tau_r)
        if y_peak > 0:
            dt_model = max(duration / 200, 1.0)
            amp = area / (y_peak * duration) * y_peak * (duration / dt_model)
            amp = area / duration * (1.0 / y_peak)  # simpler: scale by peak
            # Approximate: area * (peak / integral)
            # For double-exp, integral ≈ area already. Peak height:
            t = np.linspace(0, duration, 500)
            y = np.maximum(np.exp(-t / tau_f) - np.exp(-t / tau_r), 0)
            amp = area * y.max() / (y.sum() * duration / 500) if y.sum() > 0 else 0
        else:
            amp = 0
    else:
        amp = 0

    label = prefix.upper()
    color = style.BLUE_MAIN if prefix == "s1" else style.GREEN_POSITIVE
    text = (
        f"{label}:  Area = {area:.1f} PE\n"
        f"          Width = {width:.0f} ns\n"
        f"          Amp = {amp:.2f} PE/ns"
    )
    ax.text(
        0.97, 0.95, text,
        transform=ax.transAxes,
        fontsize=style.plt.rcParams["legend.fontsize"],
        color=color,
        fontweight="bold",
        va="top", ha="right",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor=color, alpha=0.85),
    )


def _draw_hit_pattern(
    peaks_subset: np.ndarray,
    t_start: int,
    t_end: int,
    pmt_positions: np.ndarray,
    to_pe: np.ndarray,
    ax: plt.Axes,
    array_name: str,
    cmap: str,
    **kwargs,
) -> None:
    """Sum area_per_channel over peaks_subset in [t_start, t_end], plot on *ax*."""
    if len(peaks_subset) == 0:
        area = np.zeros(len(to_pe))
    else:
        area = peaks_subset["area_per_channel"].sum(axis=0)
    plot_pmt_hit_pattern(
        area, pmt_positions, to_pe,
        array_name=array_name, ax=ax, cmap=cmap, **kwargs,
    )


def _mark_peak_span(
    ax: plt.Axes,
    event: np.ndarray,
    prefix: str,
    t0: int,
    color: str,
) -> None:
    """Draw a shaded span and label for a main/alt peak."""
    t_field = f"{prefix}_time"
    et_field = f"{prefix}_endtime"
    if t_field not in event.dtype.names:
        return
    t1, t2 = int(event[t_field]), int(event[et_field])
    if t1 <= 0:
        return
    x1 = (t1 - t0) / 1000
    x2 = (t2 - t0) / 1000
    ylim = ax.get_ylim()
    yh = ylim[1] * 0.92
    ax.axvspan(x1, x2, color=color, alpha=0.08, linewidth=0)
    ax.annotate(
        prefix.upper(), (x1, yh),
        fontsize=style.plt.rcParams["legend.fontsize"],
        color=color, fontweight="bold", va="top", ha="left",
    )


def plot_peak_zoom(
    peak: np.ndarray,
    all_peaks: np.ndarray,
    to_pe: np.ndarray,
    pmt_positions: np.ndarray,
    event: np.ndarray,
    highlight_idx: int,
    event_area_per_channel: Optional[np.ndarray] = None,
    raw_records: Optional[np.ndarray] = None,
    figsize: Tuple[float, float] = (16, 10),
    title: Optional[str] = None,
    fig: Optional[plt.Figure] = None,
    run_id: Optional[str] = None,
) -> plt.Figure:
    """Single-peak zoom with 3-component waveform (top+bottom+total).

    Layout::

        ┌───────────────────────────────┐
        │   Peak waveform (top+bottom)  │
        │   Legend: [top] [bot] [total] │
        ├──────────────┬────────────────┤
        │  PMT Top     │  PMT Bottom    │
        └──────────────┴────────────────┘
    """
    if fig is None:
        fig = plt.figure(figsize=figsize, facecolor="white")
    else:
        fig.set_size_inches(figsize)
        fig.clf()

    gs = gridspec.GridSpec(2, 2, figure=fig,
                           height_ratios=[1.2, 1.0],
                           hspace=0.5, wspace=0.4)

    ax_wf = fig.add_subplot(gs[0, :])  # full-width waveform
    ax_pmt_top = fig.add_subplot(gs[1, 0])
    ax_pmt_bot = fig.add_subplot(gs[1, 1])

    fig._peak_axes = [ax_wf]

    ptype = int(peak["type"])
    color = style.PEAK_COLORS.get(ptype, style.NEUTRAL_MID)
    label = style.PEAK_LABELS.get(ptype, f"type={ptype}")
    _rsize = style.plt.rcParams["font.size"]

    t_peak = int(peak["time"])
    t_end = int(peak["endtime"]) if "endtime" in peak.dtype.names else t_peak + int(peak["length"]) * int(peak["dt"])
    margin = max(500, int((t_end - t_peak) * 1.0))
    t0 = t_peak - margin

    # ── 3-component waveform: top PMT + bottom PMT = total ──
    frac_top = float(peak["area_fraction_top"]) if "area_fraction_top" in peak.dtype.names else 0.5
    area_total = float(peak["area"])
    area_top = area_total * frac_top
    area_bot = area_total * (1 - frac_top)

    # Build copies of the peak with scaled areas for top/bottom
    peak_top = peak.copy()
    peak_top["area"] = area_top
    peak_bot = peak.copy()
    peak_bot["area"] = area_bot

    # Plot top (violet/orange)
    top_color = "#2196F3"   # bright blue
    bot_color = "#4CAF50"   # bright green
    sum_color = "#F44336"   # bright red

    if has_waveform(np.array([peak])):
        artists_top = []
        artists_bot = []
        if has_top_waveform(np.array([peak])):
            artists_top = plot_peak_component_waveform(
                peak, "top", t0, ax_wf, top_color,
                alpha_fill=0.25, linewidth=2.4, label=f"Top PMT ({area_top:.0f} PE)",
            )
            artists_bot = plot_peak_component_waveform(
                peak, "bottom", t0, ax_wf, bot_color,
                alpha_fill=0.25, linewidth=2.4, label=f"Bottom PMT ({area_bot:.0f} PE)",
            )
        artists_sum = plot_peak_component_waveform(
            peak, "total", t0, ax_wf, sum_color,
            alpha_fill=0.18, linewidth=4.5, label=f"Total ({area_total:.0f} PE)",
        )
        if not artists_top:
            artists_top = artists_sum
        if not artists_bot:
            artists_bot = artists_sum
        ax_wf.set_ylabel("Real peak waveform [PE/ns]")
    elif raw_records is not None and len(raw_records) and pmt_positions is not None:
        from . import io as _io
        rec_mask = (raw_records["time"] >= t0) & (raw_records["time"] <= t_end + margin)
        recs = raw_records[rec_mask]
        dt = int(np.median(recs["dt"])) if len(recs) and "dt" in recs.dtype.names else int(peak["dt"])
        x, y_top, y_bot, y_total = _io.build_array_waveforms(
            recs, t0, t_end + margin, pmt_positions, t0=t0, dt_out=dt, to_pe=to_pe
        )
        artists = _plot_step_arrays(
            ax_wf, x, [y_top, y_bot, y_total],
            [top_color, bot_color, sum_color],
            [f"Top PMT ({area_top:.0f} PE)", f"Bottom PMT ({area_bot:.0f} PE)", f"Total ({area_total:.0f} PE)"],
            linewidths=[2.4, 2.4, 4.5],
            alphas=[0.25, 0.25, 0.18],
        )
        artists_top = artists[f"top pmt ({area_top:.0f} pe)"]
        artists_bot = artists[f"bottom pmt ({area_bot:.0f} pe)"]
        artists_sum = artists[f"total ({area_total:.0f} pe)"]
        ax_wf.set_ylabel("Intensity [PE/ns]")
    else:
        artists_top = plot_peak_waveform_model(peak_top, t0=t0, ax=ax_wf,
            color=top_color, alpha_fill=0.3, linewidth=2.4, label=f"Top PMT ({area_top:.0f} PE)")
        artists_bot = plot_peak_waveform_model(peak_bot, t0=t0, ax=ax_wf,
            color=bot_color, alpha_fill=0.3, linewidth=2.4, label=f"Bottom PMT ({area_bot:.0f} PE)")
        artists_sum = plot_peak_waveform_model(peak, t0=t0, ax=ax_wf,
            color=sum_color, alpha_fill=0.4, linewidth=4.5, label=f"Total ({area_total:.0f} PE)")
        ax_wf.set_ylabel("Model pulse [PE/ns]")

    ax_wf.set_title(f"{label} Peak  |  area={area_total:.0f} PE", fontweight="bold")
    ax_wf.set_xlabel("Time [μs]")
    ax_wf.axhline(0, color="k", alpha=0.15, linewidth=0.4)
    style.tighten_ylim(ax_wf)

    # Interactive legend: click to toggle top/bottom/total
    leg = ax_wf.legend(loc="upper right", fontsize=_rsize - 1)
    for lh in leg.legend_handles:
        lh.set_picker(True)
        lh.set_linewidth(2.0)
    for txt in leg.get_texts():
        txt.set_picker(True)
    # Store legend state on axes for toggle handling
    ax_wf._legend_artists = {
        "top": artists_top,
        "bottom": artists_bot,
        "total": artists_sum,
    }
    ax_wf._legend_state = {"top": True, "bottom": True, "total": True}

    # Clickable region for returning to overview
    x_range = (t_end + margin - (t_peak - margin)) / 1000
    ax_wf._peak_regions = [{
        "x_start": (t_peak - margin) / 1000,
        "x_end": (t_end + margin) / 1000,
        "center_x": (t_peak + t_end) / 2e9,
        "index": highlight_idx,
        "type": ptype,
        "area": area_total,
    }]

    # ── PMT hit patterns ──
    area_pmt = np.zeros(len(to_pe))
    pmt_suffix = ""

    peak_area = float(peak["area"])
    if has_per_channel(np.array([peak])):
        area_pmt = peak["area_per_channel"]
        pmt_suffix = " (peak true)"
    elif event_area_per_channel is not None:
        eac = event_area_per_channel
        if ptype == 1 and "s1_area_per_channel" in eac.dtype.names:
            main_s1 = float(event["s1_area"]) if "s1_area" in event.dtype.names else eac["s1_area_per_channel"].sum()
            scale = peak_area / main_s1 if main_s1 > 0 else 1.0
            area_pmt = eac["s1_area_per_channel"] * scale
            pmt_suffix = f" (estimated from main S1 x{scale:.3f})"
        elif ptype == 2 and "s2_area_per_channel" in eac.dtype.names:
            main_s2 = float(event["s2_area"]) if "s2_area" in event.dtype.names else eac["s2_area_per_channel"].sum()
            scale = peak_area / main_s2 if main_s2 > 0 else 1.0
            area_pmt = eac["s2_area_per_channel"] * scale
            pmt_suffix = f" (estimated from main S2 x{scale:.3f})"
        else:
            for key in ("s1_area_per_channel", "s2_area_per_channel",
                         "alt_s1_area_per_channel", "alt_s2_area_per_channel"):
                if key in eac.dtype.names:
                    area_pmt = area_pmt + eac[key]
            pmt_suffix = " (event total)"

    for ax_pmt, arr_name in [(ax_pmt_top, "top"), (ax_pmt_bot, "bottom")]:
        if np.all(area_pmt == 0):
            ax_pmt.text(0.5, 0.5, f"No per-channel\ndata for {label}",
                       transform=ax_pmt.transAxes, ha="center", va="center",
                       color="grey", fontsize=_rsize)
            ax_pmt.set_aspect("equal")
        else:
            plot_pmt_hit_pattern(area_pmt, pmt_positions, to_pe,
                                 array_name=arr_name, ax=ax_pmt, cmap="plasma",
                                 vmin=0, marker_size=120,
                                 show_colorbar=True, label="Area [PE]")
        ax_pmt.set_title(f"{arr_name.capitalize()} PMT{pmt_suffix}", fontweight="bold")

    if title is None:
        title = _make_event_title(event, run_id=run_id)
    fig.suptitle(title, fontsize=_rsize + 4, fontweight="bold", y=0.97)

    return fig


def _make_event_title(event: np.ndarray, run_id: Optional[str] = None) -> str:
    """Format an event title string."""
    evt_num = event["event_number"] if "event_number" in event.dtype.names else "?"
    if run_id is None:
        run_id = event["run_id"] if "run_id" in event.dtype.names else "?"
    t_ns = int(event["time"])
    # human-readable time
    try:
        import datetime
        dt = datetime.datetime.utcfromtimestamp(t_ns / 1000)
        ts = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except Exception:
        ts = f"{t_ns} ns"
    return f"Event {evt_num}  |  Run {run_id}  |  {ts}"

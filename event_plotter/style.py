"""Nature-journal publication style for matplotlib figures.

Applies font, spine, color, and layout conventions derived from
nature-skills-main. Call apply_style() once at the top of any plotting
script.
"""

import platform
import matplotlib
import matplotlib.pyplot as plt
import numpy as np

_IS_MACOS = platform.system() == "Darwin"

# ── semantic colour palette (nature-skills derived) ──────────────

BLUE_MAIN = "#0F4D92"
BLUE_SECONDARY = "#3775BA"
GREEN_POSITIVE = "#8BCF8B"
RED_STRONG = "#B64342"
RED_SOFT = "#E9A6A1"
NEUTRAL_LIGHT = "#CFCECE"
NEUTRAL_MID = "#767676"
NEUTRAL_DARK = "#4D4D4D"
NEUTRAL_BLACK = "#272727"
TEAL = "#42949E"
VIOLET = "#9A4D8E"
GOLD = "#FFD700"
HIGHLIGHT = "#FFD700"     # peak selection highlight
HIGHLIGHT_ALPHA = 0.30

# semantic mapping for XENON peak types
PEAK_COLORS = {
    1: BLUE_MAIN,      # S1
    2: GREEN_POSITIVE,  # S2
    0: NEUTRAL_MID,     # unknown
    3: VIOLET,          # S0 / other
}

PEAK_LABELS = {1: "S1", 2: "S2", 0: "Unknown", 3: "S0"}

# default colour order for multi-category figures
DEFAULT_COLOUR_ORDER = [
    BLUE_MAIN,
    GREEN_POSITIVE,
    RED_STRONG,
    TEAL,
    VIOLET,
    NEUTRAL_MID,
]


def apply_style(
    font_size: int = 9,
    axes_linewidth: float = 1.5,
    use_tex: bool = False,
) -> None:
    """Set global matplotlib rcParams to Nature-journal conventions.

    Parameters
    ----------
    font_size : int
        Base font size. 7-9 for dense journal figures, 15-16 for
        compact presentations.
    axes_linewidth : float
        Spine thickness.  0.8 for journal, 2-3 for slides.
    use_tex : bool
        Use LaTeX for text rendering.  Requires a working tex
        installation.
    """
    # ── fonts ──
    plt.rcParams["font.family"] = "sans-serif"
    if _IS_MACOS:
        plt.rcParams["font.sans-serif"] = [
            "Helvetica Neue",
            "Helvetica",
            "Arial",
            "DejaVu Sans",
            "Liberation Sans",
            "sans-serif",
        ]
    else:
        plt.rcParams["font.sans-serif"] = [
            "Arial",
            "Helvetica",
            "DejaVu Sans",
            "Liberation Sans",
            "sans-serif",
        ]
    plt.rcParams["font.size"] = font_size
    plt.rcParams["mathtext.default"] = "regular"

    # editable text in vector output (non-negotiable)
    plt.rcParams["svg.fonttype"] = "none"      # <text> nodes, not paths
    plt.rcParams["pdf.fonttype"] = 42           # TrueType, not Type 3

    # ── spines ──
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.linewidth"] = axes_linewidth

    # ── ticks ──
    plt.rcParams["xtick.major.width"] = axes_linewidth
    plt.rcParams["ytick.major.width"] = axes_linewidth
    plt.rcParams["xtick.major.size"] = 5
    plt.rcParams["ytick.major.size"] = 5
    plt.rcParams["xtick.minor.width"] = axes_linewidth * 0.6
    plt.rcParams["ytick.minor.width"] = axes_linewidth * 0.6
    plt.rcParams["xtick.minor.size"] = 3
    plt.rcParams["ytick.minor.size"] = 3

    # ── legend ──
    plt.rcParams["legend.frameon"] = False
    plt.rcParams["legend.fontsize"] = font_size + 56
    plt.rcParams["legend.handlelength"] = 2.0
    plt.rcParams["legend.handletextpad"] = 0.8
    plt.rcParams["legend.borderpad"] = 0.6

    # ── LaTeX (optional) ──
    if use_tex:
        plt.rcParams["text.usetex"] = True
        plt.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"

    # ── figure defaults ──
    plt.rcParams["figure.dpi"] = 150
    plt.rcParams["savefig.dpi"] = 300
    plt.rcParams["savefig.bbox"] = "tight"
    plt.rcParams["savefig.pad_inches"] = 0.05


# ── helper utilities ──────────────────────────────────────────


def add_panel_label(
    ax: plt.Axes,
    label: str,
    x: float = -0.08,
    y: float = 1.05,
    fontsize: int = 12,
    fontweight: str = "bold",
    color: str = NEUTRAL_BLACK,
) -> None:
    """Place a bold lower-case panel label (a, b, c, ...) at the
    top-left of *ax* in transAxes coordinates."""
    ax.text(
        x, y, label,
        transform=ax.transAxes,
        fontsize=fontsize,
        fontweight=fontweight,
        va="top",
        ha="left",
        color=color,
    )


def is_dark(hex_color: str, threshold: int = 128) -> bool:
    """Return True if *hex_color* is perceptually dark."""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return luminance < threshold


def save_figure(
    fig: plt.Figure,
    basepath: str,
    formats: tuple = ("pdf", "svg", "png"),
    dpi: int = 300,
    pad: float = 0.5,
) -> None:
    """tight_layout, then save *fig* to *basepath* in each format."""
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*not compatible with tight_layout.*")
        fig.tight_layout(pad=pad)
    for fmt in formats:
        path = f"{basepath}.{fmt}"
        kw = {"dpi": dpi} if fmt in ("png", "tiff", "tif") else {}
        fig.savefig(path, **kw)
    print(f"Saved to {basepath}.{{{', '.join(formats)}}}")


def tighten_ylim(ax: plt.Axes, pad_frac: float = 0.10) -> None:
    """Set y-limits to data range plus a small fractional pad."""
    lines = ax.get_lines()
    ymin, ymax = np.inf, -np.inf
    for line in lines:
        yd = np.asarray(line.get_ydata(), dtype=float)
        yd = yd[np.isfinite(yd)]
        if len(yd):
            ymin = min(ymin, yd.min())
            ymax = max(ymax, yd.max())
    # Also check collections (fill_between)
    for coll in ax.collections:
        try:
            offs = coll.get_offsets()
            if len(offs) > 0 and offs.shape[1] >= 2:
                yvals = offs[:, 1]
                yvals = yvals[np.isfinite(yvals)]
                if len(yvals):
                    ymin = min(ymin, yvals.min())
                    ymax = max(ymax, yvals.max())
        except Exception:
            pass
    if not np.isfinite(ymin) or not np.isfinite(ymax):
        return
    pad = (ymax - ymin) * pad_frac + 1e-12
    ax.set_ylim(ymin - pad, ymax + pad)

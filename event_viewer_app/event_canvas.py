"""Matplotlib canvas widget for event display, embedded in Qt."""

import matplotlib

# Try modern QtAgg backend first (mpl >= 3.5), fall back to Qt5Agg
for backend in ("QtAgg", "Qt5Agg"):
    try:
        matplotlib.use(backend)
        break
    except (ValueError, ImportError):
        continue

from matplotlib.figure import Figure

# Import the right canvas class for the active backend
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

# Import Qt widgets via compat layer
from .qt_compat import QWidget, QVBoxLayout, QLabel
from .qt_compat import Signal


class EventCanvas(QWidget):
    """Widget containing the matplotlib figure canvas and navigation toolbar.

    The toolbar is optional — on older matplotlib + PySide2 combos
    it may fail to construct, in which case keyboard shortcuts are
    available: p=pan, o=zoom, h=home, s=save.

    Signals:
        peak_clicked(int): emitted when user clicks on a peak region.
            Carries the original peak index in the full peaks array.
    """

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig = None
        self._canvas = None
        self._toolbar = None
        self._click_cid = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._fig = Figure(figsize=(18, 14), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setMinimumWidth(600)

        # Connect matplotlib events for interactive peak clicking
        self._click_cid = self._canvas.mpl_connect(
            'button_press_event', self._on_canvas_click
        )

        # Toolbar may fail on some matplotlib+PySide2 combos
        try:
            self._toolbar = NavigationToolbar2QT(self._canvas, self)
            self._toolbar.setMaximumHeight(36)
        except Exception:
            self._toolbar = None
            hint = QLabel("  Zoom: o  |  Pan: p  |  Home: h  |  Save: s")
            hint.setMaximumHeight(22)
            hint.setStyleSheet("color: grey; font-size: 10px;")
            layout.addWidget(hint)

        if self._toolbar is not None:
            layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)

    @property
    def figure(self) -> Figure:
        return self._fig

    @property
    def canvas(self) -> FigureCanvasQTAgg:
        return self._canvas

    def clear(self):
        """Clear the figure."""
        self._fig.clear()

    def draw(self):
        """Refresh the canvas."""
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*not compatible with tight_layout.*")
            self._fig.tight_layout(pad=0.8)
        self._canvas.draw_idle()

    def set_message(self, text: str):
        """Show a text message on the canvas (no data state)."""
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._canvas.draw_idle()

    def _on_canvas_click(self, event):
        """Handle matplotlib button press — hit-test peaks and emit signal."""
        # Only respond to single clicks (not double-clicks used by zoom tool)
        if event.dblclick:
            return
        if event.inaxes is None:
            return
        # Don't intercept when toolbar pan/zoom is active
        if self._toolbar is not None and self._toolbar.mode != '':
            return

        peak_regions = getattr(event.inaxes, '_peak_regions', None)
        if not peak_regions:
            return

        x = event.xdata
        if x is None:
            return

        # Hit-test: find peaks whose time span contains the click x.
        # If multiple overlap, pick the one with the largest area.
        hits = []
        for region in peak_regions:
            if region['x_start'] <= x <= region['x_end']:
                hits.append(region)

        if hits:
            best = max(hits, key=lambda r: r['area'])
            self.peak_clicked.emit(best['index'])

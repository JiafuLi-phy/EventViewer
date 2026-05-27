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

    Keyboard shortcuts available when toolbar fails:
    p=pan, o=zoom, h=home, s=save.

    Signals:
        peak_clicked(int): emitted when user clicks on a peak region.
    """

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig = None
        self._canvas = None
        self._toolbar = None
        self._click_cid = None
        self._resizing = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._fig = Figure(figsize=(16, 12), facecolor="white")
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setSizePolicy(
            QWidget().sizePolicy().horizontalPolicy().Expanding,
            QWidget().sizePolicy().verticalPolicy().Expanding,
        )

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

    def resizeEvent(self, event):
        """Scale figure to match widget size."""
        super().resizeEvent(event)
        if self._resizing or self._canvas is None:
            return
        w = self._canvas.width()
        h = self._canvas.height()
        if w > 200 and h > 200:
            self._resizing = True
            dpi = self._fig.get_dpi()
            self._fig.set_size_inches(w / dpi, h / dpi)
            self._resizing = False

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
            self._fig.tight_layout(pad=1.5)
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
        if event.dblclick:
            return
        if event.inaxes is None:
            return
        if self._toolbar is not None and self._toolbar.mode != '':
            return

        peak_regions = getattr(event.inaxes, '_peak_regions', None)
        if not peak_regions:
            return

        x = event.xdata
        if x is None:
            return

        MAX_CLICK_DIST = 0.0005
        best = None
        best_dist = MAX_CLICK_DIST
        for region in peak_regions:
            cx = region.get('center_x', (region['x_start'] + region['x_end']) / 2)
            dist = abs(x - cx)
            if dist < best_dist:
                best_dist = dist
                best = region
            elif region['x_start'] <= x <= region['x_end']:
                if best is None or region['area'] > best['area']:
                    best = region

        if best is not None:
            self.peak_clicked.emit(best['index'])

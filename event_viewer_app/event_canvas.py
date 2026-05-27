"""Matplotlib canvas widget for event display, embedded in Qt."""

import matplotlib

for backend in ("QtAgg", "Qt5Agg"):
    try:
        matplotlib.use(backend)
        break
    except (ValueError, ImportError):
        continue

from matplotlib.figure import Figure

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
except ImportError:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

from .qt_compat import QWidget, QVBoxLayout, QLabel, QScrollArea
from .qt_compat import Qt, Signal


class EventCanvas(QWidget):
    """Matplotlib figure + toolbar in a scrollable container.

    The canvas is wrapped in a QScrollArea so users with smaller
    screens can scroll to see the full figure.

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
        self._scroll_cid = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Figure sized to show detail while fitting most screens
        self._fig = Figure(figsize=(18, 14), facecolor="white", dpi=80)
        self._canvas = FigureCanvasQTAgg(self._fig)

        # Peak click handler
        self._click_cid = self._canvas.mpl_connect(
            'button_press_event', self._on_canvas_click
        )
        # Mouse scroll for zoom
        self._scroll_cid = self._canvas.mpl_connect(
            'scroll_event', self._on_scroll
        )

        # Toolbar
        try:
            self._toolbar = NavigationToolbar2QT(self._canvas, self)
            self._toolbar.setMaximumHeight(36)
        except Exception:
            self._toolbar = None
            hint = QLabel("  Scroll=zoom  |  Pan: p  |  Home: h  |  Save: s")
            hint.setMaximumHeight(22)
            hint.setStyleSheet("color: grey; font-size: 10px;")
            layout.addWidget(hint)

        if self._toolbar is not None:
            layout.addWidget(self._toolbar)

        # Scroll area wraps canvas for small screens
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setWidget(self._canvas)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        layout.addWidget(self._scroll)

    @property
    def figure(self) -> Figure:
        return self._fig

    @property
    def canvas(self) -> FigureCanvasQTAgg:
        return self._canvas

    def clear(self):
        self._fig.clear()

    def draw(self):
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*not compatible with tight_layout.*")
            self._fig.tight_layout(pad=2.0, rect=[0, 0.02, 1, 0.93])
        self._canvas.draw_idle()
        # Tell scroll area the real canvas size
        self._canvas.resize(self._canvas.sizeHint())

    def set_message(self, text: str):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._canvas.draw_idle()

    # ── interaction ──────────────────────────────────────────────

    def _on_canvas_click(self, event):
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

    def _on_scroll(self, event):
        """Mouse wheel: scroll without modifier = zoom, with Shift = horizontal pan."""
        if event.inaxes is None:
            return
        if self._toolbar is not None and self._toolbar.mode != '':
            return  # let toolbar handle it

        base_scale = 1.25
        if event.modifiers & Qt.ShiftModifier:
            # Shift+scroll: horizontal pan
            dx = event.step * 0.1
            xlim = event.inaxes.get_xlim()
            event.inaxes.set_xlim(xlim[0] - dx, xlim[1] - dx)
        elif event.button == 'up':
            # Scroll up: zoom in
            scale = 1 / base_scale
            self._zoom_at(event.inaxes, event.xdata, event.ydata, scale)
        elif event.button == 'down':
            # Scroll down: zoom out
            scale = base_scale
            self._zoom_at(event.inaxes, event.xdata, event.ydata, scale)

        self._canvas.draw_idle()

    def _zoom_at(self, ax, cx, cy, scale):
        """Zoom *ax* by *scale* centered at (*cx*, *cy*)."""
        if cx is None or cy is None:
            return
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        new_w = (xmax - xmin) * scale
        new_h = (ymax - ymin) * scale
        ax.set_xlim(cx - new_w / 2, cx + new_w / 2)
        ax.set_ylim(cy - new_h / 2, cy + new_h / 2)

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

from .qt_compat import QWidget, QVBoxLayout, QLabel
from .qt_compat import Qt, Signal


class EventCanvas(QWidget):
    """Matplotlib canvas with mouse-wheel zoom and peak click."""

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig = Figure(figsize=(18, 14), facecolor="white", dpi=80)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._toolbar = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._canvas.mpl_connect('button_press_event', self._on_click)
        self._canvas.mpl_connect('scroll_event', self._on_scroll)

        try:
            self._toolbar = NavigationToolbar2QT(self._canvas, self)
            self._toolbar.setMaximumHeight(36)
            layout.addWidget(self._toolbar)
        except Exception:
            pass

        layout.addWidget(self._canvas)

    @property
    def figure(self):
        return self._fig

    @property
    def canvas(self):
        return self._canvas

    def clear(self):
        self._fig.clear()

    def draw(self):
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*not compatible with tight_layout.*")
            self._fig.tight_layout(pad=2.0, rect=[0, 0.02, 1, 0.93])
        self._canvas.draw_idle()

    def set_message(self, text: str):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._canvas.draw_idle()

    def _on_click(self, event):
        if event.dblclick or event.inaxes is None:
            return
        if self._toolbar is not None and self._toolbar.mode != '':
            return
        regions = getattr(event.inaxes, '_peak_regions', None)
        if not regions:
            return
        x = event.xdata
        if x is None:
            return
        best, best_d = None, 0.0005
        for r in regions:
            cx = r.get('center_x', (r['x_start'] + r['x_end']) / 2)
            d = abs(x - cx)
            if d < best_d:
                best_d = d; best = r
            elif r['x_start'] <= x <= r['x_end']:
                if best is None or r['area'] > best['area']:
                    best = r
        if best is not None:
            self.peak_clicked.emit(best['index'])

    def _on_scroll(self, event):
        s = 0.8 if event.button == 'up' else 1.25
        # Zoom ALL axes together (whole-page zoom)
        for ax in self._fig.axes:
            if not ax.get_lines() and not ax.collections:
                continue
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            cx = (xmin + xmax) / 2
            cy = (ymin + ymax) / 2
            ax.set_xlim(cx - (cx - xmin) * s, cx + (xmax - cx) * s)
            ax.set_ylim(cy - (cy - ymin) * s, cy + (ymax - cy) * s)
        self._canvas.draw_idle()

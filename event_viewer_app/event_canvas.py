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
    """Scrollable matplotlib canvas.

    Large figure + scroll bars + mouse-wheel zoom.
    """

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig = None
        self._canvas = None
        self._scroll = None
        self._toolbar = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Large figure — scroll to see all content
        self._fig = Figure(figsize=(20, 16), facecolor="white", dpi=80)
        self._canvas = FigureCanvasQTAgg(self._fig)

        # Peak click
        self._canvas.mpl_connect('button_press_event', self._on_canvas_click)
        # Mouse wheel zoom
        self._canvas.mpl_connect('scroll_event', self._on_scroll)

        # Toolbar
        try:
            self._toolbar = NavigationToolbar2QT(self._canvas, self)
            self._toolbar.setMaximumHeight(36)
            layout.addWidget(self._toolbar)
        except Exception:
            pass

        # Scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setWidget(self._canvas)
        layout.addWidget(self._scroll)

    @property
    def figure(self) -> Figure:
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
        # Tell canvas its real size so scroll area knows
        w_in, h_in = self._fig.get_size_inches()
        dpi = self._fig.get_dpi()
        self._canvas.resize(int(w_in * dpi), int(h_in * dpi))
        self._canvas.draw_idle()

    def set_message(self, text: str):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._canvas.draw_idle()

    def _on_canvas_click(self, event):
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
        best = None
        best_dist = 0.0005
        for r in regions:
            cx = r.get('center_x', (r['x_start'] + r['x_end']) / 2)
            d = abs(x - cx)
            if d < best_dist:
                best_dist = d
                best = r
            elif r['x_start'] <= x <= r['x_end']:
                if best is None or r['area'] > best['area']:
                    best = r
        if best is not None:
            self.peak_clicked.emit(best['index'])

    def _on_scroll(self, event):
        """Ctrl+scroll=zoom, plain scroll=vertical pan, Shift+scroll=horizontal pan."""
        if event.inaxes is None:
            return
        ax = event.inaxes
        if event.modifiers & Qt.ControlModifier:
            # Ctrl+scroll: zoom centered at cursor
            s = 0.8 if event.button == 'up' else 1.25
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            cx, cy = event.xdata, event.ydata
            if cx is None or cy is None:
                return
            ax.set_xlim(cx - (cx - xmin) * s, cx + (xmax - cx) * s)
            ax.set_ylim(cy - (cy - ymin) * s, cy + (ymax - cy) * s)
        elif event.modifiers & Qt.ShiftModifier:
            # Shift+scroll: horizontal pan
            dx = (ax.get_xlim()[1] - ax.get_xlim()[0]) * 0.15
            dx = dx if event.button == 'up' else -dx
            xmin, xmax = ax.get_xlim()
            ax.set_xlim(xmin + dx, xmax + dx)
        else:
            # Plain scroll: vertical pan
            dy = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.15
            dy = dy if event.button == 'up' else -dy
            ymin, ymax = ax.get_ylim()
            ax.set_ylim(ymin - dy, ymax - dy)
        self._canvas.draw_idle()

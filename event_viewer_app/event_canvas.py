"""Matplotlib canvas with zoom-percentage control and scroll."""

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

from .qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QSlider, QPushButton,
)
from .qt_compat import Qt, Signal


class EventCanvas(QWidget):
    """Canvas + zoom slider + scroll. Like a PDF reader."""

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_dpi = 80
        self._zoom = 100  # percent
        self._fig = Figure(figsize=(18, 14), facecolor="white", dpi=self._base_dpi)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._scroll = None
        self._zoom_label = None
        self._toolbar = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # ── Top bar: toolbar + zoom controls ──
        top = QHBoxLayout()
        top.setSpacing(6)

        try:
            self._toolbar = NavigationToolbar2QT(self._canvas, self)
            self._toolbar.setMaximumHeight(36)
            top.addWidget(self._toolbar)
        except Exception:
            pass

        top.addStretch()

        btn_out = QPushButton("-")
        btn_out.setFixedSize(28, 28)
        btn_out.clicked.connect(lambda: self._set_zoom(self._zoom - 10))
        top.addWidget(btn_out)

        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(42)
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        top.addWidget(self._zoom_label)

        btn_in = QPushButton("+")
        btn_in.setFixedSize(28, 28)
        btn_in.clicked.connect(lambda: self._set_zoom(self._zoom + 10))
        top.addWidget(btn_in)

        layout.addLayout(top)

        # ── Scroll area ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(False)
        self._scroll.setWidget(self._canvas)
        layout.addWidget(self._scroll)

        # ── Events ──
        self._canvas.mpl_connect('button_press_event', self._on_click)
        self._canvas.mpl_connect('scroll_event', self._on_scroll)

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
        self._update_canvas_size()

    def set_message(self, text: str):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._canvas.draw_idle()

    def _set_zoom(self, pct: int):
        pct = max(30, min(300, pct))
        if pct == self._zoom:
            return
        self._zoom = pct
        dpi = int(self._base_dpi * pct / 100)
        self._fig.set_dpi(dpi)
        self._zoom_label.setText(f"{pct}%")
        self._update_canvas_size()
        self._canvas.draw_idle()

    def _update_canvas_size(self):
        w_in, h_in = self._fig.get_size_inches()
        dpi = self._fig.get_dpi()
        pw, ph = int(w_in * dpi), int(h_in * dpi)
        self._canvas.setMinimumSize(pw, ph)
        self._canvas.resize(pw, ph)

    def _on_click(self, event):
        if event.dblclick or event.inaxes is None:
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
        if event.inaxes is None:
            return
        ax = event.inaxes
        if event.modifiers & Qt.ControlModifier:
            # Ctrl+scroll: change page zoom
            self._set_zoom(self._zoom + (10 if event.button == 'up' else -10))
        else:
            s = 0.8 if event.button == 'up' else 1.25
            cx, cy = event.xdata, event.ydata
            if cx is None or cy is None:
                return
            xmin, xmax = ax.get_xlim()
            ymin, ymax = ax.get_ylim()
            ax.set_xlim(cx - (cx - xmin) * s, cx + (xmax - cx) * s)
            ax.set_ylim(cy - (cy - ymin) * s, cy + (ymax - cy) * s)
            self._canvas.draw_idle()

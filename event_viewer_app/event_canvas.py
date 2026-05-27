"""Matplotlib canvas with zoom percentage and scroll."""

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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
)
from .qt_compat import Qt, Signal


class EventCanvas(QWidget):
    """Canvas with zoom controls. No scroll area — clean rendering."""

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_dpi = 80
        self._zoom = 100
        self._fig = None
        self._canvas = None
        self._zoom_label = None
        self._hover_annot = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Zoom bar
        bar = QHBoxLayout()
        bar.setSpacing(4)
        bar.addStretch()
        btn_out = QPushButton("-")
        btn_out.setFixedSize(32, 28)
        btn_out.clicked.connect(lambda: self._set_zoom(self._zoom - 10))
        bar.addWidget(btn_out)
        self._zoom_label = QLabel("100%")
        self._zoom_label.setFixedWidth(42)
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        bar.addWidget(self._zoom_label)
        btn_in = QPushButton("+")
        btn_in.setFixedSize(32, 28)
        btn_in.clicked.connect(lambda: self._set_zoom(self._zoom + 10))
        bar.addWidget(btn_in)
        bar.addStretch()
        layout.addLayout(bar)

        # Figure
        self._fig = Figure(figsize=(14, 12), facecolor="white", dpi=self._base_dpi)
        self._canvas = FigureCanvasQTAgg(self._fig)
        layout.addWidget(self._canvas)

        # Events
        self._canvas.mpl_connect('button_press_event', self._on_click)
        self._canvas.mpl_connect('scroll_event', self._on_scroll)
        self._canvas.mpl_connect('motion_notify_event', self._on_hover)

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
            self._fig.tight_layout(pad=2.0, rect=[0, 0.02, 1, 0.95])
        self._canvas.draw_idle()

    def set_message(self, text: str):
        self._fig.clear()
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._canvas.draw_idle()

    def _set_zoom(self, pct):
        pct = max(30, min(300, int(pct)))
        if pct == self._zoom:
            return
        self._zoom = pct
        dpi = int(self._base_dpi * pct / 100)
        self._fig.set_dpi(dpi)
        self._zoom_label.setText(f"{pct}%")
        self._canvas.draw_idle()

    def _on_click(self, event):
        if event.dblclick or event.inaxes is None:
            return
        self._check_legend_click(event)
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

    def _check_legend_click(self, event):
        state = getattr(event.inaxes, '_legend_state', None)
        artists = getattr(event.inaxes, '_legend_artists', None)
        if state is None or artists is None:
            return
        leg = event.inaxes.get_legend()
        if leg is None:
            return
        for txt in leg.get_texts():
            if txt.contains(event)[0]:
                label = txt.get_text().lower()
                for key in state:
                    if key in label:
                        state[key] = not state[key]
                        art_obj = artists.get(key)
                        if art_obj is not None:
                            if isinstance(art_obj, list):
                                for a in art_obj: a.set_visible(state[key])
                            else:
                                art_obj.set_visible(state[key])
                        self._canvas.draw_idle()
                        return

    def _on_scroll(self, event):
        if event.inaxes is None:
            return
        ax = event.inaxes
        if event.modifiers & Qt.ControlModifier:
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

    def _on_hover(self, event):
        if event.inaxes is None:
            if self._hover_annot is not None:
                self._hover_annot.remove()
                self._hover_annot = None
                self._canvas.draw_idle()
            return
        for coll in event.inaxes.collections:
            if not hasattr(coll, 'get_offsets'):
                continue
            cont, info = coll.contains(event)
            if cont:
                idx = info['ind'][0]
                offsets = coll.get_offsets()
                if idx < len(offsets):
                    x, y = offsets[idx]
                    pmt_info = getattr(event.inaxes, '_pmt_ids', None)
                    pid = pmt_info[idx] if pmt_info is not None and idx < len(pmt_info) else idx
                    if self._hover_annot is not None:
                        self._hover_annot.remove()
                    self._hover_annot = event.inaxes.annotate(
                        f"PMT {pid}", (x, y),
                        xytext=(5, 5), textcoords='offset points',
                        fontsize=8, color='black',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8),
                    )
                    self._canvas.draw_idle()
                    return
        if self._hover_annot is not None:
            self._hover_annot.remove()
            self._hover_annot = None
            self._canvas.draw_idle()

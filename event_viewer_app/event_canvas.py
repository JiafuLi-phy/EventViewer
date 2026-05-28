"""Matplotlib canvas widget for event display, embedded in Qt."""

import matplotlib
import warnings

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
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from .qt_compat import Qt, Signal


class EventCanvas(QWidget):
    """Matplotlib page with mouse-wheel axes zoom."""

    peak_clicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fig = None
        self._canvas = None
        self._toolbar = None
        self._hover_annot = None
        self._zoom_label = None
        self._page_zoom = 100
        self._base_dpi = 90
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        self._fig = Figure(figsize=(16, 18), facecolor="white", dpi=self._base_dpi)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setStyleSheet("background: white;")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        controls = QHBoxLayout()
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(4)
        try:
            self._toolbar = NavigationToolbar2QT(self._canvas, self)
            self._toolbar.setMaximumHeight(36)
            controls.addWidget(self._toolbar)
        except Exception:
            pass
        controls.addStretch()
        zoom_out = QPushButton("-")
        zoom_out.setFixedSize(30, 26)
        zoom_out.clicked.connect(lambda: self.set_page_zoom(self._page_zoom - 10))
        controls.addWidget(zoom_out)
        self._zoom_label = QLabel("100%")
        self._zoom_label.setAlignment(Qt.AlignCenter)
        self._zoom_label.setFixedWidth(48)
        controls.addWidget(self._zoom_label)
        zoom_in = QPushButton("+")
        zoom_in.setFixedSize(30, 26)
        zoom_in.clicked.connect(lambda: self.set_page_zoom(self._page_zoom + 10))
        controls.addWidget(zoom_in)
        controls.addStretch()
        layout.addLayout(controls)

        layout.addWidget(self._canvas, 1)

        self._canvas.mpl_connect('button_press_event', self._on_click)
        self._canvas.mpl_connect('scroll_event', self._on_scroll)
        self._canvas.mpl_connect('motion_notify_event', self._on_hover)
        self._update_canvas_size()

    @property
    def figure(self):
        return self._fig

    @property
    def canvas(self):
        return self._canvas

    def clear(self):
        if self._hover_annot:
            try: self._hover_annot.remove()
            except Exception: pass
            self._hover_annot = None
        # Replace entire figure to eliminate ghosting
        old_canvas = self._canvas
        self._fig = Figure(figsize=(16, 18), facecolor="white", dpi=self._base_dpi)
        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setStyleSheet("background: white;")
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Reconnect events
        self._canvas.mpl_connect('button_press_event', self._on_click)
        self._canvas.mpl_connect('scroll_event', self._on_scroll)
        self._canvas.mpl_connect('motion_notify_event', self._on_hover)
        # Swap in layout
        layout = self.layout()
        if layout:
            idx = layout.indexOf(old_canvas)
            if idx >= 0:
                layout.insertWidget(idx, self._canvas)
            else:
                layout.addWidget(self._canvas)
        old_canvas.setParent(None)
        old_canvas.deleteLater()
        # Update toolbar to use new canvas (fixes save button)
        if self._toolbar is not None:
            self._toolbar.canvas = self._canvas
        self._update_canvas_size()

    def draw(self):
        self._update_canvas_size()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*not compatible with tight_layout.*")
            self._fig.tight_layout(pad=2.0, rect=[0, 0.02, 1, 0.95])
        self._canvas.draw()

    def set_message(self, text: str):
        self._fig.clf()
        self._fig.set_size_inches(10, 8, forward=True)
        ax = self._fig.add_subplot(111)
        ax.text(0.5, 0.5, text, transform=ax.transAxes,
                ha="center", va="center", fontsize=14, color="grey")
        ax.set_axis_off()
        self._update_canvas_size()
        self._canvas.draw()

    def set_page_zoom(self, pct: int):
        pct = max(50, min(250, int(pct)))
        if pct == self._page_zoom:
            return
        self._page_zoom = pct
        if self._zoom_label is not None:
            self._zoom_label.setText(f"{pct}%")
        self._update_canvas_size()
        self._canvas.draw()

    def _update_canvas_size(self):
        scale = self._page_zoom / 100.0
        self._fig.set_dpi(self._base_dpi * scale)

    def _on_click(self, event):
        if event.dblclick or event.inaxes is None:
            return
        # legend toggle: click to show only that layer, click again to show all
        state = getattr(event.inaxes, '_legend_state', None)
        artists = getattr(event.inaxes, '_legend_artists', None)
        if state and artists:
            leg = event.inaxes.get_legend()
            if leg:
                for txt in leg.get_texts():
                    if txt.contains(event)[0]:
                        clicked_key = None
                        for key in state:
                            if key in txt.get_text().lower():
                                clicked_key = key
                                break
                        if clicked_key:
                            # If only this layer is visible, show all
                            visible_count = sum(1 for v in state.values() if v)
                            if visible_count == 1 and state[clicked_key]:
                                for k in state: state[k] = True
                            else:
                                # Show only clicked layer
                                for k in state: state[k] = (k == clicked_key)
                            for k, a in artists.items():
                                if a is not None:
                                    v = state[k]
                                    if isinstance(a, list):
                                        for x in a: x.set_visible(v)
                                    else:
                                        a.set_visible(v)
                            self._canvas.draw_idle()
                            return
        # PMT pattern click: open zoomed standalone figure
        if event.inaxes.collections and not event.inaxes.lines:
            self._zoom_pmt_pattern(event.inaxes)
            return

        # peak hit test
        regions = getattr(event.inaxes, '_peak_regions', None)
        if not regions:
            return
        x = event.xdata
        if x is None:
            return
        best, best_d = None, 500  # 500 μs tolerance
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
        s = 0.8 if event.button == 'up' else 1.25
        cx, cy = event.xdata, event.ydata
        if cx is None or cy is None:
            return
        xmin, xmax = ax.get_xlim()
        ymin, ymax = ax.get_ylim()
        if xmax <= xmin or ymax <= ymin:
            return
        ax.set_xlim(cx - (cx - xmin) * s, cx + (xmax - cx) * s)
        ax.set_ylim(cy - (cy - ymin) * s, cy + (ymax - cy) * s)
        self._canvas.draw()

    def _zoom_pmt_pattern(self, ax):
        """Open a standalone zoomed PMT hit pattern figure."""
        import matplotlib.pyplot as plt
        title = ax.get_title()
        fig, new_ax = plt.subplots(figsize=(8, 8))
        pmt_ids = getattr(ax, '_pmt_ids', None)
        hover_annot = [None]  # mutable for closure
        # Copy PMT scatter data
        for coll in ax.collections:
            if hasattr(coll, 'get_offsets'):
                offsets = coll.get_offsets()
                facecolors = coll.get_facecolors()
                sc = new_ax.scatter(offsets[:, 0], offsets[:, 1],
                              s=100, c=facecolors, edgecolors='white', linewidths=0.3)
        # Copy circle artists
        for artist in ax.artists:
            if hasattr(artist, 'radius'):
                r = artist.radius
                new_ax.add_artist(plt.Circle((0, 0), r, edgecolor='k', facecolor='none', linewidth=1.2))
        new_ax._pmt_ids = pmt_ids
        new_ax.set_aspect('equal')
        new_ax.set_xlim(ax.get_xlim())
        new_ax.set_ylim(ax.get_ylim())
        new_ax.set_xlabel(ax.get_xlabel())
        new_ax.set_ylabel(ax.get_ylabel())
        new_ax.set_title(title)
        # Add colorbar
        for coll in new_ax.collections:
            if hasattr(coll, 'get_array'):
                fig.colorbar(coll, ax=new_ax, fraction=0.046, pad=0.04, label='Area [PE]')
                break
        fig.tight_layout()
        # Hover handler for PMT ID
        def on_hover(event):
            if event.inaxes != new_ax:
                if hover_annot[0]:
                    hover_annot[0].remove()
                    hover_annot[0] = None
                    fig.canvas.draw_idle()
                return
            for coll in new_ax.collections:
                if not hasattr(coll, 'get_offsets'):
                    continue
                cont, info = coll.contains(event)
                if cont:
                    idx = info['ind'][0]
                    offsets = coll.get_offsets()
                    x, y = offsets[idx]
                    pid = pmt_ids[idx] if pmt_ids and idx < len(pmt_ids) else idx
                    if hover_annot[0]:
                        hover_annot[0].remove()
                    hover_annot[0] = new_ax.annotate(
                        f"PMT {pid}", (x, y), xytext=(5, 5),
                        textcoords='offset points', fontsize=10, color='black',
                        bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
                    fig.canvas.draw_idle()
                    return
            if hover_annot[0]:
                hover_annot[0].remove()
                hover_annot[0] = None
                fig.canvas.draw_idle()
        fig.canvas.mpl_connect('motion_notify_event', on_hover)
        fig.show()

    def _on_hover(self, event):
        if event.inaxes is None:
            if self._hover_annot:
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
                x, y = coll.get_offsets()[idx]
                ids = getattr(event.inaxes, '_pmt_ids', None)
                pid = ids[idx] if ids and idx < len(ids) else idx
                if self._hover_annot:
                    self._hover_annot.remove()
                self._hover_annot = event.inaxes.annotate(
                    f"PMT {pid}", (x, y), xytext=(5, 5),
                    textcoords='offset points', fontsize=8, color='black',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
                self._canvas.draw_idle()
                return
        if self._hover_annot:
            self._hover_annot.remove()
            self._hover_annot = None
            self._canvas.draw_idle()

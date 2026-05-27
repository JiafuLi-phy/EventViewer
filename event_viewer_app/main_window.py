"""Main application window for the XENONnT Event Viewer."""

import sys
import os

import numpy as np

from .qt_compat import (
    QMainWindow, QSplitter, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QLabel, QInputDialog,
)
from .qt_compat import Qt
from .qt_compat import QAction, QKeySequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from event_viewer_app.data_manager import DataManager
from event_viewer_app.event_browser import EventBrowser
from event_viewer_app.event_canvas import EventCanvas
from event_plotter import plotter, style


class MainWindow(QMainWindow):
    """Main window for the XENONnT Event Viewer."""

    def __init__(self):
        super().__init__()
        self._dm = DataManager()
        self._current_event = None

        style.apply_style(font_size=9)

        self.setWindowTitle("XENONnT Event Viewer")
        self.setMinimumSize(1200, 750)
        self.resize(1600, 950)

        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()
        self._setup_shortcuts()

    # ── UI setup ──────────────────────────────────────────────────

    def _setup_menu(self):
        menu = self.menuBar()

        # File menu
        file_menu = menu.addMenu("&File")

        open_npz = QAction("Open Event Bundle...", self)
        open_npz.setShortcut(QKeySequence("Ctrl+O"))
        open_npz.triggered.connect(self._on_open_bundle)
        file_menu.addAction(open_npz)

        open_npz_dir = QAction("Open .npz Directory...", self)
        open_npz_dir.triggered.connect(self._on_open_npz)
        file_menu.addAction(open_npz_dir)

        open_run = QAction("Open Strax Run...", self)
        open_run.setShortcut(QKeySequence("Ctrl+R"))
        open_run.triggered.connect(self._on_open_run_dialog)
        file_menu.addAction(open_run)

        file_menu.addSeparator()

        export_pdf = QAction("Export Current Event as PDF...", self)
        export_pdf.setShortcut(QKeySequence("Ctrl+S"))
        export_pdf.triggered.connect(self._on_export_pdf)
        file_menu.addAction(export_pdf)

        export_png = QAction("Export Current Event as PNG...", self)
        export_png.triggered.connect(self._on_export_png)
        file_menu.addAction(export_png)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Navigate menu
        nav_menu = menu.addMenu("&Navigate")

        prev_action = QAction("Previous Event", self)
        prev_action.setShortcut(QKeySequence("Up"))
        prev_action.triggered.connect(lambda: self._browser.navigate(-1))
        nav_menu.addAction(prev_action)

        next_action = QAction("Next Event", self)
        next_action.setShortcut(QKeySequence("Down"))
        next_action.triggered.connect(lambda: self._browser.navigate(1))
        nav_menu.addAction(next_action)

    def _setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        # Left panel: browser
        self._browser = EventBrowser(self._dm)
        self._browser.setMaximumWidth(320)
        self._browser.setMinimumWidth(220)
        self._browser.event_selected.connect(self._on_event_selected)
        self._browser.data_source_changed.connect(self._on_data_source_changed)
        splitter.addWidget(self._browser)

        # Right panel: canvas
        self._canvas = EventCanvas()
        self._canvas.setMinimumWidth(600)
        splitter.addWidget(self._canvas)

        splitter.setSizes([280, 1320])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._status_label = QLabel("Ready – open a data source to begin")
        self._statusbar.addWidget(self._status_label)

    def _setup_shortcuts(self):
        """Additional keyboard shortcuts not bound to menu actions."""
        pass

    # ── slots ─────────────────────────────────────────────────────

    def _on_open_bundle(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Event Bundle", "",
            "NPZ Bundles (*.npz);;All Files (*)"
        )
        if not path:
            return
        try:
            n = self._dm.open_npz_bundle(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open bundle:\n{e}")
            return
        self._browser._on_data_loaded(n, f"Bundle: {os.path.basename(path)}")
        self._status_label.setText(f"Loaded {n} events from {os.path.basename(path)}")

    def _on_open_npz(self):
        path = QFileDialog.getExistingDirectory(self, "Select .npz Data Directory")
        if not path:
            return
        n = self._dm.open_npz_directory(path)
        if n == 0:
            QMessageBox.warning(self, "No Data", f"No event .npz files found in:\n{path}")
            return
        self._browser._on_data_loaded(n, f"NPZ directory: {path}")
        self._status_label.setText(f"Loaded {n} events from {path}")

    def _on_open_run_dialog(self):
        """Simple dialog to ask for a run ID."""
        run_id, ok = QInputDialog.getText(
            self, "Open Strax Run", "Run ID:", text="023756"
        )
        if not ok or not run_id.strip():
            return
        try:
            n = self._dm.open_strax_run(run_id.strip())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load run {run_id}:\n{e}")
            return
        self._browser._on_data_loaded(n, f"Strax run: {run_id}")
        self._status_label.setText(f"Loaded {n} events from run {run_id}")

    def _on_data_source_changed(self):
        """Called when the browser changes data source."""
        self._canvas.set_message("Select an event from the list")

    def _on_event_selected(self, event_number: int):
        """Render the selected event on the canvas."""
        self._status_label.setText(f"Loading event {event_number} ...")
        self._canvas.clear()
        self._canvas.canvas.draw_idle()

        try:
            event = self._dm.get_event(event_number)
            if event is None:
                self._canvas.set_message(f"Event {event_number} not found")
                return

            peaks = self._dm.get_peaks(event_number)
            to_pe = self._dm.get_to_pe()
            pmt_pos = self._dm.get_pmt_positions()

            if to_pe is None or pmt_pos is None:
                self._canvas.set_message("Missing PMT geometry / gain data")
                return

            eac = None
            if self._dm.mode == "strax":
                eac = self._dm.get_event_area_per_channel(event_number)

            # Draw into the canvas figure
            fig = self._canvas.figure

            plotter.plot_event_full(
                event, peaks, to_pe, pmt_pos,
                event_area_per_channel=eac,
                show_largest=200,
                fig=fig,
                run_id=self._dm.run_id,
            )

            self._canvas.draw()

            # Status
            n_peaks = len(peaks) if peaks is not None else 0
            s1_info = s2_info = ""
            if self._dm.mode == "strax" and event is not None:
                if "s1_area" in event.dtype.names:
                    s1_info = f"  S1={event['s1_area']:.0f} PE"
                if "s2_area" in event.dtype.names:
                    s2_info = f"  S2={event['s2_area']:.0f} PE"
            self._status_label.setText(
                f"Event {event_number}  |  {n_peaks} peaks{s1_info}{s2_info}"
            )
            self._current_event = event_number

        except Exception as e:
            self._canvas.set_message(f"Error loading event {event_number}:\n{e}")
            self._status_label.setText(f"Error: {e}")

    # ── export ────────────────────────────────────────────────────

    def _on_export_pdf(self):
        if self._current_event is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", f"event_{self._current_event}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return
        self._canvas.figure.savefig(path, dpi=300, bbox_inches="tight")
        self._status_label.setText(f"Exported → {path}")

    def _on_export_png(self):
        if self._current_event is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG", f"event_{self._current_event}.png",
            "PNG Files (*.png)"
        )
        if not path:
            return
        self._canvas.figure.savefig(path, dpi=300, bbox_inches="tight")
        self._status_label.setText(f"Exported → {path}")

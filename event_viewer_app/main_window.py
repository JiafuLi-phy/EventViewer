"""Main application window for the XENONnT Event Viewer."""

import sys
import os

import numpy as np

from .qt_compat import (
    QMainWindow, QSplitter, QStatusBar, QMenuBar, QMenu,
    QFileDialog, QMessageBox, QLabel, QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QVBoxLayout, QHBoxLayout, QShortcut, QComboBox,
    QGroupBox, QPushButton, QLineEdit,
)
from .qt_compat import Qt, QObject, QThread, Signal, Slot
from .qt_compat import QAction, QKeySequence

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJ = os.path.dirname(_HERE)
if _PROJ not in sys.path:
    sys.path.insert(0, _PROJ)

from event_viewer_app.data_manager import DataManager
from event_viewer_app.event_browser import EventBrowser
from event_viewer_app.event_canvas import EventCanvas
from event_plotter import plotter, style


class StraxLoadWorker(QObject):
    """Background worker for slow strax run initialization."""

    finished = Signal(object, int, str)
    failed = Signal(str, str)

    def __init__(self, run_id: str):
        super().__init__()
        self._run_id = run_id

    @Slot()
    def run(self):
        try:
            dm = DataManager()
            n = dm.open_strax_run(self._run_id, peak_data_type="peaks")
            dm.preload_peaks()
            self.finished.emit(dm, n, self._run_id)
        except Exception as e:
            self.failed.emit(self._run_id, str(e))


class PeakListWidget(QWidget):
    """Table widget listing all peaks for the current event."""

    COLUMNS = ["Type", "Area [PE]", "Width [μs]", "Rise [μs]"]

    class NumericItem(QTableWidgetItem):
        @staticmethod
        def _sort_value(text):
            try:
                if any(ch in text for ch in ".eE"):
                    return float(text)
                return int(text)
            except Exception:
                return text

        def __lt__(self, other):
            left = self._sort_value(self.text())
            right = self._sort_value(other.text())
            if isinstance(left, (int, float)) and isinstance(right, (int, float)):
                return left < right
            return super().__lt__(other)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header = QLabel("Peaks")
        header.setStyleSheet("font-weight: bold; font-size: 12px; padding: 4px 0;")
        header_row.addWidget(header)
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("peak search...")
        self._search_edit.setMaximumWidth(180)
        self._search_edit.textChanged.connect(self._apply_search)
        header_row.addWidget(self._search_edit)
        layout.addLayout(header_row)

        self._event_info = QLabel("")
        self._event_info.setStyleSheet("font-size: 10px; color: #555; padding: 2px 0;")
        layout.addWidget(self._event_info)

        self._table = QTableWidget(0, len(self.COLUMNS))
        self._table.setHorizontalHeaderLabels(self.COLUMNS)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setSortingEnabled(True)
        layout.addWidget(self._table)

        self._peak_indices = []  # maps table row → original peak index
        self._all_peaks = np.array([])
        self._main_s1_idx = None
        self._main_s2_idx = None
        self._event_time_ns = None

    def populate(self, peaks, main_s1_idx=None, main_s2_idx=None, event_time_ns=None,
                 drift_time_us=None, s2_x=None, s2_y=None):
        """Fill table with peak data."""
        self._all_peaks = peaks if peaks is not None else np.array([])
        self._main_s1_idx = main_s1_idx
        self._main_s2_idx = main_s2_idx
        self._event_time_ns = event_time_ns
        # Update event info label
        parts = []
        if drift_time_us is not None:
            parts.append(f"Drift: {drift_time_us:.1f} μs")
        if s2_x is not None and s2_y is not None and (abs(s2_x) > 0.01 or abs(s2_y) > 0.01):
            parts.append(f"S2 pos: ({s2_x:.1f}, {s2_y:.1f}) cm")
        self._event_info.setText("  |  ".join(parts))
        self._render_table()

    def _apply_search(self):
        self._render_table()

    def _peak_display_values(self, p, orig_i):
        ptype = int(p["type"])
        type_label = style.PEAK_LABELS.get(ptype, f"?{ptype}")
        display_type = type_label
        if orig_i == self._main_s1_idx:
            display_type = "Main S1"
        elif orig_i == self._main_s2_idx:
            display_type = "Main S2"

        if "range_90p_area" in p.dtype.names:
            width = float(p["range_90p_area"]) / 1000
        else:
            if "endtime" in p.dtype.names:
                width = (int(p["endtime"]) - int(p["time"])) / 1000
            elif "length" in p.dtype.names and "dt" in p.dtype.names:
                width = int(p["length"]) * int(p["dt"]) / 1000
            else:
                width = 0

        rise = float(p["rise_time"]) / 1000 if "rise_time" in p.dtype.names else 0
        t0 = int(self._event_time_ns) if self._event_time_ns is not None else 0
        ev_time = (int(p["time"]) - t0) / 1000

        return display_type, float(p["area"]), width, rise, ev_time

    def _matches_query(self, p, orig_i, query: str) -> bool:
        if not query:
            return True
        display_type, area, width, rise, ev_time = self._peak_display_values(p, orig_i)
        ptype = int(p["type"])

        # Parse numeric filters: area>1000, width<50, rise>=10, time<=100
        numeric_ops = {"area": area, "width": width, "rise": rise, "time": ev_time}
        text_tokens = []
        for token in query.lower().replace("#", " ").split():
            matched = False
            for key, val in numeric_ops.items():
                for op in (">=", "<=", ">", "<", "="):
                    prefix = key + op
                    if token.startswith(prefix):
                        try:
                            threshold = float(token[len(prefix):])
                            if op == ">" and not (val > threshold):
                                return False
                            if op == ">=" and not (val >= threshold):
                                return False
                            if op == "<" and not (val < threshold):
                                return False
                            if op == "<=" and not (val <= threshold):
                                return False
                            if op == "=" and not (abs(val - threshold) < 1e-9):
                                return False
                            matched = True
                        except ValueError:
                            return False
                        break
                if matched:
                    break
            if not matched:
                text_tokens.append(token)

        if not text_tokens:
            return True

        # Text search in remaining tokens
        if len(text_tokens) >= 2 and text_tokens[0] in ("idx", "index", "peak"):
            try:
                return orig_i == int(text_tokens[1])
            except ValueError:
                return False

        haystack = " ".join([
            display_type,
            style.PEAK_LABELS.get(ptype, ""),
            f"type {ptype}",
            f"index {orig_i}",
            f"idx {orig_i}",
            f"{orig_i}",
            f"{area:.0f}",
            f"{width:.1f}",
            f"{rise:.1f}",
            f"{ev_time:.1f}",
        ]).lower()
        return all(token in haystack for token in text_tokens)

    def _render_table(self):
        peaks = self._all_peaks
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        self._peak_indices = []

        # Custom sort: Main S1, Main S2, S1s, S2s, unknown. Within group by area desc.
        if len(peaks):
            original_idx = np.arange(len(peaks))
            # Assign sort group: 0=Main S1, 1=Main S2, 2=S1, 3=S2, 4=unknown
            groups = np.full(len(peaks), 4, dtype=int)
            groups[peaks['type'] == 1] = 2
            groups[peaks['type'] == 2] = 3
            if self._main_s1_idx is not None and self._main_s1_idx < len(peaks):
                groups[self._main_s1_idx] = 0
            if self._main_s2_idx is not None and self._main_s2_idx < len(peaks):
                groups[self._main_s2_idx] = 1
            # Sort by (group, -area)
            order = np.lexsort((-peaks["area"], groups))
            peaks = peaks[order]
            original_idx = original_idx[order]
        else:
            original_idx = []

        query = self._search_edit.text().strip()

        for i, p in enumerate(peaks):
            orig_i = original_idx[i]
            if not self._matches_query(p, int(orig_i), query):
                continue
            row = self._table.rowCount()
            self._table.insertRow(row)

            ptype = int(p["type"])
            display_type, area, width, rise, ev_time = self._peak_display_values(p, int(orig_i))

            # Type
            item = QTableWidgetItem(display_type)
            item.setForeground(Qt.GlobalColor.black)
            self._table.setItem(row, 0, item)

            # Area
            item = self.NumericItem(f"{area:.0f}")
            self._table.setItem(row, 1, item)

            item = self.NumericItem(f"{width:.1f}")
            self._table.setItem(row, 2, item)

            item = self.NumericItem(f"{rise:.1f}")
            self._table.setItem(row, 3, item)

            # Color-code S1/S2 rows
            if ptype == 1:
                for col in range(len(self.COLUMNS)):
                    self._table.item(row, col).setBackground(Qt.GlobalColor(0xE8F0FE))
            elif ptype == 2:
                for col in range(len(self.COLUMNS)):
                    self._table.item(row, col).setBackground(Qt.GlobalColor(0xE8F8E8))

            # Bold rename for main S1/S2
            if orig_i == self._main_s1_idx:
                type_item = self._table.item(row, 0)
                font = type_item.font(); font.setBold(True); type_item.setFont(font)
            elif orig_i == self._main_s2_idx:
                type_item = self._table.item(row, 0)
                font = type_item.font(); font.setBold(True); type_item.setFont(font)

            for col in range(len(self.COLUMNS)):
                self._table.item(row, col).setData(Qt.UserRole, int(orig_i))
            self._peak_indices.append(int(orig_i))

        self._table.resizeColumnsToContents()

    def get_selected_peak_index(self) -> int:
        """Return the original peak index for the selected row, or -1."""
        rows = set()
        for idx in self._table.selectionModel().selectedRows():
            rows.add(idx.row())
        if len(rows) != 1:
            return -1
        row = rows.pop()
        item = self._table.item(row, 0)
        if item is not None:
            data = item.data(Qt.UserRole)
            if data is not None:
                return int(data)
        return -1

    def clear_selection(self):
        self._table.clearSelection()


class MainWindow(QMainWindow):
    """Main window for the XENONnT Event Viewer."""

    def __init__(self):
        super().__init__()
        self._dm = DataManager()
        self._current_event = None
        self._current_peaks_index = None  # original index of each peak in full array

        # Interaction state
        self._view_mode = "overview"     # "overview" or "peak_zoom"
        self._selected_peak_idx = None
        self._peaks_for_event = None     # all peaks for current event (original order)
        self._eac_for_event = None       # event_area_per_channel for current event
        self._raw_records_for_event = None
        self._strax_thread = None
        self._strax_worker = None

        style.apply_style(font_size=11, axes_linewidth=2.0)

        self.setWindowTitle("XENONnT Event Viewer")
        self.setMinimumSize(1200, 750)
        self.resize(1600, 950)

        self._setup_menu()
        self._setup_ui()
        self._setup_statusbar()
        self._setup_shortcuts()
        self._load_initial_bundle()

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

        prev_action = QAction("Previous Event (←)", self)
        prev_action.triggered.connect(lambda: self._browser.navigate(-1))
        nav_menu.addAction(prev_action)

        next_action = QAction("Next Event (→)", self)
        next_action.triggered.connect(lambda: self._browser.navigate(1))
        nav_menu.addAction(next_action)

    def _setup_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        # ── Left panel: browser + peak list ──
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Run Selector
        run_group = QGroupBox("Run Selector")
        run_layout = QVBoxLayout(run_group)
        run_row = QHBoxLayout()
        self._run_combo = QComboBox()
        self._run_combo.currentIndexChanged.connect(self._on_run_selected)
        run_row.addWidget(self._run_combo, 1)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_open_bundle)
        run_row.addWidget(browse_btn)
        run_layout.addLayout(run_row)
        left_layout.addWidget(run_group)

        self._browser = EventBrowser(self._dm)
        self._browser.setMaximumWidth(500)
        self._browser.setMinimumWidth(220)
        self._browser.event_selected.connect(self._on_event_selected)
        self._browser.data_source_changed.connect(self._on_data_source_changed)
        self._browser.strax_run_requested.connect(self._start_strax_load)

        self._peak_list = PeakListWidget()
        self._peak_list.setMaximumWidth(500)
        self._peak_list.setMinimumWidth(220)
        self._peak_list._table.itemSelectionChanged.connect(self._on_peak_list_selection)

        left_layout.addWidget(self._browser, 3)
        left_layout.addWidget(self._peak_list, 2)

        # Populate run list
        self._scan_npz_files()

        splitter.addWidget(left_panel)

        # ── Right panel: canvas ──
        self._canvas = EventCanvas()
        self._canvas.setMinimumWidth(600)
        self._canvas.peak_clicked.connect(self._on_peak_clicked)
        splitter.addWidget(self._canvas)

        splitter.setSizes([300, 1300])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)

        self.setCentralWidget(splitter)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)
        self._status_label = QLabel("Ready – open a data source to begin")
        self._statusbar.addWidget(self._status_label)

    def _setup_shortcuts(self):
        """Additional keyboard shortcuts not bound to menu actions."""
        QShortcut(QKeySequence("Escape"), self).activated.connect(
            self._clear_peak_selection
        )
        QShortcut(QKeySequence("Left"), self).activated.connect(
            lambda: self._browser.navigate(-1)
        )
        QShortcut(QKeySequence("Right"), self).activated.connect(
            lambda: self._browser.navigate(1)
        )

    # ── Run Selector ─────────────────────────────────────────────

    def _scan_npz_files(self):
        """Scan for .npz files in common locations and populate the run combo."""
        search_dirs = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts', 'output'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'dali_probe'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'),
            os.getcwd(),
            os.path.expanduser('~/Desktop/EventViewer/dali_probe'),
            os.path.expanduser('~/Desktop/EventViewer/scripts/output'),
        ]
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            search_dirs.insert(0, sys._MEIPASS)
        if getattr(sys, 'frozen', False):
            exe_dir = os.path.dirname(sys.executable)
            search_dirs.insert(0, os.path.abspath(os.path.join(exe_dir, '..', 'Resources')))
            search_dirs.insert(0, os.path.abspath(os.path.join(exe_dir, '..', 'Frameworks')))

        self._run_combo.blockSignals(True)
        self._run_combo.clear()
        self._run_paths = {}

        seen_paths = set()
        seen_labels = set()
        for d in search_dirs:
            if not os.path.isdir(d):
                continue
            try:
                for f in sorted(os.listdir(d)):
                    if not f.endswith('.npz'):
                        continue
                    full = os.path.abspath(os.path.join(d, f))
                    canonical = os.path.realpath(full)
                    if canonical in seen_paths:
                        continue
                    try:
                        with np.load(full, allow_pickle=True) as b:
                            run_id = str(b.get('run_id', '?'))
                            n_ev = len(b['events']) if 'events' in b else '?'
                        label = f"Run {run_id} ({n_ev} ev)  [{os.path.basename(f)}]"
                    except Exception:
                        label = os.path.basename(f)
                    if label in seen_labels:
                        continue
                    seen_paths.add(canonical)
                    seen_labels.add(label)
                    self._run_paths[label] = full
                    self._run_combo.addItem(label)
            except OSError:
                pass

        self._run_combo.blockSignals(False)

    def _load_initial_bundle(self):
        """Load the current Run Selector item after the whole window exists."""
        if not self._run_combo.count():
            return
        preferred_idx = 0
        for i in range(self._run_combo.count()):
            if "events_run_023756.npz" in self._run_combo.itemText(i):
                preferred_idx = i
                break
        self._run_combo.blockSignals(True)
        self._run_combo.setCurrentIndex(preferred_idx)
        self._run_combo.blockSignals(False)
        self._on_run_selected(preferred_idx)

    def _on_run_selected(self, idx):
        if idx < 0:
            return
        label = self._run_combo.currentText()
        path = self._run_paths.get(label)
        if not path or not os.path.isfile(path):
            return
        self._view_mode = "overview"
        self._selected_peak_idx = None
        try:
            n = self._dm.open_npz_bundle(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open:\n{e}")
            return
        self._browser._on_data_loaded(n, f"Run: {os.path.basename(path)}")
        self._status_label.setText(f"Loaded {n} events from {os.path.basename(path)}")

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
        # Rescan to pick up any new files
        self._scan_npz_files()

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
        self._start_strax_load(run_id.strip())

    def _start_strax_load(self, run_id: str):
        """Load a strax run in a worker thread so the GUI stays responsive."""
        if self._strax_thread is not None:
            QMessageBox.information(self, "Loading", "A strax run is already loading.")
            return
        self._set_loading(True, f"Loading strax run {run_id} ...")
        self._canvas.set_message(f"Loading strax run {run_id} ...")

        self._strax_thread = QThread(self)
        self._strax_worker = StraxLoadWorker(run_id)
        self._strax_worker.moveToThread(self._strax_thread)
        self._strax_thread.started.connect(self._strax_worker.run)
        self._strax_worker.finished.connect(self._on_strax_loaded)
        self._strax_worker.failed.connect(self._on_strax_failed)
        self._strax_worker.finished.connect(self._strax_thread.quit)
        self._strax_worker.failed.connect(self._strax_thread.quit)
        self._strax_thread.finished.connect(self._cleanup_strax_thread)
        self._strax_thread.start()

    def _set_loading(self, loading: bool, text: str = ""):
        self._run_combo.setEnabled(not loading)
        self._browser.set_loading(loading, text or None)
        if text:
            self._status_label.setText(text)

    def _on_strax_loaded(self, dm: DataManager, n: int, run_id: str):
        self._dm = dm
        self._browser._dm = dm
        self._view_mode = "overview"
        self._selected_peak_idx = None
        self._peaks_for_event = None
        self._eac_for_event = None
        self._raw_records_for_event = None
        self._browser._on_data_loaded(n, f"Strax run: {run_id}")
        self._status_label.setText(f"Loaded {n} events from run {run_id}")
        self._set_loading(False)

    def _on_strax_failed(self, run_id: str, message: str):
        self._set_loading(False)
        self._canvas.set_message("Select an event from the list")
        QMessageBox.critical(
            self, "Error",
            "Failed to load this strax run.\n\n"
            "Direct strax loading needs strax/cutax plus a mounted XENONnT data path "
            "such as /dali/lgrandi/xenonnt/processed or /project/lgrandi/xenonnt/processed.\n\n"
            f"Run: {run_id}\nDetails: {message}"
        )

    def _cleanup_strax_thread(self):
        if self._strax_worker is not None:
            self._strax_worker.deleteLater()
        if self._strax_thread is not None:
            self._strax_thread.deleteLater()
        self._strax_worker = None
        self._strax_thread = None

    def _on_data_source_changed(self):
        """Called when the browser changes data source."""
        self._canvas.set_message("Select an event from the list")

    def _on_event_selected(self, event_number: int):
        """Render the selected event on the canvas."""
        self._status_label.setText(f"Loading event {event_number} ...")

        # Reset to overview mode
        self._view_mode = "overview"
        self._selected_peak_idx = None

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

            # Always load EAC (not just for strax mode)
            eac = self._dm.get_event_area_per_channel(event_number)
            # raw_records can be very large; avoid blocking the GUI in live strax mode.
            raw_records = None if self._dm.mode == "strax" else self._dm.get_raw_records(event_number)

            # Cache for interaction
            self._current_event = event_number
            self._peaks_for_event = peaks
            self._eac_for_event = eac
            self._raw_records_for_event = raw_records

            # Populate peak list
            s1_idx = int(event["s1_index"]) if "s1_index" in event.dtype.names else None
            s2_idx = int(event["s2_index"]) if "s2_index" in event.dtype.names else None
            event_time_ns = int(event["time"]) if "time" in event.dtype.names else None
            # Compute drift time
            drift_us = None
            if "s1_time" in event.dtype.names and "s2_time" in event.dtype.names:
                drift_us = (int(event["s2_time"]) - int(event["s1_time"])) / 1000
            s2x = float(event["s2_x"]) if "s2_x" in event.dtype.names else None
            s2y = float(event["s2_y"]) if "s2_y" in event.dtype.names else None
            self._peak_list.populate(
                peaks,
                main_s1_idx=s1_idx,
                main_s2_idx=s2_idx,
                event_time_ns=event_time_ns,
                drift_time_us=drift_us,
                s2_x=s2x, s2_y=s2y,
            )

            # Render
            self._render_event(event, peaks, to_pe, pmt_pos, eac, raw_records)

        except Exception as e:
            self._canvas.set_message(f"Error loading event {event_number}:\n{e}")
            self._status_label.setText(f"Error: {e}")

    def _render_event(self, event, peaks, to_pe, pmt_pos, eac, raw_records=None):
        """Render the current event (overview or peak zoom)."""
        self._canvas.clear()
        self._canvas.canvas.draw_idle()

        fig = self._canvas.figure

        if self._view_mode == "peak_zoom" and self._selected_peak_idx is not None:
            # Find the highlighted peak in the full peaks array
            if self._peaks_for_event is not None and len(self._peaks_for_event) > self._selected_peak_idx:
                peak = self._peaks_for_event[self._selected_peak_idx]
            else:
                peak = peaks[self._selected_peak_idx] if self._selected_peak_idx < len(peaks) else peaks[0]

            plotter.plot_peak_zoom(
                peak, peaks, to_pe, pmt_pos,
                event,
                highlight_idx=self._selected_peak_idx,
                event_area_per_channel=eac,
                raw_records=raw_records,
                fig=fig,
                figsize=(12, 13),
                run_id=self._dm.run_id,
            )

            ptype = int(peak["type"])
            ptype_label = style.PEAK_LABELS.get(ptype, f"type={ptype}")
            area = float(peak["area"])
            self._status_label.setText(
                f"Event {self._current_event}  |  {ptype_label} peak  |  area={area:.0f} PE  |  "
                f"(Escape to return to overview)"
            )
        else:
            plotter.plot_event_full(
                event, peaks, to_pe, pmt_pos,
                event_area_per_channel=eac,
                show_largest=200,
                raw_records=raw_records,
                fig=fig,
                figsize=(12, 16),
                run_id=self._dm.run_id,
            )

            n_peaks = len(peaks) if peaks is not None else 0
            s1_info = s2_info = ""
            if event is not None and "s1_area" in event.dtype.names:
                s1_info = f"  S1={event['s1_area']:.0f} PE"
            if event is not None and "s2_area" in event.dtype.names:
                s2_info = f"  S2={event['s2_area']:.0f} PE"
            has_peak_waveforms = peaks is not None and plotter.has_waveform(peaks)
            has_raw_records = raw_records is not None and len(raw_records)
            source_info = "  |  real waveforms" if has_peak_waveforms or has_raw_records else "  |  model waveforms"
            self._status_label.setText(
                f"Event {self._current_event}  |  {n_peaks} peaks{s1_info}{s2_info}{source_info}"
            )

        self._canvas.draw()

    def _on_peak_clicked(self, peak_idx: int):
        """Canvas click on a peak region — enter zoom mode."""
        if self._peaks_for_event is None:
            return

        if self._view_mode == "peak_zoom" and self._selected_peak_idx == peak_idx:
            # Click same peak again → go back to overview
            self._clear_peak_selection()
            return

        self._view_mode = "peak_zoom"
        self._selected_peak_idx = peak_idx
        self._peak_list.clear_selection()

        # Re-render
        event = self._dm.get_event(self._current_event)
        peaks = self._peaks_for_event
        to_pe = self._dm.get_to_pe()
        pmt_pos = self._dm.get_pmt_positions()
        eac = self._eac_for_event
        raw_records = self._raw_records_for_event
        self._render_event(event, peaks, to_pe, pmt_pos, eac, raw_records)

    def _on_peak_list_selection(self):
        """Peak selected from the table — enter zoom mode."""
        original_idx = self._peak_list.get_selected_peak_index()
        if original_idx < 0:
            return
        self._on_peak_clicked(original_idx)

    def _clear_peak_selection(self):
        """Return to overview mode."""
        if self._view_mode == "overview":
            return
        self._view_mode = "overview"
        self._selected_peak_idx = None
        self._peak_list.clear_selection()

        event = self._dm.get_event(self._current_event)
        peaks = self._peaks_for_event
        to_pe = self._dm.get_to_pe()
        pmt_pos = self._dm.get_pmt_positions()
        eac = self._eac_for_event
        raw_records = self._raw_records_for_event
        self._render_event(event, peaks, to_pe, pmt_pos, eac, raw_records)

    # ── export ────────────────────────────────────────────────────

    def _do_export(self, ext):
        if self._current_event is None:
            self._status_label.setText("Select an event first")
            return
        run_id = self._dm.run_id or "?"
        suffix = f"_peak{self._selected_peak_idx}" if self._selected_peak_idx is not None else ""
        desktop = os.path.expanduser("~/Desktop")
        base = f"run{run_id}_event_{self._current_event}{suffix}"
        # Find unique filename
        for i in range(100):
            path = os.path.join(desktop, f"{base}_{i}.{ext}")
            if not os.path.exists(path):
                break
        try:
            self._canvas.figure.savefig(path, dpi=200, bbox_inches="tight")
            self._status_label.setText(f"Exported → {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def _on_export_pdf(self):
        self._do_export("pdf")

    def _on_export_png(self):
        self._do_export("png")

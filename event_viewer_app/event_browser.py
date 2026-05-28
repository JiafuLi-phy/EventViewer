"""Event browser panel – left sidebar with event list, search, and filters."""

from typing import Optional, List

import numpy as np

from .qt_compat import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QLabel, QPushButton, QFileDialog, QGroupBox,
    QSpinBox, QDoubleSpinBox, QSplitter,
)
from .qt_compat import Qt, Signal


class EventBrowser(QWidget):
    """Left panel: event list with search, filter, and data-source controls."""

    event_selected = Signal(int)     # emitted when user selects an event
    data_source_changed = Signal()   # emitted when data source changes
    strax_run_requested = Signal(str)

    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self._dm = data_manager
        self._all_event_numbers = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # ── data source ──
        src_group = QGroupBox("Data Source")
        src_layout = QVBoxLayout(src_group)

        # open NPZ directory button
        self._btn_npz = QPushButton("Open .npz Directory...")
        self._btn_npz.clicked.connect(self._open_npz)
        src_layout.addWidget(self._btn_npz)

        # open strax run
        run_layout = QHBoxLayout()
        run_layout.addWidget(QLabel("Run ID:"))
        self._run_id_edit = QLineEdit("023756")
        self._run_id_edit.setMaximumWidth(80)
        run_layout.addWidget(self._run_id_edit)
        self._btn_strax = QPushButton("Load Run")
        self._btn_strax.clicked.connect(self._open_strax)
        run_layout.addWidget(self._btn_strax)
        src_layout.addLayout(run_layout)

        self._src_label = QLabel("No data loaded")
        self._src_label.setWordWrap(True)
        self._src_label.setStyleSheet("color: grey; font-size: 10px;")
        src_layout.addWidget(self._src_label)

        layout.addWidget(src_group)

        # ── filters ──
        filt_group = QGroupBox("Filters")
        filt_layout = QVBoxLayout(filt_group)

        s1_row = QHBoxLayout()
        s1_row.addWidget(QLabel("S1 min:"))
        self._s1_min = QDoubleSpinBox()
        self._s1_min.setRange(0, 1e9)
        self._s1_min.setValue(1000)
        self._s1_min.setDecimals(0)
        s1_row.addWidget(self._s1_min)
        filt_layout.addLayout(s1_row)

        s2_row = QHBoxLayout()
        s2_row.addWidget(QLabel("S2 min:"))
        self._s2_min = QDoubleSpinBox()
        self._s2_min.setRange(0, 1e9)
        self._s2_min.setValue(100000)
        self._s2_min.setDecimals(0)
        s2_row.addWidget(self._s2_min)
        filt_layout.addLayout(s2_row)

        self._btn_filter = QPushButton("Apply Filters")
        self._btn_filter.clicked.connect(self._apply_filters)
        filt_layout.addWidget(self._btn_filter)

        layout.addWidget(filt_group)

        # ── search ──
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("event number...")
        self._search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self._search_edit)
        layout.addLayout(search_layout)

        # ── event count label ──
        self._count_label = QLabel("0 events")
        self._count_label.setStyleSheet("font-size: 10px; color: grey;")
        layout.addWidget(self._count_label)

        # ── event list ──
        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list)

    # ── data loading ──────────────────────────────────────────────

    def _open_npz(self):
        path = QFileDialog.getExistingDirectory(self, "Select .npz Data Directory")
        if not path:
            return
        n = self._dm.open_npz_directory(path)
        self._on_data_loaded(n, f"NPZ directory: {path}")

    def _open_strax(self):
        run_id = self._run_id_edit.text().strip()
        if not run_id:
            return
        self.strax_run_requested.emit(run_id)

    def set_loading(self, loading: bool, text: Optional[str] = None):
        """Enable/disable browser controls during slow data loading."""
        self._btn_npz.setEnabled(not loading)
        self._btn_strax.setEnabled(not loading)
        self._run_id_edit.setEnabled(not loading)
        self._btn_filter.setEnabled(not loading)
        if text is not None:
            self._src_label.setText(text)

    def _on_data_loaded(self, n_events: int, source_desc: str):
        self._src_label.setText(f"{source_desc}\n{n_events} events loaded")
        self._populate_list()
        self.data_source_changed.emit()

    # ── list population ───────────────────────────────────────────

    def _populate_list(self):
        """Fill the list widget with events, applying current filters."""
        events = self._dm.events
        if events is None or len(events) == 0:
            self._list.clear()
            self._count_label.setText("0 events")
            return

        # Apply filters if event_info fields exist
        mask = np.ones(len(events), dtype=bool)
        if "s1_area" in events.dtype.names:
            mask &= events["s1_area"] > self._s1_min.value()
        if "s2_area" in events.dtype.names:
            mask &= events["s2_area"] > self._s2_min.value()

        filtered = events[mask]

        # Apply event-number search on top of S1/S2 filters.  Users often
        # type "#38991" from the visible list or only the last few digits.
        query = self._search_edit.text().strip().lstrip("#")
        if query:
            filtered = filtered[
                np.array(
                    [query in str(int(ev["event_number"])) for ev in filtered],
                    dtype=bool,
                )
            ]

        # Sort by S2 descending if available
        if "s2_area" in events.dtype.names:
            order = np.argsort(filtered["s2_area"])[::-1]
            filtered = filtered[order]

        self._all_event_numbers = [int(ev["event_number"]) for ev in filtered]

        self._list.clear()
        self._list.blockSignals(True)
        for ev in filtered:
            ev_num = int(ev["event_number"])
            if "s1_area" in ev.dtype.names or "s2_area" in ev.dtype.names:
                s1 = ev["s1_area"] if "s1_area" in ev.dtype.names else 0
                s2 = ev["s2_area"] if "s2_area" in ev.dtype.names else 0
                text = f"#{ev_num}  S1={s1:.0f}  S2={s2:.0f}"
            else:
                text = f"Event {ev_num}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, ev_num)
            self._list.addItem(item)
        self._list.blockSignals(False)

        self._count_label.setText(f"{len(filtered)} events shown")

        # Auto-select first event
        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _apply_filters(self):
        self._populate_list()

    # ── search ────────────────────────────────────────────────────

    def _on_search(self, text: str):
        """Filter the event list by event number as the user types."""
        self._populate_list()

    # ── selection ─────────────────────────────────────────────────

    def _on_selection_changed(self, row: int):
        if row < 0 or row >= self._list.count():
            return
        item = self._list.item(row)
        ev_num = item.data(Qt.UserRole)
        if ev_num is not None:
            self.event_selected.emit(ev_num)

    # ── public API ────────────────────────────────────────────────

    def select_event(self, event_number: int):
        """Programmatically select an event."""
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.UserRole) == event_number:
                self._list.setCurrentRow(i)
                return

    def navigate(self, delta: int):
        """Move selection by *delta* rows (+1 or -1)."""
        cur = self._list.currentRow()
        new = cur + delta
        if 0 <= new < self._list.count():
            self._list.setCurrentRow(new)

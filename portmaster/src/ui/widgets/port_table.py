"""Port table widget for displaying active ports."""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHeaderView, QMenu, QCheckBox,
    QMessageBox
)
from PyQt6.QtGui import QAction

from ...core import PortScanner, ProcessManager, PortInfo


class PortTableWidget(QWidget):
    """Widget displaying active ports with filtering and actions."""

    port_selected = pyqtSignal(int)  # Emitted when a port is selected
    process_killed = pyqtSignal(int)  # Emitted when a process is killed

    COLUMNS = ['Port', 'Protocol', 'State', 'Process', 'PID', 'Command Line']

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.port_scanner = PortScanner()
        self.process_manager = ProcessManager()
        self.current_data: list[PortInfo] = []

        self._setup_ui()
        self._setup_refresh_timer()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with controls
        header = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by port, process name, or PID...")
        self.search_input.textChanged.connect(self._apply_filter)
        header.addWidget(self.search_input)

        self.listening_only_cb = QCheckBox("Listening only")
        self.listening_only_cb.setChecked(True)
        self.listening_only_cb.stateChanged.connect(self.refresh)
        header.addWidget(self.listening_only_cb)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Port table
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMNS))
        self.table.setHorizontalHeaderLabels(self.COLUMNS)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        # Configure header
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Port
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Protocol
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # State
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Process
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # PID
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)  # Command Line

        self.table.setColumnWidth(0, 70)   # Port
        self.table.setColumnWidth(1, 70)   # Protocol
        self.table.setColumnWidth(2, 100)  # State
        self.table.setColumnWidth(3, 150)  # Process
        self.table.setColumnWidth(4, 70)   # PID

        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def _setup_refresh_timer(self):
        """Setup auto-refresh timer."""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)  # Refresh every 5 seconds

    def refresh(self):
        """Refresh the port list."""
        listening_only = self.listening_only_cb.isChecked()

        if listening_only:
            self.current_data = self.port_scanner.get_listening_ports()
        else:
            self.current_data = self.port_scanner.get_all_ports()

        self._populate_table()
        self._update_status()

    def _populate_table(self):
        """Populate table with current data."""
        filter_text = self.search_input.text().lower()

        self.table.setRowCount(0)

        for port_info in self.current_data:
            # Apply filter
            if filter_text:
                searchable = f"{port_info.port} {port_info.protocol.value} "
                if port_info.process:
                    searchable += f"{port_info.process.name} {port_info.process.pid} {port_info.process.cmdline}"
                if filter_text not in searchable.lower():
                    continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Port
            port_item = QTableWidgetItem(str(port_info.port))
            port_item.setData(Qt.ItemDataRole.UserRole, port_info)
            self.table.setItem(row, 0, port_item)

            # Protocol
            self.table.setItem(row, 1, QTableWidgetItem(port_info.protocol.value))

            # State
            self.table.setItem(row, 2, QTableWidgetItem(port_info.display_state))

            # Process name
            proc_name = port_info.process.name if port_info.process else "<unknown>"
            self.table.setItem(row, 3, QTableWidgetItem(proc_name))

            # PID
            pid = str(port_info.process.pid) if port_info.process else ""
            self.table.setItem(row, 4, QTableWidgetItem(pid))

            # Command line
            cmdline = port_info.process.cmdline if port_info.process else ""
            cmdline_item = QTableWidgetItem(cmdline)
            cmdline_item.setToolTip(cmdline)  # Full text in tooltip
            self.table.setItem(row, 5, cmdline_item)

    def _apply_filter(self):
        """Apply current filter to table."""
        self._populate_table()

    def _update_status(self):
        """Update status label."""
        total = len(self.current_data)
        shown = self.table.rowCount()
        mode = "listening" if self.listening_only_cb.isChecked() else "all"
        self.status_label.setText(f"Showing {shown} of {total} {mode} ports")

    def _on_selection_changed(self):
        """Handle selection change."""
        items = self.table.selectedItems()
        if items:
            port_info = items[0].data(Qt.ItemDataRole.UserRole)
            if port_info:
                self.port_selected.emit(port_info.port)

    def _show_context_menu(self, pos):
        """Show context menu for port actions."""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        port_item = self.table.item(row, 0)
        port_info: PortInfo = port_item.data(Qt.ItemDataRole.UserRole)

        if not port_info or not port_info.process:
            return

        menu = QMenu(self)

        # Capture values to avoid closure issues
        pid = port_info.process.pid
        proc_name = port_info.process.name
        exe_path = port_info.process.exe_path
        port_num = port_info.port

        # Kill process action
        kill_action = QAction(f"Kill Process ({proc_name})", self)
        kill_action.triggered.connect(lambda checked, p=pid: self._kill_process(p))
        menu.addAction(kill_action)

        # Kill process tree action
        kill_tree_action = QAction("Kill Process Tree", self)
        kill_tree_action.triggered.connect(lambda checked, p=pid: self._kill_process_tree(p))
        menu.addAction(kill_tree_action)

        menu.addSeparator()

        # Force kill action
        force_kill_action = QAction("Force Kill (SIGKILL)", self)
        force_kill_action.triggered.connect(lambda checked, p=pid: self._kill_process(p, force=True))
        menu.addAction(force_kill_action)

        menu.addSeparator()

        # Open file location
        if exe_path:
            open_location_action = QAction("Open File Location", self)
            open_location_action.triggered.connect(
                lambda checked, path=exe_path: self.process_manager.open_file_location(path)
            )
            menu.addAction(open_location_action)

        # Copy actions
        menu.addSeparator()
        copy_port = QAction(f"Copy Port: {port_num}", self)
        copy_port.triggered.connect(lambda checked, pn=port_num: self._copy_to_clipboard(str(pn)))
        menu.addAction(copy_port)

        copy_pid = QAction(f"Copy PID: {pid}", self)
        copy_pid.triggered.connect(lambda checked, p=pid: self._copy_to_clipboard(str(p)))
        menu.addAction(copy_pid)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _kill_process(self, pid: int, force: bool = False):
        """Kill a process after confirmation."""
        details = self.process_manager.get_process_details(pid)
        name = details.get('name', 'Unknown') if details else 'Unknown'

        action = "Force kill" if force else "Terminate"
        reply = QMessageBox.question(
            self,
            "Confirm Kill",
            f"{action} process '{name}' (PID: {pid})?\n\nThis may cause data loss.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.process_manager.kill_process(pid, force)
            if success:
                self.process_killed.emit(pid)
                self.refresh()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Failed", message)

    def _kill_process_tree(self, pid: int):
        """Kill a process tree after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Kill Tree",
            f"Kill process (PID: {pid}) and all its children?\n\nThis may cause data loss.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.process_manager.kill_process_tree(pid)
            if success:
                self.process_killed.emit(pid)
                self.refresh()
                QMessageBox.information(self, "Success", message)
            else:
                QMessageBox.warning(self, "Failed", message)

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        from PyQt6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def get_selected_port(self) -> Optional[int]:
        """Get currently selected port."""
        items = self.table.selectedItems()
        if items:
            port_info = items[0].data(Qt.ItemDataRole.UserRole)
            if port_info:
                return port_info.port
        return None

#!/usr/bin/env python3
"""
PortMaster - Simple Port Monitor for C:/Claude Projects

Shows only ports being used by processes running from C:/Claude subfolders.
No config scanning, no complexity - just what's actually running.
"""

import sys
import os
import psutil
import socket
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QHeaderView,
    QMessageBox, QLineEdit, QCheckBox, QMenu
)
from PyQt6.QtGui import QAction


# The root folder to monitor
CLAUDE_ROOT = Path("C:/Claude")


@dataclass
class PortProcess:
    """A port being used by a Claude project."""
    port: int
    protocol: str
    pid: int
    process_name: str
    project_folder: str  # The immediate subfolder under C:\Claude
    exe_path: str
    cmdline: str
    cwd: str


def get_claude_ports() -> list[PortProcess]:
    """Get all ports being used by processes in C:\\Claude subfolders."""
    results = []
    seen = set()  # (port, protocol) to avoid duplicates

    try:
        connections = psutil.net_connections(kind='inet')
    except psutil.AccessDenied:
        return results

    for conn in connections:
        # Only listening ports
        if conn.status != 'LISTEN':
            continue

        if not conn.laddr or not conn.pid:
            continue

        port = conn.laddr.port
        protocol = "TCP" if conn.type == socket.SOCK_STREAM else "UDP"

        # Skip duplicates
        key = (port, protocol)
        if key in seen:
            continue

        # Get process info
        try:
            proc = psutil.Process(conn.pid)

            # Get paths to check if it's a Claude project
            exe_path = ""
            cwd = ""
            cmdline = ""

            try:
                exe_path = proc.exe() or ""
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            try:
                cwd = proc.cwd() or ""
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            try:
                cmdline = " ".join(proc.cmdline()) or ""
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Check if this process is related to C:\Claude
            project_folder = get_project_folder(exe_path, cwd, cmdline)

            if project_folder:
                seen.add(key)
                results.append(PortProcess(
                    port=port,
                    protocol=protocol,
                    pid=conn.pid,
                    process_name=proc.name(),
                    project_folder=project_folder,
                    exe_path=exe_path,
                    cmdline=cmdline,
                    cwd=cwd
                ))

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return sorted(results, key=lambda x: (x.project_folder, x.port))


def get_project_folder(exe_path: str, cwd: str, cmdline: str) -> Optional[str]:
    """
    Determine if this process is from a C:\\Claude project.
    Returns the project folder name (immediate subfolder) or None.
    """
    claude_root = str(CLAUDE_ROOT).lower().replace("\\", "/")

    # Check exe path, cwd, and cmdline for C:\Claude references
    for path_str in [exe_path, cwd, cmdline]:
        if not path_str:
            continue

        path_lower = path_str.lower().replace("\\", "/")

        if claude_root in path_lower:
            # Extract the project folder (first subfolder under C:\Claude)
            try:
                # Find where C:\Claude starts in the path
                idx = path_lower.find(claude_root)
                if idx >= 0:
                    remainder = path_str[idx + len(claude_root):].strip("/\\")
                    if remainder:
                        # Get first folder component
                        parts = Path(remainder).parts
                        if parts:
                            return parts[0]
            except Exception:
                pass

    return None


def kill_process(pid: int) -> tuple[bool, str]:
    """Kill a process by PID."""
    try:
        proc = psutil.Process(pid)
        name = proc.name()
        proc.terminate()
        try:
            proc.wait(timeout=3)
            return True, f"Terminated {name} (PID: {pid})"
        except psutil.TimeoutExpired:
            proc.kill()
            return True, f"Force killed {name} (PID: {pid})"
    except psutil.NoSuchProcess:
        return False, f"Process {pid} not found"
    except psutil.AccessDenied:
        return False, f"Access denied - run as administrator"
    except Exception as e:
        return False, str(e)


class PortMasterWindow(QMainWindow):
    """Main window - simple port monitor."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"PortMaster - Monitoring {CLAUDE_ROOT}")
        self.setMinimumSize(900, 500)
        self.resize(1100, 600)

        self._setup_ui()
        self._apply_style()

        # Initial load
        self.refresh()

        # Auto-refresh timer (every 3 seconds)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(3000)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header = QHBoxLayout()

        title = QLabel(f"<b>Active Ports in {CLAUDE_ROOT}</b>")
        title.setStyleSheet("font-size: 16px;")
        header.addWidget(title)

        header.addStretch()

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter by project, port, or process...")
        self.filter_input.setFixedWidth(250)
        self.filter_input.textChanged.connect(self._apply_filter)
        header.addWidget(self.filter_input)

        self.auto_refresh_cb = QCheckBox("Auto-refresh")
        self.auto_refresh_cb.setChecked(True)
        self.auto_refresh_cb.toggled.connect(self._toggle_auto_refresh)
        header.addWidget(self.auto_refresh_cb)

        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.clicked.connect(self.refresh)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            'Port', 'Project', 'Process', 'PID', 'Working Directory', 'Action'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Column sizing
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Port
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Project
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Process
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # PID
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # CWD
        header_view.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Action

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(5, 80)

        layout.addWidget(self.table)

        # Status bar
        self.status_label = QLabel()
        layout.addWidget(self.status_label)

    def _apply_style(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QWidget { background-color: #1e1e1e; color: #d4d4d4; font-family: "Segoe UI"; }
            QTableWidget {
                background-color: #252526;
                alternate-background-color: #2d2d2d;
                gridline-color: #3c3c3c;
                border: none;
                selection-background-color: #094771;
            }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section {
                background-color: #333333;
                color: #d4d4d4;
                padding: 8px;
                border: none;
                border-right: 1px solid #3c3c3c;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton#killBtn { background-color: #c42b1c; }
            QPushButton#killBtn:hover { background-color: #d63a2c; }
            QLineEdit {
                background-color: #3c3c3c;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
            QCheckBox { spacing: 5px; }
            QMenu { background-color: #252526; border: 1px solid #454545; }
            QMenu::item { padding: 5px 20px; }
            QMenu::item:selected { background-color: #094771; }
        """)

    def refresh(self):
        """Refresh the port list."""
        # Show visual feedback
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⟳ Refreshing...")
        self.status_label.setText("Scanning ports...")
        QApplication.processEvents()

        # Do the actual refresh
        self.ports_data = get_claude_ports()
        self._populate_table()

        # Restore button
        self.refresh_btn.setText("Refresh Now")
        self.refresh_btn.setEnabled(True)

    def _populate_table(self):
        """Fill the table with current data."""
        filter_text = self.filter_input.text().lower()

        self.table.setRowCount(0)

        for pp in self.ports_data:
            # Apply filter
            if filter_text:
                searchable = f"{pp.port} {pp.project_folder} {pp.process_name} {pp.pid} {pp.cwd}".lower()
                if filter_text not in searchable:
                    continue

            row = self.table.rowCount()
            self.table.insertRow(row)

            # Port
            port_item = QTableWidgetItem(str(pp.port))
            port_item.setData(Qt.ItemDataRole.UserRole, pp)
            self.table.setItem(row, 0, port_item)

            # Project
            self.table.setItem(row, 1, QTableWidgetItem(pp.project_folder))

            # Process
            self.table.setItem(row, 2, QTableWidgetItem(pp.process_name))

            # PID
            self.table.setItem(row, 3, QTableWidgetItem(str(pp.pid)))

            # CWD
            cwd_item = QTableWidgetItem(pp.cwd)
            cwd_item.setToolTip(pp.cmdline)  # Full command line in tooltip
            self.table.setItem(row, 4, cwd_item)

            # Kill button
            kill_btn = QPushButton("Kill")
            kill_btn.setObjectName("killBtn")
            kill_btn.setFixedWidth(60)
            kill_btn.clicked.connect(lambda checked, pid=pp.pid, name=pp.process_name: self._kill(pid, name))
            self.table.setCellWidget(row, 5, kill_btn)

        # Update status
        shown = self.table.rowCount()
        total = len(self.ports_data)
        if filter_text:
            self.status_label.setText(f"Showing {shown} of {total} ports (filtered)")
        else:
            self.status_label.setText(f"{total} port(s) in use by Claude projects")

    def _apply_filter(self):
        """Re-filter the table."""
        self._populate_table()

    def _toggle_auto_refresh(self, enabled: bool):
        """Toggle auto-refresh."""
        if enabled:
            self.timer.start(3000)
        else:
            self.timer.stop()

    def _kill(self, pid: int, name: str):
        """Kill a process after confirmation."""
        reply = QMessageBox.question(
            self,
            "Confirm Kill",
            f"Kill {name} (PID: {pid})?\n\nThis will free up the port.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, msg = kill_process(pid)
            if success:
                QMessageBox.information(self, "Success", msg)
                self.refresh()
            else:
                QMessageBox.warning(self, "Failed", msg)

    def _show_context_menu(self, pos):
        """Right-click menu."""
        item = self.table.itemAt(pos)
        if not item:
            return

        row = item.row()
        port_item = self.table.item(row, 0)
        pp: PortProcess = port_item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        # Kill
        kill_action = QAction(f"Kill {pp.process_name}", self)
        kill_action.triggered.connect(lambda: self._kill(pp.pid, pp.process_name))
        menu.addAction(kill_action)

        menu.addSeparator()

        # Open folder
        if pp.cwd:
            open_cwd = QAction("Open Working Directory", self)
            open_cwd.triggered.connect(lambda: os.startfile(pp.cwd))
            menu.addAction(open_cwd)

        # Open project folder
        project_path = CLAUDE_ROOT / pp.project_folder
        if project_path.exists():
            open_project = QAction(f"Open {pp.project_folder} Folder", self)
            open_project.triggered.connect(lambda: os.startfile(str(project_path)))
            menu.addAction(open_project)

        menu.addSeparator()

        # Copy actions
        copy_port = QAction(f"Copy Port: {pp.port}", self)
        copy_port.triggered.connect(lambda: QApplication.clipboard().setText(str(pp.port)))
        menu.addAction(copy_port)

        copy_pid = QAction(f"Copy PID: {pp.pid}", self)
        copy_pid.triggered.connect(lambda: QApplication.clipboard().setText(str(pp.pid)))
        menu.addAction(copy_pid)

        menu.exec(self.table.viewport().mapToGlobal(pos))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PortMaster")

    window = PortMasterWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

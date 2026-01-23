"""Process details panel widget."""

from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
    QFormLayout, QPushButton, QTextEdit, QScrollArea
)

from ...core import ProcessManager


class ProcessDetailsWidget(QWidget):
    """Widget displaying detailed process information."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.process_manager = ProcessManager()
        self.current_pid: Optional[int] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroll area for details
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)

        # Title
        self.title_label = QLabel("Select a port to view process details")
        self.title_label.setObjectName("titleLabel")
        content_layout.addWidget(self.title_label)

        # Basic info group
        basic_group = QGroupBox("Process Information")
        basic_layout = QFormLayout(basic_group)

        self.name_label = QLabel("-")
        basic_layout.addRow("Name:", self.name_label)

        self.pid_label = QLabel("-")
        basic_layout.addRow("PID:", self.pid_label)

        self.status_label = QLabel("-")
        basic_layout.addRow("Status:", self.status_label)

        self.user_label = QLabel("-")
        basic_layout.addRow("User:", self.user_label)

        self.created_label = QLabel("-")
        basic_layout.addRow("Started:", self.created_label)

        content_layout.addWidget(basic_group)

        # Path info group
        path_group = QGroupBox("Paths")
        path_layout = QFormLayout(path_group)

        self.exe_label = QLabel("-")
        self.exe_label.setWordWrap(True)
        self.exe_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_layout.addRow("Executable:", self.exe_label)

        self.cwd_label = QLabel("-")
        self.cwd_label.setWordWrap(True)
        self.cwd_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        path_layout.addRow("Working Dir:", self.cwd_label)

        content_layout.addWidget(path_group)

        # Command line group
        cmdline_group = QGroupBox("Command Line")
        cmdline_layout = QVBoxLayout(cmdline_group)

        self.cmdline_text = QTextEdit()
        self.cmdline_text.setReadOnly(True)
        self.cmdline_text.setMaximumHeight(80)
        cmdline_layout.addWidget(self.cmdline_text)

        content_layout.addWidget(cmdline_group)

        # Parent/Children group
        family_group = QGroupBox("Process Tree")
        family_layout = QFormLayout(family_group)

        self.parent_label = QLabel("-")
        family_layout.addRow("Parent:", self.parent_label)

        self.children_label = QLabel("-")
        self.children_label.setWordWrap(True)
        family_layout.addRow("Children:", self.children_label)

        content_layout.addWidget(family_group)

        # Resource usage group
        resource_group = QGroupBox("Resources")
        resource_layout = QFormLayout(resource_group)

        self.memory_label = QLabel("-")
        resource_layout.addRow("Memory:", self.memory_label)

        self.cpu_label = QLabel("-")
        resource_layout.addRow("CPU:", self.cpu_label)

        content_layout.addWidget(resource_group)

        # Connections group
        conn_group = QGroupBox("Network Connections")
        conn_layout = QVBoxLayout(conn_group)

        self.connections_text = QTextEdit()
        self.connections_text.setReadOnly(True)
        self.connections_text.setMaximumHeight(100)
        conn_layout.addWidget(self.connections_text)

        content_layout.addWidget(conn_group)

        content_layout.addStretch()

        # Actions
        actions_layout = QHBoxLayout()

        self.kill_btn = QPushButton("Terminate Process")
        self.kill_btn.setObjectName("dangerButton")
        self.kill_btn.setEnabled(False)
        self.kill_btn.clicked.connect(self._kill_current)
        actions_layout.addWidget(self.kill_btn)

        self.open_location_btn = QPushButton("Open File Location")
        self.open_location_btn.setObjectName("secondaryButton")
        self.open_location_btn.setEnabled(False)
        self.open_location_btn.clicked.connect(self._open_location)
        actions_layout.addWidget(self.open_location_btn)

        actions_layout.addStretch()
        content_layout.addLayout(actions_layout)

        scroll.setWidget(content)
        layout.addWidget(scroll)

    def show_process(self, pid: int):
        """Display details for a process."""
        self.current_pid = pid
        details = self.process_manager.get_process_details(pid)

        if not details:
            self._clear()
            self.title_label.setText(f"Process {pid} not found")
            return

        if 'error' in details:
            self._clear()
            self.title_label.setText(f"Access denied for PID {pid}")
            return

        # Update UI
        self.title_label.setText(f"Process: {details['name']}")

        self.name_label.setText(details['name'])
        self.pid_label.setText(str(details['pid']))
        self.status_label.setText(details['status'])
        self.user_label.setText(details.get('username', '-'))

        if details.get('create_time'):
            created = datetime.fromtimestamp(details['create_time'])
            self.created_label.setText(created.strftime("%Y-%m-%d %H:%M:%S"))
        else:
            self.created_label.setText("-")

        self.exe_label.setText(details.get('exe', '-') or '-')
        self.cwd_label.setText(details.get('cwd', '-') or '-')
        self.cmdline_text.setText(details.get('cmdline', '-') or '-')

        # Parent
        parent = details.get('parent')
        if parent:
            self.parent_label.setText(f"{parent['name']} (PID: {parent['pid']})")
        else:
            self.parent_label.setText("-")

        # Children
        children = details.get('children', [])
        if children:
            children_text = ", ".join(f"{c['name']} ({c['pid']})" for c in children[:5])
            if len(children) > 5:
                children_text += f" (+{len(children) - 5} more)"
            self.children_label.setText(children_text)
        else:
            self.children_label.setText("None")

        # Memory
        mem = details.get('memory_info', {})
        if mem:
            self.memory_label.setText(f"{mem.get('rss_mb', 0):.1f} MB")
        else:
            self.memory_label.setText("-")

        self.cpu_label.setText(f"{details.get('cpu_percent', 0):.1f}%")

        # Connections
        conns = details.get('connections', [])
        if conns:
            conn_lines = []
            for c in conns[:10]:
                line = f"{c['local']}"
                if c.get('remote'):
                    line += f" → {c['remote']}"
                line += f" [{c['status']}]"
                conn_lines.append(line)
            if len(conns) > 10:
                conn_lines.append(f"... and {len(conns) - 10} more")
            self.connections_text.setText("\n".join(conn_lines))
        else:
            self.connections_text.setText("No connections")

        # Enable buttons
        self.kill_btn.setEnabled(True)
        self.open_location_btn.setEnabled(bool(details.get('exe')))

    def _clear(self):
        """Clear all fields."""
        self.current_pid = None
        self.name_label.setText("-")
        self.pid_label.setText("-")
        self.status_label.setText("-")
        self.user_label.setText("-")
        self.created_label.setText("-")
        self.exe_label.setText("-")
        self.cwd_label.setText("-")
        self.cmdline_text.clear()
        self.parent_label.setText("-")
        self.children_label.setText("-")
        self.memory_label.setText("-")
        self.cpu_label.setText("-")
        self.connections_text.clear()
        self.kill_btn.setEnabled(False)
        self.open_location_btn.setEnabled(False)

    def _kill_current(self):
        """Kill the current process."""
        if self.current_pid:
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Confirm Kill",
                f"Terminate process (PID: {self.current_pid})?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                success, msg = self.process_manager.kill_process(self.current_pid)
                if success:
                    QMessageBox.information(self, "Success", msg)
                    self._clear()
                    self.title_label.setText("Process terminated")
                else:
                    QMessageBox.warning(self, "Failed", msg)

    def _open_location(self):
        """Open the executable's file location."""
        exe_path = self.exe_label.text()
        if exe_path and exe_path != '-':
            self.process_manager.open_file_location(exe_path)

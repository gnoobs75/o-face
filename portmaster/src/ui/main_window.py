"""Main window for PortMaster application."""

import subprocess
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QSplitter, QStatusBar, QLabel, QMenuBar, QMessageBox
)
from PyQt6.QtGui import QAction, QKeySequence

from .styles import MAIN_STYLESHEET
from .widgets.port_table import PortTableWidget
from .widgets.config_tree import ConfigTreeWidget
from .widgets.conflict_panel import ConflictPanelWidget
from .widgets.process_details import ProcessDetailsWidget
from ..core import PortScanner
from ..utils.logging_config import get_logger, get_log_file_path, PerfTimer

logger = get_logger('main_window')


class MainWindow(QMainWindow):
    """Main application window for PortMaster."""

    def __init__(self, scan_root: str = "C:\\Claude"):
        super().__init__()
        logger.info("Initializing MainWindow")
        self.scan_root = scan_root

        # Shared scanner instance to avoid creating multiple
        self._port_scanner = PortScanner()

        with PerfTimer("MainWindow setup", logger):
            self._setup_window()
            self._setup_menu()
            self._setup_ui()
            self._setup_status_bar()
            self._connect_signals()

        # Initial data load
        self._initial_load()
        logger.info("MainWindow initialization complete")

    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("PortMaster - Port Management Tool")
        self.setMinimumSize(1200, 700)
        self.resize(1400, 800)

        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

    def _setup_menu(self):
        """Setup menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        refresh_action = QAction("&Refresh All", self)
        refresh_action.setShortcut(QKeySequence.StandardKey.Refresh)
        refresh_action.triggered.connect(self._refresh_all)
        file_menu.addAction(refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        ports_action = QAction("&Active Ports", self)
        ports_action.setShortcut("Ctrl+1")
        ports_action.triggered.connect(lambda: self.tabs.setCurrentIndex(0))
        view_menu.addAction(ports_action)

        config_action = QAction("&Configurations", self)
        config_action.setShortcut("Ctrl+2")
        config_action.triggered.connect(lambda: self.tabs.setCurrentIndex(1))
        view_menu.addAction(config_action)

        conflicts_action = QAction("C&onflicts", self)
        conflicts_action.setShortcut("Ctrl+3")
        conflicts_action.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        view_menu.addAction(conflicts_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        view_logs_action = QAction("View &Logs", self)
        view_logs_action.setShortcut("Ctrl+L")
        view_logs_action.triggered.connect(self._open_log_file)
        help_menu.addAction(view_logs_action)

        help_menu.addSeparator()

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        """Setup main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Main splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - tabs
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs = QTabWidget()

        # Tab 1: Active Ports
        self.port_table = PortTableWidget()
        self.tabs.addTab(self.port_table, "Active Ports")

        # Tab 2: Configuration Scanner
        self.config_tree = ConfigTreeWidget(self.scan_root)
        self.tabs.addTab(self.config_tree, "Configurations")

        # Tab 3: Conflicts
        self.conflict_panel = ConflictPanelWidget(self.scan_root)
        self.tabs.addTab(self.conflict_panel, "Conflicts")

        left_layout.addWidget(self.tabs)
        splitter.addWidget(left_widget)

        # Right side - process details
        self.process_details = ProcessDetailsWidget()
        splitter.addWidget(self.process_details)

        # Set splitter sizes (70% left, 30% right)
        splitter.setSizes([980, 420])

        layout.addWidget(splitter)

    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Port count
        self.port_count_label = QLabel()
        self.status_bar.addWidget(self.port_count_label)

        # Spacer
        self.status_bar.addWidget(QLabel(" | "))

        # Conflict indicator
        self.conflict_indicator = QLabel()
        self.status_bar.addWidget(self.conflict_indicator)

        # Permanent message on right
        self.scan_root_label = QLabel(f"Scan root: {self.scan_root}")
        self.status_bar.addPermanentWidget(self.scan_root_label)

    def _connect_signals(self):
        """Connect widget signals."""
        # Port table selection -> process details
        self.port_table.port_selected.connect(self._on_port_selected)
        self.port_table.process_killed.connect(self._on_process_killed)

        # Config tree selection
        self.config_tree.config_selected.connect(self._on_config_selected)

        # Share scan results between config_tree and conflict_panel
        # When config_tree scans, pass results to conflict_panel
        self.config_tree.scan_completed.connect(self.conflict_panel.set_config_matches)

        # Tab changes
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _initial_load(self):
        """Load initial data."""
        self.port_table.refresh()
        self._update_status_bar()

    def _refresh_all(self):
        """Refresh all data."""
        self.port_table.refresh()
        if self.tabs.currentIndex() == 1:
            self.config_tree.scan()
        elif self.tabs.currentIndex() == 2:
            self.conflict_panel.analyze()
        self._update_status_bar()

    def _on_port_selected(self, port: int):
        """Handle port selection."""
        logger.debug(f"Port selected: {port}")
        # Find the process for this port
        port_infos = self._port_scanner.get_port_info(port)
        for pi in port_infos:
            if pi.process:
                self.process_details.show_process(pi.process.pid)
                break

    def _on_process_killed(self, pid: int):
        """Handle process killed event."""
        logger.info(f"Process killed: PID {pid}")
        self._update_status_bar()
        # Don't auto-refresh conflicts - let user click button manually

    def _on_config_selected(self, config):
        """Handle config selection."""
        logger.debug(f"Config selected: port {config.port} in {config.file_path}")
        # Show port info if the port is active
        port_infos = self._port_scanner.get_port_info(config.port)
        for pi in port_infos:
            if pi.process:
                self.process_details.show_process(pi.process.pid)
                break

    def _on_tab_changed(self, index: int):
        """Handle tab change."""
        tab_names = {0: "Active Ports", 1: "Configurations", 2: "Conflicts"}
        logger.debug(f"Tab changed to: {tab_names.get(index, index)}")
        # NO auto-scan - let user click buttons manually to avoid blocking UI

    def _update_status_bar(self):
        """Update status bar information."""
        logger.debug("Updating status bar")
        # Port count
        ports = self._port_scanner.get_listening_ports()
        self.port_count_label.setText(f"Listening ports: {len(ports)}")

        # Quick conflict check
        config_matches = self.config_tree.current_matches if self.config_tree.current_matches else []
        active_ports = {p.port for p in ports}
        config_ports = {m.port for m in config_matches}

        overlaps = active_ports & config_ports
        if overlaps:
            self.conflict_indicator.setText(f"⚠ {len(overlaps)} potential conflict(s)")
            self.conflict_indicator.setStyleSheet("color: #f48771;")
        else:
            self.conflict_indicator.setText("No conflicts")
            self.conflict_indicator.setStyleSheet("color: #89d185;")

    def _show_about(self):
        """Show about dialog."""
        log_path = get_log_file_path()
        QMessageBox.about(
            self,
            "About PortMaster",
            "<h2>PortMaster</h2>"
            "<p>A Windows port management tool for developers.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>View active ports and their processes</li>"
            "<li>Scan configuration files for port definitions</li>"
            "<li>Detect and resolve port conflicts</li>"
            "<li>Kill processes by port</li>"
            "</ul>"
            "<p>Version 1.0.1</p>"
            f"<p><small>Log file: {log_path}</small></p>"
        )

    def _open_log_file(self):
        """Open the log file in the default text editor."""
        import os
        log_path = get_log_file_path()
        logger.info(f"Opening log file: {log_path}")
        try:
            os.startfile(str(log_path))
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
            QMessageBox.warning(self, "Error", f"Could not open log file: {e}\n\nPath: {log_path}")

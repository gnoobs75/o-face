"""Conflict panel widget for displaying port conflicts."""

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox, QProgressBar
)

from ...core import PortScanner, ConfigScanner, ProcessManager, ConflictInfo, ConfigMatch
from ...utils.logging_config import get_logger

logger = get_logger('conflict_panel')


class AnalyzeWorker(QObject):
    """Worker thread for conflict analysis."""
    finished = pyqtSignal(list, list)  # (conflicts, config_matches)
    error = pyqtSignal(str)

    def __init__(self, port_scanner: PortScanner, config_scanner: ConfigScanner,
                 cached_matches: Optional[list] = None):
        super().__init__()
        self.port_scanner = port_scanner
        self.config_scanner = config_scanner
        self.cached_matches = cached_matches

    def run(self):
        """Run analysis in background thread."""
        try:
            logger.info("AnalyzeWorker starting")

            # Get active ports (fast)
            active_ports = self.port_scanner.get_listening_ports()
            active_by_port = {p.port: p for p in active_ports}
            logger.debug(f"Found {len(active_ports)} active ports")

            # Use cached config matches if available, otherwise scan
            if self.cached_matches:
                logger.info(f"Using {len(self.cached_matches)} cached config matches")
                config_matches = self.cached_matches
            else:
                logger.info("No cached matches, scanning configs...")
                config_matches = self.config_scanner.scan_all()
                logger.info(f"Scan found {len(config_matches)} config matches")

            # Group by port
            config_by_port: dict[int, list[ConfigMatch]] = {}
            for match in config_matches:
                if match.port not in config_by_port:
                    config_by_port[match.port] = []
                config_by_port[match.port].append(match)

            # Find conflicts
            conflicts = []
            all_ports = set(active_by_port.keys()) | set(config_by_port.keys())

            for port in sorted(all_ports):
                active = active_by_port.get(port)
                configs = config_by_port.get(port, [])

                conflict = ConflictInfo(
                    port=port,
                    active_process=active,
                    config_matches=configs
                )

                if conflict.is_conflict:
                    conflicts.append(conflict)

            logger.info(f"AnalyzeWorker found {len(conflicts)} conflicts")
            self.finished.emit(conflicts, config_matches)

        except Exception as e:
            logger.exception("AnalyzeWorker error")
            self.error.emit(str(e))


class ConflictPanelWidget(QWidget):
    """Widget displaying conflicts between active ports and configurations."""

    conflict_selected = pyqtSignal(int)  # Emitted when a conflict port is selected
    scan_completed = pyqtSignal(list)  # Emitted with config matches after scan

    def __init__(self, scan_root: str = "C:\\Claude", parent: Optional[QWidget] = None):
        super().__init__(parent)
        logger.info(f"ConflictPanelWidget initializing")
        self.port_scanner = PortScanner()
        self.config_scanner = ConfigScanner(scan_root)
        self.process_manager = ProcessManager()
        self.conflicts: list[ConflictInfo] = []
        self._cached_config_matches: Optional[list[ConfigMatch]] = None

        # Threading
        self._analyze_thread: Optional[QThread] = None
        self._analyze_worker: Optional[AnalyzeWorker] = None

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()

        title = QLabel("Port Conflicts")
        title.setObjectName("titleLabel")
        header.addWidget(title)

        header.addStretch()

        self.refresh_btn = QPushButton("Analyze Conflicts")
        self.refresh_btn.clicked.connect(self.analyze)
        header.addWidget(self.refresh_btn)

        layout.addLayout(header)

        # Description
        desc = QLabel(
            "Shows ports that are both in use AND configured in files, "
            "or configured in multiple places. Click 'Analyze' to scan."
        )
        desc.setObjectName("subtitleLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Conflicts table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            'Port', 'Conflict Type', 'Active Process', 'Config Files', 'Action'
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        # Configure header
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 70)   # Port
        self.table.setColumnWidth(1, 180)  # Conflict Type
        self.table.setColumnWidth(2, 200)  # Active Process
        self.table.setColumnWidth(4, 100)  # Action

        layout.addWidget(self.table)

        # Status
        self.status_label = QLabel("Click 'Analyze Conflicts' to scan for issues")
        layout.addWidget(self.status_label)

    def set_config_matches(self, matches: list[ConfigMatch]):
        """Set cached config matches from config_tree to avoid re-scanning."""
        logger.info(f"Received {len(matches)} cached config matches")
        self._cached_config_matches = matches

    def analyze(self):
        """Analyze for conflicts in a background thread."""
        # Don't start if already analyzing
        if self._analyze_thread is not None and self._analyze_thread.isRunning():
            logger.warning("Analysis already in progress")
            return

        logger.info("Starting conflict analysis")
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("Analyzing...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText("Analyzing conflicts...")

        # Create thread and worker
        self._analyze_thread = QThread()
        self._analyze_worker = AnalyzeWorker(
            self.port_scanner,
            self.config_scanner,
            self._cached_config_matches
        )
        self._analyze_worker.moveToThread(self._analyze_thread)

        # Connect signals
        self._analyze_thread.started.connect(self._analyze_worker.run)
        self._analyze_worker.finished.connect(self._on_analyze_finished)
        self._analyze_worker.error.connect(self._on_analyze_error)
        self._analyze_worker.finished.connect(self._analyze_thread.quit)
        self._analyze_worker.error.connect(self._analyze_thread.quit)

        # Start
        self._analyze_thread.start()

    def _on_analyze_finished(self, conflicts: list, config_matches: list):
        """Handle analysis completion."""
        logger.info(f"Analysis finished: {len(conflicts)} conflicts")
        self.conflicts = conflicts

        # Cache the config matches and emit signal so others can use them
        if config_matches and not self._cached_config_matches:
            self._cached_config_matches = config_matches
            self.scan_completed.emit(config_matches)

        self._populate_table()
        self._update_status()
        self._cleanup_analyze()

    def _on_analyze_error(self, error_msg: str):
        """Handle analysis error."""
        logger.error(f"Analysis error: {error_msg}")
        QMessageBox.warning(self, "Analysis Error", f"Error analyzing conflicts: {error_msg}")
        self._cleanup_analyze()

    def _cleanup_analyze(self):
        """Clean up after analysis."""
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("Analyze Conflicts")
        self.progress_bar.setVisible(False)
        self._analyze_thread = None
        self._analyze_worker = None

    def _populate_table(self):
        """Populate table with conflicts."""
        logger.debug("Populating conflict table")
        self.table.setRowCount(0)

        for conflict in self.conflicts:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Port
            port_item = QTableWidgetItem(str(conflict.port))
            port_item.setData(Qt.ItemDataRole.UserRole, conflict)
            self.table.setItem(row, 0, port_item)

            # Conflict type
            type_item = QTableWidgetItem(conflict.conflict_type)
            type_item.setForeground(Qt.GlobalColor.red)
            self.table.setItem(row, 1, type_item)

            # Active process
            if conflict.active_process and conflict.active_process.process:
                proc = conflict.active_process.process
                proc_text = f"{proc.name} (PID: {proc.pid})"
            else:
                proc_text = "Not in use"
            self.table.setItem(row, 2, QTableWidgetItem(proc_text))

            # Config files
            if conflict.config_matches:
                files = [str(m.file_path.name) for m in conflict.config_matches]
                files_text = ", ".join(files[:3])
                if len(files) > 3:
                    files_text += f" (+{len(files) - 3} more)"
            else:
                files_text = "Not configured"

            files_item = QTableWidgetItem(files_text)
            files_item.setToolTip("\n".join(str(m.file_path) for m in conflict.config_matches))
            self.table.setItem(row, 3, files_item)

            # Action button
            if conflict.active_process and conflict.active_process.process:
                pid = conflict.active_process.process.pid
                kill_btn = QPushButton("Kill")
                kill_btn.setObjectName("dangerButton")
                kill_btn.clicked.connect(
                    lambda checked, p=pid: self._kill_process(p)
                )
                self.table.setCellWidget(row, 4, kill_btn)

    def _update_status(self):
        """Update status label."""
        if self.conflicts:
            self.status_label.setText(
                f"⚠ Found {len(self.conflicts)} conflict(s) requiring attention"
            )
            self.status_label.setStyleSheet("color: #f48771;")
        else:
            self.status_label.setText("✓ No conflicts detected")
            self.status_label.setStyleSheet("color: #89d185;")

    def _kill_process(self, pid: int):
        """Kill a conflicting process."""
        logger.info(f"User requested to kill PID {pid}")
        reply = QMessageBox.question(
            self,
            "Confirm Kill",
            f"Kill process with PID {pid}?\n\nThis will free up the port.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.process_manager.kill_process(pid)
            if success:
                logger.info(f"Successfully killed PID {pid}")
                QMessageBox.information(self, "Success", message)
                self.analyze()  # Refresh
            else:
                logger.error(f"Failed to kill PID {pid}: {message}")
                QMessageBox.warning(self, "Failed", message)

    def set_scan_root(self, path: str):
        """Update the scan root directory."""
        logger.info(f"Updating scan root to {path}")
        self.config_scanner = ConfigScanner(path)
        self._cached_config_matches = None  # Clear cache

"""Config tree widget for displaying port configurations found in files."""

from pathlib import Path
from typing import Optional
import subprocess

from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QMenu, QFileDialog, QMessageBox,
    QProgressBar, QApplication
)
from PyQt6.QtGui import QAction

from ...core import ConfigScanner, ConfigMatch
from ...utils.logging_config import get_logger, PerfTimer

logger = get_logger('config_tree')


class ScanWorker(QObject):
    """Worker thread for config scanning."""
    finished = pyqtSignal(list)  # Emits list of ConfigMatch
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # Progress messages

    def __init__(self, scanner: ConfigScanner):
        super().__init__()
        self.scanner = scanner

    def run(self):
        """Run the scan in background thread."""
        try:
            logger.info("ScanWorker starting scan")
            self.progress.emit("Scanning files...")
            matches = self.scanner.scan_all()
            logger.info(f"ScanWorker completed: {len(matches)} matches found")
            self.finished.emit(matches)
        except Exception as e:
            logger.exception("ScanWorker error")
            self.error.emit(str(e))


class ConfigTreeWidget(QWidget):
    """Widget displaying port configurations from scanned files."""

    config_selected = pyqtSignal(object)  # Emitted when a config is selected (ConfigMatch)
    scan_completed = pyqtSignal(list)  # Emitted with list of ConfigMatch when scan finishes

    def __init__(self, scan_root: str = "C:\\Claude", parent: Optional[QWidget] = None):
        super().__init__(parent)
        logger.info(f"ConfigTreeWidget initializing with scan_root={scan_root}")
        self.scan_root = Path(scan_root)
        self.config_scanner = ConfigScanner(scan_root)
        self.current_matches: list[ConfigMatch] = []

        # Threading
        self._scan_thread: Optional[QThread] = None
        self._scan_worker: Optional[ScanWorker] = None

        self._setup_ui()
        logger.debug("ConfigTreeWidget initialization complete")

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with controls
        header = QHBoxLayout()

        self.path_label = QLabel(f"Scanning: {self.scan_root}")
        self.path_label.setObjectName("subtitleLabel")
        header.addWidget(self.path_label, 1)

        self.change_path_btn = QPushButton("Change Path")
        self.change_path_btn.setObjectName("secondaryButton")
        self.change_path_btn.clicked.connect(self._change_scan_path)
        header.addWidget(self.change_path_btn)

        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.scan)
        header.addWidget(self.scan_btn)

        layout.addLayout(header)

        # Search/filter
        filter_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by port number, file name, or path...")
        self.search_input.textChanged.connect(self._apply_filter)
        filter_layout.addWidget(self.search_input)

        layout.addLayout(filter_layout)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Port / File', 'Line', 'Content', 'Match Type'])
        self.tree.setAlternatingRowColors(True)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)

        # Configure columns
        self.tree.setColumnWidth(0, 300)  # Port / File
        self.tree.setColumnWidth(1, 60)   # Line
        self.tree.setColumnWidth(2, 400)  # Content
        self.tree.setColumnWidth(3, 100)  # Match Type

        layout.addWidget(self.tree)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)

        self.conflict_label = QLabel()
        self.conflict_label.setObjectName("conflictLabel")
        status_layout.addWidget(self.conflict_label)

        status_layout.addStretch()
        layout.addLayout(status_layout)

    def scan(self):
        """Scan for configuration files in a background thread."""
        # Don't start if already scanning
        if self._scan_thread is not None and self._scan_thread.isRunning():
            logger.warning("Scan already in progress, ignoring request")
            return

        logger.info(f"Starting config scan of {self.scan_root}")
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("Scanning...")
        self.change_path_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.status_label.setText("Scanning files...")

        # Create thread and worker
        self._scan_thread = QThread()
        self._scan_worker = ScanWorker(self.config_scanner)
        self._scan_worker.moveToThread(self._scan_thread)

        # Connect signals
        self._scan_thread.started.connect(self._scan_worker.run)
        self._scan_worker.finished.connect(self._on_scan_finished)
        self._scan_worker.error.connect(self._on_scan_error)
        self._scan_worker.progress.connect(self._on_scan_progress)
        self._scan_worker.finished.connect(self._scan_thread.quit)
        self._scan_worker.error.connect(self._scan_thread.quit)

        # Start
        self._scan_thread.start()

    def _on_scan_finished(self, matches: list):
        """Handle scan completion."""
        logger.info(f"Scan finished with {len(matches)} matches")
        self.current_matches = matches

        with PerfTimer("populate_tree", logger):
            self._populate_tree()

        self._update_status()
        self._cleanup_scan()

        # Emit signal so other widgets can use the scan results
        self.scan_completed.emit(matches)

    def _on_scan_error(self, error_msg: str):
        """Handle scan error."""
        logger.error(f"Scan error: {error_msg}")
        QMessageBox.warning(self, "Scan Error", f"Error scanning files: {error_msg}")
        self._cleanup_scan()

    def _on_scan_progress(self, message: str):
        """Handle progress update."""
        logger.debug(f"Scan progress: {message}")
        self.status_label.setText(message)

    def _cleanup_scan(self):
        """Clean up after scan completes."""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("Scan")
        self.change_path_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._scan_thread = None
        self._scan_worker = None

    def _populate_tree(self):
        """Populate tree with scan results, grouped by port."""
        logger.debug("Populating tree widget")
        filter_text = self.search_input.text().lower()

        self.tree.clear()

        # Group matches by port
        by_port: dict[int, list[ConfigMatch]] = {}
        for match in self.current_matches:
            # Apply filter
            if filter_text:
                searchable = f"{match.port} {match.file_path} {match.line_content}"
                if filter_text not in searchable.lower():
                    continue

            if match.port not in by_port:
                by_port[match.port] = []
            by_port[match.port].append(match)

        logger.debug(f"Building tree with {len(by_port)} port groups")

        # Build tree
        for port in sorted(by_port.keys()):
            matches = by_port[port]
            is_conflict = len(matches) > 1

            # Port node
            port_item = QTreeWidgetItem([
                f"Port {port}" + (" (CONFLICT)" if is_conflict else ""),
                "",
                f"{len(matches)} configuration(s) found",
                ""
            ])
            port_item.setData(0, Qt.ItemDataRole.UserRole, port)

            if is_conflict:
                port_item.setForeground(0, self.tree.palette().highlight().color())

            # File nodes under port
            for match in matches:
                rel_path = self._get_relative_path(match.file_path)
                file_item = QTreeWidgetItem([
                    str(rel_path),
                    str(match.line_number),
                    match.line_content[:100],
                    match.match_type
                ])
                file_item.setData(0, Qt.ItemDataRole.UserRole, match)
                file_item.setToolTip(2, match.line_content)  # Full content in tooltip
                port_item.addChild(file_item)

            self.tree.addTopLevelItem(port_item)

            # Expand conflicts by default
            if is_conflict:
                port_item.setExpanded(True)

        logger.debug("Tree population complete")

    def _apply_filter(self):
        """Apply current filter to tree."""
        logger.debug(f"Applying filter: '{self.search_input.text()}'")
        self._populate_tree()

    def _update_status(self):
        """Update status labels."""
        total_ports = len(set(m.port for m in self.current_matches))
        total_files = len(set(m.file_path for m in self.current_matches))
        self.status_label.setText(f"Found {total_ports} ports in {total_files} files")

        # Check for conflicts
        conflicts = self.config_scanner.find_conflicts(self.current_matches)
        if conflicts:
            self.conflict_label.setText(f"⚠ {len(conflicts)} port(s) configured in multiple places")
        else:
            self.conflict_label.setText("")

    def _get_relative_path(self, path: Path) -> Path:
        """Get path relative to scan root."""
        try:
            return path.relative_to(self.scan_root)
        except ValueError:
            return path

    def _change_scan_path(self):
        """Change the scan root directory."""
        path = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(self.scan_root)
        )
        if path:
            logger.info(f"Changing scan path to {path}")
            self.scan_root = Path(path)
            self.config_scanner = ConfigScanner(path)
            self.path_label.setText(f"Scanning: {self.scan_root}")
            self.scan()

    def _on_selection_changed(self):
        """Handle selection change."""
        items = self.tree.selectedItems()
        if items:
            data = items[0].data(0, Qt.ItemDataRole.UserRole)
            if isinstance(data, ConfigMatch):
                self.config_selected.emit(data)

    def _show_context_menu(self, pos):
        """Show context menu for config actions."""
        item = self.tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)

        menu = QMenu(self)

        if isinstance(data, ConfigMatch):
            # Capture values to avoid closure issues
            file_path = data.file_path
            line_num = data.line_number
            port_num = data.port

            # Open file action
            open_action = QAction("Open File", self)
            open_action.triggered.connect(lambda checked, fp=file_path: self._open_file(fp))
            menu.addAction(open_action)

            # Open in editor at line
            open_at_line = QAction(f"Open at Line {line_num}", self)
            open_at_line.triggered.connect(
                lambda checked, fp=file_path, ln=line_num: self._open_file_at_line(fp, ln)
            )
            menu.addAction(open_at_line)

            menu.addSeparator()

            # Open folder
            open_folder = QAction("Open Containing Folder", self)
            open_folder.triggered.connect(lambda checked, fp=file_path: self._open_folder(fp.parent))
            menu.addAction(open_folder)

            menu.addSeparator()

            # Copy actions
            copy_path = QAction("Copy File Path", self)
            copy_path.triggered.connect(lambda checked, fp=file_path: self._copy_to_clipboard(str(fp)))
            menu.addAction(copy_path)

            copy_port = QAction(f"Copy Port: {port_num}", self)
            copy_port.triggered.connect(lambda checked, p=port_num: self._copy_to_clipboard(str(p)))
            menu.addAction(copy_port)

        elif isinstance(data, int):
            # Port number - copy action
            port_val = data
            copy_port = QAction(f"Copy Port: {port_val}", self)
            copy_port.triggered.connect(lambda checked, p=port_val: self._copy_to_clipboard(str(p)))
            menu.addAction(copy_port)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    def _open_file(self, file_path: Path):
        """Open file in default editor."""
        import os
        logger.debug(f"Opening file: {file_path}")
        try:
            os.startfile(str(file_path))
        except Exception as e:
            logger.error(f"Failed to open file: {e}")
            QMessageBox.warning(self, "Error", f"Could not open file: {e}")

    def _open_file_at_line(self, file_path: Path, line: int):
        """Try to open file at specific line (VS Code, Notepad++, etc.)."""
        logger.debug(f"Opening file at line: {file_path}:{line}")
        # Try VS Code first
        try:
            subprocess.run(['code', '--goto', f'{file_path}:{line}'], check=False)
            return
        except FileNotFoundError:
            pass

        # Fall back to regular open
        self._open_file(file_path)

    def _open_folder(self, folder_path: Path):
        """Open folder in Explorer."""
        logger.debug(f"Opening folder: {folder_path}")
        subprocess.run(['explorer', str(folder_path)], check=False)

    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard."""
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def get_conflicts(self) -> dict[int, list[ConfigMatch]]:
        """Get current conflicts."""
        return self.config_scanner.find_conflicts(self.current_matches)

    def get_matches_for_port(self, port: int) -> list[ConfigMatch]:
        """Get all config matches for a specific port."""
        return [m for m in self.current_matches if m.port == port]

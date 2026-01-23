"""
Process Table Widget - Shows per-process GPU memory usage
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget,
    QVBoxLayout, QLabel, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont

from config import COLORS
from core.metrics import ProcessInfo


class ProcessTable(QWidget):
    """
    A table widget showing processes using GPU memory.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Title
        title = QLabel("GPU Processes")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Process", "PID", "VRAM", "% of Total"])

        # Configure header
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(1, 70)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 90)

        # Style
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)

        # Apply dark theme styling
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['table_background']};
                alternate-background-color: {COLORS['table_alternate']};
                color: {COLORS['table_text']};
                border: 1px solid {COLORS['vram_border']};
                border-radius: 4px;
                gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 5px;
                border: none;
            }}
            QTableWidget::item:selected {{
                background-color: {COLORS['table_selected']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS['vram_border']};
                font-weight: bold;
            }}
        """)

        layout.addWidget(self.table)

    def update_processes(self, processes: list[ProcessInfo], total_vram: int):
        """Update the table with new process data"""
        self.table.setRowCount(len(processes))

        for row, proc in enumerate(processes):
            # Process name
            name_item = QTableWidgetItem(proc.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 0, name_item)

            # PID
            pid_item = QTableWidgetItem(str(proc.pid))
            pid_item.setFlags(pid_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            pid_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 1, pid_item)

            # VRAM usage
            vram_mb = proc.vram_used_bytes / (1024 ** 2)
            vram_gb = proc.vram_used_bytes / (1024 ** 3)

            if vram_gb >= 1:
                vram_text = f"{vram_gb:.2f} GB"
            else:
                vram_text = f"{vram_mb:.0f} MB"

            vram_item = QTableWidgetItem(vram_text)
            vram_item.setFlags(vram_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            vram_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row, 2, vram_item)

            # Percentage of total (calculate once)
            percent = None
            if total_vram > 0:
                percent = (proc.vram_used_bytes / total_vram) * 100
                percent_text = f"{percent:.1f}%"
            else:
                percent_text = "N/A"

            percent_item = QTableWidgetItem(percent_text)
            percent_item.setFlags(percent_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            percent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # Color code based on usage
            if percent is not None:
                if percent > 50:
                    percent_item.setForeground(QColor(COLORS["util_high"]))
                elif percent > 20:
                    percent_item.setForeground(QColor(COLORS["util_medium"]))
                else:
                    percent_item.setForeground(QColor(COLORS["util_low"]))

            self.table.setItem(row, 3, percent_item)

"""
Main Window - Central application window for VRAM Spy
"""

from typing import Optional

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QFrame, QPushButton, QFileDialog,
    QMessageBox, QSplitter, QStatusBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QAction

from config import (
    COLORS, WINDOW_TITLE, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    REFRESH_RATE_MS, TEMP_THRESHOLDS, UTIL_THRESHOLDS
)
from core.gpu_monitor import GPUMonitor
from core.data_logger import DataLogger
from core.metrics import GPUMetrics

from .widgets.gauge_widget import GaugeWidget
from .widgets.memory_bar import MemoryBar
from .widgets.process_table import ProcessTable
from .widgets.history_chart import HistoryChart, MultiLineChart
from .widgets.metrics_panel import MetricsPanel


class MainWindow(QMainWindow):
    """
    Main application window for VRAM Spy.
    """

    def __init__(self):
        super().__init__()
        self.gpu_monitor = GPUMonitor()
        self.data_logger = DataLogger()
        self.current_metrics: Optional[GPUMetrics] = None

        self._setup_window()
        self._setup_menubar()
        self._setup_ui()
        self._setup_statusbar()

        # Initialize GPU monitoring before starting timer
        if not self.gpu_monitor.initialize():
            QMessageBox.critical(
                self,
                "Initialization Error",
                "Failed to initialize NVIDIA GPU monitoring.\n\n"
                "Please ensure:\n"
                "1. You have an NVIDIA GPU installed\n"
                "2. NVIDIA drivers are properly installed\n"
                "3. The pynvml package is installed"
            )
            self.timer = None  # No timer if GPU init failed
        else:
            self._setup_timer()

    def _setup_window(self):
        """Configure the main window"""
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(1200, 800)

        # Dark theme background
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {COLORS['background']};
            }}
            QWidget {{
                color: {COLORS['text_primary']};
                font-family: 'Segoe UI', sans-serif;
            }}
            QTabWidget::pane {{
                border: 1px solid {COLORS['vram_border']};
                border-radius: 4px;
                background-color: {COLORS['surface']};
            }}
            QTabBar::tab {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_secondary']};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['accent']};
                color: {COLORS['text_primary']};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {COLORS['table_alternate']};
            }}
            QPushButton {{
                background-color: {COLORS['accent']};
                color: {COLORS['text_primary']};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #8b5cf6;
            }}
            QPushButton:pressed {{
                background-color: #6d28d9;
            }}
            QSplitter::handle {{
                background-color: {COLORS['vram_border']};
            }}
        """)

    def _setup_menubar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                padding: 4px;
            }}
            QMenuBar::item:selected {{
                background-color: {COLORS['accent']};
            }}
            QMenu {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['vram_border']};
            }}
            QMenu::item:selected {{
                background-color: {COLORS['accent']};
            }}
        """)

        # File menu
        file_menu = menubar.addMenu("File")

        export_csv_action = QAction("Export to CSV...", self)
        export_csv_action.triggered.connect(lambda: self._export_data("csv"))
        file_menu.addAction(export_csv_action)

        export_json_action = QAction("Export to JSON...", self)
        export_json_action.triggered.connect(lambda: self._export_data("json"))
        file_menu.addAction(export_json_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        clear_history_action = QAction("Clear History", self)
        clear_history_action.triggered.connect(self._clear_history)
        view_menu.addAction(clear_history_action)

    def _setup_ui(self):
        """Setup the main UI layout"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Header with GPU name
        self._create_header(main_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side: Gauges and memory bar
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)

        # Right side: Tabs with process table and charts
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions (40% left, 60% right)
        splitter.setSizes([400, 600])

        main_layout.addWidget(splitter, stretch=1)

        # Bottom: Additional metrics panel
        main_layout.addWidget(self.metrics_panel)

    def _create_header(self, layout):
        """Create the header section"""
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)

        header_layout = QHBoxLayout(header_frame)

        # GPU name label
        self.gpu_name_label = QLabel("Detecting GPU...")
        self.gpu_name_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(self.gpu_name_label)

        header_layout.addStretch()

        # CUDA version
        self.cuda_label = QLabel("")
        self.cuda_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        header_layout.addWidget(self.cuda_label)

        layout.addWidget(header_frame)

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with gauges and memory bar"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(15)

        # Gauges row
        gauges_frame = QFrame()
        gauges_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
            }}
        """)
        gauges_layout = QHBoxLayout(gauges_frame)
        gauges_layout.setSpacing(10)

        # Temperature gauge
        self.temp_gauge = GaugeWidget(
            title="Temperature",
            unit="°C",
            min_value=0,
            max_value=100,
            thresholds=TEMP_THRESHOLDS
        )
        gauges_layout.addWidget(self.temp_gauge)

        # GPU Utilization gauge
        self.util_gauge = GaugeWidget(
            title="GPU Usage",
            unit="%",
            min_value=0,
            max_value=100,
            thresholds=UTIL_THRESHOLDS
        )
        gauges_layout.addWidget(self.util_gauge)

        # Power gauge
        self.power_gauge = GaugeWidget(
            title="Power",
            unit="W",
            min_value=0,
            max_value=450,  # Will be updated to actual limit
            thresholds={"low": 50, "high": 80}
        )
        gauges_layout.addWidget(self.power_gauge)

        # VRAM gauge
        self.vram_gauge = GaugeWidget(
            title="VRAM",
            unit="%",
            min_value=0,
            max_value=100,
            thresholds={"low": 50, "high": 80}
        )
        gauges_layout.addWidget(self.vram_gauge)

        layout.addWidget(gauges_frame)

        # Memory bar
        memory_frame = QFrame()
        memory_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        memory_layout = QVBoxLayout(memory_frame)
        self.memory_bar = MemoryBar()
        memory_layout.addWidget(self.memory_bar)

        layout.addWidget(memory_frame)

        # Process table
        process_frame = QFrame()
        process_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        process_layout = QVBoxLayout(process_frame)
        self.process_table = ProcessTable()
        process_layout.addWidget(self.process_table)

        layout.addWidget(process_frame, stretch=1)

        return panel

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with charts"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Charts frame
        charts_frame = QFrame()
        charts_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        charts_layout = QVBoxLayout(charts_frame)

        # VRAM history chart
        self.vram_chart = HistoryChart(
            title="VRAM Usage History",
            y_label="GB",
            y_min=0,
            y_max=24,  # Will be updated
            line_color=COLORS["chart_vram"]
        )
        charts_layout.addWidget(self.vram_chart)

        # GPU utilization chart
        self.util_chart = HistoryChart(
            title="GPU Utilization History",
            y_label="%",
            y_min=0,
            y_max=100,
            line_color=COLORS["chart_util"]
        )
        charts_layout.addWidget(self.util_chart)

        # Temperature chart
        self.temp_chart = HistoryChart(
            title="Temperature History",
            y_label="°C",
            y_min=0,
            y_max=100,
            line_color=COLORS["chart_temp"]
        )
        charts_layout.addWidget(self.temp_chart)

        # Power chart
        self.power_chart = HistoryChart(
            title="Power Draw History",
            y_label="W",
            y_min=0,
            y_max=450,
            line_color=COLORS["chart_power"]
        )
        charts_layout.addWidget(self.power_chart)

        layout.addWidget(charts_frame, stretch=1)

        # Metrics panel
        self.metrics_panel = MetricsPanel()

        return panel

    def _setup_statusbar(self):
        """Setup the status bar"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.setStyleSheet(f"""
            QStatusBar {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_secondary']};
                border-top: 1px solid {COLORS['vram_border']};
            }}
        """)
        self.statusbar.showMessage("Initializing...")

    def _setup_timer(self):
        """Setup the refresh timer"""
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_metrics)
        self.timer.start(REFRESH_RATE_MS)

    def _update_metrics(self):
        """Fetch and update all metrics"""
        metrics = self.gpu_monitor.get_metrics()
        if metrics is None:
            self.statusbar.showMessage("Error: Could not read GPU metrics")
            return

        self.current_metrics = metrics
        self.data_logger.add_metrics(metrics)

        # Update header
        self.gpu_name_label.setText(metrics.device_name)
        self.cuda_label.setText(f"CUDA {metrics.cuda_version} | Driver {metrics.driver_version}")

        # Update gauges
        self.temp_gauge.set_value(metrics.temperature_celsius)
        self.util_gauge.set_value(metrics.gpu_utilization)
        self.power_gauge.set_value(metrics.power_draw_watts)
        self.vram_gauge.set_value(metrics.vram_used_percent)

        # Update power gauge max if needed
        if metrics.power_limit_watts > 0:
            self.power_gauge.max_value = metrics.power_limit_watts

        # Update memory bar
        self.memory_bar.set_memory(
            metrics.vram_used_bytes,
            metrics.vram_total_bytes
        )

        # Update process table
        self.process_table.update_processes(
            metrics.processes,
            metrics.vram_total_bytes
        )

        # Update charts
        x_vram, y_vram = self.data_logger.get_vram_history()
        self.vram_chart.update_data(x_vram, y_vram)
        if metrics.vram_total_gb > 0:
            self.vram_chart.set_y_range(0, metrics.vram_total_gb * 1.1)

        x_util, y_util = self.data_logger.get_utilization_history()
        self.util_chart.update_data(x_util, y_util)

        x_temp, y_temp = self.data_logger.get_temperature_history()
        self.temp_chart.update_data(x_temp, y_temp)

        x_power, y_power = self.data_logger.get_power_history()
        self.power_chart.update_data(x_power, y_power)
        if metrics.power_limit_watts > 0:
            self.power_chart.set_y_range(0, metrics.power_limit_watts * 1.1)

        # Update metrics panel
        self.metrics_panel.update_metrics(metrics)

        # Update status bar
        self.statusbar.showMessage(
            f"Last updated: {metrics.timestamp.strftime('%H:%M:%S')} | "
            f"History: {self.data_logger.length} points"
        )

    def _export_data(self, format: str):
        """Export logged data to file"""
        if self.data_logger.length == 0:
            QMessageBox.warning(
                self,
                "No Data",
                "No data to export. Please wait for some metrics to be collected."
            )
            return

        if format == "csv":
            file_filter = "CSV Files (*.csv)"
            default_ext = ".csv"
        else:
            file_filter = "JSON Files (*.json)"
            default_ext = ".json"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            f"vram_spy_export{default_ext}",
            file_filter
        )

        if filepath:
            try:
                exported_path = self.data_logger.export(filepath, format)
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data exported to:\n{exported_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Export Error",
                    f"Failed to export data:\n{str(e)}"
                )

    def _clear_history(self):
        """Clear the data history"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all recorded history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.data_logger.clear()
            self.statusbar.showMessage("History cleared")

    def closeEvent(self, event):
        """Handle window close"""
        if self.timer:
            self.timer.stop()
        self.gpu_monitor.shutdown()
        event.accept()

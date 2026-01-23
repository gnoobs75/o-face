"""
History Chart Widget - Real-time scrolling line charts using PyQtGraph
"""

import numpy as np
import pyqtgraph as pg
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt

from config import COLORS


class HistoryChart(QWidget):
    """
    A real-time scrolling line chart for displaying metric history.
    """

    def __init__(
        self,
        title: str = "",
        y_label: str = "",
        y_min: float = 0,
        y_max: float = 100,
        line_color: str = None,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.y_label = y_label
        self.y_min = y_min
        self.y_max = y_max
        self.line_color = line_color or COLORS["chart_util"]

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title_label)

        # Configure PyQtGraph
        pg.setConfigOptions(antialias=True)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(QColor(COLORS["chart_background"]))
        self.plot_widget.setMinimumHeight(100)

        # Configure axes
        self.plot_widget.setYRange(self.y_min, self.y_max)
        self.plot_widget.setXRange(-300, 0)  # 5 minutes of history
        self.plot_widget.setLabel("bottom", "Time (seconds ago)")
        self.plot_widget.setLabel("left", self.y_label)

        # Style the plot
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(color=COLORS["text_secondary"]))

        # Add grid
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Create the line
        pen = pg.mkPen(color=self.line_color, width=2)
        self.curve = self.plot_widget.plot([], [], pen=pen)

        # Create a reusable zero baseline curve for the fill
        self.zero_curve = pg.PlotDataItem([0], [0])

        # Fill under the curve
        self.fill = pg.FillBetweenItem(
            self.curve,
            self.zero_curve,
            brush=pg.mkBrush(color=self.line_color + "40")  # 25% opacity
        )
        self.plot_widget.addItem(self.fill)

        layout.addWidget(self.plot_widget)

    def update_data(self, x_data: list[float], y_data: list[float]):
        """Update chart with new data"""
        if not x_data or not y_data:
            return

        x_array = np.array(x_data)
        y_array = np.array(y_data)

        self.curve.setData(x_array, y_array)

        # Update the zero baseline curve (reuse instead of recreating)
        self.zero_curve.setData(x_array, np.zeros_like(y_array))

    def set_y_range(self, y_min: float, y_max: float):
        """Update Y-axis range"""
        self.y_min = y_min
        self.y_max = y_max
        self.plot_widget.setYRange(y_min, y_max)


class MultiLineChart(QWidget):
    """
    A chart that displays multiple metrics on the same plot.
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.curves = {}

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # Title
        title_label = QLabel(self.title)
        title_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title_label)

        # Configure PyQtGraph
        pg.setConfigOptions(antialias=True)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(QColor(COLORS["chart_background"]))
        self.plot_widget.setMinimumHeight(120)

        # Configure axes
        self.plot_widget.setYRange(0, 100)
        self.plot_widget.setXRange(-300, 0)
        self.plot_widget.setLabel("bottom", "Time (seconds ago)")

        # Style
        self.plot_widget.getAxis("bottom").setPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.getAxis("left").setPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(color=COLORS["text_secondary"]))
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Add legend
        self.legend = self.plot_widget.addLegend(offset=(10, 10))
        self.legend.setLabelTextColor(COLORS["text_primary"])

        layout.addWidget(self.plot_widget)

    def add_line(self, name: str, color: str):
        """Add a new line to the chart"""
        pen = pg.mkPen(color=color, width=2)
        curve = self.plot_widget.plot([], [], pen=pen, name=name)
        self.curves[name] = curve

    def update_line(self, name: str, x_data: list[float], y_data: list[float]):
        """Update a specific line's data"""
        if name in self.curves and x_data and y_data:
            self.curves[name].setData(np.array(x_data), np.array(y_data))

    def set_y_range(self, y_min: float, y_max: float):
        """Update Y-axis range"""
        self.plot_widget.setYRange(y_min, y_max)

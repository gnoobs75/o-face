"""
Circular Gauge Widget for displaying metrics like temperature, utilization, power
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath

from config import COLORS


class GaugeWidget(QWidget):
    """
    A circular gauge widget with animated arc and centered value display.
    """

    def __init__(
        self,
        title: str = "",
        unit: str = "",
        min_value: float = 0,
        max_value: float = 100,
        thresholds: dict = None,
        parent=None
    ):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = 0
        self.thresholds = thresholds or {"low": 50, "high": 80}

        # Colors for different states
        self.colors = {
            "low": QColor(COLORS["util_low"]),
            "medium": QColor(COLORS["util_medium"]),
            "high": QColor(COLORS["util_high"]),
        }

        self.setMinimumSize(120, 140)
        self.setMaximumSize(180, 200)

    def set_value(self, value: float):
        """Update the gauge value"""
        self.current_value = max(self.min_value, min(value, self.max_value))
        self.update()

    def set_thresholds(self, low: float, high: float):
        """Set threshold values for color changes"""
        self.thresholds = {"low": low, "high": high}

    def _get_color(self) -> QColor:
        """Get color based on current value and thresholds"""
        if self.current_value < self.thresholds.get("low", 50):
            return self.colors["low"]
        elif self.current_value < self.thresholds.get("high", 80):
            return self.colors["medium"]
        else:
            return self.colors["high"]

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Widget dimensions
        width = self.width()
        height = self.height()

        # Gauge dimensions
        gauge_size = min(width, height - 30) - 20
        x_offset = (width - gauge_size) / 2
        y_offset = 10

        rect = QRectF(x_offset, y_offset, gauge_size, gauge_size)

        # Arc configuration
        arc_width = 12
        start_angle = 225 * 16  # Qt uses 1/16th of a degree
        span_angle = -270 * 16  # Negative for clockwise

        # Draw background arc
        bg_pen = QPen(QColor(COLORS["gauge_arc"]))
        bg_pen.setWidth(arc_width)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(rect, start_angle, span_angle)

        # Draw value arc
        if self.max_value > self.min_value:
            value_ratio = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        else:
            value_ratio = 0

        value_span = int(span_angle * value_ratio)

        value_pen = QPen(self._get_color())
        value_pen.setWidth(arc_width)
        value_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(value_pen)
        painter.drawArc(rect, start_angle, value_span)

        # Draw center value
        painter.setPen(QColor(COLORS["text_primary"]))
        value_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(value_font)

        # Format value
        if self.current_value >= 100:
            value_text = f"{int(self.current_value)}"
        else:
            value_text = f"{self.current_value:.1f}"

        text_rect = QRectF(x_offset, y_offset + gauge_size * 0.3, gauge_size, gauge_size * 0.4)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, value_text)

        # Draw unit below value
        unit_font = QFont("Segoe UI", 10)
        painter.setFont(unit_font)
        painter.setPen(QColor(COLORS["text_secondary"]))
        unit_rect = QRectF(x_offset, y_offset + gauge_size * 0.55, gauge_size, gauge_size * 0.2)
        painter.drawText(unit_rect, Qt.AlignmentFlag.AlignCenter, self.unit)

        # Draw title below gauge
        title_font = QFont("Segoe UI", 10, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(COLORS["text_primary"]))
        title_rect = QRectF(0, height - 25, width, 25)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignCenter, self.title)

        painter.end()

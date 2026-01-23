"""
Memory Bar Widget - Shows VRAM usage with segmented display
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QFont, QLinearGradient, QPen, QBrush

from config import COLORS


class MemoryBar(QWidget):
    """
    A horizontal bar showing VRAM usage with gradient fill and text labels.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_bytes = 0
        self.used_bytes = 0
        self.process_segments = []  # List of (name, bytes) for top processes

        self.setMinimumHeight(60)
        self.setMaximumHeight(80)

    def set_memory(self, used_bytes: int, total_bytes: int, processes: list = None):
        """
        Update memory values.
        processes: List of (name, bytes) tuples for segment coloring
        """
        self.used_bytes = used_bytes
        self.total_bytes = total_bytes
        self.process_segments = processes or []
        self.update()

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string"""
        gb = bytes_val / (1024 ** 3)
        if gb >= 10:
            return f"{gb:.1f} GB"
        else:
            return f"{gb:.2f} GB"

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        # Bar dimensions
        bar_height = 24
        bar_y = (height - bar_height) / 2 + 5
        bar_margin = 10
        bar_width = width - (bar_margin * 2)
        corner_radius = 6

        # Draw background
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS["vram_free"]))
        painter.drawRoundedRect(
            QRectF(bar_margin, bar_y, bar_width, bar_height),
            corner_radius, corner_radius
        )

        # Draw used portion with gradient
        if self.total_bytes > 0:
            used_ratio = self.used_bytes / self.total_bytes
            used_width = bar_width * used_ratio

            if used_width > 0:
                gradient = QLinearGradient(bar_margin, 0, bar_margin + used_width, 0)
                gradient.setColorAt(0, QColor("#9333ea"))  # Purple start
                gradient.setColorAt(1, QColor("#7c3aed"))  # Purple end

                painter.setBrush(QBrush(gradient))

                # Clip to rounded rect shape
                if used_width < bar_width:
                    # Not full - draw rounded left, flat right
                    painter.drawRoundedRect(
                        QRectF(bar_margin, bar_y, used_width + corner_radius, bar_height),
                        corner_radius, corner_radius
                    )
                    # Cover the right rounded corner with square
                    painter.drawRect(
                        QRectF(bar_margin + used_width, bar_y, corner_radius, bar_height)
                    )
                else:
                    painter.drawRoundedRect(
                        QRectF(bar_margin, bar_y, used_width, bar_height),
                        corner_radius, corner_radius
                    )

        # Draw border
        painter.setPen(QPen(QColor(COLORS["vram_border"]), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(
            QRectF(bar_margin, bar_y, bar_width, bar_height),
            corner_radius, corner_radius
        )

        # Draw text labels
        painter.setPen(QColor(COLORS["text_primary"]))

        # Title on top left
        title_font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.drawText(bar_margin, int(bar_y - 5), "VRAM")

        # Usage on top right
        if self.total_bytes > 0:
            used_text = f"{self._format_bytes(self.used_bytes)} / {self._format_bytes(self.total_bytes)}"
            percent = (self.used_bytes / self.total_bytes) * 100
            usage_text = f"{used_text} ({percent:.1f}%)"
        else:
            usage_text = "N/A"

        value_font = QFont("Segoe UI", 9)
        painter.setFont(value_font)
        text_width = painter.fontMetrics().horizontalAdvance(usage_text)
        painter.drawText(int(width - bar_margin - text_width), int(bar_y - 5), usage_text)

        # Free memory indicator at bottom
        if self.total_bytes > 0:
            free_bytes = self.total_bytes - self.used_bytes
            free_text = f"Free: {self._format_bytes(free_bytes)}"
            painter.setPen(QColor(COLORS["text_secondary"]))
            small_font = QFont("Segoe UI", 8)
            painter.setFont(small_font)
            painter.drawText(bar_margin, int(bar_y + bar_height + 15), free_text)

        painter.end()

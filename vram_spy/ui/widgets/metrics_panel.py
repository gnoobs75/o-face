"""
Metrics Panel - Grid display of current GPU metrics
"""

from PyQt6.QtWidgets import QWidget, QGridLayout, QLabel, QVBoxLayout, QFrame
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from config import COLORS


class MetricCard(QFrame):
    """A single metric display card"""

    def __init__(self, title: str, unit: str = "", parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit

        self._setup_ui()

    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border-radius: 8px;
                border: 1px solid {COLORS['vram_border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        # Title
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Segoe UI", 9))
        self.title_label.setStyleSheet(f"color: {COLORS['text_secondary']}; border: none;")
        layout.addWidget(self.title_label)

        # Value
        self.value_label = QLabel("--")
        self.value_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.value_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        layout.addWidget(self.value_label)

    def set_value(self, value: str, color: str = None):
        """Update the displayed value"""
        self.value_label.setText(f"{value}{self.unit}")
        if color:
            self.value_label.setStyleSheet(f"color: {color}; border: none;")


class MetricsPanel(QWidget):
    """
    A panel displaying multiple GPU metrics in a grid.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create metric cards
        self.cards = {}

        # Row 1: Clocks
        self.cards["graphics_clock"] = MetricCard("Graphics Clock", " MHz")
        self.cards["memory_clock"] = MetricCard("Memory Clock", " MHz")
        self.cards["sm_clock"] = MetricCard("SM Clock", " MHz")

        # Row 2: Utilization
        self.cards["memory_util"] = MetricCard("Memory BW", "%")
        self.cards["encoder"] = MetricCard("Encoder", "%")
        self.cards["decoder"] = MetricCard("Decoder", "%")

        # Row 3: PCIe
        self.cards["pcie_gen"] = MetricCard("PCIe Gen", "")
        self.cards["pcie_tx"] = MetricCard("PCIe TX", "")
        self.cards["pcie_rx"] = MetricCard("PCIe RX", "")

        # Row 4: Misc
        self.cards["pstate"] = MetricCard("P-State", "")
        self.cards["fan"] = MetricCard("Fan Speed", "%")
        self.cards["driver"] = MetricCard("Driver", "")

        # Add to grid
        row = 0
        col = 0
        for name, card in self.cards.items():
            layout.addWidget(card, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def update_metrics(self, metrics):
        """Update all metric cards from GPUMetrics object"""
        # Clocks
        self.cards["graphics_clock"].set_value(str(metrics.graphics_clock_mhz))
        self.cards["memory_clock"].set_value(str(metrics.memory_clock_mhz))
        self.cards["sm_clock"].set_value(str(metrics.sm_clock_mhz))

        # Utilization
        self.cards["memory_util"].set_value(f"{metrics.memory_utilization:.1f}")
        self.cards["encoder"].set_value(f"{metrics.encoder_utilization:.1f}")
        self.cards["decoder"].set_value(f"{metrics.decoder_utilization:.1f}")

        # PCIe
        self.cards["pcie_gen"].set_value(f"Gen {metrics.pcie_gen} x{metrics.pcie_width}")

        # Format PCIe throughput
        tx_mb = metrics.pcie_tx_bytes_per_sec / (1024 * 1024)
        rx_mb = metrics.pcie_rx_bytes_per_sec / (1024 * 1024)

        if tx_mb >= 1000:
            tx_text = f"{tx_mb/1024:.1f} GB/s"
        else:
            tx_text = f"{tx_mb:.0f} MB/s"

        if rx_mb >= 1000:
            rx_text = f"{rx_mb/1024:.1f} GB/s"
        else:
            rx_text = f"{rx_mb:.0f} MB/s"

        self.cards["pcie_tx"].set_value(tx_text)
        self.cards["pcie_rx"].set_value(rx_text)

        # Misc
        self.cards["pstate"].set_value(metrics.performance_state)
        self.cards["fan"].set_value(f"{metrics.fan_speed_percent:.0f}")
        self.cards["driver"].set_value(metrics.driver_version)

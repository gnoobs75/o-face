"""
Data Logger - Handles history buffering and CSV/JSON export
"""

import csv
import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

from .metrics import GPUMetrics
from config import HISTORY_POINTS


class DataLogger:
    """
    Buffers GPU metrics history and handles data export.
    """

    def __init__(self, max_points: int = HISTORY_POINTS):
        self.max_points = max_points
        self.history: deque[GPUMetrics] = deque(maxlen=max_points)

    def add_metrics(self, metrics: GPUMetrics):
        """Add a metrics snapshot to history"""
        self.history.append(metrics)

    def clear(self):
        """Clear all history"""
        self.history.clear()

    @property
    def length(self) -> int:
        """Number of recorded data points"""
        return len(self.history)

    def get_time_series(self, field: str) -> tuple[list[datetime], list[float]]:
        """
        Get time series data for a specific field.
        Returns (timestamps, values) tuple.
        """
        timestamps = []
        values = []

        for metrics in self.history:
            timestamps.append(metrics.timestamp)
            value = getattr(metrics, field, 0)
            if value is None:
                value = 0
            values.append(float(value))

        return timestamps, values

    def get_vram_history(self) -> tuple[list[float], list[float]]:
        """Get VRAM usage history as (seconds_ago, gb_used) for plotting"""
        if not self.history:
            return [], []

        now = datetime.now()
        seconds_ago = []
        values = []

        for metrics in self.history:
            delta = (now - metrics.timestamp).total_seconds()
            seconds_ago.append(-delta)  # Negative so newest is at right
            values.append(metrics.vram_used_gb)

        return seconds_ago, values

    def get_utilization_history(self) -> tuple[list[float], list[float]]:
        """Get GPU utilization history"""
        if not self.history:
            return [], []

        now = datetime.now()
        seconds_ago = []
        values = []

        for metrics in self.history:
            delta = (now - metrics.timestamp).total_seconds()
            seconds_ago.append(-delta)
            values.append(metrics.gpu_utilization)

        return seconds_ago, values

    def get_temperature_history(self) -> tuple[list[float], list[float]]:
        """Get temperature history"""
        if not self.history:
            return [], []

        now = datetime.now()
        seconds_ago = []
        values = []

        for metrics in self.history:
            delta = (now - metrics.timestamp).total_seconds()
            seconds_ago.append(-delta)
            values.append(metrics.temperature_celsius)

        return seconds_ago, values

    def get_power_history(self) -> tuple[list[float], list[float]]:
        """Get power draw history"""
        if not self.history:
            return [], []

        now = datetime.now()
        seconds_ago = []
        values = []

        for metrics in self.history:
            delta = (now - metrics.timestamp).total_seconds()
            seconds_ago.append(-delta)
            values.append(metrics.power_draw_watts)

        return seconds_ago, values

    def export_csv(self, filepath: Optional[str] = None) -> str:
        """
        Export history to CSV file.
        Returns the path to the created file.
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"vram_spy_export_{timestamp}.csv"

        path = Path(filepath)

        with open(path, "w", newline="", encoding="utf-8") as f:
            if not self.history:
                return str(path)

            # Get field names from first entry
            fieldnames = list(self.history[0].to_dict().keys())
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for metrics in self.history:
                writer.writerow(metrics.to_dict())

        return str(path)

    def export_json(self, filepath: Optional[str] = None) -> str:
        """
        Export history to JSON file.
        Returns the path to the created file.
        """
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"vram_spy_export_{timestamp}.json"

        path = Path(filepath)

        data = {
            "export_time": datetime.now().isoformat(),
            "data_points": len(self.history),
            "metrics": [m.to_dict() for m in self.history]
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return str(path)

    def export(self, filepath: str, format: str = "csv") -> str:
        """Export to specified format"""
        if format.lower() == "json":
            return self.export_json(filepath)
        else:
            return self.export_csv(filepath)

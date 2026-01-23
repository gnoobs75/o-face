"""
Data structures for GPU metrics
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class ProcessInfo:
    """Information about a process using GPU memory"""
    pid: int
    name: str
    vram_used_bytes: int
    gpu_utilization: Optional[float] = None  # Percentage if available
    memory_utilization: Optional[float] = None  # Percentage if available

    @property
    def vram_used_mb(self) -> float:
        """VRAM usage in megabytes"""
        return self.vram_used_bytes / (1024 * 1024)

    @property
    def vram_used_gb(self) -> float:
        """VRAM usage in gigabytes"""
        return self.vram_used_bytes / (1024 * 1024 * 1024)


@dataclass
class GPUMetrics:
    """Complete GPU metrics snapshot"""
    timestamp: datetime = field(default_factory=datetime.now)

    # Device info
    device_name: str = ""
    device_index: int = 0
    driver_version: str = ""
    cuda_version: str = ""

    # Memory
    vram_total_bytes: int = 0
    vram_used_bytes: int = 0
    vram_free_bytes: int = 0

    # Utilization
    gpu_utilization: float = 0.0  # Percentage
    memory_utilization: float = 0.0  # Percentage (bandwidth)

    # Temperature and power
    temperature_celsius: float = 0.0
    power_draw_watts: float = 0.0
    power_limit_watts: float = 0.0

    # Clocks
    graphics_clock_mhz: int = 0
    memory_clock_mhz: int = 0
    sm_clock_mhz: int = 0

    # Fan
    fan_speed_percent: float = 0.0

    # Performance state
    performance_state: str = "P0"  # P0 = max, P8 = idle

    # PCIe
    pcie_gen: int = 0
    pcie_width: int = 0
    pcie_tx_bytes_per_sec: int = 0
    pcie_rx_bytes_per_sec: int = 0

    # Encoder/Decoder utilization
    encoder_utilization: float = 0.0
    decoder_utilization: float = 0.0

    # Process list
    processes: list[ProcessInfo] = field(default_factory=list)

    @property
    def vram_total_gb(self) -> float:
        return self.vram_total_bytes / (1024 ** 3)

    @property
    def vram_used_gb(self) -> float:
        return self.vram_used_bytes / (1024 ** 3)

    @property
    def vram_free_gb(self) -> float:
        return self.vram_free_bytes / (1024 ** 3)

    @property
    def vram_used_percent(self) -> float:
        if self.vram_total_bytes == 0:
            return 0.0
        return (self.vram_used_bytes / self.vram_total_bytes) * 100

    @property
    def power_percent(self) -> float:
        if self.power_limit_watts == 0:
            return 0.0
        return (self.power_draw_watts / self.power_limit_watts) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for export"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "device_name": self.device_name,
            "vram_total_gb": round(self.vram_total_gb, 2),
            "vram_used_gb": round(self.vram_used_gb, 2),
            "vram_used_percent": round(self.vram_used_percent, 1),
            "gpu_utilization": round(self.gpu_utilization, 1),
            "memory_utilization": round(self.memory_utilization, 1),
            "temperature_celsius": round(self.temperature_celsius, 1),
            "power_draw_watts": round(self.power_draw_watts, 1),
            "power_limit_watts": round(self.power_limit_watts, 1),
            "graphics_clock_mhz": self.graphics_clock_mhz,
            "memory_clock_mhz": self.memory_clock_mhz,
            "fan_speed_percent": round(self.fan_speed_percent, 1),
            "performance_state": self.performance_state,
            "encoder_utilization": round(self.encoder_utilization, 1),
            "decoder_utilization": round(self.decoder_utilization, 1),
            "process_count": len(self.processes),
        }

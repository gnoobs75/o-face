"""
GPU Monitor - NVML wrapper for collecting GPU metrics
"""

import pynvml
from typing import Optional
from .metrics import GPUMetrics, ProcessInfo
from .process_tracker import ProcessTracker


class GPUMonitor:
    """
    Monitors NVIDIA GPU using NVML library.
    Collects all available metrics and per-process VRAM usage.
    """

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.handle: Optional[object] = None
        self.initialized = False
        self.process_tracker = ProcessTracker()
        self._device_name = ""
        self._driver_version = ""
        self._cuda_version = ""

    def initialize(self) -> bool:
        """Initialize NVML and get device handle"""
        try:
            pynvml.nvmlInit()
            self.handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            self.initialized = True

            # Cache static device info
            self._device_name = pynvml.nvmlDeviceGetName(self.handle)
            if isinstance(self._device_name, bytes):
                self._device_name = self._device_name.decode("utf-8")

            self._driver_version = pynvml.nvmlSystemGetDriverVersion()
            if isinstance(self._driver_version, bytes):
                self._driver_version = self._driver_version.decode("utf-8")

            # Get CUDA version
            cuda_version = pynvml.nvmlSystemGetCudaDriverVersion_v2()
            major = cuda_version // 1000
            minor = (cuda_version % 1000) // 10
            self._cuda_version = f"{major}.{minor}"

            return True
        except pynvml.NVMLError as e:
            print(f"Failed to initialize NVML: {e}")
            self.initialized = False
            return False

    def shutdown(self):
        """Shutdown NVML"""
        if self.initialized:
            try:
                pynvml.nvmlShutdown()
            except pynvml.NVMLError:
                pass
            self.initialized = False

    def get_device_count(self) -> int:
        """Get number of NVIDIA GPUs"""
        if not self.initialized:
            return 0
        try:
            return pynvml.nvmlDeviceGetCount()
        except pynvml.NVMLError:
            return 0

    def _safe_get(self, func, *args, default=0):
        """Safely call NVML function with default on error"""
        try:
            return func(*args)
        except pynvml.NVMLError:
            return default

    def get_metrics(self) -> Optional[GPUMetrics]:
        """Collect all GPU metrics"""
        if not self.initialized or self.handle is None:
            return None

        metrics = GPUMetrics()
        metrics.device_index = self.device_index
        metrics.device_name = self._device_name
        metrics.driver_version = self._driver_version
        metrics.cuda_version = self._cuda_version

        # Memory info
        try:
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(self.handle)
            metrics.vram_total_bytes = mem_info.total
            metrics.vram_used_bytes = mem_info.used
            metrics.vram_free_bytes = mem_info.free
        except pynvml.NVMLError:
            pass

        # Utilization
        try:
            util = pynvml.nvmlDeviceGetUtilizationRates(self.handle)
            metrics.gpu_utilization = util.gpu
            metrics.memory_utilization = util.memory
        except pynvml.NVMLError:
            pass

        # Temperature
        metrics.temperature_celsius = self._safe_get(
            pynvml.nvmlDeviceGetTemperature,
            self.handle,
            pynvml.NVML_TEMPERATURE_GPU,
            default=0
        )

        # Power
        try:
            # Power draw is in milliwatts
            power_mw = pynvml.nvmlDeviceGetPowerUsage(self.handle)
            metrics.power_draw_watts = power_mw / 1000.0
        except pynvml.NVMLError:
            pass

        try:
            # Power limit is in milliwatts
            limit_mw = pynvml.nvmlDeviceGetEnforcedPowerLimit(self.handle)
            metrics.power_limit_watts = limit_mw / 1000.0
        except pynvml.NVMLError:
            pass

        # Clocks
        metrics.graphics_clock_mhz = self._safe_get(
            pynvml.nvmlDeviceGetClockInfo,
            self.handle,
            pynvml.NVML_CLOCK_GRAPHICS,
            default=0
        )
        metrics.memory_clock_mhz = self._safe_get(
            pynvml.nvmlDeviceGetClockInfo,
            self.handle,
            pynvml.NVML_CLOCK_MEM,
            default=0
        )
        metrics.sm_clock_mhz = self._safe_get(
            pynvml.nvmlDeviceGetClockInfo,
            self.handle,
            pynvml.NVML_CLOCK_SM,
            default=0
        )

        # Fan speed
        try:
            metrics.fan_speed_percent = pynvml.nvmlDeviceGetFanSpeed(self.handle)
        except pynvml.NVMLError:
            # Some GPUs don't report fan speed
            metrics.fan_speed_percent = 0

        # Performance state
        try:
            pstate = pynvml.nvmlDeviceGetPerformanceState(self.handle)
            metrics.performance_state = f"P{pstate}"
        except pynvml.NVMLError:
            metrics.performance_state = "N/A"

        # PCIe info
        try:
            metrics.pcie_gen = pynvml.nvmlDeviceGetCurrPcieLinkGeneration(self.handle)
            metrics.pcie_width = pynvml.nvmlDeviceGetCurrPcieLinkWidth(self.handle)
        except pynvml.NVMLError:
            pass

        # PCIe throughput
        try:
            metrics.pcie_tx_bytes_per_sec = pynvml.nvmlDeviceGetPcieThroughput(
                self.handle, pynvml.NVML_PCIE_UTIL_TX_BYTES
            ) * 1024  # KB/s to B/s
            metrics.pcie_rx_bytes_per_sec = pynvml.nvmlDeviceGetPcieThroughput(
                self.handle, pynvml.NVML_PCIE_UTIL_RX_BYTES
            ) * 1024
        except pynvml.NVMLError:
            pass

        # Encoder/Decoder utilization
        try:
            enc_util, _ = pynvml.nvmlDeviceGetEncoderUtilization(self.handle)
            metrics.encoder_utilization = enc_util
        except pynvml.NVMLError:
            pass

        try:
            dec_util, _ = pynvml.nvmlDeviceGetDecoderUtilization(self.handle)
            metrics.decoder_utilization = dec_util
        except pynvml.NVMLError:
            pass

        # Per-process information
        metrics.processes = self._get_process_list()

        return metrics

    def _get_process_list(self) -> list[ProcessInfo]:
        """Get list of processes using GPU memory"""
        processes = []

        if not self.initialized or self.handle is None:
            return processes

        # Get compute processes
        try:
            compute_procs = pynvml.nvmlDeviceGetComputeRunningProcesses(self.handle)
            for proc in compute_procs:
                name = self.process_tracker.get_process_name(proc.pid)
                processes.append(ProcessInfo(
                    pid=proc.pid,
                    name=name,
                    vram_used_bytes=proc.usedGpuMemory if proc.usedGpuMemory else 0,
                ))
        except pynvml.NVMLError:
            pass

        # Get graphics processes
        try:
            graphics_procs = pynvml.nvmlDeviceGetGraphicsRunningProcesses(self.handle)
            existing_pids = {p.pid for p in processes}

            for proc in graphics_procs:
                if proc.pid not in existing_pids:
                    name = self.process_tracker.get_process_name(proc.pid)
                    processes.append(ProcessInfo(
                        pid=proc.pid,
                        name=name,
                        vram_used_bytes=proc.usedGpuMemory if proc.usedGpuMemory else 0,
                    ))
                else:
                    # Add graphics memory to existing compute process
                    for p in processes:
                        if p.pid == proc.pid and proc.usedGpuMemory:
                            p.vram_used_bytes += proc.usedGpuMemory
                            break
        except pynvml.NVMLError:
            pass

        # Sort by VRAM usage descending
        processes.sort(key=lambda p: p.vram_used_bytes, reverse=True)

        return processes

    def __enter__(self):
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

"""
Process tracker for resolving process names from PIDs
"""

import psutil
from functools import lru_cache
from typing import Optional


class ProcessTracker:
    """Tracks and resolves process information from PIDs"""

    def __init__(self):
        self._process_cache: dict[int, str] = {}

    def get_process_name(self, pid: int) -> str:
        """
        Get process name from PID with caching.
        Returns 'Unknown' if process cannot be found.
        """
        # Check cache first
        if pid in self._process_cache:
            # Verify process still exists
            if psutil.pid_exists(pid):
                return self._process_cache[pid]
            else:
                # Process ended, remove from cache
                del self._process_cache[pid]

        # Look up process
        try:
            proc = psutil.Process(pid)
            name = proc.name()
            self._process_cache[pid] = name
            return name
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return f"PID {pid}"

    def get_process_info(self, pid: int) -> Optional[dict]:
        """
        Get detailed process information.
        Returns None if process cannot be accessed.
        """
        try:
            proc = psutil.Process(pid)
            return {
                "pid": pid,
                "name": proc.name(),
                "exe": proc.exe() if proc.exe() else None,
                "cmdline": " ".join(proc.cmdline()) if proc.cmdline() else None,
                "create_time": proc.create_time(),
                "status": proc.status(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def clear_cache(self):
        """Clear the process name cache"""
        self._process_cache.clear()

    def cleanup_dead_processes(self):
        """Remove dead processes from cache"""
        dead_pids = [
            pid for pid in self._process_cache
            if not psutil.pid_exists(pid)
        ]
        for pid in dead_pids:
            del self._process_cache[pid]

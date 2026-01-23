"""Process management functionality."""

import subprocess
import psutil
from typing import Optional

from .models import ProcessInfo
from .port_scanner import PortScanner
from ..utils.logging_config import get_logger, timed

logger = get_logger('process_manager')


class ProcessManager:
    """Manages process termination and information."""

    def __init__(self):
        self.port_scanner = PortScanner()
        logger.debug("ProcessManager initialized")

    def kill_process(self, pid: int, force: bool = False) -> tuple[bool, str]:
        """
        Kill a process by PID.

        Args:
            pid: Process ID to kill.
            force: If True, use SIGKILL (force). If False, use SIGTERM (graceful).

        Returns:
            Tuple of (success, message).
        """
        logger.info(f"Attempting to kill process PID={pid} (force={force})")
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            logger.debug(f"Found process: {proc_name}")

            if force:
                proc.kill()  # SIGKILL
                action = "Force killed"
            else:
                proc.terminate()  # SIGTERM
                action = "Terminated"

            # Wait briefly to confirm
            try:
                proc.wait(timeout=2)
                logger.info(f"Successfully {action.lower()} process {proc_name} (PID: {pid})")
                return True, f"{action} process {proc_name} (PID: {pid})"
            except psutil.TimeoutExpired:
                if not force:
                    logger.warning(f"Process {proc_name} (PID: {pid}) still running after terminate")
                    return True, f"{action} process {proc_name} (PID: {pid}) - still running, may need force kill"
                logger.error(f"Process {proc_name} (PID: {pid}) did not terminate even with force kill")
                return False, f"Process {proc_name} (PID: {pid}) did not terminate"

        except psutil.NoSuchProcess:
            logger.warning(f"Process PID={pid} not found")
            return False, f"Process with PID {pid} not found"
        except psutil.AccessDenied:
            logger.error(f"Access denied when trying to kill PID={pid}")
            return False, f"Access denied - cannot kill PID {pid}. Try running as administrator."
        except Exception as e:
            logger.exception(f"Error killing process PID={pid}")
            return False, f"Error killing process: {e}"

    def kill_by_port(self, port: int, force: bool = False) -> tuple[bool, str]:
        """
        Kill process(es) using a specific port.

        Args:
            port: Port number.
            force: If True, force kill.

        Returns:
            Tuple of (success, message).
        """
        process = self.port_scanner.find_process_by_port(port)

        if not process:
            return False, f"No process found using port {port}"

        return self.kill_process(process.pid, force)

    def kill_process_tree(self, pid: int, force: bool = False) -> tuple[bool, str]:
        """
        Kill a process and all its children.

        Args:
            pid: Parent process ID.
            force: If True, force kill.

        Returns:
            Tuple of (success, message).
        """
        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # Kill children first
            killed_count = 0
            for child in children:
                try:
                    if force:
                        child.kill()
                    else:
                        child.terminate()
                    killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            # Kill parent
            success, msg = self.kill_process(pid, force)

            if success:
                return True, f"Killed process tree: parent + {killed_count} children"
            return success, msg

        except psutil.NoSuchProcess:
            return False, f"Process with PID {pid} not found"
        except psutil.AccessDenied:
            return False, f"Access denied - cannot kill PID {pid}. Try running as administrator."
        except Exception as e:
            return False, f"Error killing process tree: {e}"

    @timed
    def get_process_details(self, pid: int) -> Optional[dict]:
        """Get detailed information about a process."""
        logger.debug(f"Getting details for PID={pid}")
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                info = {
                    'pid': pid,
                    'name': proc.name(),
                    'status': proc.status(),
                    'cmdline': ' '.join(proc.cmdline()) if proc.cmdline() else '',
                    'exe': proc.exe() if proc.exe() else '',
                    'cwd': '',
                    'username': '',
                    'create_time': proc.create_time(),
                    'cpu_percent': proc.cpu_percent(),
                    'memory_info': {},
                    'connections': [],
                    'children': [],
                    'parent': None,
                }

                try:
                    info['cwd'] = proc.cwd()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                try:
                    info['username'] = proc.username()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                try:
                    mem = proc.memory_info()
                    info['memory_info'] = {
                        'rss': mem.rss,
                        'vms': mem.vms,
                        'rss_mb': round(mem.rss / (1024 * 1024), 2),
                    }
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                try:
                    conns = proc.net_connections()
                    info['connections'] = [
                        {
                            'local': f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "",
                            'remote': f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "",
                            'status': c.status,
                        }
                        for c in conns
                    ]
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                try:
                    children = proc.children()
                    info['children'] = [
                        {'pid': c.pid, 'name': c.name()}
                        for c in children
                    ]
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                try:
                    parent = proc.parent()
                    if parent:
                        info['parent'] = {'pid': parent.pid, 'name': parent.name()}
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

                return info

        except psutil.NoSuchProcess:
            return None
        except psutil.AccessDenied:
            return {'pid': pid, 'error': 'Access denied'}

    def open_file_location(self, exe_path: str) -> tuple[bool, str]:
        """Open the folder containing an executable in Explorer."""
        try:
            from pathlib import Path
            path = Path(exe_path)
            if path.exists():
                subprocess.run(['explorer', '/select,', str(path)], check=False)
                return True, f"Opened folder for {path.name}"
            return False, f"Path does not exist: {exe_path}"
        except Exception as e:
            return False, f"Error opening location: {e}"

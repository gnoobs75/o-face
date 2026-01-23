"""Port scanning functionality using psutil."""

import socket
import psutil
from typing import Optional

from .models import PortInfo, ProcessInfo, Protocol, ConnectionState
from ..utils.logging_config import get_logger, timed, PerfTimer

logger = get_logger('port_scanner')


class PortScanner:
    """Scans system for active port usage."""

    # Map psutil connection states to our enum
    STATE_MAP = {
        'LISTEN': ConnectionState.LISTEN,
        'ESTABLISHED': ConnectionState.ESTABLISHED,
        'TIME_WAIT': ConnectionState.TIME_WAIT,
        'CLOSE_WAIT': ConnectionState.CLOSE_WAIT,
    }

    @timed
    def get_all_ports(self, include_established: bool = True) -> list[PortInfo]:
        """
        Get all ports currently in use.

        Args:
            include_established: If True, include established connections.
                                If False, only show listening ports.

        Returns:
            List of PortInfo objects sorted by port number.
        """
        logger.debug(f"get_all_ports called (include_established={include_established})")
        ports: list[PortInfo] = []
        seen = set()  # Track (port, protocol, state) to avoid duplicates

        try:
            with PerfTimer("psutil.net_connections", logger):
                connections = psutil.net_connections(kind='inet')
            logger.debug(f"Found {len(connections)} total connections")
        except psutil.AccessDenied:
            logger.warning("AccessDenied when getting network connections")
            return ports

        for conn in connections:
            if not conn.laddr:
                continue

            port = conn.laddr.port
            protocol = Protocol.TCP if conn.type == socket.SOCK_STREAM else Protocol.UDP

            # Map state
            state_str = conn.status if conn.status else 'NONE'
            state = self.STATE_MAP.get(state_str, ConnectionState.OTHER)

            # Filter based on preference
            if not include_established and state != ConnectionState.LISTEN:
                continue

            # Skip duplicates
            key = (port, protocol, state, conn.laddr.ip)
            if key in seen:
                continue
            seen.add(key)

            # Get process info
            process = None
            if conn.pid:
                process = self._get_process_info(conn.pid)

            remote = ""
            if conn.raddr:
                remote = f"{conn.raddr.ip}:{conn.raddr.port}"

            port_info = PortInfo(
                port=port,
                protocol=protocol,
                state=state,
                local_address=f"{conn.laddr.ip}:{port}",
                remote_address=remote,
                process=process
            )
            ports.append(port_info)

        logger.info(f"Found {len(ports)} ports (filtered from {len(connections)} connections)")
        return sorted(ports, key=lambda p: (p.port, p.protocol.value))

    def get_listening_ports(self) -> list[PortInfo]:
        """Get only listening ports."""
        return self.get_all_ports(include_established=False)

    def get_port_info(self, port: int) -> list[PortInfo]:
        """Get all connections for a specific port."""
        all_ports = self.get_all_ports()
        return [p for p in all_ports if p.port == port]

    def is_port_in_use(self, port: int) -> bool:
        """Check if a specific port is in use."""
        return len(self.get_port_info(port)) > 0

    def _get_process_info(self, pid: int) -> Optional[ProcessInfo]:
        """Get detailed process information."""
        try:
            proc = psutil.Process(pid)
            with proc.oneshot():
                # Get parent info
                parent_pid = None
                parent_name = ""
                try:
                    parent = proc.parent()
                    if parent:
                        parent_pid = parent.pid
                        parent_name = parent.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

                # Get command line
                try:
                    cmdline = " ".join(proc.cmdline())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    cmdline = ""

                # Get exe path
                try:
                    exe_path = proc.exe()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    exe_path = ""

                # Get username
                try:
                    username = proc.username()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    username = ""

                # Get create time
                try:
                    create_time = proc.create_time()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    create_time = None

                try:
                    name = proc.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    name = "<unknown>"

                return ProcessInfo(
                    pid=pid,
                    name=name,
                    cmdline=cmdline,
                    exe_path=exe_path,
                    parent_pid=parent_pid,
                    parent_name=parent_name,
                    username=username,
                    create_time=create_time
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return ProcessInfo(pid=pid, name="<unknown>")

    def find_process_by_port(self, port: int) -> Optional[ProcessInfo]:
        """Find the process using a specific port (listening preferred)."""
        port_infos = self.get_port_info(port)
        # Prefer listening process
        for pi in port_infos:
            if pi.is_listening and pi.process:
                return pi.process
        # Fall back to any process
        for pi in port_infos:
            if pi.process:
                return pi.process
        return None

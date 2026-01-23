"""Data models for PortMaster."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class Protocol(Enum):
    TCP = "TCP"
    UDP = "UDP"


class ConnectionState(Enum):
    LISTEN = "LISTEN"
    ESTABLISHED = "ESTABLISHED"
    TIME_WAIT = "TIME_WAIT"
    CLOSE_WAIT = "CLOSE_WAIT"
    OTHER = "OTHER"


@dataclass
class ProcessInfo:
    """Information about a process."""
    pid: int
    name: str
    cmdline: str = ""
    exe_path: str = ""
    parent_pid: Optional[int] = None
    parent_name: str = ""
    username: str = ""
    create_time: Optional[float] = None

    @property
    def display_name(self) -> str:
        """Get a display-friendly name."""
        if self.cmdline:
            return self.cmdline[:100] + ("..." if len(self.cmdline) > 100 else "")
        return self.name


@dataclass
class PortInfo:
    """Information about a port in use."""
    port: int
    protocol: Protocol
    state: ConnectionState
    local_address: str
    remote_address: str = ""
    process: Optional[ProcessInfo] = None

    @property
    def is_listening(self) -> bool:
        return self.state == ConnectionState.LISTEN

    @property
    def display_state(self) -> str:
        return self.state.value


@dataclass
class ConfigMatch:
    """A port configuration found in a file."""
    file_path: Path
    port: int
    line_number: int
    line_content: str
    context: str = ""  # Surrounding context
    match_type: str = ""  # e.g., "PORT=", "--port", "port:", etc.

    @property
    def relative_path(self) -> str:
        """Get path relative to scan root for display."""
        return str(self.file_path)


@dataclass
class ConflictInfo:
    """Information about a port conflict."""
    port: int
    active_process: Optional[PortInfo] = None
    config_matches: list[ConfigMatch] = field(default_factory=list)

    @property
    def conflict_type(self) -> str:
        """Describe the type of conflict."""
        has_active = self.active_process is not None
        config_count = len(self.config_matches)

        if has_active and config_count > 0:
            return "Port in use AND configured"
        elif has_active:
            return "Port in use"
        elif config_count > 1:
            return f"Configured in {config_count} places"
        return "No conflict"

    @property
    def is_conflict(self) -> bool:
        """Check if this represents an actual conflict."""
        has_active = self.active_process is not None
        config_count = len(self.config_matches)
        # Conflict if: port is in use AND configured, OR configured in multiple places
        return (has_active and config_count > 0) or config_count > 1

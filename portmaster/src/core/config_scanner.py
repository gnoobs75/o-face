"""Configuration file scanner for port definitions."""

import json
import re
from pathlib import Path
from typing import Generator, Optional

import yaml

try:
    import toml
except ImportError:
    toml = None

from .models import ConfigMatch
from ..utils.logging_config import get_logger, timed, PerfTimer

logger = get_logger('config_scanner')


class ConfigScanner:
    """Scans configuration files for port definitions."""

    # File extensions to scan
    SCRIPT_EXTENSIONS = {'.bat', '.cmd', '.ps1'}
    CONFIG_EXTENSIONS = {'.env', '.json', '.yaml', '.yml', '.toml', '.xml', '.properties'}

    # Regex patterns to find port numbers
    PORT_PATTERNS = [
        # PORT=3000, port=8080
        (r'(?i)\bport\s*[=:]\s*(\d{2,5})\b', 'PORT='),
        # --port 3000, --port=3000, -p 3000
        (r'(?i)(?:--port|(?<!-)-p)\s*[=\s]\s*(\d{2,5})\b', '--port'),
        # :3000 (common in URLs and bind addresses)
        (r':(\d{2,5})(?:\s|$|/|")', ':port'),
        # "port": 3000 (JSON)
        (r'"port"\s*:\s*(\d{2,5})', '"port":'),
        # port: 3000 (YAML)
        (r'(?m)^[\s]*port:\s*(\d{2,5})', 'port:'),
        # localhost:3000, 127.0.0.1:3000, 0.0.0.0:3000
        (r'(?:localhost|127\.0\.0\.1|0\.0\.0\.0):(\d{2,5})', 'host:port'),
        # VITE_PORT=3000, REACT_APP_PORT=3000, etc.
        (r'(?i)\w*_PORT\s*[=:]\s*(\d{2,5})\b', 'ENV_PORT'),
        # server.port=8080 (properties files)
        (r'(?i)server\.port\s*=\s*(\d{2,5})', 'server.port'),
    ]

    # Common port range
    MIN_PORT = 1024  # Skip well-known ports unless explicitly configured
    MAX_PORT = 65535

    def __init__(self, scan_root: str | Path = "C:\\Claude"):
        """Initialize scanner with root directory."""
        self.scan_root = Path(scan_root)
        logger.info(f"ConfigScanner initialized with root: {self.scan_root}")

    @timed
    def scan_all(self) -> list[ConfigMatch]:
        """Scan all configuration files for port definitions."""
        logger.info(f"Starting full scan of {self.scan_root}")
        matches: list[ConfigMatch] = []
        files_scanned = 0
        files_with_matches = 0

        with PerfTimer("find_config_files", logger):
            config_files = list(self._find_config_files())
        logger.info(f"Found {len(config_files)} config files to scan")

        for file_path in config_files:
            files_scanned += 1
            if files_scanned % 100 == 0:
                logger.debug(f"Scanned {files_scanned}/{len(config_files)} files...")

            file_matches = self.scan_file(file_path)
            if file_matches:
                files_with_matches += 1
                matches.extend(file_matches)
                logger.debug(f"Found {len(file_matches)} port(s) in {file_path}")

        logger.info(f"Scan complete: {files_scanned} files scanned, {files_with_matches} with matches, {len(matches)} total port configs found")
        return sorted(matches, key=lambda m: (m.port, str(m.file_path)))

    def scan_file(self, file_path: Path) -> list[ConfigMatch]:
        """Scan a single file for port definitions."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except (OSError, IOError):
            return []

        matches: list[ConfigMatch] = []
        lines = content.split('\n')

        # Use appropriate parser based on extension
        ext = file_path.suffix.lower()

        if ext == '.json':
            matches.extend(self._scan_json(file_path, content, lines))
        elif ext in {'.yaml', '.yml'}:
            matches.extend(self._scan_yaml(file_path, content, lines))
        elif ext == '.toml' and toml:
            matches.extend(self._scan_toml(file_path, content, lines))
        else:
            # Fall back to regex for scripts and other files
            matches.extend(self._scan_regex(file_path, lines))

        return matches

    def _find_config_files(self) -> Generator[Path, None, None]:
        """Find all configuration files in the scan directory."""
        all_extensions = self.SCRIPT_EXTENSIONS | self.CONFIG_EXTENSIONS
        logger.debug(f"Searching for files with extensions: {all_extensions}")
        skipped_dirs = 0
        found_count = 0

        try:
            for file_path in self.scan_root.rglob('*'):
                if file_path.is_file() and file_path.suffix.lower() in all_extensions:
                    # Skip common non-config directories
                    parts = file_path.parts
                    if any(skip in parts for skip in {'node_modules', '.git', '__pycache__', 'venv', '.venv'}):
                        skipped_dirs += 1
                        continue
                    found_count += 1
                    yield file_path
        except PermissionError as e:
            logger.warning(f"Permission denied during scan: {e}")

        logger.debug(f"File discovery complete: {found_count} files found, {skipped_dirs} skipped (node_modules, .git, etc.)")

    def _scan_regex(self, file_path: Path, lines: list[str]) -> list[ConfigMatch]:
        """Scan using regex patterns."""
        matches: list[ConfigMatch] = []
        seen = set()  # Avoid duplicate matches on same line

        for line_num, line in enumerate(lines, start=1):
            for pattern, match_type in self.PORT_PATTERNS:
                for match in re.finditer(pattern, line):
                    try:
                        port = int(match.group(1))
                        if self._is_valid_port(port):
                            key = (line_num, port)
                            if key not in seen:
                                seen.add(key)
                                matches.append(ConfigMatch(
                                    file_path=file_path,
                                    port=port,
                                    line_number=line_num,
                                    line_content=line.strip(),
                                    match_type=match_type
                                ))
                    except (ValueError, IndexError):
                        continue

        return matches

    def _scan_json(self, file_path: Path, content: str, lines: list[str]) -> list[ConfigMatch]:
        """Scan JSON file for port configurations."""
        matches: list[ConfigMatch] = []

        try:
            data = json.loads(content)
            port_values = self._extract_ports_from_dict(data)

            for port, key_path in port_values:
                # Find line number by searching for the value
                line_num = self._find_line_number(lines, str(port), key_path)
                matches.append(ConfigMatch(
                    file_path=file_path,
                    port=port,
                    line_number=line_num,
                    line_content=lines[line_num - 1].strip() if line_num <= len(lines) else "",
                    match_type=f"json:{key_path}"
                ))
        except json.JSONDecodeError:
            # Fall back to regex
            matches.extend(self._scan_regex(file_path, lines))

        return matches

    def _scan_yaml(self, file_path: Path, content: str, lines: list[str]) -> list[ConfigMatch]:
        """Scan YAML file for port configurations."""
        matches: list[ConfigMatch] = []

        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                port_values = self._extract_ports_from_dict(data)

                for port, key_path in port_values:
                    line_num = self._find_line_number(lines, str(port), key_path)
                    matches.append(ConfigMatch(
                        file_path=file_path,
                        port=port,
                        line_number=line_num,
                        line_content=lines[line_num - 1].strip() if line_num <= len(lines) else "",
                        match_type=f"yaml:{key_path}"
                    ))
        except yaml.YAMLError:
            # Fall back to regex
            matches.extend(self._scan_regex(file_path, lines))

        return matches

    def _scan_toml(self, file_path: Path, content: str, lines: list[str]) -> list[ConfigMatch]:
        """Scan TOML file for port configurations."""
        matches: list[ConfigMatch] = []

        try:
            data = toml.loads(content)
            port_values = self._extract_ports_from_dict(data)

            for port, key_path in port_values:
                line_num = self._find_line_number(lines, str(port), key_path)
                matches.append(ConfigMatch(
                    file_path=file_path,
                    port=port,
                    line_number=line_num,
                    line_content=lines[line_num - 1].strip() if line_num <= len(lines) else "",
                    match_type=f"toml:{key_path}"
                ))
        except Exception:
            # Fall back to regex
            matches.extend(self._scan_regex(file_path, lines))

        return matches

    def _extract_ports_from_dict(self, data: dict, prefix: str = "") -> list[tuple[int, str]]:
        """Extract port values from a nested dictionary."""
        results: list[tuple[int, str]] = []

        for key, value in data.items():
            key_path = f"{prefix}.{key}" if prefix else key
            key_lower = key.lower()

            # Check if this key looks port-related
            if isinstance(value, int) and self._is_valid_port(value):
                if 'port' in key_lower or key_lower in {'port', 'ports', 'listen'}:
                    results.append((value, key_path))
            elif isinstance(value, dict):
                results.extend(self._extract_ports_from_dict(value, key_path))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        results.extend(self._extract_ports_from_dict(item, f"{key_path}[{i}]"))

        return results

    def _find_line_number(self, lines: list[str], value: str, key_hint: str = "") -> int:
        """Find the line number containing a value."""
        key_part = key_hint.split('.')[-1].split('[')[0] if key_hint else ""

        for i, line in enumerate(lines, start=1):
            if value in line:
                if not key_part or key_part.lower() in line.lower():
                    return i

        # If not found with key hint, just find the value
        for i, line in enumerate(lines, start=1):
            if value in line:
                return i

        return 1

    def _is_valid_port(self, port: int) -> bool:
        """Check if port number is in valid range."""
        return self.MIN_PORT <= port <= self.MAX_PORT

    def get_ports_by_directory(self) -> dict[Path, list[ConfigMatch]]:
        """Get port configurations grouped by directory."""
        matches = self.scan_all()
        by_dir: dict[Path, list[ConfigMatch]] = {}

        for match in matches:
            dir_path = match.file_path.parent
            if dir_path not in by_dir:
                by_dir[dir_path] = []
            by_dir[dir_path].append(match)

        return by_dir

    def find_conflicts(self, matches: Optional[list[ConfigMatch]] = None) -> dict[int, list[ConfigMatch]]:
        """Find ports configured in multiple places."""
        if matches is None:
            matches = self.scan_all()

        by_port: dict[int, list[ConfigMatch]] = {}
        for match in matches:
            if match.port not in by_port:
                by_port[match.port] = []
            by_port[match.port].append(match)

        # Return only ports with multiple configs
        return {port: configs for port, configs in by_port.items() if len(configs) > 1}

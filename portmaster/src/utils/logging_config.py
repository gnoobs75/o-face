"""Logging configuration for PortMaster."""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import time
from functools import wraps

# Log directory
LOG_DIR = Path.home() / ".portmaster" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Log file with timestamp
LOG_FILE = LOG_DIR / f"portmaster_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Create formatters
DETAILED_FORMAT = logging.Formatter(
    '%(asctime)s.%(msecs)03d | %(levelname)-8s | %(name)-25s | %(funcName)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

SIMPLE_FORMAT = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)


def setup_logging(level: int = logging.DEBUG) -> logging.Logger:
    """
    Setup application-wide logging.

    Args:
        level: Logging level (default DEBUG for diagnostics)

    Returns:
        Root logger for the application
    """
    # Get root logger for our app
    logger = logging.getLogger('portmaster')
    logger.setLevel(level)

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # File handler - detailed logging
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(DETAILED_FORMAT)
    logger.addHandler(file_handler)

    # Console handler - less verbose
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(SIMPLE_FORMAT)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {LOG_FILE}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(f'portmaster.{name}')


def timed(func):
    """Decorator to log function execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger('perf')
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = (time.perf_counter() - start) * 1000  # ms
            if elapsed > 100:  # Log slow operations (>100ms)
                logger.warning(f"SLOW: {func.__qualname__} took {elapsed:.2f}ms")
            else:
                logger.debug(f"{func.__qualname__} took {elapsed:.2f}ms")
            return result
        except Exception as e:
            elapsed = (time.perf_counter() - start) * 1000
            logger.error(f"{func.__qualname__} failed after {elapsed:.2f}ms: {e}")
            raise
    return wrapper


class PerfTimer:
    """Context manager for timing code blocks."""

    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or get_logger('perf')
        self.start: float = 0
        self.elapsed: float = 0

    def __enter__(self):
        self.start = time.perf_counter()
        self.logger.debug(f"Starting: {self.name}")
        return self

    def __exit__(self, *args):
        self.elapsed = (time.perf_counter() - self.start) * 1000
        if self.elapsed > 100:
            self.logger.warning(f"SLOW: {self.name} took {self.elapsed:.2f}ms")
        else:
            self.logger.debug(f"Completed: {self.name} in {self.elapsed:.2f}ms")


def get_log_file_path() -> Path:
    """Get current log file path."""
    return LOG_FILE


def get_recent_logs(lines: int = 100) -> str:
    """Get recent log entries."""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except Exception:
        return "Could not read log file"

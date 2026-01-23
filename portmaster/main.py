#!/usr/bin/env python3
"""
PortMaster - Windows Port Management Tool

A desktop application for managing ports during development and testing.
Features:
- View active ports and their processes
- Scan configuration files for port definitions
- Detect and resolve port conflicts
- Kill processes by port
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from src.utils.logging_config import setup_logging, get_log_file_path
from src.ui.main_window import MainWindow


def main():
    """Main entry point for PortMaster."""
    # Initialize logging FIRST
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("PortMaster starting up")
    logger.info(f"Log file: {get_log_file_path()}")
    logger.info("=" * 60)

    # High DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("PortMaster")
    app.setApplicationVersion("1.0.1")
    app.setOrganizationName("PortMaster")

    # Default scan root - can be changed in the app
    scan_root = "C:\\Claude"

    # Check if scan root exists, use current directory if not
    if not Path(scan_root).exists():
        scan_root = str(Path.cwd())

    logger.info(f"Scan root: {scan_root}")

    window = MainWindow(scan_root=scan_root)
    window.show()

    logger.info("Main window displayed, entering event loop")
    exit_code = app.exec()

    logger.info(f"PortMaster shutting down (exit code: {exit_code})")
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

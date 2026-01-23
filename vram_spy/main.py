#!/usr/bin/env python3
"""
VRAM Spy - NVIDIA GPU Monitoring Utility

A real-time GPU monitoring tool for NVIDIA graphics cards.
Displays VRAM usage, temperature, utilization, and per-process memory consumption.

Usage:
    python main.py

Requirements:
    - NVIDIA GPU with driver installed
    - Python 3.10+
    - Dependencies: pip install -r requirements.txt
"""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow
from config import WINDOW_TITLE


def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(WINDOW_TITLE)

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

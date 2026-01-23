"""
VRAM Spy Configuration
"""

# Refresh rate in milliseconds
REFRESH_RATE_MS = 1000

# History settings
HISTORY_LENGTH_SECONDS = 300  # 5 minutes of history
HISTORY_POINTS = HISTORY_LENGTH_SECONDS  # One point per second

# Colors (RGBA format for PyQt)
COLORS = {
    # Gauge colors
    "gauge_background": "#2d2d2d",
    "gauge_arc": "#3d3d3d",

    # Temperature gradient
    "temp_cold": "#00ff88",      # Green - < 50°C
    "temp_warm": "#ffaa00",      # Orange - 50-75°C
    "temp_hot": "#ff4444",       # Red - > 75°C

    # Utilization
    "util_low": "#00ff88",       # Green - < 50%
    "util_medium": "#ffaa00",    # Orange - 50-80%
    "util_high": "#ff4444",      # Red - > 80%

    # Memory bar segments
    "vram_used": "#7c3aed",      # Purple
    "vram_free": "#1e1e2e",      # Dark
    "vram_border": "#4a4a5e",    # Border

    # Process table
    "table_background": "#1e1e2e",
    "table_alternate": "#252535",
    "table_selected": "#3d3d5c",
    "table_text": "#e0e0e0",

    # Charts
    "chart_vram": "#7c3aed",
    "chart_util": "#00ff88",
    "chart_temp": "#ff6b6b",
    "chart_power": "#ffd93d",
    "chart_grid": "#3d3d3d",
    "chart_background": "#1e1e2e",

    # General UI
    "background": "#1a1a2e",
    "surface": "#252535",
    "text_primary": "#ffffff",
    "text_secondary": "#a0a0a0",
    "accent": "#7c3aed",
}

# Thresholds
TEMP_THRESHOLDS = {
    "cold": 50,
    "warm": 75,
}

UTIL_THRESHOLDS = {
    "low": 50,
    "medium": 80,
}

# Window settings
WINDOW_TITLE = "VRAM Spy"
WINDOW_MIN_WIDTH = 1000
WINDOW_MIN_HEIGHT = 700

# Export settings
EXPORT_FORMATS = ["csv", "json"]
DEFAULT_EXPORT_FORMAT = "csv"

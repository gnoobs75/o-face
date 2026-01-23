"""Qt stylesheet definitions for PortMaster."""

MAIN_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #252526;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    color: #969696;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:selected {
    background-color: #252526;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #3c3c3c;
}

QTableWidget {
    background-color: #252526;
    alternate-background-color: #2d2d2d;
    gridline-color: #3c3c3c;
    border: none;
    selection-background-color: #094771;
    selection-color: #ffffff;
}

QTableWidget::item {
    padding: 6px;
    border: none;
}

QTableWidget::item:selected {
    background-color: #094771;
}

QHeaderView::section {
    background-color: #333333;
    color: #d4d4d4;
    padding: 8px;
    border: none;
    border-right: 1px solid #3c3c3c;
    border-bottom: 1px solid #3c3c3c;
    font-weight: bold;
}

QTreeWidget {
    background-color: #252526;
    alternate-background-color: #2d2d2d;
    border: none;
    selection-background-color: #094771;
}

QTreeWidget::item {
    padding: 4px;
}

QTreeWidget::item:selected {
    background-color: #094771;
}

QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #1177bb;
}

QPushButton:pressed {
    background-color: #094771;
}

QPushButton:disabled {
    background-color: #3c3c3c;
    color: #6c6c6c;
}

QPushButton#dangerButton {
    background-color: #c42b1c;
}

QPushButton#dangerButton:hover {
    background-color: #d63a2c;
}

QPushButton#secondaryButton {
    background-color: #3c3c3c;
}

QPushButton#secondaryButton:hover {
    background-color: #4c4c4c;
}

QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 6px 10px;
    color: #d4d4d4;
}

QLineEdit:focus {
    border-color: #0e639c;
}

QLabel {
    color: #d4d4d4;
}

QLabel#titleLabel {
    font-size: 16px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#subtitleLabel {
    font-size: 12px;
    color: #969696;
}

QLabel#conflictLabel {
    color: #f48771;
    font-weight: bold;
}

QLabel#successLabel {
    color: #89d185;
}

QLabel#warningLabel {
    color: #cca700;
}

QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #5a5a5a;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #6a6a6a;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #1e1e1e;
    height: 12px;
}

QScrollBar::handle:horizontal {
    background-color: #5a5a5a;
    min-width: 30px;
    border-radius: 6px;
    margin: 2px;
}

QStatusBar {
    background-color: #007acc;
    color: white;
}

QToolTip {
    background-color: #252526;
    color: #d4d4d4;
    border: 1px solid #454545;
    padding: 4px;
}

QMessageBox {
    background-color: #252526;
}

QMessageBox QLabel {
    color: #d4d4d4;
}

QMenu {
    background-color: #252526;
    border: 1px solid #454545;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
}

QMenu::item:selected {
    background-color: #094771;
}

QSplitter::handle {
    background-color: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 2px;
}

QSplitter::handle:vertical {
    height: 2px;
}

QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
    color: #d4d4d4;
}

QCheckBox {
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #555555;
    background-color: #3c3c3c;
}

QCheckBox::indicator:checked {
    background-color: #0e639c;
    border-color: #0e639c;
}

QCheckBox::indicator:hover {
    border-color: #0e639c;
}
"""

"""PyQt6 全局样式 - 朴素原生风格"""
from PyQt6.QtCore import Qt


def BASE_CSS() -> str:
    return """
    * {
        font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
        font-size: 13px;
        color: #333;
    }
    QWidget {
        background: #f5f5f5;
    }
    QLabel {
        color: #333;
    }
    QPushButton:disabled {
        opacity: 0.5;
    }
    QPushButton {
        background: #fff;
        color: #333;
        border: 1px solid #ccc;
        border-radius: 4px;
        padding: 6px 14px;
    }
    QPushButton:hover {
        background: #f0f0f0;
        border-color: #aaa;
    }
    QPushButton:pressed {
        background: #e5e5e5;
    }
    QPushButton.primary {
        background: #fff;
        color: #333;
        border: 1px solid #999;
    }
    QPushButton.primary:hover {
        background: #f5f5f5;
    }
    QPushButton.outline {
        background: #fff;
        color: #555;
        border: 1px solid #ccc;
    }
    QPushButton.outline:hover {
        background: #f8f8f8;
        border-color: #aaa;
    }
    QPushButton.ghost {
        background: transparent;
        color: #666;
        border: none;
    }
    QPushButton.ghost:hover {
        background: #e8e8e8;
    }
    QPushButton.danger {
        background: transparent;
        color: #c00;
        border: none;
    }
    QPushButton.danger:hover {
        background: #fee;
    }
    QPushButton.large {
        padding: 10px 20px;
        font-size: 14px;
    }
    QLineEdit, QTextEdit {
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 7px 10px;
        background: #fff;
        selection-background-color: #add;
    }
    QLineEdit:focus, QTextEdit:focus {
        border-color: #888;
    }
    QLineEdit[placeholder="true"], QTextEdit[placeholder="true"] {
        color: #999;
    }
    QComboBox {
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 6px 10px;
        background: #fff;
    }
    QComboBox:hover {
        border-color: #aaa;
    }
    QComboBox::drop-down {
        border: none;
        width: 18px;
    }
    QComboBox::down-arrow {
        image: none;
        border-left: 3px solid transparent;
        border-right: 3px solid transparent;
        border-top: 4px solid #888;
        margin-right: 6px;
    }
    QScrollBar:vertical {
        background: #f0f0f0;
        width: 8px;
        margin: 0;
    }
    QScrollBar::handle:vertical {
        background: #c0c0c0;
        border-radius: 4px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #a8a8a8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    QScrollBar:horizontal {
        background: #f0f0f0;
        height: 8px;
    }
    QScrollBar::handle:horizontal {
        background: #c0c0c0;
        border-radius: 4px;
        min-width: 30px;
    }
    QScrollBar::handle:horizontal:hover {
        background: #a8a8a8;
    }
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0;
    }
    QTableWidget {
        border: 1px solid #ddd;
        gridline-color: #e5e5e5;
        background: #fff;
        alternate-background-color: #fafafa;
    }
    QTableWidget::item {
        padding: 6px 8px;
        border-bottom: 1px solid #eee;
    }
    QTableWidget::item:selected {
        background: #e0e0e0;
        color: #333;
    }
    QHeaderView::section {
        background: #f0f0f0;
        color: #555;
        font-size: 12px;
        padding: 8px 10px;
        border: none;
        border-right: 1px solid #e0e0e0;
        border-bottom: 1px solid #ddd;
    }
    QTabWidget::pane {
        border: none;
        background: transparent;
    }
    QTabBar::tab {
        padding: 7px 18px;
        color: #666;
        background: transparent;
        margin-right: 2px;
        border: 1px solid transparent;
        border-bottom: none;
    }
    QTabBar::tab:selected {
        background: #fff;
        color: #333;
        border: 1px solid #ddd;
        border-bottom: 1px solid #fff;
    }
    QTabBar::tab:hover:!selected {
        background: #e8e8e8;
    }
    QCheckBox {
        spacing: 6px;
        color: #333;
    }
    QCheckBox::indicator {
        width: 14px;
        height: 14px;
        border-radius: 2px;
        border: 1px solid #aaa;
        background: #fff;
    }
    QCheckBox::indicator:checked {
        background: #555;
        border-color: #555;
    }
    QSpinBox {
        border: 1px solid #ccc;
        border-radius: 3px;
        padding: 6px 10px;
        background: #fff;
    }
    QMessageBox {
        background: #fff;
    }
    QDialog {
        background: #fff;
    }
    """


def SIDEBAR_CSS() -> str:
    return """
    QWidget#sidebar {
        background: #f8f8f8;
        border-right: 1px solid #ddd;
    }
    QWidget#logo_widget {
        padding: 16px 14px 12px;
    }
    QLabel#logo_name {
        font-size: 14px;
        font-weight: 600;
        color: #333;
    }
    QLabel#logo_sub {
        font-size: 11px;
        color: #888;
    }
    QLabel#nav_group_label {
        font-size: 11px;
        color: #888;
        padding: 12px 10px 3px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    QLabel#nav_badge {
        font-size: 10px;
        color: #888;
        background: #e5e5e5;
        border-radius: 3px;
        padding: 1px 5px;
    }
    QWidget#nav_item {
        padding: 7px 10px;
        border-radius: 4px;
        margin: 1px 0;
    }
    QWidget#nav_item:hover {
        background: #ebebeb;
    }
    QWidget#nav_item.active {
        background: #ddd;
    }
    QWidget#nav_item.disabled {
        opacity: 0.4;
    }
    QLabel#nav_icon {
        font-size: 14px;
        width: 16px;
    }
    QLabel#nav_text {
        font-size: 13px;
        color: #555;
    }
    QLabel#nav_text.active {
        color: #333;
        font-weight: 500;
    }
    QLabel#nav_sub_text {
        font-size: 12px;
        color: #888;
        padding-left: 6px;
    }
    """


def CARD_CSS() -> str:
    return """
    QFrame#card {
        background: #fff;
        border: 1px solid #ddd;
        border-radius: 4px;
    }
    """


def CHIP_CSS(status: str) -> str:
    colors = {
        "pending": ("#666", "#f0f0f0"),
        "processing": ("#555", "#e8e8e8"),
        "completed": ("#2a5", "#e8f8e5"),
        "failed": ("#c33", "#fee"),
    }
    fg, bg = colors.get(status, colors["pending"])
    return f"""
    QLabel#chip {{
        background: {bg};
        color: {fg};
        border-radius: 3px;
        padding: 2px 8px;
        font-size: 12px;
        border: 1px solid {bg};
    }}
    """


def DIALOG_CSS() -> str:
    return """
    QDialog {
        background: #fff;
        border-radius: 6px;
    }
    """

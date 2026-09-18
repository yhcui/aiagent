"""ContentForge Fluent Design 全局补充样式"""
from PyQt6.QtCore import Qt


def BASE_CSS() -> str:
    return """
    * {
        font-family: "Microsoft YaHei", "PingFang SC", "Segoe UI", sans-serif;
    }
    QWidget {
        background: transparent;
    }
    QPushButton {
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 13px;
    }
    QLineEdit, QTextEdit, PlainTextEdit {
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 13px;
    }
    QLineEdit:focus, QTextEdit:focus, PlainTextEdit:focus {
        border-color: #3370ff;
    }
    QScrollBar:vertical {
        width: 6px;
        background: transparent;
    }
    QScrollBar::handle:vertical {
        background: #c0c7cf;
        border-radius: 3px;
        min-height: 30px;
    }
    QScrollBar::handle:vertical:hover {
        background: #a8b0b8;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0;
    }
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
        background: none;
    }
    QToolTip {
        background: #1f2329;
        color: white;
        border: none;
        padding: 6px 10px;
        border-radius: 6px;
        font-size: 12px;
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

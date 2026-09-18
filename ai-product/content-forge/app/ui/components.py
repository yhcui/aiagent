"""
Common reusable UI components for ContentForge Fluent Design
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame

from qfluentwidgets import (
    CardWidget,
    CaptionLabel, TitleLabel,
    themeColor,
)


class StatusPill(CardWidget):
    """状态徽章（胶囊形，自适应深浅色）"""

    status_style = {
        "pending":    ("待处理", "#8a8f99"),
        "processing": ("生成中", None),          # None → use current theme color
        "completed":  ("已完成", "#16a34a"),
        "failed":     ("失败",   "#e5484d"),
    }

    @staticmethod
    def get_theme_color():
        return themeColor().name()

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        self.label = CaptionLabel()
        lay.addWidget(self.label)
        self.set_status(status)

    def set_status(self, status: str):
        text, color = self.status_style[status]
        color = color or self.get_theme_color()
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {color}; font-weight: 600; background: transparent; border: none;")
        self.setStyleSheet(
            f"StatusPill {{ background: {color}1a; border: 1px solid {color}55; border-radius: 12px; }}")


class PageHeader(QWidget):
    """页面标题区（统一样式）"""

    def __init__(self, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 10, 4, 10)
        lay.setSpacing(4)
        t = TitleLabel(title)
        s = CaptionLabel(subtitle)
        s.setTextColor("#8a8f99", "#9aa0a8")
        lay.addWidget(t)
        lay.addWidget(s)

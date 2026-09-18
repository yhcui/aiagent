"""
ContentForge
通用占位页（用于即将上线的功能）
"""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QWidget

from qfluentwidgets import (
    ElevatedCardWidget,
    SubtitleLabel, CaptionLabel,
    SmoothScrollArea as ScrollArea,
)

from app.ui.components import PageHeader


class ReservedPage(ScrollArea):
    def __init__(self, name: str, title: str, desc: str, parent=None):
        super().__init__(parent)
        self.setObjectName(name)
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.addWidget(PageHeader(title, desc))
        lay.addStretch()
        card = ElevatedCardWidget()
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 30, 20, 30)
        t = SubtitleLabel("🚧 即将上线")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d = CaptionLabel("此能力已在产品路线图中预留，UI 骨架已就位")
        d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d.setTextColor("#8a8f99", "#9aa0a8")
        cl.addWidget(t)
        cl.addWidget(d)
        lay.addWidget(card)
        lay.addStretch()

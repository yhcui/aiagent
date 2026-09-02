"""PyQt6 通用 UI 组件 - 朴素风格"""
from PyQt6.QtWidgets import QFrame, QLabel, QWidget, QHBoxLayout, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QPainter, QColor, QPalette


def card_frame(parent=None) -> QFrame:
    """创建卡片容器"""
    f = QFrame(parent)
    f.setObjectName("card")
    f.setStyleSheet("""
        QFrame#card {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
    """)
    return f


def chip(parent, text: str, status: str) -> QLabel:
    """状态标签 - 朴素风格"""
    colors = {
        "pending": ("#666", "#f0f0f0"),
        "processing": ("#555", "#e8e8e8"),
        "completed": ("#2a5", "#e8f8e5"),
        "failed": ("#c33", "#fee"),
    }
    fg, bg = colors.get(status, colors["pending"])
    lbl = QLabel(text, parent)  # 去掉 ● 前缀
    lbl.setObjectName("chip")
    lbl.setStyleSheet(f"""
        QLabel#chip {{
            background: {bg};
            color: {fg};
            border-radius: 3px;
            padding: 2px 8px;
            font-size: 12px;
            border: 1px solid {bg};
        }}
    """)
    return lbl


def section_title(text: str, parent=None) -> QLabel:
    """区块标题"""
    lbl = QLabel(text, parent)
    lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #333;")
    return lbl


def hint_text(text: str, parent=None) -> QLabel:
    """提示文字"""
    lbl = QLabel(text, parent)
    lbl.setStyleSheet("font-size: 12px; color: #999;")
    return lbl


def divider(parent=None) -> QFrame:
    """分隔线"""
    f = QFrame(parent)
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("border: none; border-top: 1px solid #e0e0e0; margin: 10px 0;")
    return f


def empty_placeholder(icon: str, title: str, desc: str, parent=None) -> QWidget:
    """空状态占位组件 - 简化版"""
    w = QWidget(parent)
    lay = QVBoxLayout(w)
    lay.setContentsMargins(0, 50, 0, 50)
    lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    # 使用纯文字提示，不使用大图标
    title_lbl = QLabel(title, w)
    title_lbl.setStyleSheet("font-size: 14px; color: #666; margin-top: 12px;")
    title_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    desc_lbl = QLabel(desc, w)
    desc_lbl.setStyleSheet("font-size: 12px; color: #999; margin-top: 6px;")
    desc_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
    desc_lbl.setWordWrap(True)
    lay.addWidget(title_lbl)
    lay.addWidget(desc_lbl)
    return w


class LoadingOverlay(QWidget):
    """加载遮罩 - 朴素风格"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.hide()
        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self._lbl = QLabel("处理中...", self)
        self._lbl.setStyleSheet("""
            background: rgba(255,255,255,0.95);
            border-radius: 4px;
            padding: 12px 24px;
            font-size: 13px;
            color: #555;
            border: 1px solid #ccc;
        """)
        lay.addWidget(self._lbl)

    def show_loading(self, text: str = "处理中..."):
        self._lbl.setText(text)
        self.show()

    def hide_loading(self):
        self.hide()

"""ContentForge 主窗口"""
import sys
import re
import json
import threading
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
    QTextEdit, QPushButton, QFrame, QScrollArea, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QCheckBox,
    QComboBox, QTabWidget, QMessageBox, QDialog, QTextBrowser,
    QSpinBox, QFileDialog, QSizePolicy, QSpacerItem,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

from loguru import logger
from app.models.task import Task, TaskStatus
from app.core.task_manager import TaskManager
from app.core.channel_manager import ChannelManager
from app.core.content_generator import ContentGenerator
from app.core.content_fetcher import ContentFetcher
from app.ui.styles import BASE_CSS
from app.ui.components import card_frame, chip, section_title, hint_text, divider, empty_placeholder, LoadingOverlay


class ResultDialog(QDialog):
    """生成结果查看对话框"""

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle(f"生成结果 · {task.channel}")
        self.resize(700, 560)
        self.setStyleSheet("""
            QDialog { background: white; border-radius: 14px; }
            .dlg-head {
                padding: 16px 20px;
                border-bottom: 1px solid #e8eaf0;
                font-size: 15px;
                font-weight: 600;
                color: #1f2329;
            }
            .dlg-foot {
                padding: 12px 20px;
                border-top: 1px solid #e8eaf0;
                background: #fafbfc;
                border-radius: 0 0 14px 14px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        # 头部
        head = QLabel("生成结果", self)
        head.setStyleSheet(".dlg-head { padding: 16px 20px; border-bottom: 1px solid #e8eaf0; font-size: 15px; font-weight: 600; }")
        head_w = QWidget()
        head_w.setStyleSheet(".dlg-head { padding: 16px 20px; border-bottom: 1px solid #e8eaf0; font-size: 15px; font-weight: 600; }")
        head_lay = QVBoxLayout(head_w)
        head_lay.setContentsMargins(16, 16, 16, 16)
        head_lay.addWidget(QLabel("生成结果 · " + ("微信公众号" if task.channel == "wechat" else task.channel)))
        lay.addWidget(head_w)

        # 内容区
        self.editor = QTextEdit(self)
        self.editor.setText(task.generated_content or "（无内容）")
        self.editor.setStyleSheet("""
            border: none;
            padding: 16px 20px;
            font-family: "Cascadia Code", "Fira Code", "Consolas", monospace;
            font-size: 13px;
            line-height: 1.8;
            color: #1f2329;
            background: #f7f8fa;
        """)
        lay.addWidget(self.editor)

        # 底部按钮
        foot_w = QWidget()
        foot_w.setStyleSheet(".dlg-foot { padding: 12px 20px; border-top: 1px solid #e8eaf0; background: #fafbfc; }")
        foot_lay = QHBoxLayout(foot_w)
        foot_lay.setContentsMargins(20, 12, 20, 12)
        foot_lay.addStretch()
        for label, style, cb in [
            ("📋 复制 Markdown", "outline", self._copy),
            ("⬇️ 导出 .md", "outline", self._export),
            ("🔄 重新生成", "primary", self._regenerate),
        ]:
            btn = QPushButton(label)
            cls = "outline" if style == "outline" else "primary"
            btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid #e8eaf0; border-radius: 8px; padding: 8px 16px;
                               font-size: 13px; color: #646a73; background: white; cursor: pointer; }}
                QPushButton:hover {{ border-color: #3370ff; color: #3370ff; }}
                QPushButton[cls="primary"] {{ background: #3370ff; color: white; border: none; }}
                QPushButton[cls="primary"]:hover {{ background: #2b5fe0; }}
            """)
            btn.clicked.connect(cb)
            foot_lay.addWidget(btn)
        lay.addWidget(foot_w)

    def _copy(self):
        cb = QApplication.instance().clipboard()
        cb.setText(self.editor.toPlainText())
        QMessageBox.information(self, "已复制", "Markdown 内容已复制到剪贴板")

    def _export(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出图文", f"图文_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", "Markdown (*.md)"
        )
        if path:
            Path(path).write_text(self.editor.toPlainText(), encoding="utf-8")
            QMessageBox.information(self, "已导出", f"文件已保存到：{path}")

    def _regenerate(self):
        self.accept()
        # 由父窗口处理重新生成


class MainWindow(QWidget):
    """ContentForge 主窗口"""

    # 信号：通知任务状态变更
    task_updated = pyqtSignal(str)  # task_id
    # 信号：显示错误弹框
    show_error = pyqtSignal(str)  # error_msg

    def __init__(self, config, storage):
        super().__init__()
        self.config = config
        self.storage = storage
        self.channel_manager = ChannelManager(storage)
        self.task_manager = TaskManager(storage, self.channel_manager, config)
        self.task_manager.add_listener(self._on_task_updated)
        self.current_channel = "wechat"
        self._opinion_candidates = []  # 当前候选观点

        self.setWindowTitle("内容锻造师 ContentForge v0.1")
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(BASE_CSS())

        self._setup_ui()
        self._load_tasks()
        self._mode = "url"  # 默认使用链接抓取模式

        # 连接信号
        self.show_error.connect(self._on_show_error)

    def _set_input_mode(self, mode: str):
        """设置输入模式：url=链接抓取, text=直接粘贴原文"""
        self.mode_url_btn.setObjectName("mode_active" if mode == "url" else "")
        self.mode_text_btn.setObjectName("mode_active" if mode == "text" else "")
        for btn in [self.mode_url_btn, self.mode_text_btn]:
            btn.setStyleSheet("""
                QPushButton#mode_active {
                    background: #555; border: 1px solid #555; border-radius: 4px;
                    padding: 7px 14px; font-size: 13px; color: white;
                }
                QPushButton {
                    background: transparent; border: 1px solid transparent; border-radius: 4px;
                    padding: 7px 14px; font-size: 13px; color: #666;
                }
                QPushButton:hover { background: #eee; }
            """)
        self.url_container.setVisible(mode == "url")
        self.text_container.setVisible(mode == "text")
        self._mode = mode

    # ==================== UI 初始化 ====================

    def _setup_ui(self):
        """搭建全部 UI"""
        main_lay = QHBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # 左侧导航
        self.sidebar = self._build_sidebar()
        main_lay.addWidget(self.sidebar)

        # 右侧主区域
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(0)

        # 顶部栏
        self.topbar = self._build_topbar()
        right_lay.addWidget(self.topbar)

        # 页面容器
        self.page_stack = QWidget()
        self.page_lay = QVBoxLayout(self.page_stack)
        self.page_lay.setContentsMargins(24, 24, 24, 24)
        self.page_lay.setSpacing(0)

        # 各页面
        self._page_wechat = self._build_page_wechat()
        self._page_toutiao = self._build_page_reserved("📰", "头条号", "生文 → 头条号渠道即将上线")
        self._page_history = self._build_page_history()
        self._page_api = self._build_page_api()
        self._page_channel = self._build_page_channel()
        self._page_general = self._build_page_general()

        for page in [self._page_wechat, self._page_toutiao, self._page_history,
                     self._page_api, self._page_channel, self._page_general]:
            self.page_lay.addWidget(page)

        right_lay.addWidget(self.page_stack)
        main_lay.addWidget(right, stretch=1)
        self._show_page("wechat")

    # ==================== 侧边导航 ====================

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setStyleSheet("""
            QWidget#sidebar {
                width: 220px;
                background: white;
                border-right: 1px solid #e8eaf0;
            }
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # Logo 区 - 朴素风格
        logo_w = QWidget()
        logo_w.setStyleSheet("padding: 16px 14px 12px; border-bottom: 1px solid #ddd; background: #fafafa;")
        logo_lay = QHBoxLayout(logo_w)
        logo_lay.setContentsMargins(14, 16, 14, 12)
        icon_lbl = QLabel("CF")
        icon_lbl.setStyleSheet("""
            width: 34px; height: 34px;
            background: #555;
            border-radius: 4px;
            color: white; font-size: 14px; font-weight: bold;
            text-align: center;
        """)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text_lay = QVBoxLayout()
        text_lay.setSpacing(1)
        name_lbl = QLabel("内容锻造师")
        name_lbl.setStyleSheet("font-size: 14px; font-weight: 500; color: #333;")
        sub_lbl = QLabel("ContentForge v0.1")
        sub_lbl.setStyleSheet("font-size: 11px; color: #888;")
        text_lay.addWidget(name_lbl)
        text_lay.addWidget(sub_lbl)
        logo_lay.addWidget(icon_lbl)
        logo_lay.addLayout(text_lay)
        lay.addWidget(logo_w)

        # 导航内容
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        nav_scroll.setStyleSheet("border: none; background: transparent;")
        nav_w = QWidget()
        nav_lay = QVBoxLayout(nav_w)
        nav_lay.setContentsMargins(10, 8, 10, 20)
        nav_lay.setSpacing(2)

        # 能力：生文
        nav_lay.addWidget(self._nav_group("内容生成"))
        nav_lay.addWidget(self._nav_item("wechat", "", "微信公众号", True, "page"))
        nav_lay.addWidget(self._nav_item("toutiao", "", "头条号", False, "page"))
        nav_lay.addWidget(divider())

        # 能力：生图（预留）
        nav_lay.addWidget(self._nav_group("图片生成", badge="预留"))
        nav_lay.addWidget(self._nav_item_disabled("", "配图生成"))
        nav_lay.addWidget(divider())

        # 能力：生视频（预留）
        nav_lay.addWidget(self._nav_group("视频生成", badge="预留"))
        nav_lay.addWidget(self._nav_item_disabled("", "视频生成"))
        nav_lay.addWidget(divider())

        # 其他
        nav_lay.addWidget(self._nav_group("记录"))
        nav_lay.addWidget(self._nav_item("history", "", "历史记录", False, "page"))
        nav_lay.addWidget(divider())
        nav_lay.addWidget(self._nav_group("设置"))
        nav_lay.addWidget(self._nav_item("api", "", "API 配置", False, "page"))
        nav_lay.addWidget(self._nav_item("channel", "", "渠道管理", False, "page"))
        nav_lay.addWidget(self._nav_item("general", "", "通用设置", False, "page"))

        nav_lay.addStretch()
        nav_scroll.setWidget(nav_w)
        lay.addWidget(nav_scroll, stretch=1)

        # 底部
        footer = QLabel("本地运行 · 数据不出本机")
        footer.setStyleSheet("padding: 10px 16px; font-size: 11px; color: #8f959e; border-top: 1px solid #e8eaf0;")
        lay.addWidget(footer)
        return sidebar

    def _nav_group(self, text: str, badge: str = None) -> QLabel:
        lbl = QLabel()
        lbl.setStyleSheet("font-size: 11px; color: #8f959e; padding: 12px 10px 4px;")
        if badge:
            lbl.setText(f'{text}  <span style="font-size:10px;background:#f2f3f5;color:#8f959e;padding:1px 6px;border-radius:4px;">{badge}</span>')
        else:
            lbl.setText(text)
        return lbl

    def _nav_item(self, page_id: str, icon: str, text: str, active: bool, kind: str) -> QWidget:
        w = QWidget()
        w.setObjectName("nav_item")
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        w.setProperty("page_id", page_id)
        w.setProperty("kind", kind)
        if active:
            w.setStyleSheet("""
                QWidget#nav_item {
                    padding: 8px 10px;
                    border-radius: 4px;
                    margin: 1px 0;
                    background: #e0e0e0;
                }
            """)
        else:
            w.setStyleSheet("""
                QWidget#nav_item {
                    padding: 8px 10px;
                    border-radius: 4px;
                    margin: 1px 0;
                }
                QWidget#nav_item:hover {
                    background: #e8e8e8;
                }
            """)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(9)
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 15px;")
        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(f"font-size: 13px; color: {'#3370ff' if active else '#646a73'}; font-weight: {'600' if active else '400'};")
        lay.addWidget(icon_lbl)
        lay.addWidget(text_lbl)
        if badge := "":
            badge_lbl = QLabel(badge)
            badge_lbl.setStyleSheet("font-size: 10px; background: #f2f3f5; color: #8f959e; padding: 1px 6px; border-radius: 4px;")
            lay.addWidget(badge_lbl)
        lay.addStretch()
        w.mousePressEvent = lambda e, pid=page_id, k=kind: self._on_nav_click(pid, k)
        return w

    def _nav_item_disabled(self, icon: str, text: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("padding: 8px 10px; opacity: 0.45;")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(9)
        lay.addWidget(QLabel(icon, styleSheet="font-size: 15px;"))
        lbl = QLabel(text, styleSheet="font-size: 13px; color: #c3c7cf;")
        lay.addWidget(lbl)
        lay.addStretch()
        return w

    def _on_nav_click(self, page_id: str, kind: str):
        if kind == "page":
            self._show_page(page_id)

    def _show_page(self, page_id: str):
        pages = {
            "wechat": self._page_wechat,
            "toutiao": self._page_toutiao,
            "history": self._page_history,
            "api": self._page_api,
            "channel": self._page_channel,
            "general": self._page_general,
        }
        crumbs = {
            "wechat": '生文 / <b style="color:#1f2329;">微信公众号</b>',
            "toutiao": '生文 / <b style="color:#1f2329;">头条号</b>',
            "history": '<b style="color:#1f2329;">历史记录</b>',
            "api": '设置 / <b style="color:#1f2329;">API 配置</b>',
            "channel": '设置 / <b style="color:#1f2329;">渠道管理</b>',
            "general": '设置 / <b style="color:#1f2329;">通用设置</b>',
        }
        self.crumb_lbl.setText(crumbs.get(page_id, ""))
        for pid, p in pages.items():
            p.setVisible(pid == page_id)

    # ==================== 顶部栏 ====================

    def _build_topbar(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("height: 54px; background: white; border-bottom: 1px solid #e8eaf0;")
        w.setFixedHeight(54)
        lay = QHBoxLayout(w)
        lay.setContentsMargins(24, 0, 24, 0)
        self.crumb_lbl = QLabel()
        self.crumb_lbl.setStyleSheet("font-size: 13px; color: #8f959e;")
        self.crumb_lbl.setText('生文 / <b style="color:#1f2329;">微信公众号</b>')
        lay.addWidget(self.crumb_lbl)
        lay.addStretch()
        api_status_btn = QPushButton("🔌 API 状态：未配置")
        api_status_btn.setObjectName("api_status")
        api_status_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #e8eaf0;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 12px;
                color: #646a73;
                background: white;
                cursor: pointer;
            }
            QPushButton:hover { border-color: #3370ff; color: #3370ff; }
        """)
        api_status_btn.clicked.connect(lambda: self._show_page("api"))
        self._api_status_btn = api_status_btn
        self._update_api_status()
        lay.addWidget(api_status_btn)
        return w

    def _update_api_status(self):
        cfg = self.config.get_api_config("text")
        if cfg.get("api_key"):
            self._api_status_btn.setText("🔌 API 状态：已配置")
            self._api_status_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #34c724;
                    border-radius: 8px;
                    padding: 7px 14px;
                    font-size: 12px;
                    color: #34c724;
                    background: #e8f8e5;
                    cursor: pointer;
                }
            """)
        else:
            self._api_status_btn.setText("🔌 API 状态：未配置")

    # ==================== 页面：微信公众号（生文主页面）====================

    def _build_page_wechat(self) -> QWidget:
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page.setStyleSheet("border: none; background: transparent;")
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setSpacing(16)
        inner_lay.setContentsMargins(0, 0, 0, 20)

        # Demo 提示 - 朴素风格
        banner = QLabel("ContentForge v0.1 开发版，所有功能均可操作体验")
        banner.setStyleSheet("""
            background: #f5f5f5;
            border: 1px solid #ddd;
            color: #666;
            border-radius: 4px;
            padding: 9px 14px;
            font-size: 12px;
        """)
        inner_lay.addWidget(banner)

        # ===== 卡片1：新增任务 =====
        c1 = card_frame()
        c1_lay = QVBoxLayout(c1)
        c1_lay.setContentsMargins(20, 20, 20, 20)
        c1_lay.setSpacing(12)

        c1_lay.addWidget(section_title("新增任务"))
        hint = hint_text("填入文章链接和你的观点，可连续添加多条，提交后批量生成")
        c1_lay.addWidget(hint)

        # 输入模式切换 - 朴素风格
        mode_row = QWidget()
        mode_row.setStyleSheet("background: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; padding: 2px;")
        mode_lay = QHBoxLayout(mode_row)
        mode_lay.setContentsMargins(4, 4, 4, 4)
        mode_lay.setSpacing(4)
        self.mode_url_btn = QPushButton("链接抓取")
        self.mode_url_btn.setObjectName("mode_active")
        self.mode_url_btn.setStyleSheet("""
            QPushButton#mode_active {
                background: #555; border: 1px solid #555; border-radius: 3px;
                padding: 6px 14px; font-size: 13px; color: white;
            }
            QPushButton {
                background: transparent; border: 1px solid transparent; border-radius: 3px;
                padding: 6px 14px; font-size: 13px; color: #666;
            }
            QPushButton:hover { background: #e5e5e5; }
        """)
        self.mode_text_btn = QPushButton("直接粘贴原文")
        self.mode_text_btn.setStyleSheet("""
            QPushButton#mode_active {
                background: #555; border: 1px solid #555; border-radius: 3px;
                padding: 6px 14px; font-size: 13px; color: white;
            }
            QPushButton {
                background: transparent; border: 1px solid transparent; border-radius: 3px;
                padding: 6px 14px; font-size: 13px; color: #666;
            }
            QPushButton:hover { background: #e5e5e5; }
        """)
        self.mode_url_btn.clicked.connect(lambda: self._set_input_mode("url"))
        self.mode_text_btn.clicked.connect(lambda: self._set_input_mode("text"))
        mode_lay.addWidget(self.mode_url_btn)
        mode_lay.addWidget(self.mode_text_btn)
        mode_lay.addStretch()
        c1_lay.addWidget(mode_row)

        # 链接输入区
        self.url_container = QWidget()
        url_container_lay = QVBoxLayout(self.url_container)
        url_container_lay.setContentsMargins(0, 8, 0, 0)
        url_container_lay.setSpacing(6)
        url_lbl = QLabel("文章链接 *")
        url_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://mp.weixin.qq.com/s/xxxxxx")
        self.url_input.setStyleSheet("""
            QLineEdit { border: 1px solid #e8eaf0; border-radius: 8px; padding: 9px 12px; font-size: 13px; background: white; }
            QLineEdit:focus { border-color: #3370ff; }
        """)
        url_container_lay.addWidget(url_lbl)
        url_container_lay.addWidget(self.url_input)
        c1_lay.addWidget(self.url_container)

        # 原文粘贴区（初始隐藏）
        self.text_container = QWidget()
        self.text_container.setVisible(False)
        text_container_lay = QVBoxLayout(self.text_container)
        text_container_lay.setContentsMargins(0, 8, 0, 0)
        text_container_lay.setSpacing(6)
        text_lbl = QLabel("文章原文 *")
        text_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.original_text_input = QTextEdit()
        self.original_text_input.setPlaceholderText("将无法抓取的文章原文直接粘贴到这里（如头条、公众号长图等）")
        self.original_text_input.setMinimumHeight(120)
        self.original_text_input.setMaximumHeight(200)
        self.original_text_input.setStyleSheet("""
            QTextEdit { border: 1px solid #e8eaf0; border-radius: 8px; padding: 9px 12px; font-size: 13px; background: white; }
            QTextEdit:focus { border-color: #3370ff; }
        """)
        text_container_lay.addWidget(text_lbl)
        text_container_lay.addWidget(self.original_text_input)
        text_hint = hint_text("适用于：链接无法自动抓取时（如今日头条、部分付费内容等）")
        text_container_lay.addWidget(text_hint)
        c1_lay.addWidget(self.text_container)

        # 观点输入
        op_lbl = QLabel("我的观点 / 看法 *")
        op_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        self.opinion_input = QTextEdit()
        self.opinion_input.setPlaceholderText("写下你对这篇文章的看法、补充或反驳，AI 会把它融入生成的图文（建议 100-500 字）")
        self.opinion_input.setMinimumHeight(100)
        self.opinion_input.setMaximumHeight(160)
        self.opinion_input.setStyleSheet("""
            QTextEdit { border: 1px solid #e8eaf0; border-radius: 8px; padding: 9px 12px; font-size: 13px; background: white; }
            QTextEdit:focus { border-color: #3370ff; }
        """)
        opinion_row = QWidget()
        opinion_row_lay = QHBoxLayout(opinion_row)
        opinion_row_lay.setContentsMargins(0, 0, 0, 0)
        opinion_row_lay.addWidget(op_lbl)
        opinion_row_lay.addStretch()
        self.ai_opinion_btn = QPushButton("✨ AI 生成观点")
        self.ai_opinion_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #e8eaf0;
                border-radius: 8px;
                padding: 7px 14px;
                font-size: 13px;
                color: #646a73;
                background: white;
                cursor: pointer;
            }
            QPushButton:hover { border-color: #3370ff; color: #3370ff; }
        """)
        self.ai_opinion_btn.clicked.connect(self._on_ai_opinion)
        opinion_row_lay.addWidget(self.ai_opinion_btn)
        c1_lay.addWidget(opinion_row)
        c1_lay.addWidget(self.opinion_input)
        c1_lay.addWidget(hint_text("建议 100–500 字；没思路可点「✨ AI 生成观点」，由 AI 基于原文生成候选观点"))

        # AI 候选观点区（初始隐藏）
        self.opinion_panel = QWidget()
        self.opinion_panel.setStyleSheet("""
            background: #f8faff;
            border: 1px solid #d6e0ff;
            border-radius: 10px;
            padding: 14px 16px;
        """)
        self.opinion_panel.setVisible(False)
        op_panel_lay = QVBoxLayout(self.opinion_panel)
        op_panel_lay.setSpacing(8)

        op_head = QWidget()
        op_head_lay = QHBoxLayout(op_head)
        op_head_lay.setContentsMargins(0, 0, 0, 0)
        op_head_lbl = QLabel("✨ AI 基于原文生成了候选观点，勾选一个或多个，每个观点将各生成一篇图文")
        op_head_lbl.setStyleSheet("font-size: 13px; font-weight: 600; color: #3b5bd9;")
        self.opinion_close_btn = QPushButton("收起 ✕")
        self.opinion_close_btn.setStyleSheet("background: transparent; border: none; color: #8f959e; cursor: pointer; font-size: 12px;")
        self.opinion_close_btn.clicked.connect(lambda: self.opinion_panel.setVisible(False))
        op_head_lay.addWidget(op_head_lbl)
        op_head_lay.addWidget(self.opinion_close_btn)
        op_panel_lay.addWidget(op_head)

        self.opinion_loading = QLabel("⏳ 正在抓取原文并生成观点...")
        self.opinion_loading.setStyleSheet("font-size: 13px; color: #8f959e; padding: 14px 0; text-align: center;")
        self.opinion_loading.setVisible(False)
        op_panel_lay.addWidget(self.opinion_loading)

        self.opinion_list_w = QWidget()
        self.opinion_list_lay = QVBoxLayout(self.opinion_list_w)
        self.opinion_list_lay.setSpacing(6)
        self.opinion_list_lay.setContentsMargins(0, 0, 0, 0)
        self.opinion_list_w.setVisible(False)
        op_panel_lay.addWidget(self.opinion_list_w)

        op_foot = QWidget()
        op_foot_lay = QHBoxLayout(op_foot)
        op_foot_lay.setContentsMargins(0, 6, 0, 0)
        self.sel_count_lbl = QLabel("已选 0 个观点")
        self.sel_count_lbl.setStyleSheet("font-size: 12px; color: #8f959e;")
        self.add_selected_btn = QPushButton("＋ 添加所选到任务列表")
        self.add_selected_btn.setStyleSheet("""
            QPushButton { background: #3370ff; color: white; border-radius: 8px; padding: 8px 18px; font-size: 13px; cursor: pointer; }
            QPushButton:hover { background: #2b5fe0; }
        """)
        self.add_selected_btn.clicked.connect(self._on_add_selected_opinions)
        op_foot_lay.addWidget(self.sel_count_lbl)
        op_foot_lay.addStretch()
        op_foot_lay.addWidget(self.add_selected_btn)
        self.opinion_foot = op_foot
        self.opinion_foot.setVisible(False)
        op_panel_lay.addWidget(self.opinion_foot)

        c1_lay.addWidget(self.opinion_panel)

        # 添加按钮
        add_btn_row = QWidget()
        add_btn_row_lay = QHBoxLayout(add_btn_row)
        add_btn_row_lay.setContentsMargins(0, 0, 0, 0)
        add_btn_row_lay.addStretch()
        add_btn = QPushButton("＋ 添加到任务列表")
        add_btn.setStyleSheet("""
            QPushButton {
                border: 1px solid #e8eaf0;
                border-radius: 8px;
                padding: 9px 18px;
                font-size: 13px;
                color: #646a73;
                background: white;
                cursor: pointer;
            }
            QPushButton:hover { border-color: #3370ff; color: #3370ff; }
        """)
        add_btn.clicked.connect(self._on_add_task)
        add_btn_row_lay.addWidget(add_btn)
        c1_lay.addWidget(add_btn_row)

        inner_lay.addWidget(c1)

        # ===== 卡片2：任务列表 =====
        c2 = card_frame()
        c2_lay = QVBoxLayout(c2)
        c2_lay.setContentsMargins(20, 20, 20, 20)
        c2_lay.setSpacing(12)

        # 工具栏
        toolbar = QWidget()
        toolbar_lay = QHBoxLayout(toolbar)
        toolbar_lay.setContentsMargins(0, 0, 0, 0)
        left_info = QVBoxLayout()
        left_info.setSpacing(2)
        left_info.addWidget(section_title("任务列表"))
        self.task_count_lbl = hint_text("共 0 条")
        left_info.addWidget(self.task_count_lbl)
        toolbar_lay.addLayout(left_info)
        toolbar_lay.addStretch()
        self.start_gen_btn = QPushButton("🚀 开始生成（0）")
        self.start_gen_btn.setStyleSheet("""
            QPushButton {
                background: #3370ff;
                color: white;
                border-radius: 8px;
                padding: 10px 24px;
                font-size: 14px;
                font-weight: 600;
                cursor: pointer;
            }
            QPushButton:hover { background: #2b5fe0; }
            QPushButton:disabled { background: #c0c7cf; cursor: not-allowed; }
        """)
        self.start_gen_btn.clicked.connect(self._on_start_generation)
        toolbar_lay.addWidget(self.start_gen_btn)
        c2_lay.addWidget(toolbar)

        # 任务表格
        self.task_table = QTableWidget()
        self.task_table.setObjectName("task_table")
        self.task_table.setColumnCount(4)
        self.task_table.setHorizontalHeaderLabels(["文章链接", "我的观点", "状态", "操作"])
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.task_table.setColumnWidth(0, 260)
        self.task_table.setColumnWidth(2, 100)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setShowGrid(False)
        self.task_table.setStyleSheet("""
            QTableWidget {
                border: none;
                background: white;
                gridline-color: #f2f3f5;
                font-size: 13px;
            }
            QTableWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #f2f3f5;
            }
            QTableWidget::item:selected {
                background: #eef3ff;
            }
            QHeaderView::section {
                background: #fafbfc;
                color: #8f959e;
                font-size: 12px;
                font-weight: 500;
                padding: 8px 12px;
                border: none;
                border-bottom: 1px solid #e8eaf0;
            }
        """)
        self.task_table.setMinimumHeight(200)
        c2_lay.addWidget(self.task_table)

        self._update_task_table()
        inner_lay.addWidget(c2)

        page.setWidget(inner)
        return page

    # ==================== AI 生成观点 ====================

    def _on_ai_opinion(self):
        """点击「AI 生成观点」"""
        # 支持两种输入模式
        if self._mode == "text":
            # 直接粘贴原文模式
            content = self.original_text_input.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "请先粘贴原文", "请先将文章原文粘贴到上面的文本框中")
                return
            url_hint = "(直接粘贴原文)"
        else:
            # 链接抓取模式
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "请先填写链接", "请先在「文章链接」中填入要分析的文章 URL")
                return
            url_hint = url
            content = None  # 稍后在线程中抓取

        self.opinion_panel.setVisible(True)
        self.opinion_loading.setVisible(True)
        self.opinion_list_w.setVisible(False)
        self.opinion_foot.setVisible(False)
        self._opinion_candidates = []
        # 清空已有的选项 widget
        while self.opinion_list_lay.count():
            w = self.opinion_list_lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.opinion_input.clear()
        self.opinion_input.setPlaceholderText("（已选择 AI 生成的候选观点，可直接添加到任务列表）")
        self.opinion_input.setEnabled(False)
        self.ai_opinion_btn.setEnabled(False)

        def worker():
            try:
                # 抓取原文（仅URL模式需要）
                article_content = content
                if article_content is None:
                    fetcher = ContentFetcher()
                    article_content = fetcher.fetch(url_hint)
                    if not article_content:
                        self._opinion_error("无法抓取文章内容，请检查链接是否正确或稍后重试")
                        return
                # 生成观点
                generator = ContentGenerator(self.config)
                opinions = generator.generate_opinions(article_content, "wechat", count=5)
                if not opinions:
                    self._opinion_error("AI 生成观点失败，请检查 API 配置或网络连接")
                    return
                self._show_opinions(opinions)
            except ValueError as e:
                # 业务异常，通过信号显示给用户
                logger.warning(f"AI 生成观点业务错误：{e}")
                self.show_error.emit(str(e))
            except Exception as e:
                logger.error(f"AI 生成观点异常：{e}")
                self.show_error.emit("发生错误，请查看日志了解详情")

        threading.Thread(target=worker, daemon=True).start()

    def _opinion_error(self, msg: str):
        self.opinion_loading.setVisible(False)
        self.show_error.emit(msg)
        self.ai_opinion_btn.setEnabled(True)
        self.opinion_input.setEnabled(True)
        self.opinion_input.setPlaceholderText("写下你对这篇文章的看法、补充或反驳...")

    def _on_show_error(self, msg: str):
        QMessageBox.warning(self, "AI 生成观点失败", msg)

    def _show_error_dialog(self, msg: str):
        QMessageBox.warning(self, "AI 生成观点失败", msg)

    def _do_show_opinions(self, opinions: list):
        self._opinion_candidates = opinions
        self.opinion_loading.setVisible(False)
        self.opinion_list_w.setVisible(True)
        self.opinion_foot.setVisible(True)
        self.ai_opinion_btn.setEnabled(True)
        self.ai_opinion_btn.setText("✨ 重新生成观点")
        self._selected_opinions = []

        for i, op in enumerate(opinions):
            tag = op.get("tag", f"观点{i + 1}")
            text = op.get("opinion", "")
            item_w = QWidget()
            item_w.setCursor(Qt.CursorShape.PointingHandCursor)
            item_w.setStyleSheet("""
                QWidget {
                    background: white;
                    border: 1px solid #e8eaf0;
                    border-radius: 8px;
                    padding: 10px 12px;
                }
                QWidget:hover { border-color: #3370ff; }
                QWidget.selected { border-color: #3370ff; background: #eef3ff; }
            """)
            item_w.setObjectName(f"opinion_item_{i}")
            item_lay = QHBoxLayout(item_w)
            item_lay.setContentsMargins(10, 10, 10, 10)
            item_lay.setSpacing(10)
            tag_lbl = QLabel(tag)
            tag_lbl.setStyleSheet("""
                background: #f2f3f5;
                color: #8f959e;
                border-radius: 10px;
                padding: 2px 8px;
                font-size: 11px;
                flex-shrink: 0;
            """)
            text_lbl = QLabel(text)
            text_lbl.setWordWrap(True)
            text_lbl.setStyleSheet("font-size: 13px; color: #646a73; line-height: 1.7;")
            check_lbl = QLabel("")
            check_lbl.setStyleSheet("font-size: 14px; color: #3370ff; font-weight: bold; flex-shrink: 0;")
            check_lbl.setFixedWidth(20)
            item_lay.addWidget(tag_lbl)
            item_lay.addWidget(text_lbl)
            item_lay.addWidget(check_lbl)

            def make_click(idx=i, iw=item_w, tl=tag_lbl, cl=check_lbl):
                def click(e):
                    if idx not in self._selected_opinions:
                        self._selected_opinions.append(idx)
                        iw.setStyleSheet("QWidget { background: #eef3ff; border: 1px solid #3370ff; border-radius: 8px; padding: 10px 12px; }")
                        tag_lbl.setStyleSheet("background: #3370ff; color: white; border-radius: 10px; padding: 2px 8px; font-size: 11px; flex-shrink: 0;")
                        cl.setText("✓")
                    else:
                        self._selected_opinions.remove(idx)
                        iw.setStyleSheet("QWidget { background: white; border: 1px solid #e8eaf0; border-radius: 8px; padding: 10px 12px; }")
                        tag_lbl.setStyleSheet("background: #f2f3f5; color: #8f959e; border-radius: 10px; padding: 2px 8px; font-size: 11px; flex-shrink: 0;")
                        cl.setText("")
                    n = len(self._selected_opinions)
                    self.sel_count_lbl.setText(f"已选 {n} 个观点（将生成 {n} 篇图文）")
                return click
            item_w.mousePressEvent = make_click()

            self.opinion_list_lay.addWidget(item_w)

    def _on_add_selected_opinions(self):
        if not self._selected_opinions:
            QMessageBox.information(self, "请先选择", "请先勾选至少一个候选观点")
            return
        url = self.url_input.text().strip() or "(未填写链接)"
        new_tasks = []
        for idx in self._selected_opinions:
            op = self._opinion_candidates[idx]
            task = self.task_manager.add_task(url, op.get("opinion", ""), "wechat")
            new_tasks.append(task)
        self._update_task_table()
        self.opinion_panel.setVisible(False)
        self.opinion_input.setEnabled(True)
        self.opinion_input.clear()
        self.opinion_input.setPlaceholderText("写下你对这篇文章的看法...")
        self.ai_opinion_btn.setText("✨ AI 生成观点")
        self._selected_opinions = []
        QMessageBox.information(
            self, "已添加",
            f"已添加 {len(new_tasks)} 个任务（同一链接 × {len(new_tasks)} 个观点 = {len(new_tasks)} 篇图文）\n\n点击「🚀 开始生成」提交批量处理"
        )

    # ==================== 任务管理 ====================

    def _on_add_task(self):
        opinion = self.opinion_input.toPlainText().strip()
        if not opinion:
            QMessageBox.warning(self, "请填写观点", "请输入你的观点或使用「AI 生成观点」")
            return

        if self._mode == "text":
            # 直接粘贴原文模式
            original_content = self.original_text_input.toPlainText().strip()
            if not original_content:
                QMessageBox.warning(self, "请粘贴原文", "请将文章原文粘贴到上面的文本框中")
                return
            url = "(直接粘贴原文)"
            task = self.task_manager.add_task(url, opinion, self.current_channel, original_content)
            self.original_text_input.clear()
        else:
            # 链接抓取模式
            url = self.url_input.text().strip()
            if not url:
                url = "(未填写链接)"
            task = self.task_manager.add_task(url, opinion, self.current_channel)
            self.url_input.clear()

        self._update_task_table()
        self.opinion_input.clear()
        if not self.opinion_input.isEnabled():
            self.opinion_input.setEnabled(True)
            self.opinion_input.setPlaceholderText("写下你对这篇文章的看法...")

    def _on_start_generation(self):
        pending = [t for t in self.task_manager.tasks if t.status == TaskStatus.PENDING]
        if not pending:
            QMessageBox.information(self, "无待处理任务", "当前没有待处理的任务")
            return
        cfg = self.config.get_api_config("text")
        if not cfg.get("api_key"):
            QMessageBox.warning(
                self, "请先配置 API",
                "请先在「设置 → API 配置」中配置 AI 服务商信息",
            )
            self._show_page("api")
            return
        self.start_gen_btn.setEnabled(False)
        self.start_gen_btn.setText("⏳ 生成中...")
        self.task_manager.start_generation()

    def _on_task_updated(self, task: Task):
        QTimer.singleShot(0, lambda: self._refresh_task_row(task))

    def _refresh_task_row(self, task: Task):
        self._update_task_table()
        # 如果全部完成
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            pending = [t for t in self.task_manager.tasks if t.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)]
            if not pending:
                self.start_gen_btn.setEnabled(True)
                self.start_gen_btn.setText(f"🚀 开始生成（{len(self.task_manager.tasks)}）")

    def _update_task_table(self):
        tasks = self.task_manager.tasks
        self.task_table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            # 链接
            url_item = QTableWidgetItem(task.url)
            url_item.setForeground(QColor("#3370ff"))
            url_item.setToolTip(task.url)
            self.task_table.setItem(row, 0, url_item)
            # 观点
            op_item = QTableWidgetItem(task.user_opinion)
            op_item.setForeground(QColor("#646a73"))
            op_item.setToolTip(task.user_opinion)
            self.task_table.setItem(row, 1, op_item)
            # 状态
            status_item = QTableWidgetItem()
            status_map = {
                TaskStatus.PENDING: "待处理",
                TaskStatus.PROCESSING: "生成中",
                TaskStatus.COMPLETED: "已完成",
                TaskStatus.FAILED: "失败",
            }
            status_item.setText(status_map.get(task.status, str(task.status)))
            status_colors = {
                TaskStatus.PENDING: ("#8f959e", "#f2f3f5"),
                TaskStatus.PROCESSING: ("#3370ff", "#eef3ff"),
                TaskStatus.COMPLETED: ("#34c724", "#e8f8e5"),
                TaskStatus.FAILED: ("#f54a45", "#feeceb"),
            }
            fg, bg = status_colors.get(task.status, ("#8f959e", "#f2f3f5"))
            status_item.setBackground(QColor(bg))
            status_item.setForeground(QColor(fg))
            self.task_table.setItem(row, 2, status_item)
            # 操作
            ops_w = QWidget()
            ops_lay = QHBoxLayout(ops_lay := QHBoxLayout())
            ops_lay.setContentsMargins(0, 0, 0, 0)
            ops_lay.setSpacing(6)
            if task.status == TaskStatus.COMPLETED:
                for label, cb in [("查看", lambda t=task: self._show_result(t)),
                                   ("复制", lambda t=task: self._copy_result(t))]:
                    btn = QPushButton(label)
                    btn.setStyleSheet("background: transparent; color: #3370ff; border: none; cursor: pointer; font-size: 13px; padding: 2px 6px;")
                    btn.clicked.connect(cb)
                    ops_lay.addWidget(btn)
            elif task.status == TaskStatus.FAILED:
                for label, cb in [("原因", lambda t=task: self._show_error(t)),
                                   ("重试", lambda t=task: self._on_retry(t))]:
                    btn = QPushButton(label)
                    btn.setStyleSheet("background: transparent; color: #646a73; border: none; cursor: pointer; font-size: 13px; padding: 2px 6px;")
                    btn.clicked.connect(cb)
                    ops_lay.addWidget(btn)
            elif task.status == TaskStatus.PROCESSING:
                lbl = QLabel("处理中…")
                lbl.setStyleSheet("color: #3370ff; font-size: 12px;")
                ops_lay.addWidget(lbl)
            else:
                rm_btn = QPushButton("移除")
                rm_btn.setStyleSheet("background: transparent; color: #f54a45; border: none; cursor: pointer; font-size: 13px; padding: 2px 6px;")
                rm_btn.clicked.connect(lambda _, tid=task.id: self._on_remove_task(tid))
                ops_lay.addWidget(rm_btn)
            ops_lay.addStretch()
            self.task_table.setCellWidget(row, 3, ops_w)

        # 更新计数
        counts = {"pending": 0, "processing": 0, "completed": 0, "failed": 0}
        for t in tasks:
            counts[t.status.value] = counts.get(t.status.value, 0) + 1
        parts = [f"共 {len(tasks)} 条：{counts['completed']} 已完成 · {counts['processing']} 生成中 · {counts['pending']} 待处理"]
        if counts["failed"]:
            parts.append(f"· {counts['failed']} 失败")
        self.task_count_lbl.setText("".join(parts))
        pending_count = len([t for t in tasks if t.status == TaskStatus.PENDING])
        self.start_gen_btn.setText(f"🚀 开始生成（{pending_count}）")
        self.start_gen_btn.setEnabled(pending_count > 0)

    def _show_result(self, task: Task):
        dlg = ResultDialog(task, self)
        dlg.finished.connect(lambda r: self._on_result_dialog_close(r, task))
        dlg.exec()

    def _on_result_dialog_close(self, r, task: Task):
        if r == QDialog.DialogCode.Accepted:
            pass  # 重新生成由对话框处理

    def _copy_result(self, task: Task):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(task.generated_content)
        QMessageBox.information(self, "已复制", "图文内容已复制到剪贴板")

    def _show_error(self, task: Task):
        QMessageBox.information(self, "失败原因", task.error_message or "未知错误")

    def _on_retry(self, task: Task):
        self.task_manager.regenerate(task.id)
        self._update_task_table()

    def _on_remove_task(self, task_id: str):
        self.task_manager.remove_task(task_id)
        self._update_task_table()

    def _load_tasks(self):
        self._update_task_table()

    # ==================== 页面：预留 ====================

    def _build_page_reserved(self, icon: str, title: str, desc: str) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(empty_placeholder(icon, f"{title} · 即将上线", desc))
        return page

    # ==================== 页面：历史记录 ====================

    def _build_page_history(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)

        c = card_frame()
        c_lay = QVBoxLayout(c)
        c_lay.setContentsMargins(20, 20, 20, 20)
        c_lay.setSpacing(12)

        toolbar = QWidget()
        toolbar_lay = QHBoxLayout(toolbar)
        toolbar_lay.setContentsMargins(0, 0, 0, 0)
        toolbar_lay.addWidget(section_title("历史记录"))
        toolbar_lay.addStretch()
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("🔍 搜索标题 / 关键词")
        self.history_search.setFixedWidth(220)
        self.history_search.setStyleSheet("""
            QLineEdit { border: 1px solid #e8eaf0; border-radius: 8px; padding: 7px 12px; font-size: 13px; background: white; }
            QLineEdit:focus { border-color: #3370ff; }
        """)
        self.history_channel_filter = QComboBox()
        self.history_channel_filter.addItems(["全部渠道", "微信公众号"])
        self.history_channel_filter.setFixedWidth(130)
        self.history_channel_filter.setStyleSheet("""
            QComboBox { border: 1px solid #e8eaf0; border-radius: 8px; padding: 7px 12px; background: white; }
        """)
        toolbar_lay.addWidget(self.history_search)
        toolbar_lay.addWidget(self.history_channel_filter)
        c_lay.addWidget(toolbar)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(["生成时间", "标题（观点摘要）", "渠道", "状态", "操作"])
        self.history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history_table.setShowGrid(False)
        self.history_table.setStyleSheet("""
            QTableWidget { border: none; background: white; gridline-color: #f2f3f5; font-size: 13px; }
            QTableWidget::item { padding: 10px 8px; border-bottom: 1px solid #f2f3f5; }
            QHeaderView::section { background: #fafbfc; color: #8f959e; font-size: 12px; padding: 8px 12px; border: none; border-bottom: 1px solid #e8eaf0; }
        """)
        self.history_table.setMinimumHeight(300)
        self._load_history()
        c_lay.addWidget(self.history_table)
        lay.addWidget(c)
        return page

    def _load_history(self):
        tasks = self.task_manager.tasks
        completed = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        self.history_table.setRowCount(len(completed))
        for row, t in enumerate(completed):
            self.history_table.setItem(row, 0, QTableWidgetItem(
                t.completed_at.strftime("%Y-%m-%d %H:%M") if t.completed_at else t.created_at.strftime("%Y-%m-%d %H:%M")))
            title = t.generated_content.split("\n")[0][:50] if t.generated_content else "(无标题)"
            self.history_table.setItem(row, 1, QTableWidgetItem(title))
            self.history_table.setItem(row, 2, QTableWidgetItem("微信公众号"))
            status_item = QTableWidgetItem("已完成")
            status_item.setBackground(QColor("#e8f8e5"))
            status_item.setForeground(QColor("#34c724"))
            self.history_table.setItem(row, 2, status_item)
            status_item2 = QTableWidgetItem("已完成")
            status_item2.setBackground(QColor("#e8f8e5"))
            status_item2.setForeground(QColor("#34c724"))
            self.history_table.setItem(row, 3, status_item2)
            view_btn = QPushButton("查看")
            view_btn.setStyleSheet("background: transparent; color: #3370ff; border: none; cursor: pointer;")
            view_btn.clicked.connect(lambda _, task=t: self._show_result(task))
            self.history_table.setCellWidget(row, 4, view_btn)

    # ==================== 页面：API 配置 ====================

    def _build_page_api(self) -> QWidget:
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page.setStyleSheet("border: none; background: transparent;")
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 20)
        inner_lay.setSpacing(16)

        c = card_frame()
        c_lay = QVBoxLayout(c)
        c_lay.setContentsMargins(20, 20, 20, 20)
        c_lay.setSpacing(12)

        c_lay.addWidget(section_title("API 配置"))
        c_lay.addWidget(hint_text("按「能力类型」分别配置；每个能力有一套全局默认配置，单个渠道可开启专属配置覆盖。API Key 加密存储在本地，不上传任何服务器。"))

        # 能力类型 Tab
        self.api_tabs = QTabWidget()
        self.api_tabs.setStyleSheet("""
            QTabWidget::pane { border: none; background: transparent; }
            QTabBar::tab { padding: 8px 22px; border-radius: 8px; color: #646a73; background: transparent; margin-right: 4px; }
            QTabBar::tab:selected { background: white; color: #3370ff; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
            QTabBar::tab:hover:!selected { background: #f2f4f9; }
        """)
        self.api_tabs.addTab(self._build_api_tab("text"), "📝 生文")
        self.api_tabs.addTab(self._build_api_tab("image", reserved=True), "🖼️ 生图")
        self.api_tabs.addTab(self._build_api_tab("video", reserved=True), "🎬 生视频")
        c_lay.addWidget(self.api_tabs)
        inner_lay.addWidget(c)
        page.setWidget(inner)
        return page

    def _build_api_tab(self, ability: str, reserved: bool = False) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        if reserved:
            placeholder = empty_placeholder(
                "🎨" if ability == "image" else "🎥",
                f"{'生图' if ability == 'image' else '生视频'}能力 · 预留",
                "界面已预留，功能上线前可提前配置 api_key / base_url / model_id"
            )
            lay.addWidget(placeholder)
            return w

        cfg = self.config.get_api_config(ability)
        lay.addWidget(QLabel("全局默认配置（生文能力下所有渠道共用）"))
        lay.addWidget(hint_text("凡兼容 OpenAI 协议的服务商均可填写（硅基流动 / DeepSeek / 智谱 / OpenAI 等）"))

        base_url_w = self._api_input("接口地址 base_url", cfg.get("base_url", ""), placeholder="https://api.siliconflow.cn/v1")
        api_key_w = self._api_input("API Key", cfg.get("api_key", ""), is_password=True)
        model_id_w = self._api_input("模型唯一标识 model_id", cfg.get("model_id", ""), placeholder="Qwen/Qwen2.5-72B-Instruct")
        for wdg in [base_url_w, api_key_w, model_id_w]:
            lay.addWidget(wdg)

        lay.addWidget(divider())
        lay.addWidget(QLabel("渠道专属配置（覆盖全局默认，可选）"))
        lay.addWidget(hint_text("开启后，该渠道生成时使用专属配置而非全局默认"))

        # 微信公众号渠道覆盖
        wechat_override = self._build_override_section("wechat", "💬", "微信公众号", ability)
        lay.addWidget(wechat_override)

        # 头条号渠道覆盖
        toutiao_override = self._build_override_section("toutiao", "📰", "头条号", ability, disabled=True)
        lay.addWidget(toutiao_override)

        # 保存按钮
        btn_row = QWidget()
        btn_row_lay = QHBoxLayout(btn_row)
        btn_row_lay.setContentsMargins(0, 0, 0, 0)
        btn_row_lay.addStretch()
        test_btn = QPushButton("🔌 测试连接")
        test_btn.setStyleSheet("border: 1px solid #e8eaf0; border-radius: 8px; padding: 8px 16px; color: #646a73; cursor: pointer;")
        test_btn.clicked.connect(lambda: self._test_connection(ability, base_url_w, api_key_w, model_id_w))
        save_btn = QPushButton("保存配置")
        save_btn.setStyleSheet("background: #3370ff; color: white; border-radius: 8px; padding: 8px 18px; cursor: pointer;")
        save_btn.clicked.connect(lambda: self._save_api_config(ability, base_url_w, api_key_w, model_id_w))
        btn_row_lay.addWidget(test_btn)
        btn_row_lay.addWidget(save_btn)
        lay.addWidget(btn_row)
        return w

    def _api_input(self, label: str, value: str, placeholder: str = "", is_password: bool = False) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        inp = QLineEdit()
        inp.setPlaceholderText(placeholder)
        inp.setText(value)
        inp.setEchoMode(QLineEdit.EchoMode.Password) if is_password else None
        inp.setStyleSheet("""
            QLineEdit { border: 1px solid #e8eaf0; border-radius: 8px; padding: 9px 12px; font-size: 13px; background: white; }
            QLineEdit:focus { border-color: #3370ff; }
        """)
        inp.setObjectName(label)
        lay.addWidget(lbl)
        lay.addWidget(inp)
        return w

    def _build_override_section(self, channel: str, icon: str, name: str, ability: str, disabled: bool = False) -> QWidget:
        w = QWidget()
        w.setStyleSheet("border: 1px solid #e8eaf0; border-radius: 10px; padding: 14px 16px;")
        w.setObjectName(f"override_{channel}")
        lay = QVBoxLayout(w)
        lay.setSpacing(8)
        head = QWidget()
        head_lay = QHBoxLayout(head)
        head_lay.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel(f"{icon} {name}")
        icon_lbl.setStyleSheet("font-size: 13px; font-weight: 600;")
        note_lbl = QLabel("当前：使用全局默认" if not disabled else "当前：使用全局默认 · 渠道即将上线")
        note_lbl.setStyleSheet("font-size: 12px; color: #8f959e;")
        head_lay.addWidget(icon_lbl)
        head_lay.addWidget(note_lbl)
        head_lay.addStretch()
        sw = QLabel("专属配置")
        sw.setStyleSheet("font-size: 12px; color: #8f959e;")
        head_lay.addWidget(sw)
        switch = QCheckBox()
        switch.setEnabled(not disabled)
        head_lay.addWidget(switch)
        lay.addWidget(head)

        body = QWidget()
        body.setVisible(False)
        body_lay = QGridLayout(body)
        body_lay.setSpacing(10)
        for i, (lbl_txt, ph) in enumerate([
            ("接口地址 base_url", "留空则继承全局默认"),
            ("API Key", "留空则继承全局默认"),
            ("模型唯一标识 model_id", "留空则继承全局默认"),
        ]):
            lbl = QLabel(lbl_txt)
            lbl.setStyleSheet("font-size: 12px; font-weight: 500;")
            inp = QLineEdit()
            inp.setPlaceholderText(ph)
            inp.setStyleSheet("border: 1px solid #e8eaf0; border-radius: 6px; padding: 7px 10px; font-size: 13px; background: white;")
            inp.setEnabled(not disabled)
            body_lay.addWidget(lbl, i, 0)
            body_lay.addWidget(inp, i, 1)
        lay.addWidget(body)

        switch.toggled.connect(lambda on: body.setVisible(on))
        return w

    def _test_connection(self, ability: str, base_url_w, api_key_w, model_id_w):
        base_url = base_url_w.findChild(QLineEdit).text().strip()
        api_key = api_key_w.findChild(QLineEdit).text().strip()
        model_id = model_id_w.findChild(QLineEdit).text().strip()
        if not base_url or not api_key:
            QMessageBox.warning(self, "配置不完整", "请填写 base_url 和 api_key")
            return
        try:
            from app.core.content_generator import ContentGenerator
            ok = ContentGenerator(self.config).test_connection(base_url, api_key, model_id)
            if ok:
                QMessageBox.information(self, "连接成功", "API 连接测试通过 ✅")
            else:
                QMessageBox.warning(self, "连接失败", "无法连接到服务器，请检查配置是否正确")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"连接测试出错：{e}")

    def _save_api_config(self, ability: str, base_url_w, api_key_w, model_id_w):
        base_url = base_url_w.findChild(QLineEdit).text().strip()
        api_key = api_key_w.findChild(QLineEdit).text().strip()
        model_id = model_id_w.findChild(QLineEdit).text().strip()
        self.config.set_api_config(ability, {
            "base_url": base_url,
            "api_key": api_key,
            "model_id": model_id,
        })
        self._update_api_status()
        QMessageBox.information(self, "已保存", "API 配置已保存到本地")

    # ==================== 页面：渠道管理 ====================

    def _build_page_channel(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        c = card_frame()
        c_lay = QVBoxLayout(c)
        c_lay.setContentsMargins(20, 20, 20, 20)
        c_lay.setSpacing(12)
        c_lay.addWidget(section_title("渠道管理"))
        c_lay.addWidget(hint_text("每个渠道绑定一份独立的系统提示词；新增渠道即新增一份提示词配置"))

        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["所属能力", "渠道", "状态", "提示词摘要", "操作"])
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setShowGrid(False)
        table.setStyleSheet("""
            QTableWidget { border: none; background: white; gridline-color: #f2f3f5; font-size: 13px; }
            QTableWidget::item { padding: 10px 8px; border-bottom: 1px solid #f2f3f5; }
            QHeaderView::section { background: #fafbfc; color: #8f959e; font-size: 12px; padding: 8px 12px; border: none; border-bottom: 1px solid #e8eaf0; }
        """)
        channels = self.channel_manager.get_all_channels()
        table.setRowCount(len(channels))
        status_map = {
            "builtin-wechat": ("已上线", "#e8f8e5", "#34c724"),
        }
        for row, ch in enumerate(channels):
            table.setItem(row, 0, QTableWidgetItem("📝 生文"))
            name_item = QTableWidgetItem(f"<b>{ch.display_name}</b>")
            name_item.setData(Qt.ItemDataRole.UserRole, ch)
            table.setItem(row, 1, name_item)
            if ch.name == "wechat":
                si = QTableWidgetItem("已上线")
                si.setBackground(QColor("#e8f8e5"))
                si.setForeground(QColor("#34c724"))
            else:
                si = QTableWidgetItem("即将上线")
                si.setBackground(QColor("#f2f3f5"))
                si.setForeground(QColor("#8f959e"))
            table.setItem(row, 2, si)
            table.setItem(row, 3, QTableWidgetItem(ch.system_prompt[:80] + "..." if len(ch.system_prompt) > 80 else ch.system_prompt))
            view_btn = QPushButton("查看/编辑")
            view_btn.setStyleSheet("background: transparent; color: #3370ff; border: none; cursor: pointer;")
            view_btn.clicked.connect(lambda _, channel=ch: self._edit_channel_prompt(channel))
            table.setCellWidget(row, 4, view_btn)
        table.setMinimumHeight(200)
        c_lay.addWidget(table)
        lay.addWidget(c)
        return page

    def _edit_channel_prompt(self, channel):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"编辑提示词 · {channel.display_name}")
        dlg.resize(640, 480)
        lay = QVBoxLayout(dlg)
        lay.setSpacing(12)
        lay.addWidget(QLabel(f"系统提示词（{channel.display_name}）"))
        editor = QTextEdit()
        editor.setText(channel.system_prompt)
        editor.setStyleSheet("""
            QTextEdit { border: 1px solid #e8eaf0; border-radius: 8px; padding: 12px; font-size: 13px;
                         font-family: "Cascadia Code", "Consolas", monospace; background: #f7f8fa; }
        """)
        lay.addWidget(editor)
        btn_row = QWidget()
        btn_row_lay = QHBoxLayout(btn_row)
        btn_row_lay.setContentsMargins(0, 0, 0, 0)
        btn_row_lay.addStretch()
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("border: 1px solid #e8eaf0; border-radius: 8px; padding: 8px 16px; cursor: pointer;")
        cancel_btn.clicked.connect(dlg.reject)
        save_btn = QPushButton("保存")
        save_btn.setStyleSheet("background: #3370ff; color: white; border-radius: 8px; padding: 8px 18px; cursor: pointer;")
        save_btn.clicked.connect(lambda: (
            setattr(channel, 'system_prompt', editor.toPlainText()),
            self.channel_manager.update_channel(channel),
            dlg.accept()
        ))
        btn_row_lay.addWidget(cancel_btn)
        btn_row_lay.addWidget(save_btn)
        lay.addWidget(btn_row)
        dlg.exec()

    # ==================== 页面：通用设置 ====================

    def _build_page_general(self) -> QWidget:
        page = QScrollArea()
        page.setWidgetResizable(True)
        page.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        page.setStyleSheet("border: none; background: transparent;")
        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 20)
        inner_lay.setSpacing(16)

        # 数据存储目录设置
        c1 = card_frame()
        c1_lay = QVBoxLayout(c1)
        c1_lay.setContentsMargins(20, 20, 20, 20)
        c1_lay.setSpacing(12)

        c1_lay.addWidget(section_title("数据存储"))
        c1_lay.addWidget(hint_text("文章内容、生成结果等数据存储位置"))

        data_dir = self.config.get("data_dir", str(self.config.data_dir))
        
        dir_row = QWidget()
        dir_row_lay = QHBoxLayout(dir_row)
        dir_row_lay.setContentsMargins(0, 0, 0, 0)
        dir_lbl = QLabel("存储路径")
        dir_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        dir_row_lay.addWidget(dir_lbl)
        dir_row_lay.addStretch()

        self.general_path_input = QLineEdit(data_dir)
        self.general_path_input.setReadOnly(True)
        self.general_path_input.setMinimumWidth(300)
        self.general_path_input.setStyleSheet("""
            QLineEdit { 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                padding: 7px 10px; 
                font-size: 12px; 
                background: #f5f5f5; 
                color: #666;
            }
        """)
        dir_row_lay.addWidget(self.general_path_input)

        browse_btn = QPushButton("浏览")
        browse_btn.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 6px 14px;")
        browse_btn.clicked.connect(self._browse_data_dir)
        dir_row_lay.addWidget(browse_btn)

        c1_lay.addWidget(dir_row)
        inner_lay.addWidget(c1)

        # 日志设置
        c2 = card_frame()
        c2_lay = QVBoxLayout(c2)
        c2_lay.setContentsMargins(20, 20, 20, 20)
        c2_lay.setSpacing(12)

        c2_lay.addWidget(section_title("日志"))
        c2_lay.addWidget(hint_text("控制日志输出的详细程度"))

        log_row = QWidget()
        log_row_lay = QHBoxLayout(log_row)
        log_row_lay.setContentsMargins(0, 0, 0, 0)
        log_lbl = QLabel("日志级别")
        log_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        log_row_lay.addWidget(log_lbl)
        log_row_lay.addStretch()

        self.log_combo = QComboBox()
        self.log_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        self.log_combo.setCurrentText(self.config.log_level)
        self.log_combo.setMinimumWidth(150)
        self.log_combo.currentTextChanged.connect(lambda v: setattr(self.config, 'log_level', v))
        log_row_lay.addWidget(self.log_combo)

        c2_lay.addWidget(log_row)
        inner_lay.addWidget(c2)

        # 界面设置
        c3 = card_frame()
        c3_lay = QVBoxLayout(c3)
        c3_lay.setContentsMargins(20, 20, 20, 20)
        c3_lay.setSpacing(12)

        c3_lay.addWidget(section_title("界面"))
        c3_lay.addWidget(hint_text("应用外观和行为设置"))

        # 默认渠道
        ch_row = QWidget()
        ch_row_lay = QHBoxLayout(ch_row)
        ch_row_lay.setContentsMargins(0, 0, 0, 0)
        ch_lbl = QLabel("默认渠道")
        ch_lbl.setStyleSheet("font-size: 13px; font-weight: 500;")
        ch_row_lay.addWidget(ch_lbl)
        ch_row_lay.addStretch()

        self.default_channel_combo = QComboBox()
        self.default_channel_combo.addItem("微信公众号", "wechat")
        self.default_channel_combo.addItem("头条号", "toutiao")
        self.default_channel_combo.setMinimumWidth(150)
        ch_row_lay.addWidget(self.default_channel_combo)

        c3_lay.addWidget(ch_row)
        inner_lay.addWidget(c3)

        # 保存按钮
        btn_row = QWidget()
        btn_row_lay = QHBoxLayout(btn_row)
        btn_row_lay.setContentsMargins(0, 0, 0, 0)
        btn_row_lay.addStretch()
        save_btn = QPushButton("保存设置")
        save_btn.setStyleSheet("background: #555; color: white; border-radius: 4px; padding: 8px 18px; border: none;")
        save_btn.clicked.connect(self._save_general_settings)
        btn_row_lay.addWidget(save_btn)
        inner_lay.addWidget(btn_row)

        page.setWidget(inner)
        return page

    def _browse_data_dir(self):
        """浏览选择数据目录"""
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据存储目录")
        if dir_path:
            self.general_path_input.setText(dir_path)
            self.config.data_dir = dir_path

    def _save_general_settings(self):
        """保存通用设置"""
        self.config.set("data_dir", self.general_path_input.text())
        self.config.log_level = self.log_combo.currentText()
        self.config.save()
        QMessageBox.information(self, "保存成功", "通用设置已保存")

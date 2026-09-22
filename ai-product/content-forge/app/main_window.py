"""ContentForge 主窗口 - Fluent Design"""
import sys
import threading
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QDialog, QTextEdit, QMessageBox, QFileDialog,
    QPushButton, QHBoxLayout, QVBoxLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor

from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF, NavigationItemPosition,
    setTheme, Theme, setThemeColor, themeColor,
    CaptionLabel,
)

from loguru import logger
from app.models.task import Task, TaskStatus
from app.core.task_manager import TaskManager
from app.core.channel_manager import ChannelManager
from app.core.content_generator import ContentGenerator
from app.core.content_fetcher import ContentFetcher

# Import new UI pages
from app.ui.pages import (
    WechatPage, HistoryPage, ApiConfigPage, ChannelPage,
    SettingsPage, ReservedPage
)


class ResultDialog(QDialog):
    """生成结果查看对话框 - Fluent Design"""

    def __init__(self, task: Task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle(f"生成结果 · {task.channel}")
        self.resize(700, 560)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)

        # 配图信息（如果有）
        if task.image_paths:
            img_lay = QHBoxLayout()
            img_info = CaptionLabel(f"已生成 {len(task.image_paths)} 张配图")
            img_info.setTextColor("#16a34a", "#16a34a")
            img_lay.addWidget(img_info)
            img_lay.addStretch()
            open_dir_btn = QPushButton("打开图片目录")
            open_dir_btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid #e8eaf0; border-radius: 6px; padding: 4px 12px;
                               font-size: 12px; color: #646a73; background: white; }}
                QPushButton:hover {{ border-color: {themeColor().name()}; color: {themeColor().name()}; }}
            """)
            open_dir_btn.clicked.connect(self._open_image_dir)
            img_lay.addWidget(open_dir_btn)
            lay.addLayout(img_lay)

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
            border-radius: 8px;
        """)
        lay.addWidget(self.editor)

        # 底部按钮
        foot_lay = QHBoxLayout()
        foot_lay.addStretch()
        for label, cb in [
            ("📋 复制 Markdown", self._copy),
            ("⬇️ 导出 .md", self._export),
            ("🔄 重新生成", self._regenerate),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(f"""
                QPushButton {{ border: 1px solid #e8eaf0; border-radius: 8px; padding: 8px 16px;
                               font-size: 13px; color: #646a73; background: white;  }}
                QPushButton:hover {{ border-color: {themeColor().name()}; color: {themeColor().name()}; }}
            """)
            btn.clicked.connect(cb)
            foot_lay.addWidget(btn)
        lay.addLayout(foot_lay)

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

    def _open_image_dir(self):
        if not self.task.image_paths:
            return
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices
        dir_path = Path(self.task.image_paths[0]).parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(dir_path)))


class MainWindow(FluentWindow):
    """ContentForge 主窗口 - Fluent Design with qfluentwidgets"""

    # 信号：通知任务状态变更
    task_updated = pyqtSignal(str)  # task_id
    # 信号：显示错误弹框
    show_error = pyqtSignal(str)  # error_msg
    # 信号：显示AI生成的候选观点
    show_opinions = pyqtSignal(object)  # opinions list
    # 信号：AI 生成观点失败（worker 线程触发，主线程恢复 UI 状态）
    opinion_failed = pyqtSignal(str)  # error_msg

    def __init__(self, config, storage):
        super().__init__()
        self.config = config
        self.storage = storage
        self.channel_manager = ChannelManager(storage)
        self.task_manager = TaskManager(storage, self.channel_manager, config)
        self.task_manager.task_updated.connect(self._on_task_updated)
        self.current_channel = "wechat"
        self._opinion_candidates = []
        self._selected_opinions = []

        # Window setup
        self.setWindowTitle("内容锻造师 ContentForge v0.1")
        self.resize(1180, 780)
        self.setMinimumSize(1000, 680)
        setTheme(Theme.LIGHT)
        setThemeColor("#3370ff")

        # Enable Mica on Windows 11
        try:
            self.setMicaEffectEnabled(True)
        except Exception:
            pass

        # Setup navigation and pages
        self._setup_ui()
        self._load_tasks()

        # Connect signals
        self.show_error.connect(self._on_show_error)
        self.show_opinions.connect(self._do_show_opinions)
        self.opinion_failed.connect(self._on_opinion_failed)

    def _setup_ui(self):
        """Setup all pages and navigation with Fluent Design"""

        # Create pages
        self.text_group = ReservedPage("g_text", "生文", "文字内容生产能力")
        self.image_group = ReservedPage("g_image", "生图", "图片生成能力（预留）")
        self.video_group = ReservedPage("g_video", "生视频", "视频生成能力（预留）")

        self.wechat_page = WechatPage(self.task_manager, self.config, self)
        self.toutiao_page = ReservedPage("toutiao", "头条号", "生文 → 头条号渠道即将上线")
        self.image_gen_page = ReservedPage("image_gen", "配图生成", "生图能力即将上线")
        self.video_gen_page = ReservedPage("video_gen", "视频生成", "生视频能力即将上线")
        self.history_page = HistoryPage(self.task_manager, self)
        self.api_page = ApiConfigPage(self.config, self)
        self.channel_page = ChannelPage(self.channel_manager, self)
        self.settings_page = SettingsPage(self.config, self)

        # 连接微信页面的事件
        self.wechat_page.gen_btn.clicked.connect(self._on_start_generation)
        self.wechat_page.add_btn.clicked.connect(self._on_add_task)

        # Build navigation
        # First level: ability groups
        self.addSubInterface(self.text_group, FIF.DOCUMENT, "生文")
        self.addSubInterface(self.wechat_page, FIF.CHAT, "微信公众号", parent=self.text_group)
        self.addSubInterface(self.toutiao_page, FIF.ALIGNMENT, "头条号", parent=self.text_group)

        self.addSubInterface(self.image_group, FIF.PHOTO, "生图")
        self.addSubInterface(self.image_gen_page, FIF.BRUSH, "配图生成", parent=self.image_group)

        self.addSubInterface(self.video_group, FIF.VIDEO, "生视频")
        self.addSubInterface(self.video_gen_page, FIF.PLAY, "视频生成", parent=self.video_group)

        self.addSubInterface(self.history_page, FIF.HISTORY, "历史记录")

        # Settings section at bottom
        self.addSubInterface(self.api_page, FIF.GLOBE, "API 配置", position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.channel_page, FIF.TAG, "渠道管理", position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settings_page, FIF.SETTING, "偏好设置", position=NavigationItemPosition.BOTTOM)

        # Default open wechat page
        self.switchTo(self.wechat_page)

    # ==================== Business logic (kept from original) ====================

    def _load_tasks(self):
        self.wechat_page.refresh_tasks()

    def _on_task_updated(self, task: Task):
        if task is None:
            self.wechat_page.gen_btn.setEnabled(True)
            self.wechat_page.gen_btn.setText("🚀 开始生成")
            return
        QTimer.singleShot(0, lambda: self.wechat_page.refresh_tasks())
        if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            pending = [t for t in self.task_manager.tasks if t.status in (TaskStatus.PENDING, TaskStatus.PROCESSING)]
            if not pending:
                self.wechat_page.gen_btn.setEnabled(True)
                completed = sum(1 for t in self.task_manager.tasks if t.status == TaskStatus.COMPLETED)
                failed = sum(1 for t in self.task_manager.tasks if t.status == TaskStatus.FAILED)
                total = len(self.task_manager.tasks)
                if failed == 0:
                    self.wechat_page.gen_btn.setText("✅ 全部完成")
                    QMessageBox.information(self, "生成完成", f"🎉 所有 {total} 个任务已成功完成！\n\n点击「查看」按钮查看生成的图文内容")
                else:
                    self.wechat_page.gen_btn.setText("⚠️ 部分失败")
                    QMessageBox.warning(self, "生成完成", f"完成 {completed} 个，失败 {failed} 个\n\n失败的任务可点击「原因」查看详情或「重试」")

    def _on_show_error(self, msg: str):
        QMessageBox.warning(self, "操作失败", msg)

    def _on_opinion_failed(self, msg: str):
        """AI 生成观点失败（主线程槽函数，恢复 UI 状态）"""
        self.wechat_page.op_loading.setVisible(False)
        self.wechat_page.ai_btn.setEnabled(True)
        self.wechat_page.opinion_input.setEnabled(True)
        self.wechat_page.opinion_input.setPlaceholderText("写下你对这篇文章的看法、补充或反驳...")
        QMessageBox.warning(self, "AI 生成失败", msg)

    def _do_show_opinions(self, opinions: list):
        self._opinion_candidates = opinions
        self.wechat_page.op_loading.setVisible(False)
        self.wechat_page.op_cards.setVisible(True)
        self.wechat_page.ai_btn.setEnabled(True)
        self.wechat_page.ai_btn.setText("✨ 重新生成观点")
        self._selected_opinions = []

        for i, op in enumerate(opinions):
            self.wechat_page.op_flow.addWidget(self.wechat_page._make_opinion_card(i, op))
        self.wechat_page.sel_lbl.setText("已选 0 个观点（将生成 0 篇图文）")

    def _on_add_task(self):
        self.wechat_page._on_add_task()

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
            self.switchTo(self.api_page)
            return
        self.wechat_page.gen_btn.setEnabled(False)
        self.wechat_page.gen_btn.setText("⏳ 生成中...")
        self.task_manager.start_generation()

    def _show_result(self, task: Task):
        dlg = ResultDialog(task, self)
        dlg.finished.connect(lambda r: self._on_result_dialog_close(r, task))
        dlg.exec()

    def _on_result_dialog_close(self, r, task: Task):
        if r == QDialog.DialogCode.Accepted:
            # 用户在结果对话框点击了「重新生成」
            self.task_manager.regenerate(task.id)
            self.wechat_page.refresh_tasks()

    def _copy_result(self, task: Task):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(task.generated_content)
        QMessageBox.information(self, "已复制", "图文内容已复制到剪贴板")

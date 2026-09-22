"""
ContentForge
页面：生文 → 微信公众号 工作台
"""
import threading
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
)

from qfluentwidgets import (
    FluentIcon as FIF,
    setThemeColor, themeColor,
    HeaderCardWidget, CardWidget, ElevatedCardWidget,
    PrimaryPushButton, PushButton, TransparentToolButton, SwitchButton,
    LineEdit, PlainTextEdit,
    ProgressBar, IndeterminateProgressBar, ProgressRing,
    BodyLabel, CaptionLabel, StrongBodyLabel,
    InfoBadge, InfoBar, InfoBarPosition,
    SmoothScrollArea as ScrollArea, FlowLayout,
)

from app.models.task import Task, TaskStatus
from app.ui.components import StatusPill, PageHeader


class TaskCard(ElevatedCardWidget):
    """任务卡片：链接 + 观点摘要 + 状态徽章 + 操作"""

    def __init__(self, task: Task, on_remove, on_copy, on_retry, parent=None):
        super().__init__(parent)
        self.task = task
        self.on_remove = on_remove
        self.on_copy = on_copy
        self.on_retry = on_retry
        self.setFixedHeight(88)
        root = QHBoxLayout(self)
        root.setContentsMargins(14, 10, 14, 10)
        root.setSpacing(12)

        # 左侧状态色条
        self.strip = QWidget()
        self.strip.setFixedWidth(4)
        root.addWidget(self.strip)

        body = QVBoxLayout()
        body.setSpacing(4)
        url = task.url if len(task.url) <= 50 else task.url[:47] + "…"
        self.url_lbl = StrongBodyLabel(url)
        opinion = task.user_opinion if len(task.user_opinion) <= 60 else task.user_opinion[:57] + "…"
        self.opinion_lbl = CaptionLabel(opinion)
        self.opinion_lbl.setTextColor("#8a8f99", "#9aa0a8")
        self.img_lbl = CaptionLabel("")
        self.img_lbl.setTextColor("#16a34a", "#16a34a")
        self.img_lbl.setVisible(False)
        body.addWidget(self.url_lbl)
        body.addWidget(self.opinion_lbl)
        body.addWidget(self.img_lbl)
        root.addLayout(body, stretch=1)

        self.ring = ProgressRing(self)
        self.ring.setFixedSize(22, 22)
        self.ring.setStrokeWidth(3)
        self.ring.setVisible(False)
        root.addWidget(self.ring)

        self.pill = StatusPill(task.status.value, self)
        root.addWidget(self.pill)

        # 动态操作区
        self.ops_widget = QWidget()
        self.ops_lay = QHBoxLayout(self.ops_widget)
        self.ops_lay.setContentsMargins(0, 0, 0, 0)
        self.ops_lay.setSpacing(6)
        root.addWidget(self.ops_widget)

        self.del_btn = TransparentToolButton(FIF.DELETE, self)
        self.del_btn.setToolTip("移除任务")
        self.del_btn.clicked.connect(lambda: self.on_remove(self))
        root.addWidget(self.del_btn)

        self._refresh_strip()
        self._update_ops()

    def _refresh_strip(self):
        _, color = StatusPill.status_style[self.task.status.value]
        color = color or StatusPill.get_theme_color()
        self.strip.setStyleSheet(f"QWidget {{ background: {color}; border-radius: 2px; }}")

    def _update_ops(self):
        while self.ops_lay.count():
            item = self.ops_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if self.task.status == TaskStatus.COMPLETED and self.task.generated_content:
            copy_btn = TransparentToolButton(FIF.COPY, self)
            copy_btn.setToolTip("复制生成内容")
            copy_btn.clicked.connect(lambda: self.on_copy(self.task))
            self.ops_lay.addWidget(copy_btn)

        elif self.task.status == TaskStatus.FAILED:
            if self.task.error_message:
                reason_btn = PushButton("原因")
                reason_btn.setStyleSheet("""
                    QPushButton {
                        border: 1px solid #e5484d;
                        border-radius: 6px;
                        padding: 4px 12px;
                        font-size: 12px;
                        color: #e5484d;
                        background: white;
                    }
                    QPushButton:hover {
                        background: #fee;
                    }
                """)
                reason_btn.clicked.connect(lambda: self._show_error())
                self.ops_lay.addWidget(reason_btn)

            retry_btn = PushButton("重试")
            retry_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ff7d00;
                    border-radius: 6px;
                    padding: 4px 12px;
                    font-size: 12px;
                    color: #ff7d00;
                    background: white;
                }
                QPushButton:hover {
                    background: #fff4e5;
                }
            """)
            retry_btn.clicked.connect(lambda: self.on_retry(self.task))
            self.ops_lay.addWidget(retry_btn)

        elif self.task.status == TaskStatus.PROCESSING:
            lbl = CaptionLabel("处理中…")
            lbl.setTextColor("#3370ff", "#3370ff")
            self.ops_lay.addWidget(lbl)

    def _show_error(self):
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "失败原因", self.task.error_message or "未知错误")

    def refresh(self):
        self.pill.set_status(self.task.status.value)
        self.ring.setVisible(self.task.status == TaskStatus.PROCESSING)
        if self.task.status == TaskStatus.PROCESSING:
            self.ring.setValue(50)
        self._refresh_strip()
        self._update_ops()
        if self.task.status == TaskStatus.COMPLETED and self.task.image_paths:
            self.img_lbl.setText(f"🖼 已生成 {len(self.task.image_paths)} 张配图")
            self.img_lbl.setVisible(True)
        else:
            self.img_lbl.setVisible(False)


class WechatPage(ScrollArea):
    """生文 → 微信公众号 工作台"""

    # 信号：任务状态更新
    task_updated = pyqtSignal()

    def __init__(self, task_manager, config, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.config = config
        self.setObjectName("wechat")
        self.setWidgetResizable(True)
        self._task_cards: list[TaskCard] = []
        self._selected_opinions: set[int] = set()

        self.canvas = QWidget()
        self.setWidget(self.canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(self.canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader(
            "微信公众号",
            "链接 + 观点 → 批量生成原创图文 · 数据本地存储"
        ))

        lay.addWidget(self._build_input_card())
        self.opinion_panel = self._build_opinion_panel()
        lay.addWidget(self.opinion_panel)
        lay.addWidget(self._build_task_card())
        lay.addStretch()

        # 连接任务更新信号
        self.task_manager.task_updated.connect(self.refresh_tasks)

        # 保存主窗口引用，用于线程中安全调用信号
        self._main_window = None
        p = self.parent()
        while p:
            if p.__class__.__name__ == "MainWindow":
                self._main_window = p
                break
            p = p.parent()

    def _build_input_card(self):
        card = HeaderCardWidget()
        card.setTitle("新增任务")
        lay = QVBoxLayout()
        lay.setSpacing(10)

        # 输入模式切换
        mode_row = QHBoxLayout()
        self.mode_url_btn = PushButton("链接抓取")
        self.mode_text_btn = PushButton("直接粘贴原文")
        self._mode = "url"
        self.mode_url_btn.clicked.connect(lambda: self._set_input_mode("url"))
        self.mode_text_btn.clicked.connect(lambda: self._set_input_mode("text"))
        self._update_mode_style()
        mode_row.addWidget(self.mode_url_btn)
        mode_row.addWidget(self.mode_text_btn)
        mode_row.addStretch()
        lay.addLayout(mode_row)

        # 链接输入区（默认显示）
        self.url_container = QWidget()
        url_container_lay = QVBoxLayout(self.url_container)
        url_container_lay.setContentsMargins(0, 8, 0, 0)
        url_lbl = BodyLabel("文章链接")
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("🔗 粘贴文章链接，如 https://mp.weixin.qq.com/s/…")
        self.url_input.setClearButtonEnabled(True)
        url_container_lay.addWidget(url_lbl)
        url_container_lay.addWidget(self.url_input)
        lay.addWidget(self.url_container)

        # 原文粘贴区（初始隐藏）
        self.text_container = QWidget()
        self.text_container.setVisible(False)
        text_container_lay = QVBoxLayout(self.text_container)
        text_container_lay.setContentsMargins(0, 8, 0, 0)
        text_lbl = BodyLabel("文章原文")
        self.original_text_input = PlainTextEdit()
        self.original_text_input.setPlaceholderText("链接无法抓取时，直接粘贴文章原文到这里（比如付费文章、头条文章等）")
        self.original_text_input.setFixedHeight(140)
        self.original_text_input.setStyleSheet("""
            PlainTextEdit {
                border: 1px solid #e8eaf0;
                border-radius: 8px;
                padding: 10px 12px;
                font-size: 13px;
                background: white;
            }
            PlainTextEdit:focus {
                border-color: #3370ff;
            }
        """)
        text_container_lay.addWidget(text_lbl)
        text_container_lay.addWidget(self.original_text_input)
        text_hint = CaptionLabel("适用于：链接无法自动抓取的文章（如今日头条、付费文章、公众号长图等）")
        text_hint.setTextColor("#8a8f99", "#9aa0a8")
        text_container_lay.addWidget(text_hint)
        lay.addWidget(self.text_container)

        # 观点输入
        op_lbl = BodyLabel("我的观点 / 看法")
        lay.addWidget(op_lbl)
        self.opinion_input = PlainTextEdit()
        self.opinion_input.setPlaceholderText("写下你的观点、补充或反驳（建议 100–500 字）…AI 会把它融入生成的图文")
        self.opinion_input.setFixedHeight(84)
        lay.addWidget(self.opinion_input)

        # 配图开关行
        img_row = QHBoxLayout()
        img_lbl = BodyLabel("生成前后配图")
        img_tip = CaptionLabel("需要先在「API 配置 → 生图」中设置文生图模型")
        img_tip.setTextColor("#8a8f99", "#9aa0a8")
        self.img_switch = SwitchButton()
        self.img_switch.setChecked(self.config.get("generate_images", False))
        self.img_switch.checkedChanged.connect(self._on_image_switch_changed)
        img_row.addWidget(img_lbl)
        img_row.addWidget(self.img_switch)
        img_row.addWidget(img_tip)
        img_row.addStretch()
        lay.addLayout(img_row)

        # 按钮行
        btn_row = QHBoxLayout()
        self.ai_btn = PushButton(FIF.ROBOT, "AI 生成观点")
        self.ai_btn.setToolTip("没思路？让 AI 读原文，提炼多个候选观点")
        self.ai_btn.clicked.connect(self._on_ai_opinion)
        btn_row.addWidget(self.ai_btn)
        btn_row.addStretch()
        self.add_btn = PrimaryPushButton(FIF.ADD, "添加到任务列表")
        self.add_btn.clicked.connect(self._on_add_task)
        btn_row.addWidget(self.add_btn)
        lay.addLayout(btn_row)

        card.viewLayout.addLayout(lay)
        return card

    def _set_input_mode(self, mode: str):
        self._mode = mode
        self.url_container.setVisible(mode == "url")
        self.text_container.setVisible(mode == "text")
        self._update_mode_style()

    def _update_mode_style(self):
        c = StatusPill.get_theme_color()
        if self._mode == "url":
            self.mode_url_btn.setStyleSheet(f"background: {c}; color: white; border-radius: 6px; padding: 6px 14px;")
            self.mode_text_btn.setStyleSheet("")
        else:
            self.mode_text_btn.setStyleSheet(f"background: {c}; color: white; border-radius: 6px; padding: 6px 14px;")
            self.mode_url_btn.setStyleSheet("")

    def _on_image_switch_changed(self, checked: bool):
        self.config.set("generate_images", checked)
        if checked:
            img_cfg = self.config.get_api_config("image")
            if not img_cfg.get("api_key"):
                InfoBar.warning(
                    "未配置生图 API",
                    "请先到「API 配置 → 生图」中设置 base_url、API Key 和 model_id",
                    parent=self,
                    duration=3000,
                )

    def _build_opinion_panel(self):
        card = HeaderCardWidget()
        card.setTitle("AI 候选观点 · 点击卡片多选")
        card.setVisible(False)

        lay = QVBoxLayout()
        lay.setSpacing(10)

        self.op_loading = QWidget()
        ll = QHBoxLayout(self.op_loading)
        ll.setContentsMargins(0, 6, 0, 6)
        bar = IndeterminateProgressBar()
        txt = CaptionLabel("AI 正在阅读原文并提炼观点…")
        txt.setTextColor("#8a8f99", "#9aa0a8")
        ll.addWidget(bar, stretch=1)
        ll.addWidget(txt)
        lay.addWidget(self.op_loading)

        self.op_cards = QWidget()
        self.op_flow = FlowLayout(self.op_cards, needAni=False)
        self.op_flow.setContentsMargins(0, 0, 0, 0)
        self.op_flow.setSpacing(10)
        lay.addWidget(self.op_cards)

        foot = QHBoxLayout()
        self.sel_lbl = CaptionLabel("已选 0 个观点")
        self.sel_lbl.setTextColor("#8a8f99", "#9aa0a8")
        foot.addWidget(self.sel_lbl)
        foot.addStretch()
        cancel = PushButton("收起")
        cancel.clicked.connect(lambda: card.setVisible(False))
        foot.addWidget(cancel)
        add_sel = PrimaryPushButton(FIF.ACCEPT, "添加所选到任务列表")
        add_sel.clicked.connect(self._on_add_selected_opinions)
        foot.addWidget(add_sel)
        lay.addLayout(foot)

        card.viewLayout.addLayout(lay)
        return card

    def _make_opinion_card(self, idx: int, op: dict):
        card = CardWidget()
        card.setFixedSize(330, 128)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 12, 14, 12)
        lay.setSpacing(6)
        tag = BodyLabel(f"🏷 {op['tag']}")
        tag.setStyleSheet(f"color: {themeColor().name()}; font-weight: 600; background: transparent; border: none;")
        text = CaptionLabel(op["opinion"])
        text.setWordWrap(True)
        text.setTextColor("#646a73", "#aeb4bc")
        lay.addWidget(tag)
        lay.addWidget(text, stretch=1)

        def toggle():
            if idx in self._selected_opinions:
                self._selected_opinions.discard(idx)
                card.setStyleSheet("")
            else:
                self._selected_opinions.add(idx)
                c = StatusPill.get_theme_color()
                card.setStyleSheet(f"CardWidget {{ border: 1.5px solid {c}; }}")
            n = len(self._selected_opinions)
            self.sel_lbl.setText(f"已选 {n} 个观点（将生成 {n} 篇图文）")

        card.mouseReleaseEvent = lambda e: toggle()
        return card

    def _build_task_card(self):
        card = HeaderCardWidget()
        card.setTitle("任务列表")

        lay = QVBoxLayout()
        lay.setSpacing(10)

        self.task_flow = QVBoxLayout()
        self.task_flow.setSpacing(10)
        lay.addLayout(self.task_flow)

        # 底部操作条
        foot = QHBoxLayout()
        self.count_lbl = CaptionLabel("共 0 条任务")
        self.count_lbl.setTextColor("#8a8f99", "#9aa0a8")
        foot.addWidget(self.count_lbl)
        foot.addStretch()
        self.progress = ProgressBar()
        self.progress.setFixedWidth(220)
        self.progress.setVisible(False)
        foot.addWidget(self.progress)
        self.gen_btn = PrimaryPushButton(FIF.PLAY, "开始生成")
        # TODO: connect to start generation
        foot.addWidget(self.gen_btn)
        lay.addLayout(foot)

        card.viewLayout.addLayout(lay)
        return card

    def refresh_tasks(self):
        """Refresh all task cards after data change"""
        # Remove existing cards
        for card in self._task_cards:
            self.task_flow.removeWidget(card)
            card.deleteLater()
        self._task_cards.clear()

        # Add new cards
        for task in self.task_manager.tasks:
            if task.channel != "wechat":
                continue
            card = TaskCard(task, self._remove_task, self._copy_result, self._retry_task, self)
            self.task_flow.addWidget(card)
            self._task_cards.append(card)

        # Update count
        total = len(self._task_cards)
        pending = sum(1 for c in self._task_cards if c.task.status == TaskStatus.PENDING)
        self.count_lbl.setText(f"共 {total} 条 · 待生成 {pending} 条")
        self.gen_btn.setEnabled(pending > 0)
        self.task_updated.emit()

    def _remove_task(self, card: TaskCard):
        self.task_manager.remove_task(card.task.id)
        self.refresh_tasks()
        InfoBar.success("已移除", "任务已从列表中移除", parent=self, duration=1500)

    def _copy_result(self, task: Task):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(task.generated_content)
        InfoBar.success("已复制", "Markdown 内容已复制到剪贴板", parent=self, duration=1500)

    def _retry_task(self, task: Task):
        self.task_manager.regenerate(task.id)
        self.refresh_tasks()
        InfoBar.info("重试已提交", f"任务 {task.id[:8]}... 已重新加入生成队列", parent=self, duration=2000)

    def _on_add_task(self):
        opinion = self.opinion_input.toPlainText().strip()
        if not opinion:
            QMessageBox.warning(self, "请填写观点", "请输入你的观点或使用「AI 生成观点」")
            return

        if self._mode == "text":
            original_content = self.original_text_input.toPlainText().strip()
            if not original_content:
                QMessageBox.warning(self, "请粘贴原文", "请将文章原文粘贴到上面的文本框中")
                return
            url = "(直接粘贴原文)"
            task = self.task_manager.add_task(url, opinion, "wechat", original_content)
            self.original_text_input.clear()
        else:
            url = self.url_input.text().strip()
            if not url:
                url = "(未填写链接)"
            task = self.task_manager.add_task(url, opinion, "wechat")
            self.url_input.clear()

        self.opinion_input.clear()
        self.refresh_tasks()
        InfoBar.success("已添加", "任务已加入列表", parent=self, duration=1500)

    def _on_ai_opinion(self):
        if self._mode == "text":
            content = self.original_text_input.toPlainText().strip()
            if not content:
                QMessageBox.warning(self, "请先粘贴原文", "请先将文章原文粘贴到上面的文本框中")
                return
            url_hint = "(直接粘贴原文)"
        else:
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "请先填写链接", "请先在「文章链接」中填入要分析的文章 URL")
                return
            url_hint = url
            content = None

        self.opinion_panel.setVisible(True)
        self.op_loading.setVisible(True)
        self.op_cards.setVisible(False)
        self._selected_opinions.clear()
        while self.op_flow.count():
            item = self.op_flow.takeAt(0)
            if item is None:
                break
            # qfluentwidgets 的 FlowLayout.takeAt 可能直接返回 widget
            if hasattr(item, 'widget'):
                w = item.widget()
            else:
                w = item
            if w:
                w.setParent(None)
                w.deleteLater()

        def worker():
            try:
                article_content = content
                if article_content is None:
                    from app.core.content_fetcher import ContentFetcher
                    fetcher = ContentFetcher()
                    article_content = fetcher.fetch(url_hint)
                    if not article_content:
                        if self._main_window:
                            self._main_window.opinion_failed.emit("无法抓取文章内容，请检查链接是否正确或稍后重试")
                        return
                from app.core.content_generator import ContentGenerator
                generator = ContentGenerator(self.config)
                opinions = generator.generate_opinions(article_content, "wechat", count=5)
                if not opinions:
                    if self._main_window:
                        self._main_window.opinion_failed.emit("AI 生成观点失败，请检查 API 配置或网络连接")
                    return
                if self._main_window:
                    self._main_window.show_opinions.emit(opinions)
            except Exception as e:
                if self._main_window:
                    self._main_window.opinion_failed.emit(str(e))

        threading.Thread(target=worker, daemon=True).start()

    def _on_add_selected_opinions(self, checked=False):
        # checked 是按钮点击信号传进来的 bool，实际观点列表保存在主窗口
        if not self._selected_opinions:
            QMessageBox.information(self, "请先选择", "请先勾选至少一个候选观点")
            return
        if not self._main_window:
            QMessageBox.warning(self, "内部错误", "无法获取候选观点，请重新生成")
            return
        opinions = self._main_window._opinion_candidates
        if not opinions:
            QMessageBox.warning(self, "观点已失效", "候选观点列表为空，请重新生成")
            return
        url = self.url_input.text().strip() or "(未填写链接)"
        original_content = None
        if self._mode == "text":
            original_content = self.original_text_input.toPlainText().strip() or None
        new_tasks = []
        for idx in self._selected_opinions:
            if idx < 0 or idx >= len(opinions):
                continue
            op = opinions[idx]
            task = self.task_manager.add_task(url, op.get("opinion", ""), "wechat", original_content)
            new_tasks.append(task)
        self.refresh_tasks()
        self.opinion_panel.setVisible(False)
        self.opinion_input.setEnabled(True)
        self.opinion_input.clear()
        QMessageBox.information(
            self, "已添加",
            f"已添加 {len(new_tasks)} 个任务（同一链接 × {len(new_tasks)} 个观点 = {len(new_tasks)} 篇图文）"
        )

"""
ContentForge
页面：历史记录
"""
from datetime import datetime
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
)

from qfluentwidgets import (
    FluentIcon as FIF,
    SearchLineEdit,
    ElevatedCardWidget, TransparentToolButton,
    BodyLabel, CaptionLabel, StrongBodyLabel,
    SmoothScrollArea as ScrollArea,
)

from app.models.task import TaskStatus
from app.ui.components import PageHeader


class HistoryPage(ScrollArea):
    def __init__(self, task_manager, parent=None):
        super().__init__(parent)
        self.task_manager = task_manager
        self.setObjectName("history")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader("历史记录", "所有已生成的图文 · 支持即时搜索"))

        self.search = SearchLineEdit()
        self.search.setPlaceholderText("搜索标题 / 观点…")
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)

        self.cards: list[tuple[str, ElevatedCardWidget]] = []
        self._load_history()
        lay.addStretch()

    def _load_history(self):
        # 清除现有卡片
        for _, card in self.cards:
            card.deleteLater()
        self.cards.clear()

        # 从 task_manager 获取已完成的任务
        tasks = [t for t in self.task_manager.tasks if t.status == TaskStatus.COMPLETED]
        channel_names = {"wechat": "微信公众号", "toutiao": "头条号"}

        for task in tasks:
            card = self._make_card(task, channel_names)
            self.cards.append((f"{task.url}{task.user_opinion}{task.channel}".lower(), card))
            # 添加到布局（需要找到父级布局）
            # 这里我们使用一个更简单的方法：直接添加到 canvas
            self.widget().layout().insertWidget(self.widget().layout().count() - 1, card)

    def _make_card(self, task, channel_names):
        from qfluentwidgets import QVBoxLayout as QVBL
        card = ElevatedCardWidget()
        root = QVBoxLayout(card)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(8)

        # 标题行
        title_row = QHBoxLayout()
        title = StrongBodyLabel(task.url if "://" in task.url else task.url)
        title_row.addWidget(title, stretch=1)

        # 状态徽章
        from app.ui.components import StatusPill
        pill = StatusPill(task.status.value)
        title_row.addWidget(pill)
        root.addLayout(title_row)

        # 观点摘要
        snippet = task.user_opinion[:80] + ("..." if len(task.user_opinion) > 80 else "")
        s = CaptionLabel(snippet)
        s.setTextColor("#8a8f99", "#9aa0a8")
        root.addWidget(s)

        # 元信息行
        meta_row = QHBoxLayout()
        dt = task.completed_at.strftime("%Y-%m-%d %H:%M") if task.completed_at else datetime.now().strftime("%Y-%m-%d %H:%M")
        channel_name = channel_names.get(task.channel, task.channel)
        meta = CaptionLabel(f"🕘 {dt} · {channel_name}")
        meta.setTextColor("#8a8f99", "#9aa0a8")
        meta_row.addWidget(meta)
        meta_row.addStretch()

        # 操作按钮
        view_btn = TransparentToolButton(FIF.VIEW)
        view_btn.setToolTip("查看全文")
        view_btn.clicked.connect(lambda: self._view_task(task))
        meta_row.addWidget(view_btn)

        copy_btn = TransparentToolButton(FIF.COPY)
        copy_btn.setToolTip("复制内容")
        copy_btn.clicked.connect(lambda: self._copy_task(task))
        meta_row.addWidget(copy_btn)
        root.addLayout(meta_row)

        return card

    def _filter(self, text: str):
        kw = text.strip().lower()
        for hay, card in self.cards:
            card.setVisible(not kw or kw in hay)

    def _view_task(self, task):
        from app.main_window import ResultDialog
        dlg = ResultDialog(task, self.window())
        dlg.exec()

    def _copy_task(self, task):
        from PyQt6.QtWidgets import QApplication
        cb = QApplication.clipboard()
        cb.setText(task.generated_content or "")
        from qfluentwidgets import InfoBar
        InfoBar.success("已复制", "图文内容已复制到剪贴板", parent=self, duration=1500)

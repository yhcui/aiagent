"""
ContentForge 设计预览（Design Preview）
======================================
独立运行的 Fluent Design 界面预览，使用模拟数据，不连接真实业务。
目的：在正式重写 UI 前，先确认设计风格与交互。

运行：python preview_ui.py
"""
import sys
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QApplication,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)

from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon as FIF,
    setTheme, Theme, setThemeColor, themeColor, isDarkTheme,
    CardWidget, ElevatedCardWidget, SimpleCardWidget, HeaderCardWidget,
    PrimaryPushButton, PushButton, TransparentPushButton, TransparentToolButton, ToolButton,
    LineEdit, PasswordLineEdit, SearchLineEdit, PlainTextEdit, TextEdit,
    ProgressBar, IndeterminateProgressBar, ProgressRing,
    SwitchButton, ComboBox, TableWidget, CheckBox,
    BodyLabel, CaptionLabel, StrongBodyLabel, SubtitleLabel, TitleLabel, LargeTitleLabel,
    InfoBadge, InfoBar, InfoBarPosition,
    SmoothScrollArea as ScrollArea, FlowLayout,
    MessageBox, Dialog, StateToolTip,
)

# ==================== 主题色候选 ====================
THEME_COLORS = [
    ("品牌蓝", "#3370ff"),
    ("霞光紫", "#7c5cff"),
    ("翡翠绿", "#0f9f6e"),
    ("暖阳橙", "#e8710a"),
]

STATUS_STYLE = {
    "pending":    ("待处理", "#8a8f99"),
    "processing": ("生成中", None),          # None → 使用当前主题色
    "completed":  ("已完成", "#16a34a"),
    "failed":     ("失败",   "#e5484d"),
}


# ==================== 通用小部件 ====================

class StatusPill(CardWidget):
    """状态徽章（胶囊形，自适应深浅色）"""

    def __init__(self, status: str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(24)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 10, 0)
        self.label = CaptionLabel()
        lay.addWidget(self.label)
        self.set_status(status)

    def set_status(self, status: str):
        text, color = STATUS_STYLE[status]
        color = color or themeColor().name()
        self.label.setText(text)
        self.label.setStyleSheet(f"color: {color}; font-weight: 600; background: transparent; border: none;")
        self.setStyleSheet(
            f"StatusPill {{ background: {color}1a; border: 1px solid {color}55; border-radius: 12px; }}")


class PageHeader(QWidget):
    """页面标题区"""

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


# ==================== 模拟数据 ====================

MOCK_OPINIONS = [
    {"tag": "落地视角", "opinion": "文章讲的方向没错，但真正落地时最大的坑是数据孤岛。我们团队踩过三次：系统打通了，人的 KPI 没打通，最后工具上线三个月没人用。工具只是入场券，组织协同才是正赛。"},
    {"tag": "反驳视角", "opinion": "作者把 AI 生成内容的质量夸大了。实测下来，没有人工观点注入的 AI 文，打开率高、完读率低——读者能嗅出『没有人味』。AI 是放大器，不是替身。"},
    {"tag": "延伸视角", "opinion": "顺着作者的思路再往前走一步：内容生产的下一步不是『写得更快』，而是『测得更快』。一篇稿子发出去，24 小时内拿数据反馈迭代，比打磨一周再发更有价值。"},
    {"tag": "数据视角", "opinion": "我们统计了过去半年 200 篇公众号文章：带明确个人观点的文章，平均转发率是资讯汇编类的 3.2 倍。观点不值钱的时代过去了，没观点才不值钱。"},
]

MOCK_HISTORY = [
    ("为什么你的团队缺的不是工具，是共识", "落地视角 · 工具只是入场券，组织协同才是正赛……", "2026-09-14 09:32", "wechat"),
    ("AI 写作最大的谎言：可以替代人", "反驳视角 · 读者能嗅出没有人味的内容……", "2026-09-14 08:15", "wechat"),
    ("内容生产的下半场：测得比写得重要", "延伸视角 · 24 小时数据反馈迭代法……", "2026-09-13 18:47", "wechat"),
    ("200 篇文章的数据：观点驱动转发", "数据视角 · 个人观点文章转发率 3.2 倍……", "2026-09-13 14:02", "wechat"),
    ("公众号排版的地毯式检查清单", "工具视角 · 从标题到摘要的 12 个细节……", "2026-09-12 20:26", "wechat"),
    ("别再把公众号当博客写了", "趋势视角 · 订阅逻辑已死，推荐逻辑当立……", "2026-09-12 11:09", "wechat"),
]


# ==================== 页面：微信公众号工作台 ====================

class TaskCard(ElevatedCardWidget):
    """任务卡片：链接 + 观点摘要 + 状态徽章 + 操作"""

    def __init__(self, url: str, opinion: str, status: str, parent=None):
        super().__init__(parent)
        self.status = status
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 12, 16, 12)
        root.setSpacing(14)

        # 左侧状态色条
        self.strip = QFrame()
        self.strip.setFixedWidth(4)
        root.addWidget(self.strip)

        body = QVBoxLayout()
        body.setSpacing(4)
        self.url_lbl = StrongBodyLabel(url)
        self.opinion_lbl = CaptionLabel(opinion if len(opinion) <= 60 else opinion[:60] + "…")
        self.opinion_lbl.setTextColor("#8a8f99", "#9aa0a8")
        body.addWidget(self.url_lbl)
        body.addWidget(self.opinion_lbl)
        root.addLayout(body, stretch=1)

        self.ring = ProgressRing(self)
        self.ring.setFixedSize(20, 20)
        self.ring.setStrokeWidth(3)
        self.ring.setVisible(False)
        root.addWidget(self.ring)

        self.pill = StatusPill(status, self)
        root.addWidget(self.pill)

        self.copy_btn = TransparentToolButton(FIF.COPY, self)
        self.copy_btn.setToolTip("复制生成内容")
        self.copy_btn.setVisible(status == "completed")
        root.addWidget(self.copy_btn)
        self.del_btn = TransparentToolButton(FIF.DELETE, self)
        self.del_btn.setToolTip("移除任务")
        root.addWidget(self.del_btn)

        self._refresh_strip()

    def _refresh_strip(self):
        _, color = STATUS_STYLE[self.status]
        color = color or themeColor().name()
        self.strip.setStyleSheet(f"QFrame {{ background: {color}; border-radius: 2px; }}")

    def set_status(self, status: str):
        self.status = status
        self.pill.set_status(status)
        self.ring.setVisible(status == "processing")
        if status == "processing":
            self.ring.setValue(50)  # 让转圈动起来
        self.copy_btn.setVisible(status == "completed")
        self._refresh_strip()


class WechatPage(ScrollArea):
    """生文 → 微信公众号 工作台"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("wechat")
        self.setWidgetResizable(True)
        self._tasks: list[TaskCard] = []
        self._selected: set[int] = set()

        self.canvas = QWidget()
        self.setWidget(self.canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(self.canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader("微信公众号", "链接 + 观点 → 批量生成原创图文 · 今日已生成 6 篇"))

        lay.addWidget(self._build_input_card())
        self.opinion_panel = self._build_opinion_panel()
        lay.addWidget(self.opinion_panel)
        lay.addWidget(self._build_task_card())
        lay.addStretch()

    # ---------- 输入区 ----------
    def _build_input_card(self):
        card = HeaderCardWidget()
        card.setTitle("新增任务")
        lay = QVBoxLayout()
        lay.setSpacing(10)

        url_row = QHBoxLayout()
        self.url_input = LineEdit()
        self.url_input.setPlaceholderText("🔗 粘贴文章链接，如 https://mp.weixin.qq.com/s/…")
        self.url_input.setClearButtonEnabled(True)
        url_row.addWidget(self.url_input)
        paste_btn = PushButton(FIF.DOCUMENT, "粘贴原文")
        paste_btn.setToolTip("链接抓不到时，直接粘贴原文")
        url_row.addWidget(paste_btn)
        lay.addLayout(url_row)

        self.opinion_input = PlainTextEdit()
        self.opinion_input.setPlaceholderText("写下你的观点、补充或反驳（建议 100–500 字）…")
        self.opinion_input.setFixedHeight(84)
        lay.addWidget(self.opinion_input)

        btn_row = QHBoxLayout()
        self.ai_btn = PushButton(FIF.ROBOT, "AI 生成观点")
        self.ai_btn.setToolTip("没思路？让 AI 读原文，给你 4 个候选观点")
        self.ai_btn.clicked.connect(self._mock_gen_opinions)
        btn_row.addWidget(self.ai_btn)
        btn_row.addStretch()
        add_btn = PrimaryPushButton(FIF.ADD, "添加任务")
        add_btn.clicked.connect(lambda: self._add_task_cards(1))
        btn_row.addWidget(add_btn)
        lay.addLayout(btn_row)

        card.viewLayout.addLayout(lay)
        return card

    # ---------- AI 观点面板 ----------
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
        cancel = TransparentPushButton("收起")
        cancel.clicked.connect(lambda: card.setVisible(False))
        foot.addWidget(cancel)
        add_sel = PrimaryPushButton(FIF.ACCEPT, "添加所选到任务列表")
        add_sel.clicked.connect(self._add_selected)
        foot.addWidget(add_sel)
        lay.addLayout(foot)

        card.viewLayout.addLayout(lay)
        return card

    def _mock_gen_opinions(self):
        """模拟 AI 生成观点：先转圈，再出卡片"""
        self.opinion_panel.setVisible(True)
        self.op_loading.setVisible(True)
        self.op_cards.setVisible(False)
        self._selected.clear()
        # 清空旧卡片
        while self.op_flow.count():
            w = self.op_flow.takeAt(0).widget()
            if w:
                w.deleteLater()
        QTimer.singleShot(1100, self._show_mock_opinions)

    def _show_mock_opinions(self):
        self.op_loading.setVisible(False)
        self.op_cards.setVisible(True)
        for i, op in enumerate(MOCK_OPINIONS):
            self.op_flow.addWidget(self._make_opinion_card(i, op))
        self.sel_lbl.setText("已选 0 个观点（将生成 0 篇图文）")

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
            if idx in self._selected:
                self._selected.discard(idx)
                card.setStyleSheet("")
            else:
                self._selected.add(idx)
                c = themeColor().name()
                card.setStyleSheet(f"CardWidget {{ border: 1.5px solid {c}; }}")
            n = len(self._selected)
            self.sel_lbl.setText(f"已选 {n} 个观点（将生成 {n} 篇图文）")

        card.mouseReleaseEvent = lambda e: toggle()
        return card

    def _add_selected(self):
        if self._selected:
            self._add_task_cards(len(self._selected))
            self.opinion_panel.setVisible(False)

    # ---------- 任务列表 ----------
    def _build_task_card(self):
        card = HeaderCardWidget()
        card.setTitle("任务列表")

        lay = QVBoxLayout()
        lay.setSpacing(10)

        self.task_flow = QVBoxLayout()
        self.task_flow.setSpacing(10)
        lay.addLayout(self.task_flow)

        # 预置两条演示任务
        QTimer.singleShot(0, lambda: self._add_task_cards(2, silent=True))

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
        self.gen_btn.clicked.connect(self._mock_generate)
        foot.addWidget(self.gen_btn)
        lay.addLayout(foot)

        card.viewLayout.addLayout(lay)
        return card

    def _add_task_cards(self, n: int, silent=False):
        demos = [
            ("https://mp.weixin.qq.com/s/AbC123", "工具只是入场券，组织协同才是正赛，重点写落地三个坑"),
            ("https://mp.weixin.qq.com/s/DeF456", "AI 是放大器不是替身，没有人味的文章完读率惨淡"),
            ("https://mp.weixin.qq.com/s/GhI789", "测得比写得重要，24 小时数据反馈迭代"),
        ]
        for i in range(n):
            url, opinion = demos[len(self._tasks) % len(demos)]
            card = TaskCard(url, opinion, "pending")
            card.del_btn.clicked.connect(lambda _, c=card: self._remove_task(c))
            card.copy_btn.clicked.connect(lambda _: InfoBar.success("已复制", "Markdown 已复制到剪贴板", parent=self, duration=1500))
            self.task_flow.addWidget(card)
            self._tasks.append(card)
        self._refresh_count()
        if not silent:
            InfoBar.success("已添加", f"{n} 个任务已加入列表", parent=self, duration=1500)

    def _remove_task(self, card: TaskCard):
        self._tasks.remove(card)
        self.task_flow.removeWidget(card)
        card.deleteLater()
        self._refresh_count()

    def _refresh_count(self):
        self.count_lbl.setText(f"共 {len(self._tasks)} 条任务 · 待生成 {sum(1 for t in self._tasks if t.status == 'pending')} 条")

    def _mock_generate(self):
        """模拟批量生成：卡片状态逐个流转 + 进度条 + 完成通知"""
        pending = [t for t in self._tasks if t.status in ("pending", "failed")]
        if not pending:
            InfoBar.info("没有待生成的任务", "请先添加任务", parent=self, duration=1500)
            return
        self.gen_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, len(pending))
        self.progress.setValue(0)

        state = {"i": 0}

        def step():
            i = state["i"]
            if i > 0:
                done = pending[i - 1]
                done.set_status("completed")
                self.progress.setValue(i)
                self._refresh_count()
            if i >= len(pending):
                self.gen_btn.setEnabled(True)
                QTimer.singleShot(600, lambda: self.progress.setVisible(False))
                InfoBar.success(
                    "🎉 全部生成完成",
                    f"{len(pending)} 篇图文已就绪，点击卡片右上角可复制",
                    parent=self, duration=3500, position=InfoBarPosition.TOP,
                )
                return
            pending[i].set_status("processing")
            state["i"] += 1
            QTimer.singleShot(900, step)

        step()


# ==================== 页面：历史记录 ====================

class HistoryPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
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
        self.search.setPlaceholderText("搜索标题 / 观点 / 渠道…")
        self.search.textChanged.connect(self._filter)
        lay.addWidget(self.search)

        self.cards: list[tuple[str, ElevatedCardWidget]] = []
        for title, snippet, dt, channel in MOCK_HISTORY:
            card = self._make_card(title, snippet, dt, channel)
            lay.addWidget(card)
            self.cards.append((f"{title}{snippet}{channel}".lower(), card))
        lay.addStretch()

    def _make_card(self, title, snippet, dt, channel):
        card = ElevatedCardWidget()
        root = QHBoxLayout(card)
        root.setContentsMargins(16, 14, 16, 14)
        root.setSpacing(14)
        body = QVBoxLayout()
        body.setSpacing(4)
        t = StrongBodyLabel(title)
        s = CaptionLabel(snippet)
        s.setTextColor("#8a8f99", "#9aa0a8")
        meta = CaptionLabel(f"🕘 {dt} · 微信公众号")
        meta.setTextColor("#8a8f99", "#9aa0a8")
        body.addWidget(t)
        body.addWidget(s)
        body.addWidget(meta)
        root.addLayout(body, stretch=1)
        view = TransparentToolButton(FIF.VIEW)
        view.setToolTip("查看全文")
        copy = TransparentToolButton(FIF.COPY)
        copy.setToolTip("复制")
        root.addWidget(view)
        root.addWidget(copy)
        return card

    def _filter(self, text: str):
        kw = text.strip().lower()
        for hay, card in self.cards:
            card.setVisible(not kw or kw in hay)


# ==================== 页面：API 配置 ====================

class ApiConfigPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("api")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader("API 配置", "生文 / 生图 / 生视频 独立配置 · API Key 加密存储于系统钥匙串"))

        card = HeaderCardWidget()
        card.setTitle("生文 · 全局默认配置")
        form = QVBoxLayout()
        form.setSpacing(12)
        self.base_url = self._row(form, "接口地址", "https://api.siliconflow.cn/v1")
        self.api_key = self._row(form, "API Key", "sk-••••••••••••••••", password=True)
        self.model_id = self._row(form, "模型标识", "Qwen/Qwen2.5-72B-Instruct")
        row = QHBoxLayout()
        test = PushButton(FIF.SYNC, "测试连接")
        test.clicked.connect(self._mock_test)
        row.addWidget(test)
        row.addStretch()
        save = PrimaryPushButton(FIF.SAVE, "保存")
        save.clicked.connect(lambda: InfoBar.success("已保存", "配置已写入系统钥匙串", parent=self, duration=1500))
        row.addWidget(save)
        form.addLayout(row)
        card.viewLayout.addLayout(form)
        lay.addWidget(card)

        # 渠道专属配置（演示 override 设计）
        ov = HeaderCardWidget()
        ov.setTitle("渠道专属配置（可选）")
        ov_lay = QVBoxLayout()
        ov_lay.setSpacing(10)
        sw_row = QHBoxLayout()
        sw_row.addWidget(BodyLabel("微信公众号使用专属配置"))
        sw_row.addStretch()
        self.ov_switch = SwitchButton()
        sw_row.addWidget(self.ov_switch)
        ov_lay.addLayout(sw_row)
        self.ov_body = QWidget()
        ob = QVBoxLayout(self.ov_body)
        ob.setContentsMargins(0, 0, 0, 0)
        ob.setSpacing(10)
        self._row(ob, "接口地址", "留空则沿用全局配置")
        self._row(ob, "API Key", "留空则沿用全局配置", password=True)
        self._row(ob, "模型标识", "留空则沿用全局配置")
        self.ov_body.setVisible(False)
        self.ov_switch.checkedChanged.connect(self.ov_body.setVisible)
        ov_lay.addWidget(self.ov_body)
        ov.viewLayout.addLayout(ov_lay)
        lay.addWidget(ov)
        lay.addStretch()

    def _row(self, form: QVBoxLayout, label: str, placeholder: str, password=False):
        row = QHBoxLayout()
        lab = BodyLabel(label)
        lab.setFixedWidth(90)
        row.addWidget(lab)
        inp = PasswordLineEdit() if password else LineEdit()
        inp.setPlaceholderText(placeholder)
        row.addWidget(inp, stretch=1)
        form.addLayout(row)
        return inp

    def _mock_test(self):
        InfoBar.success("连接成功", "延迟 132ms · 模型可用", parent=self, duration=2000, position=InfoBarPosition.TOP)


# ==================== 页面：渠道管理 ====================

class ChannelPage(ScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("channel")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader("渠道管理", "渠道 = 系统提示词 + 可选专属 API 配置 · 新增渠道即插即用"))

        for name, desc, active in [
            ("微信公众号", "内置 · 800–1500 字图文 · Markdown 排版 · 突出个人观点", True),
            ("头条号", "即将上线 · 已在导航预留", False),
        ]:
            card = ElevatedCardWidget()
            root = QHBoxLayout(card)
            root.setContentsMargins(16, 14, 16, 14)
            body = QVBoxLayout()
            body.setSpacing(4)
            body.addWidget(StrongBodyLabel(name))
            d = CaptionLabel(desc)
            d.setTextColor("#8a8f99", "#9aa0a8")
            body.addWidget(d)
            root.addLayout(body, stretch=1)
            if active:
                edit = PushButton(FIF.EDIT, "编辑提示词")
                edit.clicked.connect(lambda: self._edit_prompt(name))
                root.addWidget(edit)
            else:
                pill = StatusPill("pending")
                pill.label.setText("即将上线")
                root.addWidget(pill)
            lay.addWidget(card)
        lay.addStretch()

    def _edit_prompt(self, name: str):
        dlg = Dialog("编辑系统提示词", "", self.window())
        dlg.contentLabel.setVisible(False)
        edit = TextEdit(dlg)
        edit.setPlainText(
            "# 角色\n你是一位资深的新媒体内容创作者……\n\n"
            "# 输出要求\n1. 800–1500 字微信公众号图文\n2. Markdown 格式\n3. 突出个人观点"
        )
        edit.setMinimumSize(520, 320)
        dlg.textLayout.addWidget(edit)
        dlg.yesButton.setText("保存")
        dlg.cancelButton.setText("取消")
        dlg.exec()


# ==================== 页面：偏好设置（主题/换肤） ====================

class SettingsPage(ScrollArea):
    themeChanged = None  # 由主窗口注入回调

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settings")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader("偏好设置", "外观、主题色、窗口效果"))

        # 外观
        look = HeaderCardWidget()
        look.setTitle("外观")
        look_lay = QVBoxLayout()
        look_lay.setSpacing(12)

        dark_row = QHBoxLayout()
        dark_row.addWidget(BodyLabel("深色模式"))
        dark_row.addStretch()
        self.dark_switch = SwitchButton()
        self.dark_switch.checkedChanged.connect(
            lambda on: setTheme(Theme.DARK if on else Theme.LIGHT))
        dark_row.addWidget(self.dark_switch)
        look_lay.addLayout(dark_row)

        mica_row = QHBoxLayout()
        mica_row.addWidget(BodyLabel("Mica 云母窗口效果（Windows 11）"))
        mica_row.addStretch()
        self.mica_switch = SwitchButton()
        self.mica_switch.setChecked(True)
        self.mica_switch.checkedChanged.connect(
            lambda on: self.window().setMicaEffectEnabled(on))
        mica_row.addWidget(self.mica_switch)
        look_lay.addLayout(mica_row)

        look.viewLayout.addLayout(look_lay)
        lay.addWidget(look)

        # 主题色
        color_card = HeaderCardWidget()
        color_card.setTitle("主题色")
        color_lay = QHBoxLayout()
        color_lay.setSpacing(12)
        self.swatches = []
        for name, hexv in THEME_COLORS:
            sw = self._make_swatch(name, hexv)
            color_lay.addWidget(sw)
        color_lay.addStretch()
        color_card.viewLayout.addLayout(color_lay)
        lay.addWidget(color_card)

        about = CaptionLabel("内容锻造师 ContentForge · 设计预览 v0.2 · 本地运行，数据不出本机")
        about.setTextColor("#8a8f99", "#9aa0a8")
        lay.addWidget(about)
        lay.addStretch()

    def _make_swatch(self, name: str, hexv: str):
        w = QWidget()
        w.setCursor(Qt.CursorShape.PointingHandCursor)
        lay = QVBoxLayout(w)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(6)
        dot = QFrame()
        dot.setFixedSize(40, 40)
        dot.setStyleSheet(f"QFrame {{ background: {hexv}; border-radius: 20px; }}")
        lab = CaptionLabel(name)
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(dot, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(lab)

        def pick():
            setThemeColor(hexv)
            InfoBar.success("已换肤", f"主题色已切换为「{name}」", parent=self, duration=1500)

        w.mouseReleaseEvent = lambda e: pick()
        return w


# ==================== 占位页 ====================

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


# ==================== 主窗口 ====================

class PreviewWindow(FluentWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("内容锻造师 ContentForge · 设计预览")
        self.resize(1180, 780)
        setTheme(Theme.LIGHT)
        setThemeColor("#3370ff")
        # Windows 11 开启 Mica 云母效果
        try:
            self.setMicaEffectEnabled(True)
        except Exception:
            pass

        # 导航面板默认展开（展示两级树形结构）
        self.navigationInterface.setExpandWidth(208)
        self.navigationInterface.expand(False)

        # 能力组（父节点）
        self.text_group = ReservedPage("g_text", "生文", "文字内容生产能力")
        self.image_group = ReservedPage("g_image", "生图", "图片生成能力（预留）")
        self.video_group = ReservedPage("g_video", "生视频", "视频生成能力（预留）")

        # 页面
        self.wechat = WechatPage(self)
        self.toutiao = ReservedPage("toutiao", "头条号", "生文 → 头条号渠道即将上线")
        self.image_gen = ReservedPage("image_gen", "配图生成", "生图能力即将上线")
        self.video_gen = ReservedPage("video_gen", "视频生成", "生视频能力即将上线")
        self.history = HistoryPage(self)
        self.api = ApiConfigPage(self)
        self.channel = ChannelPage(self)
        self.settings = SettingsPage(self)

        # 两级树形导航：能力 → 渠道
        self.addSubInterface(self.text_group, FIF.DOCUMENT, "生文")
        self.addSubInterface(self.wechat, FIF.CHAT, "微信公众号", parent=self.text_group)
        self.addSubInterface(self.toutiao, FIF.ALIGNMENT, "头条号", parent=self.text_group)
        self.addSubInterface(self.image_group, FIF.PHOTO, "生图")
        self.addSubInterface(self.image_gen, FIF.BRUSH, "配图生成", parent=self.image_group)
        self.addSubInterface(self.video_group, FIF.VIDEO, "生视频")
        self.addSubInterface(self.video_gen, FIF.PLAY, "视频生成", parent=self.video_group)

        self.addSubInterface(self.history, FIF.HISTORY, "历史记录")

        # 底部设置区
        self.addSubInterface(self.api, FIF.GLOBE, "API 配置", position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.channel, FIF.TAG, "渠道管理", position=NavigationItemPosition.BOTTOM)
        self.addSubInterface(self.settings, FIF.SETTING, "偏好设置", position=NavigationItemPosition.BOTTOM)

        # 默认打开工作台
        self.switchTo(self.wechat)


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    win = PreviewWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

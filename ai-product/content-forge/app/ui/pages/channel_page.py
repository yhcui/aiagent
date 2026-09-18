"""
ContentForge
页面：渠道管理
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
)

from qfluentwidgets import (
    FluentIcon as FIF,
    ElevatedCardWidget, PushButton, Dialog, TextEdit,
    BodyLabel, CaptionLabel, StrongBodyLabel,
    SmoothScrollArea as ScrollArea,
)

from app.ui.components import PageHeader, StatusPill


class ChannelPage(ScrollArea):
    def __init__(self, channel_manager, parent=None):
        super().__init__(parent)
        self.channel_manager = channel_manager
        self.setObjectName("channel")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader(
            "渠道管理",
            "渠道 = 系统提示词 + 可选专属 API 配置 · 新增渠道即插即用"
        ))

        channels = self.channel_manager.get_all_channels()
        for channel in channels:
            card = ElevatedCardWidget()
            root = QHBoxLayout(card)
            root.setContentsMargins(16, 14, 16, 14)
            body = QVBoxLayout()
            body.setSpacing(4)

            name = StrongBodyLabel(channel.display_name)
            desc = CaptionLabel(f"{channel.name} · {'内置' if channel.is_builtin else '自定义'}")
            desc.setTextColor("#8a8f99", "#9aa0a8")

            body.addWidget(name)
            body.addWidget(desc)
            root.addLayout(body, stretch=1)

            if channel.is_active:
                edit = PushButton(FIF.EDIT, "编辑提示词")
                edit.clicked.connect(lambda: self._edit_prompt(channel))
                root.addWidget(edit)
            else:
                pill = StatusPill("pending")
                pill.label.setText("已停用")
                root.add(pill)

            lay.addWidget(card)

        lay.addStretch()

    def _edit_prompt(self, channel):
        dlg = Dialog("编辑系统提示词", "", self.window())
        dlg.contentLabel.setVisible(False)
        edit = TextEdit(dlg)
        edit.setPlainText(channel.system_prompt)
        edit.setMinimumSize(520, 320)
        dlg.textLayout.addWidget(edit)
        dlg.yesButton.setText("保存")
        dlg.cancelButton.setText("取消")
        dlg.accepted.connect(lambda: self._save_channel_prompt(channel, edit.toPlainText()))
        dlg.exec()

    def _save_channel_prompt(self, channel, new_prompt):
        channel.system_prompt = new_prompt
        self.channel_manager.update_channel(channel)
        QMessageBox.information(self, "已保存", f"「{channel.display_name}」的系统提示词已更新")

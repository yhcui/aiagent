"""
ContentForge
页面：通用设置
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
)

from qfluentwidgets import (
    FluentIcon as FIF,
    HeaderCardWidget,
    PrimaryPushButton, PushButton,
    LineEdit, ComboBox,
    BodyLabel, CaptionLabel,
    InfoBar,
    SmoothScrollArea as ScrollArea,
)

from app.ui.components import PageHeader


class SettingsPage(ScrollArea):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("settings")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader("通用设置", "数据存储、日志、界面等全局设置"))

        # 数据存储
        c1 = HeaderCardWidget()
        c1.setTitle("数据存储")
        c1_lay = QVBoxLayout()
        c1_lay.setSpacing(12)

        dir_row = QHBoxLayout()
        dir_lbl = BodyLabel("存储路径")
        dir_lbl.setFixedWidth(90)
        dir_row.addWidget(dir_lbl)
        self.data_dir_input = LineEdit()
        self.data_dir_input.setText(str(config.data_dir))
        dir_row.addWidget(self.data_dir_input, stretch=1)
        browse_btn = PushButton("浏览")
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(browse_btn)
        c1_lay.addLayout(dir_row)

        c1.viewLayout.addLayout(c1_lay)
        lay.addWidget(c1)

        # 日志设置
        c2 = HeaderCardWidget()
        c2.setTitle("日志")
        c2_lay = QVBoxLayout()
        c2_lay.setSpacing(12)

        log_row = QHBoxLayout()
        log_lbl = BodyLabel("日志级别")
        log_lbl.setFixedWidth(90)
        log_row.addWidget(log_lbl)
        self.log_combo = ComboBox()
        self.log_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_combo.setCurrentText(config.log_level)
        log_row.addWidget(self.log_combo, stretch=1)
        c2_lay.addLayout(log_row)

        c2.viewLayout.addLayout(c2_lay)
        lay.addWidget(c2)

        # 界面设置
        c3 = HeaderCardWidget()
        c3.setTitle("界面")
        c3_lay = QVBoxLayout()
        c3_lay.setSpacing(12)

        ch_row = QHBoxLayout()
        ch_lbl = BodyLabel("默认渠道")
        ch_lbl.setFixedWidth(90)
        ch_row.addWidget(ch_lbl)
        self.default_channel = ComboBox()
        self.default_channel.addItem("微信公众号", "wechat")
        self.default_channel.addItem("头条号", "toutiao")
        ch_row.addWidget(self.default_channel, stretch=1)
        c3_lay.addLayout(ch_row)

        c3.viewLayout.addLayout(c3_lay)
        lay.addWidget(c3)

        # 保存按钮
        save_row = QHBoxLayout()
        save_row.addStretch()
        save_btn = PrimaryPushButton(FIF.SAVE, "保存设置")
        save_btn.clicked.connect(self._save_settings)
        save_row.addWidget(save_btn)
        lay.addLayout(save_row)

        lay.addStretch()

    def _browse_dir(self):
        from PyQt6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择数据存储目录")
        if dir_path:
            self.data_dir_input.setText(dir_path)

    def _save_settings(self):
        self.config.data_dir = self.data_dir_input.text()
        self.config.log_level = self.log_combo.currentText()
        self.config.save()
        QMessageBox.information(self, "已保存", "通用设置已保存")

"""
ContentForge
页面：API 配置（支持 text / image / video 独立配置）
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMessageBox,
)

from qfluentwidgets import (
    FluentIcon as FIF,
    HeaderCardWidget,
    PrimaryPushButton, PushButton,
    LineEdit, PasswordLineEdit,
    BodyLabel, CaptionLabel,
    SmoothScrollArea as ScrollArea,
)

from app.ui.components import PageHeader


class _AbilityConfigCard(QWidget):
    """单个能力（text/image/video）的 API 配置卡片"""

    def __init__(self, ability: str, config, parent=None):
        super().__init__(parent)
        self.ability = ability
        self.config = config

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        current = self.config.get_api_config(ability)
        placeholders = {
            "text": {
                "base_url": "https://api.siliconflow.cn/v1",
                "model_id": "Qwen/Qwen2.5-72B-Instruct",
                "tip": "用于生成文章观点和图文内容",
            },
            "image": {
                "base_url": "https://api.siliconflow.cn/v1",
                "model_id": "black-forest-labs/FLUX.1-schnell",
                "tip": "用于为文章生成前后两张配图（可选）",
            },
            "video": {
                "base_url": "",
                "model_id": "",
                "tip": "生视频能力预留",
            },
        }
        ph = placeholders.get(ability, placeholders["text"])

        tip = CaptionLabel(ph["tip"])
        tip.setTextColor("#8a8f99", "#9aa0a8")
        lay.addWidget(tip)

        self.base_url = self._row(lay, "接口地址 base_url", ph["base_url"], current.get("base_url", ""))
        self.api_key = self._row(lay, "API Key", "sk-••••••••••••••••", current.get("api_key", ""), password=True)
        self.model_id = self._row(lay, "模型唯一标识 model_id", ph["model_id"], current.get("model_id", ""))

        row = QHBoxLayout()
        test = PushButton(FIF.SYNC, "测试连接")
        test.clicked.connect(self._test_connection)
        row.addWidget(test)
        row.addStretch()
        save = PrimaryPushButton(FIF.SAVE, "保存")
        save.clicked.connect(self._save_config)
        row.addWidget(save)
        lay.addLayout(row)
        lay.addStretch()

    def _row(self, form: QVBoxLayout, label: str, placeholder: str, value: str = "", password=False):
        row = QHBoxLayout()
        lab = BodyLabel(label)
        lab.setFixedWidth(120)
        row.addWidget(lab)
        inp = PasswordLineEdit() if password else LineEdit()
        inp.setPlaceholderText(placeholder)
        if value:
            inp.setText(value)
        row.addWidget(inp, stretch=1)
        form.addLayout(row)
        return inp

    def _test_connection(self):
        base_url = self.base_url.text().strip()
        api_key = self.api_key.text().strip()
        model_id = self.model_id.text().strip()

        if not base_url or not api_key:
            QMessageBox.warning(self, "配置不完整", "请填写 base_url 和 api_key")
            return

        try:
            from app.core.content_generator import ContentGenerator
            test_config = type('TestConfig', (), {
                'get_api_config': lambda self, ability: {
                    "base_url": base_url,
                    "api_key": api_key,
                    "model_id": model_id
                }
            })()
            generator = ContentGenerator(test_config)
            ok = generator.test_connection(base_url, api_key, model_id)
            if ok:
                QMessageBox.information(self, "连接成功", f"{self.ability} API 连接测试通过 ✅")
            else:
                QMessageBox.warning(self, "连接失败", "无法连接到服务器，请检查配置是否正确")
        except Exception as e:
            QMessageBox.warning(self, "连接失败", f"连接测试出错：{e}")

    def _save_config(self):
        base_url = self.base_url.text().strip()
        api_key = self.api_key.text().strip()
        model_id = self.model_id.text().strip()

        if not base_url or not api_key:
            QMessageBox.warning(self, "配置不完整", "请填写完整的 API 配置")
            return

        self.config.set_api_config(self.ability, {
            "base_url": base_url,
            "api_key": api_key,
            "model_id": model_id,
        })
        QMessageBox.information(self, "已保存", f"{self.ability} API 配置已保存到本地")


class ApiConfigPage(ScrollArea):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setObjectName("api")
        self.setWidgetResizable(True)
        canvas = QWidget()
        self.setWidget(canvas)
        self.enableTransparentBackground()
        lay = QVBoxLayout(canvas)
        lay.setContentsMargins(28, 16, 28, 24)
        lay.setSpacing(14)

        lay.addWidget(PageHeader(
            "API 配置",
            "生文 / 生图 / 生视频 独立配置 · API Key 加密存储于系统钥匙串"
        ))

        tabs = QTabWidget()
        tabs.addTab(_AbilityConfigCard("text", config), "生文")
        tabs.addTab(_AbilityConfigCard("image", config), "生图")
        tabs.addTab(_AbilityConfigCard("video", config), "生视频（预留）")
        lay.addWidget(tabs)

        lay.addStretch()

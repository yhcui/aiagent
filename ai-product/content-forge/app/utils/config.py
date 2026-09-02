"""配置文件管理"""
import json
import pathlib
from pathlib import Path


class AppConfig:
    """应用全局配置"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.data_dir = self.base_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.data_dir / "config.json"
        self._load()

    def _load(self):
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = self._default_config()
            self._save()

    def _default_config(self):
        return {
            "api_config": {
                "text": {
                    "default": {
                        "base_url": "https://api.siliconflow.cn/v1",
                        "api_key": "",
                        "model_id": "Qwen/Qwen2.5-72B-Instruct",
                    },
                    "overrides": {},
                },
                "image": {"default": {"base_url": "", "api_key": "", "model_id": ""}, "overrides": {}},
                "video": {"default": {"base_url": "", "api_key": "", "model_id": ""}, "overrides": {}},
            },
            "data_dir": str(self.data_dir),
            "log_level": "INFO",
            "auto_start": False,
        }

    def _save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value):
        self._data[key] = value
        self._save()

    def get_api_config(self, ability: str, channel: str = None):
        """获取 API 配置（能力 + 可选渠道覆盖）"""
        ac = self._data.get("api_config", {}).get(ability, {})
        if channel:
            override = ac.get("overrides", {}).get(channel, {})
            if override and override.get("api_key"):
                return override
        return ac.get("default", {})

    def set_api_config(self, ability: str, config: dict, channel: str = None):
        """设置 API 配置"""
        if "api_config" not in self._data:
            self._data["api_config"] = {}
        if ability not in self._data["api_config"]:
            self._data["api_config"][ability] = {"default": {}, "overrides": {}}
        if channel:
            self._data["api_config"][ability]["overrides"][channel] = config
        else:
            self._data["api_config"][ability]["default"] = config
        self._save()

    @property
    def api_config(self):
        return self._data.get("api_config", {})

    @property
    def log_level(self):
        return self._data.get("log_level", "INFO")

    @log_level.setter
    def log_level(self, value):
        self._data["log_level"] = value
        self._save()

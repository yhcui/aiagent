"""配置文件管理"""
import json
import pathlib
from pathlib import Path


class AppConfig:
    """应用全局配置"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self._data_dir = self.base_dir / "data"
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._data = {}  # 初始化，供 data_dir 属性读取
        self.config_file = self._data_dir / "config.json"
        self._load()
        # 加载完成后同步用户配置的 data_dir
        configured = self._data.get("data_dir")
        if configured:
            self._data_dir = Path(configured)
            self._data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def data_dir(self) -> Path:
        """数据存储根目录"""
        return self._data_dir

    @data_dir.setter
    def data_dir(self, value):
        """设置数据存储根目录（同步内存、配置文件并创建目录）"""
        path = Path(value)
        self._data_dir = path
        self._data["data_dir"] = str(path)
        path.mkdir(parents=True, exist_ok=True)
        self._save()

    def save(self):
        """公开的保存方法（持久化当前配置到文件）"""
        self._save()

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
            # 目录配置（独立管理）
            "directory_config": {
                "exports": "exports",           # 导出文件目录
                "images": "images",             # 生成的图片目录
                "templates": "templates",        # 模板目录
                "logs": "logs",                 # 日志目录
            },
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

    def get_directory(self, dir_key: str) -> Path:
        """
        获取用户配置的目录路径
        支持相对路径（相对于 data_dir）和绝对路径

        Args:
            dir_key: 目录键名，如 "exports", "images", "templates", "logs"

        Returns:
            解析后的完整路径
        """
        directory_config = self._data.get("directory_config", {})
        dir_value = directory_config.get(dir_key, dir_key)

        # 转为 Path 对象
        dir_path = Path(dir_value)

        # 如果是相对路径，则基于 data_dir
        if not dir_path.is_absolute():
            dir_path = self.data_dir / dir_path

        return dir_path

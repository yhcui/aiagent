"""渠道数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class Channel:
    id: str
    name: str  # 内部标识，如 wechat
    display_name: str  # 显示名称，如「微信公众号」
    system_prompt: str  # 系统提示词
    is_active: bool = True
    is_builtin: bool = False  # 内置渠道不可删除
    created_at: datetime = field(default_factory=datetime.now)

    @staticmethod
    def create(name: str, display_name: str, system_prompt: str, is_builtin: bool = False) -> "Channel":
        return Channel(
            id=str(uuid.uuid4()),
            name=name,
            display_name=display_name,
            system_prompt=system_prompt,
            is_builtin=is_builtin,
        )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "display_name": self.display_name,
            "system_prompt": self.system_prompt,
            "is_active": self.is_active,
            "is_builtin": self.is_builtin,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, d: dict):
        d = dict(d)
        if d.get("created_at") and isinstance(d["created_at"], str):
            from datetime import datetime
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        return cls(**d)

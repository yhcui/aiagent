"""任务数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    url: str
    user_opinion: str
    channel: str = "wechat"
    status: TaskStatus = TaskStatus.PENDING
    original_content: str = ""
    generated_content: str = ""
    error_message: str = ""
    image_paths: list[str] = field(default_factory=list)  # 生成的图片路径列表
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: datetime = None

    @staticmethod
    def create(url: str, opinion: str, channel: str = "wechat") -> "Task":
        return Task(
            id=str(uuid.uuid4()),
            url=url,
            user_opinion=opinion,
            channel=channel,
        )

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "user_opinion": self.user_opinion,
            "channel": self.channel,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "original_content": self.original_content,
            "generated_content": self.generated_content,
            "error_message": self.error_message,
            "image_paths": self.image_paths,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, d: dict):
        d = dict(d)
        d["status"] = TaskStatus(d.get("status", "pending"))
        if d.get("created_at") and isinstance(d["created_at"], str):
            d["created_at"] = datetime.fromisoformat(d["created_at"])
        if d.get("updated_at") and isinstance(d["updated_at"], str):
            d["updated_at"] = datetime.fromisoformat(d["updated_at"])
        if d.get("completed_at") and isinstance(d["completed_at"], str):
            d["completed_at"] = datetime.fromisoformat(d["completed_at"])
        return cls(**d)

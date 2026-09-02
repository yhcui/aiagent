"""Task 模型测试"""
import pytest
from datetime import datetime
from app.models.task import Task, TaskStatus


class TestTaskCreate:
    """Task.create() 测试"""

    def test_create_basic(self):
        """基本创建"""
        task = Task.create(
            url="https://example.com",
            opinion="测试观点"
        )
        assert task.id is not None
        assert task.url == "https://example.com"
        assert task.user_opinion == "测试观点"
        assert task.channel == "wechat"
        assert task.status == TaskStatus.PENDING
        assert task.original_content == ""
        assert task.generated_content == ""

    def test_create_with_channel(self):
        """指定渠道"""
        task = Task.create(
            url="https://example.com",
            opinion="观点",
            channel="toutiao"
        )
        assert task.channel == "toutiao"

    def test_create_unique_id(self):
        """每个任务有唯一ID"""
        t1 = Task.create(url="a", opinion="b")
        t2 = Task.create(url="a", opinion="b")
        assert t1.id != t2.id


class TestTaskSerialization:
    """任务序列化/反序列化测试"""

    def test_to_dict(self, sample_task):
        """转字典"""
        d = sample_task.to_dict()
        assert d["id"] == sample_task.id
        assert d["url"] == sample_task.url
        assert d["user_opinion"] == sample_task.user_opinion
        assert d["status"] == "pending"

    def test_from_dict(self):
        """从字典恢复"""
        data = {
            "id": "test-id-123",
            "url": "https://test.com",
            "user_opinion": "测试观点",
            "channel": "wechat",
            "status": "completed",
            "original_content": "原文",
            "generated_content": "生成内容",
            "error_message": "",
            "created_at": "2024-01-01T10:00:00",
            "updated_at": "2024-01-01T11:00:00",
            "completed_at": "2024-01-01T11:00:00",
        }
        task = Task.from_dict(data)
        assert task.id == "test-id-123"
        assert task.url == "https://test.com"
        assert task.status == TaskStatus.COMPLETED
        assert task.original_content == "原文"

    def test_roundtrip(self, sample_task):
        """往返序列化"""
        sample_task.original_content = "测试原文"
        sample_task.generated_content = "生成结果"

        d = sample_task.to_dict()
        restored = Task.from_dict(d)

        assert restored.id == sample_task.id
        assert restored.url == sample_task.url
        assert restored.original_content == sample_task.original_content
        assert restored.generated_content == sample_task.generated_content


class TestTaskStatus:
    """任务状态测试"""

    def test_status_enum_values(self):
        """状态枚举值"""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.PROCESSING.value == "processing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"

    def test_status_from_string(self):
        """从字符串创建状态"""
        assert TaskStatus("pending") == TaskStatus.PENDING
        assert TaskStatus("completed") == TaskStatus.COMPLETED

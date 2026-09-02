"""TaskManager 测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.models.task import Task, TaskStatus


class TestTaskManagerBasics:
    """TaskManager 基础测试"""

    def test_add_task(self, task_manager):
        """添加任务"""
        task = task_manager.add_task(
            url="https://example.com",
            opinion="测试观点"
        )

        assert task is not None
        assert task.url == "https://example.com"
        assert task.user_opinion == "测试观点"
        assert task.status == TaskStatus.PENDING
        assert len(task_manager.tasks) == 1

    def test_add_task_with_original_content(self, task_manager):
        """添加任务时传入原文内容"""
        task = task_manager.add_task(
            url="https://example.com",
            opinion="测试观点",
            original_content="这是原文内容"
        )

        assert task.original_content == "这是原文内容"

    def test_add_multiple_tasks(self, task_manager):
        """批量添加任务"""
        items = [
            ("https://a.com", "观点A"),
            ("https://b.com", "观点B"),
            ("https://c.com", "观点C"),
        ]
        tasks = task_manager.add_tasks(items)

        assert len(tasks) == 3
        assert len(task_manager.tasks) >= 3

    def test_remove_task(self, task_manager):
        """移除任务"""
        task = task_manager.add_task(url="https://example.com", opinion="测试")
        initial_count = len(task_manager.tasks)

        task_manager.remove_task(task.id)
        assert len(task_manager.tasks) < initial_count

    def test_get_task_by_id(self, task_manager):
        """通过ID获取任务"""
        task = task_manager.add_task(url="https://example.com", opinion="测试")
        retrieved = task_manager.get_task(task.id)

        assert retrieved is not None
        assert retrieved.id == task.id


class TestTaskProcessing:
    """任务处理测试"""

    def test_process_task_with_existing_content(self, task_manager):
        """处理已有原文的任务（跳过抓取）"""
        task = task_manager.add_task(
            url="https://example.com",
            opinion="我的观点",
            original_content="已有的原文"
        )

        # 验证任务有原文
        assert task.original_content == "已有的原文"

    def test_process_task_content_too_short(self, task_manager):
        """原文过短处理"""
        task = task_manager.add_task(
            url="https://example.com",
            opinion="观点"
        )

        # 模拟获取过短内容
        task.original_content = "太短"
        task_manager._update_task(task)

        retrieved = task_manager.get_task(task.id)
        # 任务应该仍保留
        assert retrieved is not None


class TestTaskManagerCallbacks:
    """回调测试"""

    def test_add_listener(self, task_manager):
        """添加监听器"""
        callback_result = []

        def on_task_updated(task):
            callback_result.append(task.id)

        task_manager.add_listener(on_task_updated)
        assert len(task_manager._listeners) == 1

    def test_notify_listeners(self, task_manager):
        """通知监听器"""
        callback_result = []

        def on_task_updated(task):
            callback_result.append((task.id, task.status))

        task_manager.add_listener(on_task_updated)

        task = task_manager.add_task(url="https://example.com", opinion="测试")
        assert len(callback_result) >= 1
        assert callback_result[0][0] == task.id

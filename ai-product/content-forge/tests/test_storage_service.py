"""StorageService 测试"""
import pytest
from app.models.task import Task, TaskStatus
from app.models.channel import Channel


class TestStorageServiceInit:
    """数据库初始化测试"""

    def test_init_db(self, storage_service):
        """数据库初始化"""
        # 验证表存在
        conn = storage_service._get_conn()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [t[0] for t in tables]

        assert "tasks" in table_names
        assert "channels" in table_names
        assert "config" in table_names

    def test_init_builtin_channel(self, storage_service):
        """内置渠道初始化"""
        channels = storage_service.get_all_channels()
        assert len(channels) > 0

        wechat = storage_service.get_channel("wechat")
        assert wechat is not None
        assert wechat.name == "wechat"
        assert "微信公众号" in wechat.display_name


class TestTaskCrud:
    """任务 CRUD 测试"""

    def test_save_and_get_task(self, storage_service, sample_task):
        """保存和获取任务"""
        storage_service.save_task(sample_task)
        retrieved = storage_service.get_task(sample_task.id)

        assert retrieved is not None
        assert retrieved.id == sample_task.id
        assert retrieved.url == sample_task.url
        assert retrieved.user_opinion == sample_task.user_opinion
        assert retrieved.status == TaskStatus.PENDING

    def test_update_task(self, storage_service, sample_task):
        """更新任务"""
        storage_service.save_task(sample_task)

        sample_task.status = TaskStatus.COMPLETED
        sample_task.generated_content = "生成的内容"
        storage_service.update_task(sample_task)

        retrieved = storage_service.get_task(sample_task.id)
        assert retrieved.status == TaskStatus.COMPLETED
        assert retrieved.generated_content == "生成的内容"

    def test_get_all_tasks(self, storage_service):
        """获取所有任务"""
        # 创建多个任务
        for i in range(3):
            task = Task.create(url=f"https://example.com/{i}", opinion=f"观点{i}")
            storage_service.save_task(task)

        tasks = storage_service.get_all_tasks()
        assert len(tasks) >= 3

    def test_get_tasks_by_channel(self, storage_service):
        """按渠道筛选任务"""
        t1 = Task.create(url="https://a.com", opinion="a", channel="wechat")
        t2 = Task.create(url="https://b.com", opinion="b", channel="toutiao")
        storage_service.save_task(t1)
        storage_service.save_task(t2)

        wechat_tasks = storage_service.get_all_tasks(channel="wechat")
        toutiao_tasks = storage_service.get_all_tasks(channel="toutiao")

        assert len(wechat_tasks) >= 1
        assert len(toutiao_tasks) >= 1
        assert all(t.channel == "wechat" for t in wechat_tasks)
        assert all(t.channel == "toutiao" for t in toutiao_tasks)

    def test_delete_task(self, storage_service, sample_task):
        """删除任务"""
        storage_service.save_task(sample_task)
        assert storage_service.get_task(sample_task.id) is not None

        storage_service.delete_task(sample_task.id)
        assert storage_service.get_task(sample_task.id) is None


class TestChannelCrud:
    """渠道 CRUD 测试"""

    def test_save_and_get_channel(self, storage_service):
        """保存和获取渠道"""
        channel = Channel.create(
            name="test-channel",
            display_name="测试渠道",
            system_prompt="测试提示词"
        )
        storage_service.save_channel(channel)

        retrieved = storage_service.get_channel("test-channel")
        assert retrieved is not None
        assert retrieved.name == "test-channel"
        assert retrieved.display_name == "测试渠道"

    def test_get_active_channels_only(self, storage_service):
        """只获取活跃渠道"""
        active = storage_service.get_all_channels(active_only=True)
        assert all(c.is_active for c in active)


class TestConfig:
    """配置测试"""

    def test_set_and_get_config(self, storage_service):
        """设置和获取配置"""
        storage_service.set_config("test_key", "test_value")
        value = storage_service.get_config("test_key")
        assert value == "test_value"

    def test_get_nonexistent_config(self, storage_service):
        """获取不存在的配置"""
        value = storage_service.get_config("nonexistent_key")
        assert value is None

    def test_override_config(self, storage_service):
        """覆盖配置"""
        storage_service.set_config("key", "value1")
        storage_service.set_config("key", "value2")
        assert storage_service.get_config("key") == "value2"

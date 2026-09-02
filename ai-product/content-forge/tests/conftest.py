"""Pytest 配置和 fixtures"""
import sys
from pathlib import Path

# 将项目根目录加入路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
import tempfile
import shutil
from app.models.task import Task, TaskStatus
from app.services.storage_service import StorageService
from app.core.channel_manager import ChannelManager


class MockConfig:
    """测试用配置"""
    def __init__(self):
        self.data_dir = Path(tempfile.mkdtemp())
        self.api_provider = "openai"
        self.api_key = "test-key"
        self.model = "gpt-3.5-turbo"

    def cleanup(self):
        shutil.rmtree(self.data_dir, ignore_errors=True)


@pytest.fixture
def mock_config():
    """创建测试用配置"""
    config = MockConfig()
    yield config
    config.cleanup()


@pytest.fixture
def storage_service(mock_config):
    """创建测试用存储服务"""
    service = StorageService(mock_config)
    service.init_db()
    yield service
    # 清理
    if service._conn:
        service._conn.close()
    mock_config.cleanup()


@pytest.fixture
def channel_manager(storage_service):
    """创建测试用渠道管理器"""
    return ChannelManager(storage_service)


@pytest.fixture
def task_manager(storage_service, channel_manager, mock_config):
    """创建测试用任务管理器"""
    from app.core.task_manager import TaskManager
    manager = TaskManager(storage_service, channel_manager, mock_config)
    yield manager


@pytest.fixture
def sample_task():
    """创建示例任务"""
    return Task.create(
        url="https://example.com/article",
        opinion="这是一个测试观点",
        channel="wechat"
    )

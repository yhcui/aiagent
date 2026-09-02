# ContentForge 测试指南

## 运行测试

```bash
# 安装测试依赖（如果需要）
pip install pytest pytest-cov pytest-mock

# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_task_model.py

# 运行特定测试类
pytest tests/test_task_model.py::TestTaskCreate

# 运行特定测试
pytest tests/test_task_model.py::TestTaskCreate::test_create_basic

# 显示详细输出
pytest tests/ -v

# 显示覆盖率
pytest tests/ --cov=app --cov-report=term-missing
```

## 测试结构

```
tests/
├── conftest.py           # pytest 配置和 fixtures
├── test_task_model.py    # Task 模型测试
├── test_content_fetcher.py # 内容抓取测试
├── test_storage_service.py # 存储服务测试
└── test_task_manager.py  # 任务管理器测试
```

## 编写新测试

```python
import pytest
from app.core.content_fetcher import ContentFetcher

class TestYourClass:
    """测试类使用 Test 前缀"""

    def test_your_method(self):
        """测试方法使用 test_ 前缀"""
        # Arrange - 准备测试数据
        fetcher = ContentFetcher()

        # Act - 执行被测方法
        result = fetcher.is_valid_url("https://example.com")

        # Assert - 验证结果
        assert result is True
```

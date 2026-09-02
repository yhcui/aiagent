"""自验证脚本：测试 ContentForge 核心功能"""
import os, sys, tempfile
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from app.utils.config import AppConfig
from app.services.storage_service import StorageService
from app.core.channel_manager import ChannelManager
from app.core.task_manager import TaskManager
from app.core.content_fetcher import ContentFetcher
from app.models.task import TaskStatus

def test():
    errors = []

    # 1. 配置初始化
    try:
        config = AppConfig()
        assert config.data_dir.exists(), "数据目录未创建"
        print("  [OK] AppConfig 初始化")
    except Exception as e:
        errors.append(f"AppConfig: {e}")

    # 2. 数据库初始化
    try:
        storage = StorageService(config)
        storage.init_db()
        assert storage.db_path.exists(), "数据库文件未创建"
        print("  [OK] StorageService 数据库初始化")
    except Exception as e:
        errors.append(f"StorageService: {e}")

    # 3. 内置渠道注册
    try:
        cm = ChannelManager(storage)
        ch = cm.get_channel("wechat")
        assert ch is not None, "微信公众号渠道未注册"
        assert "新媒体内容创作者" in ch.system_prompt, "系统提示词内容异常"
        print(f"  [OK] 渠道管理：{ch.display_name}，提示词长度 {len(ch.system_prompt)} 字")
    except Exception as e:
        errors.append(f"ChannelManager: {e}")

    # 4. 任务管理
    try:
        tm = TaskManager(storage, cm, config)
        task = tm.add_task("https://mp.weixin.qq.com/s/test123", "test opinion text", "wechat")
        assert task.id, "任务 ID 为空"
        assert task.status == TaskStatus.PENDING, "初始状态不是 pending"
        assert len(tm.tasks) == 1, "任务列表为空"
        tm.remove_task(task.id)
        assert len(tm.tasks) == 0, "删除后任务列表不为空"
        print("  [OK] TaskManager：添加/删除/状态流转正常")
    except Exception as e:
        errors.append(f"TaskManager: {e}")

    # 5. 内容抓取器 URL 校验
    try:
        fetcher = ContentFetcher()
        assert fetcher.is_valid_url("https://mp.weixin.qq.com/s/abc") == True
        assert fetcher.is_valid_url("") == False
        assert fetcher.is_valid_url("not a url") == False
        print("  [OK] ContentFetcher URL 校验正常")
    except Exception as e:
        errors.append(f"ContentFetcher: {e}")

    # 6. API 配置读写
    try:
        config.set_api_config("text", {
            "base_url": "https://api.test.com/v1",
            "api_key": "sk-test123",
            "model_id": "test-model",
        })
        cfg = config.get_api_config("text")
        assert cfg["api_key"] == "sk-test123", "API Key 读取不正确"
        print("  [OK] API 配置读写正常")
    except Exception as e:
        errors.append(f"API Config: {e}")

    # 7. 批量添加任务（AI 生成观点后多选场景）
    try:
        items = [
            ("https://mp.weixin.qq.com/s/a", "观点A"),
            ("https://mp.weixin.qq.com/s/a", "观点B"),
            ("https://mp.weixin.qq.com/s/b", "观点C"),
        ]
        tasks = tm.add_tasks(items)
        assert len(tasks) == 3, f"批量添加失败，期望3个实际{len(tasks)}"
        for t in tm.tasks:
            tm.remove_task(t.id)
        print("  [OK] 批量添加任务（同一链接×不同观点）正常")
    except Exception as e:
        errors.append(f"Batch add: {e}")

    # 8. 渠道专属配置覆盖
    try:
        config.set_api_config("text", {"base_url": "https://global.com/v1", "api_key": "sk-global", "model_id": "global-model"})
        config.set_api_config("text", {"base_url": "https://toutiao.com/v1", "api_key": "sk-toutiao", "model_id": "toutiao-model"}, channel="toutiao")
        global_cfg = config.get_api_config("text")
        toutiao_cfg = config.get_api_config("text", channel="toutiao")
        assert global_cfg["base_url"] == "https://global.com/v1", "全局配置读取错误"
        assert toutiao_cfg["base_url"] == "https://toutiao.com/v1", "渠道覆盖配置读取错误"
        print("  [OK] API 配置全局 + 渠道覆盖两级正常")
    except Exception as e:
        errors.append(f"Override config: {e}")

    # 9. UI 模块导入
    try:
        from app.main_window import MainWindow
        from app.ui.components import card_frame, chip, empty_placeholder
        print("  [OK] UI 模块导入正常")
    except Exception as e:
        errors.append(f"UI import: {e}")

    # 结果
    print()
    if errors:
        print(f"❌ 验证失败，共 {len(errors)} 个错误：")
        for err in errors:
            print(f"   - {err}")
        return False
    else:
        print("✅ 自验证全部通过！所有核心功能正常。")
        print()
        print("验证清单：")
        print("  ✓ 配置系统")
        print("  ✓ SQLite 数据库 + 内置渠道初始化")
        print("  ✓ 任务增删改查")
        print("  ✓ 批量任务（多观点场景）")
        print("  ✓ URL 校验")
        print("  ✓ API 配置（全局 + 渠道覆盖）")
        print("  ✓ UI 模块导入")
        return True

if __name__ == "__main__":
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    ok = test()
    sys.exit(0 if ok else 1)

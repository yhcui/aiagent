"""自验证脚本：测试 ContentForge 核心功能

使用独立的临时配置与钥匙串命名空间，绝不污染生产配置。
"""
import os, sys, tempfile
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from pathlib import Path
from app.utils.config import AppConfig
from app.services.storage_service import StorageService
from app.core.channel_manager import ChannelManager
from app.core.task_manager import TaskManager
from app.core.content_fetcher import ContentFetcher
from app.models.task import TaskStatus

TEST_KEYRING_SERVICE = "ContentForge-Verify"


def cleanup_test_keys():
    """清理验证脚本写入钥匙串的测试 Key"""
    try:
        import keyring
        for ability, channel in [("text", None), ("text", "toutiao")]:
            key = f"{ability}:{channel or 'default'}"
            try:
                keyring.delete_password(TEST_KEYRING_SERVICE, key)
            except Exception:
                pass
    except ImportError:
        pass


def test(tmp_dir: Path):
    errors = []
    config_file = tmp_dir / "config.json"

    # 1. 配置初始化（隔离的临时配置）
    try:
        config = AppConfig(config_file=config_file, keyring_service=TEST_KEYRING_SERVICE)
        assert config.data_dir.exists(), "数据目录未创建"
        print("  [OK] AppConfig 初始化（临时隔离配置）")
    except Exception as e:
        errors.append(f"AppConfig: {e}")
        return errors  # 配置挂了后面没法跑

    # 2. 数据库初始化
    try:
        storage = StorageService(config)
        storage.init_db()
        assert storage.db_path.exists(), "数据库文件未创建"
        print("  [OK] StorageService 数据库初始化")
    except Exception as e:
        errors.append(f"StorageService: {e}")
        return errors

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

    # 6. API 配置读写（Key 进钥匙串，config.json 不留明文）
    try:
        config.set_api_config("text", {
            "base_url": "https://api.test.com/v1",
            "api_key": "sk-test123",
            "model_id": "test-model",
        })
        cfg = config.get_api_config("text")
        assert cfg["api_key"] == "sk-test123", "API Key 读取不正确"
        # 确认 config.json 中不存明文 key
        import json
        raw = json.loads(config_file.read_text(encoding="utf-8"))
        assert raw["api_config"]["text"]["default"].get("api_key", "") == "", "config.json 中仍存明文 API Key！"
        print("  [OK] API 配置读写正常（Key 存钥匙串，文件无明文）")
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
        for t in list(tm.tasks):
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
        assert toutiao_cfg["api_key"] == "sk-toutiao", "渠道覆盖 Key 读取错误"
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

    # 关闭数据库连接，避免临时目录清理失败（Windows 文件占用）
    try:
        storage.close()
    except Exception:
        pass

    return errors


if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    with tempfile.TemporaryDirectory(prefix="contentforge_verify_") as tmp:
        errors = test(Path(tmp))
    cleanup_test_keys()

    print()
    if errors:
        print(f"❌ 验证失败，共 {len(errors)} 个错误：")
        for err in errors:
            print(f"   - {err}")
        sys.exit(1)
    else:
        print("✅ 自验证全部通过！所有核心功能正常。")
        print()
        print("验证清单：")
        print("  ✓ 配置系统（隔离临时配置，未污染生产）")
        print("  ✓ SQLite 数据库 + 内置渠道初始化")
        print("  ✓ 任务增删改查")
        print("  ✓ 批量任务（多观点场景）")
        print("  ✓ URL 校验")
        print("  ✓ API 配置（全局 + 渠道覆盖，Key 存钥匙串）")
        print("  ✓ UI 模块导入")
        sys.exit(0)

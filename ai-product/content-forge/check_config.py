"""临时脚本：检查 API 配置"""
import sys
sys.path.insert(0, ".")

from app.utils.config import AppConfig

config = AppConfig()
api_cfg = config.get_api_config('text')

print("=== API 配置检查 ===")
print(f"base_url: {api_cfg.get('base_url', '(空)')}")
print(f"api_key: {'已配置' if api_cfg.get('api_key') else '(未配置)'}")
print(f"model_id: {api_cfg.get('model_id', '(空)')}")

# 测试生成器
from app.core.content_generator import ContentGenerator
try:
    gen = ContentGenerator(config)
    print("\nContentGenerator 初始化: 成功")

    # 测试生成观点
    print("\n=== 测试生成观点 ===")
    test_content = "这是一篇关于人工智能发展的文章，讨论了AI技术的最新进展和未来趋势。人工智能正在改变各行各业，从医疗诊断到自动驾驶，应用范围越来越广泛。"
    opinions = gen.generate_opinions(test_content, "wechat", count=2)
    print(f"生成结果: {len(opinions)} 个观点")
    for i, op in enumerate(opinions, 1):
        print(f"  {i}. [{op.get('tag', 'N/A')}] {op.get('opinion', 'N/A')[:50]}...")

except Exception as e:
    import traceback
    print(f"\n错误: {e}")
    traceback.print_exc()

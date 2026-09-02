"""内容生成器：调用 AI 生成图文或观点"""
from loguru import logger
from app.services.ai_service import AIService


class ContentGenerator:
    """AI 内容生成器"""

    def __init__(self, app_config):
        self.app_config = app_config
        self._ability = "text"  # 当前能力：生文

    def set_ability(self, ability: str):
        self._ability = ability

    def _get_ai_service(self, channel: str = None):
        """获取当前渠道对应的 AI 服务实例"""
        cfg = self.app_config.get_api_config(self._ability, channel)
        if not cfg.get("api_key"):
            raise ValueError("API Key 未配置，请先在「设置 → API 配置」中配置")
        return AIService.create(cfg)

    def generate_opinions(self, original_content: str, channel: str = "wechat", count: int = 5) -> list[dict]:
        """
        基于原文生成 N 个候选观点
        返回 [{"tag": "...", "opinion": "..."}]
        """
        prompt = f"""你是一位资深的内容策划师。请仔细阅读下面的文章内容，然后生成 {count} 个不同角度的个人观点候选。

要求：
1. 每个观点角度不同（如：认同/反驳/延伸/数据/预测/落地等）
2. 每个观点 80-200 字，有具体论据，不是空话
3. 每个观点配一个简短标签（如「落地视角」「反驳视角」「延伸视角」等）
4. 输出 JSON 数组格式，每项包含 tag 和 opinion 字段，不要包含其他内容

文章内容：
---
{original_content[:8000]}
---

请直接输出 JSON 数组，不要有任何额外文字。"""

        system_prompt = "你是一个严格遵循格式的内容助手。你的唯一任务是按照用户要求的格式输出 JSON，不要有任何额外文字、解释或格式混乱。"

        try:
            service = self._get_ai_service(channel)
            import json
            result = service.generate(system_prompt, prompt)
            # 尝试解析 JSON
            result = result.strip()
            if result.startswith("```"):
                # 去掉 markdown 代码块
                lines = result.split("\n")
                lines = [l for l in lines if not l.startswith("```")]
                result = "\n".join(lines)
            opinions = json.loads(result)
            logger.info(f"成功生成 {len(opinions)} 个候选观点")
            return opinions[:count]
        except json.JSONDecodeError as e:
            logger.error(f"观点 JSON 解析失败：{e}，原始结果：{result[:200]}")
            raise ValueError(f"AI 返回格式错误：{e}。请检查 API 配置是否正确。")
        except Exception as e:
            error_msg = str(e)
            # 检测常见的 API 配置错误
            if "<!DOCTYPE" in error_msg or "<html" in error_msg.lower():
                raise ValueError("API 返回了网页内容而非有效响应，请检查 API 地址和 Key 是否正确配置。")
            if "401" in error_msg or "403" in error_msg:
                raise ValueError("API 认证失败，请检查 API Key 是否正确。")
            if "404" in error_msg:
                raise ValueError("API 地址无效，请检查 base_url 配置。")
            if "timeout" in error_msg.lower():
                raise ValueError("API 请求超时，请检查网络连接或稍后重试。")
            logger.error(f"生成观点失败：{e}")
            raise ValueError(f"AI 生成失败：{e}")

    def generate_article(self, system_prompt: str, user_opinion: str, original_content: str) -> str:
        """
        基于系统提示词 + 用户观点 + 原文，生成新图文
        """
        user_prompt = f"""# 用户观点
{user_opinion}

# 原文内容
{original_content[:8000]}
"""

        try:
            service = self._get_ai_service("wechat")
            result = service.generate(system_prompt, user_prompt)
            logger.info(f"图文生成成功，长度 {len(result)} 字")
            return result
        except Exception as e:
            logger.error(f"图文生成失败：{e}")
            raise

    def test_connection(self, base_url: str, api_key: str, model_id: str) -> bool:
        """测试 API 连通性"""
        try:
            service = AIService.create({"base_url": base_url, "api_key": api_key, "model_id": model_id})
            return service.test_connection(base_url, api_key, model_id)
        except Exception as e:
            logger.error(f"连接测试失败：{e}")
            return False

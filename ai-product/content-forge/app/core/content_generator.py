"""内容生成器：调用 AI 生成图文或观点"""
import base64
from pathlib import Path
from loguru import logger
from app.services.ai_service import AIService


class ContentGenerator:
    """AI 内容生成器"""

    def __init__(self, app_config):
        self.app_config = app_config
        self._ability = "text"  # 当前能力：生文

    def set_ability(self, ability: str):
        self._ability = ability

    def _get_ai_service(self, channel: str = None, ability: str = None):
        """获取当前渠道对应的 AI 服务实例"""
        ab = ability or self._ability
        cfg = self.app_config.get_api_config(ab, channel)
        if not cfg.get("api_key"):
            raise ValueError(f"API Key 未配置（{ab}），请先在「设置 → API 配置」中配置")
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
            # 检测常见的 API 配置错误，保留原始错误信息
            if "<!DOCTYPE" in error_msg or "<html" in error_msg.lower():
                raise ValueError(f"API 返回了网页内容而非有效响应，请检查 API 地址和 Key 是否正确配置。\n原始错误：{error_msg[:200]}")
            if "401" in error_msg or "403" in error_msg:
                raise ValueError(f"API 认证失败，请检查 API Key 是否正确。\n原始错误：{error_msg[:200]}")
            if "404" in error_msg:
                raise ValueError(f"API 地址无效，请检查 base_url 配置。\n原始错误：{error_msg[:200]}")
            if "timeout" in error_msg.lower():
                raise ValueError(f"API 请求超时，请检查网络连接或稍后重试。\n原始错误：{error_msg[:200]}")
            logger.error(f"生成观点失败：{e}")
            raise ValueError(f"AI 生成失败：{e}")

    def generate_article(self, system_prompt: str, user_opinion: str, original_content: str, channel: str = "wechat") -> str:
        """
        基于系统提示词 + 用户观点 + 原文，生成新图文
        """
        user_prompt = f"""# 用户观点
{user_opinion}

# 原文内容
{original_content[:8000]}
"""

        try:
            service = self._get_ai_service(channel)
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

    def generate_article_with_images(self, system_prompt: str, user_opinion: str, original_content: str, export_dir: Path = None, channel: str = "wechat") -> tuple[str, list[Path]]:
        """
        生成文章并附带两张相关图片
        返回 (文章内容, [图片1路径, 图片2路径])

        图片插入规则：
        - 第一张：若第一段>100字插在第一段后，否则找到前面段落累计>100字的位置插入
        - 第二张：插在倒数第三段左右，若该段<100字，则往前找到累计>100字的位置插入
        """
        # 1. 先生成文章
        article = self.generate_article(system_prompt, user_opinion, original_content, channel)

        image_paths = []

        # 2. 尝试生成图片（需要配置 image API）
        try:
            service = self._get_ai_service(ability="image")

            if export_dir is None:
                export_dir = self.app_config.get_directory("images")
            export_dir.mkdir(parents=True, exist_ok=True)

            import time
            import uuid
            prefix = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"

            # 生成第一张图片（开头配图）
            prompt_1 = self._build_image_prompt(user_opinion, position="header")
            img_data_1 = service.generate_image(prompt_1)
            if img_data_1:
                img_path_1 = export_dir / f"{prefix}_header.png"
                img_path_1.write_bytes(img_data_1)
                image_paths.append(img_path_1)
                logger.info(f"已生成首图：{img_path_1}")

            # 生成第二张图片（结尾配图）
            prompt_2 = self._build_image_prompt(user_opinion, position="footer")
            img_data_2 = service.generate_image(prompt_2)
            if img_data_2:
                img_path_2 = export_dir / f"{prefix}_footer.png"
                img_path_2.write_bytes(img_data_2)
                image_paths.append(img_path_2)
                logger.info(f"已生成尾图：{img_path_2}")

        except ValueError as e:
            # 配置错误（如 API Key 未配置），记录但不阻断文章生成
            logger.warning(f"图片生成跳过：{e}")
        except Exception as e:
            logger.warning(f"图片生成失败：{e}")

        # 3. 将图片插入到文章中
        if len(image_paths) >= 1 and image_paths[0].exists():
            article = self._insert_image_at_position(article, str(image_paths[0]), position="first")
        if len(image_paths) >= 2 and image_paths[1].exists():
            article = self._insert_image_at_position(article, str(image_paths[1]), position="last")

        return article, image_paths

    @staticmethod
    def _build_image_prompt(user_opinion: str, position: str = "header") -> str:
        """构建文生图提示词"""
        opinion = user_opinion[:200].strip()
        if position == "header":
            return (
                f"Create a featured illustration for a WeChat article. "
                f"Theme: {opinion}. "
                f"Style: modern, clean, suitable for social media, no text."
            )
        return (
            f"Create a concluding illustration for a WeChat article. "
            f"Theme: {opinion}. "
            f"Style: modern, clean, suitable for social media, no text."
        )

    @staticmethod
    def _insert_image_at_position(article: str, image_path: str, position: str = "first") -> str:
        """
        根据规则将图片插入到文章指定位置

        position="first":
          - 若第一段>100字，插在第一段后
          - 否则找到前面段落累计>100字的位置插入

        position="last":
          - 从倒数第三段开始（保证在后半部分）
          - 若该段及向后累计<100字，则往前找累计>100字的位置，但不越过文档中线
        """
        paragraphs = article.split('\n\n')
        if not paragraphs or not article.strip():
            return f"\n![配图]({image_path})\n\n{article}"

        image_markdown = f"\n![配图]({image_path})\n"

        if position == "first":
            total_len = 0
            insert_idx = 1
            for i, para in enumerate(paragraphs):
                total_len += len(para)
                if total_len > 100:
                    insert_idx = i + 1
                    break
            paragraphs.insert(insert_idx, image_markdown)

        elif position == "last":
            if len(paragraphs) < 3:
                paragraphs.append(image_markdown)
            else:
                mid = len(paragraphs) // 2
                target_idx = max(mid, len(paragraphs) - 3)
                target_para = paragraphs[target_idx]

                if len(target_para) < 100:
                    total_len = 0
                    for i in range(target_idx, mid - 1, -1):
                        total_len += len(paragraphs[i])
                        if total_len > 100:
                            target_idx = i + 1
                            break
                    else:
                        target_idx = mid + 1

                paragraphs.insert(target_idx, image_markdown)

        return '\n\n'.join(paragraphs)

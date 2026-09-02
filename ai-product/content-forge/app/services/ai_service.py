"""AI 服务：统一接口，兼容多提供商"""
import os
from abc import ABC, abstractmethod
from typing import Literal
from loguru import logger


class AIServiceInterface(ABC):
    """AI 服务抽象接口"""

    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, model_id: str = None) -> str:
        pass

    @abstractmethod
    def test_connection(self, base_url: str, api_key: str, model_id: str) -> bool:
        pass


class OpenAICompatibleService(AIServiceInterface):
    """兼容 OpenAI 协议的服务（如 OpenAI / 硅基流动 / DeepSeek / 智谱等）"""

    def __init__(self, base_url: str, api_key: str, model_id: str = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model_id = model_id
        self._client = None

    def _get_client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=60.0,
                )
            except ImportError:
                logger.error("请安装 openai 包：pip install openai")
                raise
        return self._client

    def generate(self, system_prompt: str, user_prompt: str, model_id: str = None) -> str:
        client = self._get_client()
        model = model_id or self.model_id
        if not model:
            raise ValueError("未指定模型，请设置 model_id")
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"AI 生成失败：{e}")
            raise

    def test_connection(self, base_url: str, api_key: str, model_id: str) -> bool:
        try:
            from openai import OpenAI
            test_client = OpenAI(api_key=api_key, base_url=base_url.rstrip("/"), timeout=10.0)
            test_client.models.list()
            return True
        except Exception as e:
            logger.warning(f"连接测试失败：{e}")
            return False


class AIService:
    """AI 服务工厂：根据配置创建对应服务实例"""

    @staticmethod
    def create(config: dict) -> AIServiceInterface:
        """
        根据配置字典创建 AI 服务实例
        config = {"base_url": "...", "api_key": "...", "model_id": "..."}
        """
        base_url = config.get("base_url", "")
        api_key = config.get("api_key", "")
        model_id = config.get("model_id", "")
        if not base_url or not api_key:
            raise ValueError("AI 配置不完整：需要 base_url 和 api_key")
        return OpenAICompatibleService(base_url, api_key, model_id)

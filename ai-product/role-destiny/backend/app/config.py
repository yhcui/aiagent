"""
应用配置管理 - 使用Pydantic Settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用基础配置
    APP_NAME: str = "角色测算小程序"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"

    # 数据库配置（SQLite）
    DATABASE_URL: str = "sqlite:///./data/role_destiny.db"

    # 微信小程序配置
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""

    # 微信支付配置
    WECHAT_MCH_ID: str = ""
    WECHAT_API_KEY: str = ""
    WECHAT_NOTIFY_URL: str = "https://yourdomain.com/api/payment/notify"

    # 支付模式开关（最重要的开关）：
    # mock = 模拟支付：不调微信，直接标记已支付（开发/演示用，无商户号也能跑通全链路）
    # real = 真实微信支付 JSAPI：需要商户号 WECHAT_MCH_ID + API密钥 WECHAT_API_KEY + 公网回调 WECHAT_NOTIFY_URL
    #       （若开关打开但凭证不全，自动回落 mock 并打警告日志）
    PAYMENT_MODE: str = "mock"  # mock | real

    # 解锁方式开关：pay = 付费解锁（配合 PAYMENT_MODE）| ad = 激励视频广告解锁（个人主体变现）
    UNLOCK_MODE: str = "pay"  # pay | ad
    # 激励视频广告位ID（小程序后台「流量主」创建后填入，如 adunit-xxxxxxxxxxxxxxxx）
    REWARDED_AD_UNIT_ID: str = ""

    # 缓存配置
    CACHE_MAX_SIZE: int = 1000
    CACHE_TTL: int = 300

    # 后台管理
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "gongge@2026"

    # CORS配置
    ALLOW_ORIGINS: List[str] = ["*"]

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 文件存储配置
    STATIC_DIR: str = "./static"
    DATA_DIR: str = "./data"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保目录存在
        os.makedirs(self.STATIC_DIR, exist_ok=True)
        os.makedirs(self.DATA_DIR, exist_ok=True)


settings = Settings()

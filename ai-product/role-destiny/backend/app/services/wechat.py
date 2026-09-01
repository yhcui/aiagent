"""
微信服务 - 小程序登录、用户信息获取
"""
import httpx
import json
from typing import Optional, Dict, Any
from app.config import settings
from app.services.cache import cache_service, cache_key
from loguru import logger


class WechatService:
    """微信服务"""

    # 微信接口地址
    LOGIN_URL = "https://api.weixin.qq.com/sns/jscode2session"
    ACCESS_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
    PHONE_URL = "https://api.weixin.qq.com/wxa/business/getuserphonenumber"

    def __init__(self):
        self.app_id = settings.WECHAT_APP_ID
        self.app_secret = settings.WECHAT_APP_SECRET
        self.cache = cache_service

    async def code2session(self, js_code: str) -> Dict[str, Any]:
        """
        小程序登录 - 微信code2session
        返回: {openid, session_key, unionid}
        """
        cache_key_str = cache_key("wechat", "session", js_code)

        # 检查缓存
        cached = self.cache.get(cache_key_str)
        if cached:
            logger.info(f"使用缓存的session: {js_code[:8]}...")
            return cached

        url = f"{self.LOGIN_URL}?appid={self.app_id}&secret={self.app_secret}&js_code={js_code}&grant_type=authorization_code"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                data = resp.json()

                if "errcode" in data and data["errcode"] != 0:
                    logger.error(f"微信登录失败: {data}")
                    return {"error": data.get("errmsg", "登录失败")}

                # 缓存session信息（有效期约2小时）
                self.cache.set(cache_key_str, data, ttl=7000)

                logger.info(f"微信登录成功: openid={data.get('openid', '')[:8]}...")
                return data

        except Exception as e:
            logger.error(f"微信登录请求异常: {e}")
            return {"error": str(e)}

    def get_access_token(self) -> Optional[str]:
        """
        获取access_token（服务端API调用用）
        """
        cache_key_str = cache_key("wechat", "access_token")

        cached = self.cache.get(cache_key_str)
        if cached:
            return cached

        url = f"{self.ACCESS_TOKEN_URL}?appid={self.app_id}&secret={self.app_secret}&grant_type=client_credential"

        try:
            resp = httpx.get(url, timeout=10.0)
            data = resp.json()

            if "access_token" in data:
                expires_in = data.get("expires_in", 7200)
                self.cache.set(cache_key_str, data["access_token"], ttl=expires_in - 200)
                return data["access_token"]

            logger.error(f"获取access_token失败: {data}")
            return None

        except Exception as e:
            logger.error(f"获取access_token异常: {e}")
            return None

    async def get_phone_number(self, access_token: str, code: str) -> Optional[str]:
        """
        获取用户手机号
        code: 手机号获取凭证
        """
        url = f"{self.PHONE_URL}?access_token={access_token}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json={"code": code})
                data = resp.json()

                if data.get("errcode") == 0:
                    phone_info = data.get("phone_info", {})
                    return phone_info.get("phoneNumber")
                else:
                    logger.error(f"获取手机号失败: {data}")
                    return None

        except Exception as e:
            logger.error(f"获取手机号异常: {e}")
            return None

    def verify_signature(self, signature: str, timestamp: str, nonce: str, echostr: str = None) -> bool:
        """
        验证微信消息签名（用于回调验证）
        """
        import hashlib
        import sort

        # 将 token、timestamp、nonce 按字典序排序
        temp_list = sorted([settings.WECHAT_TOKEN, timestamp, nonce])
        temp_str = "".join(temp_list)

        # 进行sha1加密
        hash_sha1 = hashlib.sha1(temp_str.encode()).hexdigest()

        return hash_sha1 == signature


# 全局微信服务实例
wechat_service = WechatService()

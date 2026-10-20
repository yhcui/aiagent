"""
微信支付服务（JSAPI / 小程序支付，API v2）

模式开关见 config.PAYMENT_MODE：
- mock：不调微信，由 API 层直接标记已支付
- real：本服务负责统一下单 / 回调验签 / 主动查单
"""
import time
import random
import string
import hashlib
import httpx
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.config import settings
from app.models.order import Order
from loguru import logger


class PaymentService:
    """微信支付服务（v2 JSAPI）"""

    UNIFIED_ORDER_URL = "https://api.mch.weixin.qq.com/pay/unifiedorder"
    QUERY_ORDER_URL = "https://api.mch.weixin.qq.com/pay/orderquery"

    def __init__(self):
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL
        self.app_id = settings.WECHAT_APP_ID

    @property
    def enabled(self) -> bool:
        """真实支付是否可用：开关打开 且 凭证齐全"""
        return (
            settings.PAYMENT_MODE == "real"
            and bool(self.mch_id)
            and bool(self.api_key)
            and bool(self.app_id)
        )

    # ── 签名与报文 ──
    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名（v2 MD5）"""
        sorted_params = sorted(
            (k, v) for k, v in params.items()
            if k != "sign" and v is not None and v != ""
        )
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_params)
        sign_str += f"&key={self.api_key}"
        return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()

    def _dict_to_xml(self, params: Dict[str, Any]) -> str:
        xml_parts = ["<xml>"]
        for k, v in params.items():
            xml_parts.append(f"<{k}><![CDATA[{v}]]></{k}>")
        xml_parts.append("</xml>")
        return "".join(xml_parts)

    def _xml_to_dict(self, xml_str: str) -> Dict[str, Any]:
        root = ET.fromstring(xml_str)
        return {child.tag: child.text for child in root}

    def _generate_nonce_str(self, length: int = 32) -> str:
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    # ── 统一下单（JSAPI）──
    async def request_jsapi_params(
        self, order: Order, openid: str, amount_fen: int, body: str = "角色测算报告"
    ) -> Optional[Dict[str, Any]]:
        """
        调用微信统一下单（trade_type=JSAPI），返回小程序 wx.requestPayment 所需参数
        amount_fen: 金额（分）
        """
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": self._generate_nonce_str(),
            "body": body,
            "out_trade_no": order.order_no,
            "total_fee": int(amount_fen),  # 单位：分
            "spbill_create_ip": "127.0.0.1",
            "notify_url": self.notify_url,
            "trade_type": "JSAPI",
            "openid": openid,
            "time_expire": order.expire_time or None,
        }
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        params["sign"] = self._generate_sign(params)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.UNIFIED_ORDER_URL,
                    content=self._dict_to_xml(params),
                    headers={"Content-Type": "application/xml"},
                )
                result = self._xml_to_dict(resp.text)

                if result.get("return_code") != "SUCCESS" or result.get("result_code") != "SUCCESS":
                    logger.error(f"统一下单失败: {result}")
                    return None

                prepay_id = result.get("prepay_id")
                if not prepay_id:
                    logger.error(f"统一下单未返回prepay_id: {result}")
                    return None

                # 小程序端二次签名（wx.requestPayment 所需）
                pay_params = {
                    "timeStamp": str(int(time.time())),
                    "nonceStr": self._generate_nonce_str(),
                    "package": f"prepay_id={prepay_id}",
                    "signType": "MD5",
                    "appId": self.app_id,
                }
                pay_params["paySign"] = self._generate_sign(pay_params)

                return {
                    "order_no": order.order_no,
                    "pay_params": {
                        "timeStamp": pay_params["timeStamp"],
                        "nonceStr": pay_params["nonceStr"],
                        "package": pay_params["package"],
                        "signType": pay_params["signType"],
                        "paySign": pay_params["paySign"],
                    },
                    "expire_time": order.expire_time or "",
                }

        except Exception as e:
            logger.error(f"调用微信统一下单异常: {e}")
            return None

    # ── 回调验签 ──
    def verify_notify_sign(self, params: Dict[str, Any]) -> bool:
        sign = params.get("sign")
        if not sign:
            return False
        return sign == self._generate_sign(params)

    def parse_notify(self, xml_str: str) -> Optional[Dict[str, Any]]:
        """解析并验签支付回调"""
        try:
            params = self._xml_to_dict(xml_str)
            if not self.verify_notify_sign(params):
                logger.warning("支付回调签名验证失败")
                return None
            return params
        except Exception as e:
            logger.error(f"解析支付回调异常: {e}")
            return None

    # ── 主动查单（回调延迟时的兜底）──
    async def query_wechat_order(self, order_no: str) -> Optional[Dict[str, Any]]:
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "out_trade_no": order_no,
            "nonce_str": self._generate_nonce_str(),
        }
        params["sign"] = self._generate_sign(params)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.QUERY_ORDER_URL,
                    content=self._dict_to_xml(params),
                    headers={"Content-Type": "application/xml"},
                )
                return self._xml_to_dict(resp.text)
        except Exception as e:
            logger.error(f"查询微信订单异常: {e}")
            return None


# 全局支付服务实例
payment_service = PaymentService()

"""
微信支付服务
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
from app.models.user_test import UserTest
from loguru import logger


class PaymentService:
    """微信支付服务"""

    UNIFIED_ORDER_URL = "https://api.mch.weixinpay.com/pay/unifiedorder"
    QUERY_ORDER_URL = "https://api.mch.weixinpay.com/pay/orderquery"

    def __init__(self):
        self.mch_id = settings.WECHAT_MCH_ID
        self.api_key = settings.WECHAT_API_KEY
        self.notify_url = settings.WECHAT_NOTIFY_URL
        self.app_id = settings.WECHAT_APP_ID

    def _generate_sign(self, params: Dict[str, Any]) -> str:
        """生成签名"""
        # 按字典序排序参数
        sorted_params = sorted([(k, v) for k, v in params.items() if k != "sign" and v])
        sign_str = "&".join([f"{k}={v}" for k, v in sorted_params])
        sign_str += f"&key={self.api_key}"

        # MD5签名
        return hashlib.md5(sign_str.encode()).hexdigest().upper()

    def _dict_to_xml(self, params: Dict[str, Any]) -> str:
        """字典转XML"""
        xml_str = "<xml>"
        for k, v in params.items():
            xml_str += f"<{k}><![CDATA[{v}]]></{k}>"
        xml_str += "</xml>"
        return xml_str

    def _xml_to_dict(self, xml_str: str) -> Dict[str, Any]:
        """XML转字典"""
        root = ET.fromstring(xml_str)
        return {child.tag: child.text for child in root}

    def _generate_nonce_str(self, length: int = 32) -> str:
        """生成随机字符串"""
        chars = string.ascii_letters + string.digits
        return "".join(random.choice(chars) for _ in range(length))

    async def create_order(self, db: Session, user_id: int, result_id: int, test_id: int, amount: float) -> Optional[Dict[str, Any]]:
        """
        创建支付订单
        amount: 金额（元）
        """
        # 生成订单号
        order_no = Order.generate_order_no()

        # 过期时间（15分钟）
        expire_time = (datetime.now() + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S')

        # 创建本地订单记录
        order = Order(
            order_no=order_no,
            user_id=user_id,
            result_id=result_id,
            test_id=test_id,
            amount=amount,
            status="pending",
            expire_time=expire_time,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        # 调用微信支付统一下单接口
        params = {
            "appid": self.app_id,
            "mch_id": self.mch_id,
            "nonce_str": self._generate_nonce_str(),
            "body": "角色测算报告",
            "out_trade_no": order_no,
            "total_fee": int(amount * 100),  # 转换为分
            "spbill_create_ip": "127.0.0.1",  # 实际生产应为用户IP
            "notify_url": self.notify_url,
            "trade_type": "NATIVE",
            "time_expire": expire_time,
        }

        # 生成签名
        params["sign"] = self._generate_sign(params)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.UNIFIED_ORDER_URL,
                    content=self._dict_to_xml(params),
                    headers={"Content-Type": "application/xml"},
                )
                result = self._xml_to_dict(resp.text)

                if result.get("return_code") == "SUCCESS" and result.get("result_code") == "SUCCESS":
                    return {
                        "order_no": order_no,
                        "pay_url": result.get("code_url"),
                        "expire_time": expire_time,
                    }
                else:
                    logger.error(f"创建支付订单失败: {result}")
                    order.status = "failed"
                    db.commit()
                    return None

        except Exception as e:
            logger.error(f"调用微信支付异常: {e}")
            order.status = "failed"
            db.commit()
            return None

    def verify_notify_sign(self, params: Dict[str, Any]) -> bool:
        """验证回调签名"""
        sign = params.get("sign")
        if not sign:
            return False

        calculated_sign = self._generate_sign(params)
        return sign == calculated_sign

    def parse_notify(self, xml_str: str) -> Optional[Dict[str, Any]]:
        """解析支付回调"""
        try:
            params = self._xml_to_dict(xml_str)

            # 验证签名
            if not self.verify_notify_sign(params):
                logger.warning("支付回调签名验证失败")
                return None

            return params

        except Exception as e:
            logger.error(f"解析支付回调异常: {e}")
            return None

    async def query_order(self, order_no: str) -> Optional[Dict[str, Any]]:
        """查询订单状态"""
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
            logger.error(f"查询订单异常: {e}")
            return None


# 全局支付服务实例
payment_service = PaymentService()

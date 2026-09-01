"""
订单相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class OrderSchema(BaseModel):
    """订单响应模型"""
    id: int
    order_no: str
    user_id: int
    result_id: int
    test_id: int
    amount: float
    status: str
    transaction_id: Optional[str] = None
    pay_time: Optional[str] = None
    expire_time: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class OrderCreateSchema(BaseModel):
    """创建订单请求模型"""
    result_id: int


class PaymentRequestSchema(BaseModel):
    """发起支付请求模型"""
    result_id: int


class PaymentNotifySchema(BaseModel):
    """微信支付回调模型"""
    return_code: str
    return_msg: str
    result_code: Optional[str] = None
    transaction_id: Optional[str] = None
    order_no: Optional[str] = None
    total_fee: Optional[int] = None
    time_end: Optional[str] = None


class PaymentResponseSchema(BaseModel):
    """支付响应模型"""
    order_no: str
    pay_url: str  # 微信支付二维码链接
    expire_time: str

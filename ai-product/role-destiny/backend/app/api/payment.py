"""
支付相关API

模式由 settings.PAYMENT_MODE 控制（详见 app/config.py）：
- "mock"（默认）：不调微信，直接标记已支付，返回 mock=True
- "real"        ：真实微信支付 JSAPI，返回 pay_params 由小程序调起 wx.requestPayment
                  （凭证不全时自动回落 mock 并打警告）
"""
import time
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.order import Order
from app.models.user_test import UserTest
from app.models.test import Test
from app.schemas.order import PaymentResponseSchema, PaymentRequestSchema
from app.services.payment import payment_service
from loguru import logger

router = APIRouter(prefix="/api/payment", tags=["支付"])


def _mark_paid(db: Session, order: Order, transaction_id: str, pay_time: str):
    """订单置为已支付（幂等：仅 pending 状态处理）"""
    if order.status != "pending":
        return
    order.status = "paid"
    order.transaction_id = transaction_id
    order.pay_time = pay_time
    order.updated_at = pay_time

    user_test = db.query(UserTest).filter(UserTest.id == order.result_id).first()
    if user_test and not user_test.is_paid:
        user_test.is_paid = 1
        user_test.paid_at = pay_time
    db.commit()


@router.post("/create", response_model=PaymentResponseSchema)
async def create_payment(
    data: PaymentRequestSchema,
    db: Session = Depends(get_db)
):
    """
    发起支付：根据 PAYMENT_MODE 开关走 Mock 或真实微信支付
    """
    openid = data.openid
    result_id = data.result_id

    # 验证用户
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 查询测试结果
    user_test = db.query(UserTest).filter(
        UserTest.id == result_id,
        UserTest.user_id == user.id
    ).first()
    if not user_test:
        raise HTTPException(status_code=404, detail="测试结果不存在")

    if user_test.is_paid:
        raise HTTPException(status_code=400, detail="该结果已支付")

    # 价格：数据库以「分」为准
    test = db.query(Test).filter(Test.id == user_test.test_id).first()
    amount_fen = int(test.price) if test and test.price else 99
    amount_yuan = round(amount_fen / 100, 2)

    # ── Mock 支付（开关未开 / 凭证不全）──
    if not payment_service.enabled:
        if settings.PAYMENT_MODE == "real":
            logger.warning("PAYMENT_MODE=real 但商户号/API密钥未配置，本次回落为 Mock 支付")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        order_no = f"MOCK{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

        order = Order(
            order_no=order_no,
            user_id=user.id,
            result_id=result_id,
            test_id=user_test.test_id,
            amount=amount_yuan,
            status="paid",
            transaction_id=f"MOCK{int(time.time())}",
            pay_time=now,
            expire_time="",
        )
        db.add(order)

        user_test.is_paid = 1
        user_test.paid_at = now
        db.commit()
        logger.info(f"Mock支付成功: order_no={order_no}, result_id={result_id}")

        return {
            "order_no": order_no,
            "pay_params": None,
            "expire_time": "",
            "mock": True,
        }

    # ── 真实微信支付（JSAPI）──
    order = db.query(Order).filter(
        Order.result_id == result_id,
        Order.status == "pending"
    ).first()

    if not order:
        order = Order(
            order_no=Order.generate_order_no(),
            user_id=user.id,
            result_id=result_id,
            test_id=user_test.test_id,
            amount=amount_yuan,
            status="pending",
            expire_time=(datetime.now() + timedelta(minutes=15)).strftime("%Y%m%d%H%M%S"),
        )
        db.add(order)
        db.commit()
        db.refresh(order)

    params = await payment_service.request_jsapi_params(order, openid, amount_fen)
    if not params:
        order.status = "failed"
        db.commit()
        raise HTTPException(status_code=500, detail="创建支付订单失败")

    params["mock"] = False
    return params


@router.post("/ad-unlock")
async def ad_unlock(data: PaymentRequestSchema, db: Session = Depends(get_db)):
    """
    激励视频广告解锁（用户完整观看广告后由小程序调用）

    防刷说明：微信激励视频没有服务端回调，此处信任客户端上报；
    每个结果仅可解锁一次，刷单上限即一次广告收益，风险可控。
    """
    if settings.UNLOCK_MODE != "ad":
        raise HTTPException(status_code=403, detail="未开启广告解锁模式")

    user = db.query(User).filter(User.openid == data.openid).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user_test = db.query(UserTest).filter(
        UserTest.id == data.result_id,
        UserTest.user_id == user.id
    ).first()
    if not user_test:
        raise HTTPException(status_code=404, detail="测试结果不存在")

    # 幂等：已解锁直接返回成功
    if user_test.is_paid:
        return {"unlocked": True, "order_no": ""}

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    order_no = f"AD{int(time.time())}{uuid.uuid4().hex[:8].upper()}"

    db.add(Order(
        order_no=order_no,
        user_id=user.id,
        result_id=data.result_id,
        test_id=user_test.test_id,
        amount=0,  # 广告解锁无直接收入
        status="paid",
        transaction_id=f"AD{int(time.time())}",
        pay_time=now,
        expire_time="",
    ))

    user_test.is_paid = 1
    user_test.paid_at = now
    db.commit()
    logger.info(f"广告解锁成功: order_no={order_no}, result_id={data.result_id}")

    return {"unlocked": True, "order_no": order_no}


@router.post("/notify")
async def payment_notify(request: Request, db: Session = Depends(get_db)):
    """
    微信支付异步回调
    """
    body = await request.body()
    params = payment_service.parse_notify(body.decode("utf-8"))
    if not params:
        return "<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[签名验证失败]]></return_msg></xml>"

    if params.get("return_code") == "SUCCESS" and params.get("result_code") == "SUCCESS":
        order = db.query(Order).filter(Order.order_no == params.get("out_trade_no")).first()
        if order:
            _mark_paid(db, order, params.get("transaction_id") or "", params.get("time_end") or "")
            logger.info(f"支付回调处理成功: order_no={order.order_no}")

    return "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"


@router.get("/query/{order_no}")
async def query_order(order_no: str, db: Session = Depends(get_db)):
    """
    查询订单状态
    本地还是 pending 且真实支付模式下，主动向微信查单兜底（回调可能延迟）
    """
    order = db.query(Order).filter(Order.order_no == order_no).first()
    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    if order.status == "pending" and payment_service.enabled:
        result = await payment_service.query_wechat_order(order_no)
        if (
            result
            and result.get("return_code") == "SUCCESS"
            and result.get("result_code") == "SUCCESS"
            and result.get("trade_state") == "SUCCESS"
        ):
            _mark_paid(db, order, result.get("transaction_id") or "", result.get("time_end") or "")
            db.refresh(order)
            logger.info(f"主动查单确认支付: order_no={order_no}")

    return {
        "order_no": order.order_no,
        "status": order.status,
        "amount": order.amount,
        "pay_time": order.pay_time,
        "is_paid": order.status == "paid",
    }

"""
支付相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.order import Order
from app.models.user_test import UserTest
from app.models.test import Test
from app.schemas.order import PaymentResponseSchema
from app.services.payment import payment_service
from loguru import logger

router = APIRouter(prefix="/api/payment", tags=["支付"])


@router.post("/create", response_model=PaymentResponseSchema)
async def create_payment(
    openid: str,
    result_id: int,
    db: Session = Depends(get_db)
):
    """
    发起支付
    """
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

    # 检查是否已付费
    if user_test.is_paid:
        raise HTTPException(status_code=400, detail="该结果已支付")

    # 检查是否已有待支付订单
    existing_order = db.query(Order).filter(
        Order.result_id == result_id,
        Order.status == "pending"
    ).first()

    if existing_order:
        # 返回现有订单
        return {
            "order_no": existing_order.order_no,
            "pay_url": "",  # 需要重新生成支付链接
            "expire_time": existing_order.expire_time or "",
        }

    # 获取测试价格
    test = db.query(Test).filter(Test.id == user_test.test_id).first()
    amount = (test.price / 100) if test else 0.99  # 默认0.99元

    # 创建支付订单
    result = await payment_service.create_order(
        db=db,
        user_id=user.id,
        result_id=result_id,
        test_id=user_test.test_id,
        amount=amount,
    )

    if not result:
        raise HTTPException(status_code=500, detail="创建支付订单失败")

    return result


@router.post("/notify")
async def payment_notify(request: Request):
    """
    微信支付回调
    """
    body = await request.body()
    xml_str = body.decode("utf-8")

    # 解析回调
    params = payment_service.parse_notify(xml_str)
    if not params:
        return "<xml><return_code><![CDATA[FAIL]]></return_code><return_msg><![CDATA[签名验证失败]]></return_msg></xml>"

    # 处理支付成功
    if params.get("return_code") == "SUCCESS" and params.get("result_code") == "SUCCESS":
        order_no = params.get("out_trade_no")
        transaction_id = params.get("transaction_id")
        pay_time = params.get("time_end")

        # 更新订单状态
        db_gen = next(get_db())
        order = db_gen.query(Order).filter(Order.order_no == order_no).first()

        if order and order.status == "pending":
            order.status = "paid"
            order.transaction_id = transaction_id
            order.pay_time = pay_time
            order.updated_at = pay_time

            # 更新测试结果为已付费
            user_test = db_gen.query(UserTest).filter(UserTest.id == order.result_id).first()
            if user_test:
                user_test.is_paid = 1
                user_test.paid_at = pay_time

            db_gen.commit()
            logger.info(f"支付回调处理成功: order_no={order_no}")

        db_gen.close()

    return "<xml><return_code><![CDATA[SUCCESS]]></return_code><return_msg><![CDATA[OK]]></return_msg></xml>"


@router.get("/query/{order_no}")
async def query_order(order_no: str, db: Session = Depends(get_db)):
    """
    查询订单状态
    """
    order = db.query(Order).filter(Order.order_no == order_no).first()

    if not order:
        raise HTTPException(status_code=404, detail="订单不存在")

    return {
        "order_no": order.order_no,
        "status": order.status,
        "amount": order.amount,
        "pay_time": order.pay_time,
        "is_paid": order.status == "paid",
    }

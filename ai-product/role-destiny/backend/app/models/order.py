"""
订单模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.database import Base


class Order(Base):
    """订单表"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(64), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    result_id = Column(Integer, ForeignKey("user_tests.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    amount = Column(Float, nullable=False)  # 金额，单位：元
    status = Column(String(32), default="pending")  # pending, paid, refunded, failed
    transaction_id = Column(String(128))  # 微信支付交易号
    pay_time = Column(String(32))  # 支付时间
    expire_time = Column(String(32))  # 过期时间
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    user = relationship("User", back_populates="orders")
    result = relationship("UserTest", back_populates="orders")
    test = relationship("Test")

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'paid', 'refunded', 'failed')", name='check_order_status'),
    )

    def __repr__(self):
        return f"<Order(id={self.id}, order_no={self.order_no}, status={self.status})>"

    @staticmethod
    def generate_order_no():
        """生成订单号"""
        import time
        import random
        return f"RD{int(time.time())}{random.randint(1000, 9999)}"

    def is_expired(self):
        """检查订单是否过期"""
        if self.status != "pending":
            return False
        if not self.expire_time:
            return False
        expire_dt = datetime.strptime(self.expire_time, '%Y-%m-%d %H:%M:%S')
        return datetime.now() > expire_dt

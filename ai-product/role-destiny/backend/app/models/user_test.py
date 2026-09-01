"""
用户测试记录模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class UserTest(Base):
    """用户测试记录表"""
    __tablename__ = "user_tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    answers = Column(Text, nullable=False)  # JSON数组，用户答案
    result_role_id = Column(Integer, ForeignKey("roles.id"))
    match_score = Column(Float)  # 匹配度 0-100
    is_paid = Column(Integer, default=0)  # 0: 未付费, 1: 已付费
    paid_at = Column(String(32))  # 付费时间
    status = Column(String(32), default="completed")  # completed, expired
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    user = relationship("User", back_populates="user_tests")
    test = relationship("Test", back_populates="user_tests")
    result_role = relationship("Role", back_populates="user_tests")
    orders = relationship("Order", back_populates="result")

    __table_args__ = (
        CheckConstraint('is_paid IN (0, 1)', name='check_user_test_paid'),
        CheckConstraint("status IN ('completed', 'expired')", name='check_user_test_status'),
    )

    def __repr__(self):
        return f"<UserTest(id={self.id}, user_id={self.user_id}, test_id={self.test_id})>"

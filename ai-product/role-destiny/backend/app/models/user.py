"""
用户模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    openid = Column(String(128), nullable=False, unique=True, index=True)
    unionid = Column(String(128), index=True)
    nickname = Column(String(64))
    avatar = Column(String(512))
    phone = Column(String(32))
    status = Column(Integer, default=1)  # 0: 禁用, 1: 正常
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    user_tests = relationship("UserTest", back_populates="user")
    orders = relationship("Order", back_populates="user")

    __table_args__ = (
        CheckConstraint('status IN (0, 1)', name='check_user_status'),
    )

    def __repr__(self):
        return f"<User(id={self.id}, openid={self.openid}, nickname={self.nickname})>"

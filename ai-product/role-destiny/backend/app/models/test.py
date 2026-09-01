"""
测试主题、题目、选项模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Test(Base):
    """测试主题表"""
    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(128), nullable=False)
    description = Column(Text)
    cover_image = Column(String(512))
    share_title = Column(String(128))
    share_desc = Column(String(256))
    price = Column(Integer, default=99)  # 价格，单位：分（0.99元 = 99分）
    status = Column(Integer, default=1)  # 0: 禁用, 1: 正常
    sort_order = Column(Integer, default=0)
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    updated_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    questions = relationship("Question", back_populates="test", order_by="Question.sort_order")
    roles = relationship("Role", back_populates="test")
    user_tests = relationship("UserTest", back_populates="test")

    __table_args__ = (
        CheckConstraint('status IN (0, 1)', name='check_test_status'),
    )

    def __repr__(self):
        return f"<Test(id={self.id}, title={self.title})>"


class Question(Base):
    """题目表"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    test = relationship("Test", back_populates="questions")
    options = relationship("Option", back_populates="question", order_by="Option.sort_order")

    def __repr__(self):
        return f"<Question(id={self.id}, content={self.content[:20]}...)>"


class Option(Base):
    """选项表"""
    __tablename__ = "options"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    score_map = Column(Text)  # JSON字符串，如 '{"A":2,"B":1,"C":0}'
    sort_order = Column(Integer, default=0)
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    question = relationship("Question", back_populates="options")

    def __repr__(self):
        return f"<Option(id={self.id}, content={self.content[:20]}...)>"

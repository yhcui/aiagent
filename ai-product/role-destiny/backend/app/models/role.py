"""
角色原型模型
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Role(Base):
    """角色原型表"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False, index=True)
    name = Column(String(64), nullable=False)
    code = Column(String(16), nullable=False)  # 角色代码，如 "A", "B", "C"
    description = Column(Text)  # 一句话描述（免费预览显示）
    image = Column(String(512))  # 角色图片URL
    detail_text = Column(Text)  # 详细分析报告
    personality = Column(Text)  # 性格画像
    destiny = Column(Text)  # 命运走向
    advantages = Column(Text)  # JSON数组，优势
    weaknesses = Column(Text)  # JSON数组，劣势
    suggestion = Column(Text)  # 给用户的建议
    lucky_number = Column(String(32))  # 幸运数字
    lucky_color = Column(String(32))  # 幸运颜色
    motto = Column(String(128))  # 座右铭
    rarity = Column(Float)  # 稀有度（0-1，如0.05表示5%概率）
    sort_order = Column(Integer, default=0)
    created_at = Column(String(32), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 关系
    test = relationship("Test", back_populates="roles")
    user_tests = relationship("UserTest", back_populates="result_role")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name}, code={self.code})>"

    def to_preview_dict(self):
        """转换为预览字典（免费信息）"""
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "image": self.image,
            "rarity": self.rarity,
        }

    def to_full_dict(self):
        """转换为完整信息字典（付费内容）"""
        import json
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "image": self.image,
            "detail_text": self.detail_text,
            "personality": self.personality,
            "destiny": self.destiny,
            "advantages": json.loads(self.advantages) if self.advantages else [],
            "weaknesses": json.loads(self.weaknesses) if self.weaknesses else [],
            "suggestion": self.suggestion,
            "lucky_number": self.lucky_number,
            "lucky_color": self.lucky_color,
            "motto": self.motto,
            "rarity": self.rarity,
        }

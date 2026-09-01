"""
测试相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class OptionSchema(BaseModel):
    """选项模型"""
    id: int
    content: str
    sort_order: int = 0

    class Config:
        from_attributes = True


class QuestionSchema(BaseModel):
    """题目模型"""
    id: int
    content: str
    options: List[OptionSchema] = []
    sort_order: int = 0

    class Config:
        from_attributes = True


class TestSchema(BaseModel):
    """测试详情模型"""
    id: int
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    share_title: Optional[str] = None
    share_desc: Optional[str] = None
    price: int = 99  # 单位：分
    question_count: int = 0
    questions: List[QuestionSchema] = []

    class Config:
        from_attributes = True


class TestListSchema(BaseModel):
    """测试列表模型"""
    id: int
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    share_title: Optional[str] = None
    price: int = 99
    status: int = 1
    sort_order: int = 0

    class Config:
        from_attributes = True


class TestCreateSchema(BaseModel):
    """创建测试请求模型"""
    title: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    share_title: Optional[str] = None
    share_desc: Optional[str] = None
    price: int = Field(default=99, ge=0, description="价格，单位：分")
    sort_order: int = 0

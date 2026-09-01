"""
用户测试相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from app.schemas.role import RolePreviewSchema, RoleFullSchema


class UserTestCreateSchema(BaseModel):
    """提交测试请求模型"""
    test_id: int
    answers: List[int] = Field(..., description="选项ID列表，按题目顺序")


class UserTestResultSchema(BaseModel):
    """测试结果响应模型"""
    id: int
    test_id: int
    role: RolePreviewSchema  # 预览信息（免费）
    full_role: Optional[RoleFullSchema] = None  # 完整信息（付费）
    match_score: float = Field(..., description="匹配度 0-100")
    is_paid: bool = False
    can_generate_poster: bool = True

    class Config:
        from_attributes = True


class UserTestSchema(BaseModel):
    """用户测试记录模型"""
    id: int
    test_id: int
    result_role_id: Optional[int] = None
    match_score: Optional[float] = None
    is_paid: bool = False
    status: str = "completed"
    created_at: str

    class Config:
        from_attributes = True

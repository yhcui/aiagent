"""
角色相关Schema
"""
from pydantic import BaseModel
from typing import Optional, List


class RolePreviewSchema(BaseModel):
    """角色预览模型（免费信息）"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    image: Optional[str] = None
    rarity: Optional[float] = None

    class Config:
        from_attributes = True


class RoleFullSchema(BaseModel):
    """角色完整信息模型（付费内容）"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    image: Optional[str] = None
    detail_text: Optional[str] = None
    personality: Optional[str] = None
    destiny: Optional[str] = None
    advantages: List[str] = []
    weaknesses: List[str] = []
    suggestion: Optional[str] = None
    lucky_number: Optional[str] = None
    lucky_color: Optional[str] = None
    motto: Optional[str] = None
    rarity: Optional[float] = None

    class Config:
        from_attributes = True


class RoleSchema(RolePreviewSchema):
    """角色模型"""
    detail_text: Optional[str] = None
    personality: Optional[str] = None
    destiny: Optional[str] = None
    advantages: Optional[str] = None  # JSON字符串
    weaknesses: Optional[str] = None  # JSON字符串
    suggestion: Optional[str] = None
    lucky_number: Optional[str] = None
    lucky_color: Optional[str] = None
    motto: Optional[str] = None

    class Config:
        from_attributes = True


class RoleCreateSchema(BaseModel):
    """创建角色请求模型"""
    test_id: int
    name: str
    code: str
    description: Optional[str] = None
    image: Optional[str] = None
    detail_text: Optional[str] = None
    personality: Optional[str] = None
    destiny: Optional[str] = None
    advantages: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None
    suggestion: Optional[str] = None
    lucky_number: Optional[str] = None
    lucky_color: Optional[str] = None
    motto: Optional[str] = None
    rarity: Optional[float] = None
    sort_order: int = 0

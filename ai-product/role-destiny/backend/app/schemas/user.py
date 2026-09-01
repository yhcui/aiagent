"""
用户相关Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserSchema(BaseModel):
    """用户响应模型"""
    id: int
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None
    status: int = 1
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UserCreateSchema(BaseModel):
    """创建用户请求模型"""
    openid: str
    unionid: Optional[str] = None
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class UserUpdateSchema(BaseModel):
    """更新用户请求模型"""
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    phone: Optional[str] = None

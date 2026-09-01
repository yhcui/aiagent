"""
海报相关API
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.user_test import UserTest
from app.models.role import Role
from app.models.test import Test
from app.services.poster import poster_service
from app.config import settings
import os

router = APIRouter(prefix="/api/poster", tags=["海报"])


@router.get("/generate")
async def generate_poster(
    openid: str,
    result_id: int,
    db: Session = Depends(get_db)
):
    """
    生成海报
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

    # 获取角色信息
    role = db.query(Role).filter(Role.id == user_test.result_role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 获取测试信息
    test = db.query(Test).filter(Test.id == user_test.test_id).first()

    # 生成海报
    poster_url = await poster_service.generate_role_poster(
        role_name=role.name,
        role_image_url=role.image,
        role_description=role.description or "",
        match_score=user_test.match_score or 0,
        user_nickname=user.nickname or "神秘用户",
        mini_program_path=f"/pages/result/detail?id={result_id}",
        qr_code_url=f"https://yourdomain.com/pages/result/detail?id={result_id}",
    )

    if not poster_url:
        raise HTTPException(status_code=500, detail="海报生成失败")

    return {
        "poster_url": poster_url,
        "full_url": f"https://yourdomain.com{poster_url}",
    }


@router.get("/download/{filename}")
async def download_poster(filename: str):
    """
    下载海报
    """
    # 安全检查：防止路径遍历
    filename = os.path.basename(filename)

    filepath = os.path.join(settings.STATIC_DIR, "posters", filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="海报不存在")

    return FileResponse(
        filepath,
        media_type="image/png",
        filename=filename,
    )

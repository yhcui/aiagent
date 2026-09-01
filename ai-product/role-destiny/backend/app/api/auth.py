"""
认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserSchema, UserUpdateSchema
from app.services.wechat import wechat_service
from loguru import logger

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=UserSchema)
async def login(data: dict = Body(...), db: Session = Depends(get_db)):
    """
    小程序登录
    data: 包含 code 的请求体
    """
    code = data.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="code不能为空")
    # 调用微信接口获取openid
    result = await wechat_service.code2session(code)

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    openid = result.get("openid")
    unionid = result.get("unionid")

    # 查询或创建用户
    user = db.query(User).filter(User.openid == openid).first()

    if not user:
        user = User(
            openid=openid,
            unionid=unionid,
            status=1,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"新用户注册: openid={openid[:8]}...")

    return user


@router.get("/user", response_model=UserSchema)
async def get_user_info(openid: str, db: Session = Depends(get_db)):
    """获取用户信息"""
    user = db.query(User).filter(User.openid == openid).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return user


@router.put("/user", response_model=UserSchema)
async def update_user(
    openid: str,
    data: UserUpdateSchema,
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = db.query(User).filter(User.openid == openid).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)

    from datetime import datetime
    user.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    db.commit()
    db.refresh(user)

    return user


@router.post("/bind-phone")
async def bind_phone(
    openid: str,
    code: str,
    db: Session = Depends(get_db)
):
    """绑定手机号"""
    user = db.query(User).filter(User.openid == openid).first()

    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 获取access_token
    access_token = wechat_service.get_access_token()
    if not access_token:
        raise HTTPException(status_code=500, detail="获取access_token失败")

    # 获取手机号
    phone = await wechat_service.get_phone_number(access_token, code)
    if not phone:
        raise HTTPException(status_code=400, detail="获取手机号失败")

    user.phone = phone
    from datetime import datetime
    user.updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.commit()

    return {"phone": phone}

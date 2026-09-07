"""登录 / 登出接口。"""
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from .. import auth as auth_utils

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 生产环境走 HTTPS 时建议配置 COOKIE_SECURE=true
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


class LoginPayload(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginPayload):
    if not auth_utils.verify_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    token = auth_utils.create_token()
    resp = JSONResponse({"ok": True})
    resp.set_cookie(
        key=auth_utils.COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        max_age=auth_utils.COOKIE_MAX_AGE,
        path="/",
        secure=COOKIE_SECURE,
    )
    return resp


@router.post("/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(key=auth_utils.COOKIE_NAME, path="/")
    return resp

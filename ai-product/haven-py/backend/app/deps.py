"""公共依赖：从 Cookie 校验登录态。"""
from fastapi import Depends, HTTPException, Request

from . import auth as auth_utils


def require_auth(request: Request) -> str:
    token = request.cookies.get(auth_utils.COOKIE_NAME)
    if not auth_utils.verify_token(token):
        raise HTTPException(status_code=401, detail="未登录")
    return token

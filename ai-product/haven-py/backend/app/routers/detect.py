"""AI 文本检测（腾讯朱雀 · EdgeOne Makers 内置模型）。"""
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..deps import require_auth

router = APIRouter(prefix="/api/detect", tags=["detect"], dependencies=[Depends(require_auth)])

ZHUQUE_API_KEY = os.getenv("ZHUQUE_API_KEY", "")
ZHUQUE_URL = "https://ai-gateway.edgeone.link/v1/providers/zhuque-text/classify"
REQUEST_TIMEOUT = 30.0


class DetectPayload(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    is_merge: bool = True


@router.post("")
def detect_text(payload: DetectPayload):
    if not ZHUQUE_API_KEY:
        raise HTTPException(status_code=503, detail="未配置 ZHUQUE_API_KEY，请联系管理员")

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="内容不能为空")

    try:
        resp = httpx.post(
            ZHUQUE_URL,
            headers={
                "Authorization": f"Bearer {ZHUQUE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={"text": text, "is_merge": payload.is_merge},
            timeout=REQUEST_TIMEOUT,
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="检测服务超时，请稍后重试")
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="检测服务连接失败")

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"检测服务返回错误（{resp.status_code}）")

    try:
        data = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="检测服务响应异常")

    if data.get("status") != "success":
        raise HTTPException(status_code=502, detail=data.get("msg") or "检测失败")

    return data

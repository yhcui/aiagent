"""Haven 后端入口（FastAPI）。"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .routers import auth as auth_router
from .routers import ideas as ideas_router

app = FastAPI(title="Haven API", description="个人工作台后端", version="1.0.0")

# 允许的前端来源（生产环境建议改成实际域名）
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # Cookie 鉴权必须开启
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(ideas_router.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}

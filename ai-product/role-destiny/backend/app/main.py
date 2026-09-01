"""
角色测算小程序 - FastAPI应用入口
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine, Base
from app.api import auth, test, quiz, payment, poster
from loguru import logger
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.APP_NAME} 启动中...")

    # 创建数据库表
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库表初始化完成")

    # 确保静态目录存在
    os.makedirs(settings.STATIC_DIR, exist_ok=True)
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    yield

    # 关闭时
    logger.info(f"👋 {settings.APP_NAME} 已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="角色测算小程序API - Python FastAPI版本",
    lifespan=lifespan,
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
if os.path.exists(settings.STATIC_DIR):
    app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")

# 注册路由
app.include_router(auth.router)
app.include_router(test.router)
app.include_router(quiz.router)
app.include_router(payment.router)
app.include_router(poster.router)


@app.get("/")
async def root():
    """首页"""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )

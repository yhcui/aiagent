@echo off
REM 角色测算小程序 - 快速启动脚本 (Windows)

echo ========================================
echo  角色测算小程序后端服务
echo ========================================

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    pause
    exit /b 1
)

REM 检查依赖
echo [1/4] 检查依赖...
pip show fastapi >nul 2>&1
if %errorlevel% neq 0 (
    echo [2/4] 安装依赖...
    pip install -r requirements.txt
)

REM 初始化数据库
echo [3/4] 初始化数据库...
python init_data.py

REM 启动服务
echo [4/4] 启动服务...
echo.
echo 服务地址: http://localhost:8000
echo API文档:  http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止服务
echo.

cd /d %~dp0
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

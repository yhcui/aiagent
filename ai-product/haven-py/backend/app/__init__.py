"""Haven 后端应用包。"""
from pathlib import Path

from dotenv import load_dotenv

# 包导入时自动加载 backend/.env（不存在则忽略）；
# load_dotenv 不覆盖已存在的环境变量，真实环境变量优先级更高。
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

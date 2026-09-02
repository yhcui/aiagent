"""日志模块"""
import sys
from loguru import logger

# 全局日志配置（由 main.py 初始化时进一步配置）
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
)

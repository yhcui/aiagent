"""ContentForge 内容锻造师 - 主入口"""
import sys
import loguru
from pathlib import Path
from loguru import logger

# 配置日志
LOG_DIR = Path(__file__).parent / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
logger.add(
LOG_DIR / "contentforge_{time:YYYY-MM-DD}.log",
rotation="00:00",
retention="7 days",
level="INFO",
format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <level>{message}</level>",
encoding="utf-8",
)

from app.main_window import MainWindow
from app.utils.config import AppConfig
from app.services.storage_service import StorageService
from PyQt6.QtWidgets import QApplication


def main():
    logger.info("ContentForge 启动...")
    config = AppConfig()
    storage = StorageService(config)
    storage.init_db()

    app = QApplication(sys.argv)
    app.setApplicationName("内容锻造师 ContentForge")
    app.setApplicationVersion("0.1.0")

    win = MainWindow(config, storage)
    win.show()

    logger.info("主窗口已显示")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

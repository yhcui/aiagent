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
    # 确保窗口显示在主显示器上并最大化
    from PyQt6.QtGui import QScreen
    primary_screen = QApplication.primaryScreen()
    if primary_screen:
        screen_geometry = primary_screen.availableGeometry()
        win.move(screen_geometry.x(), screen_geometry.y())
        win.resize(screen_geometry.width() - 100, screen_geometry.height() - 100)
    win.show()
    win.raise_()
    win.activateWindow()

    logger.info("主窗口已显示")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

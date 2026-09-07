"""SQLite 数据访问层（沿用原 data/haven.db）。"""
import os
import sqlite3
from pathlib import Path

# 数据目录优先使用环境变量 DB_DIR，默认项目根目录下的 data/
DB_DIR = Path(os.getenv("DB_DIR", Path(__file__).resolve().parent.parent / "data"))
DB_PATH = DB_DIR / "haven.db"


def get_conn() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def init_db() -> None:
    """建表（幂等）。"""
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS ideas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                is_completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
            """
        )
        conn.commit()

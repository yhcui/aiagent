"""存储服务：SQLite 数据库管理"""
import json
import sqlite3
import threading
from pathlib import Path
from loguru import logger
from app.models.task import Task
from app.models.channel import Channel


class StorageService:
    def __init__(self, config):
        self.config = config
        self.db_path = config.data_dir / "contentforge.db"
        self._local = threading.local()

    def _get_conn(self):
        """获取当前线程的数据库连接（线程安全）"""
        conn = getattr(self._local, 'conn', None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return conn

    def init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                user_opinion TEXT NOT NULL,
                channel TEXT DEFAULT 'wechat',
                status TEXT DEFAULT 'pending',
                original_content TEXT DEFAULT '',
                generated_content TEXT DEFAULT '',
                error_message TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                completed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                display_name TEXT NOT NULL,
                system_prompt TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_builtin INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        conn.commit()
        self._init_builtin_channels()
        logger.info(f"数据库初始化完成：{self.db_path}")

    def _init_builtin_channels(self):
        """初始化内置渠道"""
        conn = self._get_conn()
        existing = conn.execute("SELECT COUNT(*) FROM channels WHERE is_builtin=1").fetchone()[0]
        if existing == 0:
            wechat_prompt = Path(__file__).parent.parent.parent / "prompts" / "text" / "wechat.md"
            if wechat_prompt.exists():
                prompt = wechat_prompt.read_text(encoding="utf-8")
            else:
                prompt = self._default_wechat_prompt()
            conn.execute(
                """INSERT OR IGNORE INTO channels (id, name, display_name, system_prompt, is_active, is_builtin)
                   VALUES (?, ?, ?, ?, 1, 1)""",
                ("builtin-wechat", "wechat", "微信公众号", prompt),
            )
            conn.commit()
            logger.info("内置微信公众号渠道初始化完成")

    @staticmethod
    def _default_wechat_prompt():
        return """# 角色
你是一位资深的新媒体内容创作者，擅长基于原文内容，融入个人观点和独特视角，创作出有深度、有态度的微信公众号文章。

# 能力
1. 深入理解原文核心观点和信息
2. 将用户的个人看法巧妙融入文章
3. 保持微信公众号的阅读风格和排版习惯
4. 标题吸引人，内容有干货

# 输出要求
1. 生成一篇 800–1500 字的微信公众号图文
2. 使用 Markdown 格式输出
3. 包含吸引人的标题
4. 适当使用 emoji 增加生动性
5. 段落长度适中，适合手机阅读
6. 突出用户个人观点，形成差异化内容
"""

    # ===== 任务 CRUD =====
    def save_task(self, task: Task):
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO tasks
               (id, url, user_opinion, channel, status, original_content, generated_content, error_message, created_at, updated_at, completed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                task.id, task.url, task.user_opinion, task.channel,
                task.status.value if hasattr(task.status, 'value') else task.status,
                task.original_content, task.generated_content, task.error_message,
                task.created_at.isoformat(), task.updated_at.isoformat(),
                task.completed_at.isoformat() if task.completed_at else None,
            ),
        )
        conn.commit()

    def get_all_tasks(self, channel: str = None) -> list[Task]:
        conn = self._get_conn()
        if channel:
            rows = conn.execute("SELECT * FROM tasks WHERE channel=? ORDER BY created_at DESC", (channel,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [Task.from_dict(dict(r)) for r in rows]

    def get_task(self, task_id: str) -> Task | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        return Task.from_dict(dict(row)) if row else None

    def update_task(self, task: Task):
        task.updated_at = __import__("datetime").datetime.now()
        self.save_task(task)

    def delete_task(self, task_id: str):
        conn = self._get_conn()
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()

    # ===== 渠道 CRUD =====
    def get_all_channels(self, active_only: bool = False) -> list[Channel]:
        conn = self._get_conn()
        if active_only:
            rows = conn.execute("SELECT * FROM channels WHERE is_active=1 ORDER BY is_builtin DESC, created_at").fetchall()
        else:
            rows = conn.execute("SELECT * FROM channels ORDER BY is_builtin DESC, created_at").fetchall()
        return [Channel.from_dict(dict(r)) for r in rows]

    def get_channel(self, name: str) -> Channel | None:
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM channels WHERE name=?", (name,)).fetchone()
        return Channel.from_dict(dict(row)) if row else None

    def save_channel(self, channel: Channel):
        conn = self._get_conn()
        conn.execute(
            """INSERT OR REPLACE INTO channels
               (id, name, display_name, system_prompt, is_active, is_builtin, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (channel.id, channel.name, channel.display_name, channel.system_prompt,
             int(channel.is_active), int(channel.is_builtin), channel.created_at.isoformat()),
        )
        conn.commit()

    # ===== 配置 =====
    def get_config(self, key: str) -> str | None:
        conn = self._get_conn()
        row = conn.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def set_config(self, key: str, value: str):
        conn = self._get_conn()
        conn.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        conn.commit()

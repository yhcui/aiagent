"""任务管理器：管理任务队列与异步处理"""
import threading
from pathlib import Path
from queue import Queue, Empty
from datetime import datetime
from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal
from app.models.task import Task, TaskStatus
from app.services.storage_service import StorageService
from app.core.content_fetcher import ContentFetcher
from app.core.content_generator import ContentGenerator
from app.core.channel_manager import ChannelManager


class TaskManager(QObject):
    """
    任务管理器
    - 管理任务队列
    - 后台线程异步执行任务
    - 通过信号通知 UI 更新（线程安全）
    """

    # 信号：任务状态变更（用于跨线程通知 UI）
    task_updated = pyqtSignal(object)  # Task 对象

    def __init__(self, storage: StorageService, channel_manager: ChannelManager, app_config):
        super().__init__()
        self.storage = storage
        self.channel_manager = channel_manager
        self.app_config = app_config
        self.tasks: list[Task] = []
        self._fetcher = ContentFetcher()
        self._generator = ContentGenerator(app_config)
        self._queue: Queue = Queue()
        self._worker_thread = None
        self._running = False
        self._load_tasks()

    def _load_tasks(self):
        self.tasks = self.storage.get_all_tasks()

    def _notify(self, task: Task):
        """通过信号通知任务状态变更（线程安全）"""
        self.task_updated.emit(task)

    def add_task(self, url: str, opinion: str, channel: str = "wechat", original_content: str = None) -> Task:
        task = Task.create(url, opinion, channel)
        if original_content:
            task.original_content = original_content[:50000]  # 限制长度
        self.tasks.insert(0, task)
        self.storage.save_task(task)
        self._notify(task)
        return task

    def add_tasks(self, items: list[tuple[str, str]], channel: str = "wechat") -> list[Task]:
        """批量添加任务"""
        tasks = []
        for url, opinion in items:
            t = self.add_task(url, opinion, channel)
            tasks.append(t)
        return tasks

    def remove_task(self, task_id: str):
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self.storage.delete_task(task_id)

    def get_task(self, task_id: str) -> Task | None:
        return next((t for t in self.tasks if t.id == task_id), None)

    def _update_task(self, task: Task):
        self.storage.update_task(task)
        # 同步内存中任务状态
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                break
        self._notify(task)

    def start_generation(self, task_ids: list[str] = None):
        """启动后台生成（可选指定任务 ID 列表，None = 所有待处理任务）"""
        if self._running:
            logger.warning("生成线程已在运行")
            return
        self._running = True
        target_ids = set(task_ids) if task_ids else None
        
        # 统计待处理任务
        pending_tasks = [t for t in self.tasks if t.status == TaskStatus.PENDING]
        logger.info(f"总任务数：{len(self.tasks)}，待处理任务数：{len(pending_tasks)}")
        
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                if target_ids is None or task.id in target_ids:
                    self._queue.put(task)
                    logger.info(f"任务入队：{task.id[:8]}... 状态={task.status.value}")
        
        if self._queue.empty():
            logger.warning("队列为空，没有待处理的任务！")
            self._running = False
            # 通知 UI 恢复按钮
            self.task_updated.emit(None)  # 发送 None 表示无任务
            return
            
        self._worker_thread = threading.Thread(target=self._worker, daemon=True, name="TaskWorker")
        self._worker_thread.start()
        logger.info(f"启动生成线程，队列任务数：{self._queue.qsize()}")

    def _worker(self):
        while True:
            try:
                task = self._queue.get(timeout=1)
            except Empty:
                if not self._running:
                    break
                continue

            self._process_task(task)
            self._queue.task_done()
            if self._queue.empty():
                self._running = False
                logger.info("所有任务处理完毕，生成线程退出")
                break

    def _process_task(self, task: Task):
        """处理单个任务"""
        try:
            logger.info(f"[DEBUG] 开始处理任务：{task.id}，当前状态：{task.status.value}")
            
            task.status = TaskStatus.PROCESSING
            self._update_task(task)
            logger.info(f"处理任务：{task.id}，URL={task.url}")

            # 1. 抓取原文（如果有则跳过）
            if not task.original_content:
                # 检查 URL 是否有效（非占位符）
                if not task.url or task.url.startswith("(") and task.url.endswith(")"):
                    raise ValueError("未提供有效的文章链接，请填写链接或切换到「粘贴原文」模式")
                original = self._fetcher.fetch(task.url)
                if not original:
                    raise ValueError("无法抓取文章内容，请检查链接是否正确或手动粘贴原文")
                task.original_content = original[:50000]  # 限制长度

            # 2. 获取渠道系统提示词
            system_prompt = self.channel_manager.get_system_prompt(task.channel)

            # 3. 生成图文
            generated = self._generator.generate_article(
                system_prompt=system_prompt,
                user_opinion=task.user_opinion,
                original_content=task.original_content,
            )
            
            logger.info(f"[DEBUG] 生成内容长度：{len(generated) if generated else 0}")

            task.generated_content = generated
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            self._update_task(task)
            logger.info(f"[DEBUG] 任务完成并保存：{task.id}，status={task.status.value}，has_content={bool(task.generated_content)}")
            logger.info(f"任务完成：{task.id}")
            
            # 自动导出为 .md 文件
            self._auto_export(task)

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self._update_task(task)
            logger.error(f"任务失败：{task.id}，错误：{e}")

    def _auto_export(self, task: Task):
        """自动导出任务为 .md 文件"""
        try:
            # 创建导出目录
            export_dir = self.app_config.data_dir / "exports"
            export_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名（使用时间戳+任务ID前8位）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{task.id[:8]}.md"
            filepath = export_dir / filename
            
            # 写入文件（包含元数据）
            content = f"""# 生成内容

**来源**: {task.url}
**观点**: {task.user_opinion}
**渠道**: {task.channel}
**完成时间**: {task.completed_at.strftime('%Y-%m-%d %H:%M:%S') if task.completed_at else 'N/A'}

---

{task.generated_content}
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"已自动导出：{filepath}")
        except Exception as e:
            logger.error(f"自动导出失败：{e}")

    def cancel_all(self):
        """取消所有待处理任务"""
        self._running = False
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except Empty:
                break
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                task.status = TaskStatus.FAILED
                task.error_message = "用户取消"
                self._update_task(task)
        logger.info("已取消所有待处理任务")

    def regenerate(self, task_id: str):
        """重新生成单个任务"""
        task = self.get_task(task_id)
        if not task:
            return
        task.status = TaskStatus.PENDING
        task.generated_content = ""
        task.error_message = ""
        task.completed_at = None
        self._update_task(task)
        self._queue.put(task)
        if not self._running:
            self._running = True
            if not self._worker_thread or not self._worker_thread.is_alive():
                self._worker_thread = threading.Thread(target=self._worker, daemon=True, name="TaskWorker")
                self._worker_thread.start()

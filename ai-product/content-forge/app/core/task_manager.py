"""任务管理器：管理任务队列与异步处理"""
import threading
from queue import Queue, Empty
from loguru import logger
from app.models.task import Task, TaskStatus
from app.services.storage_service import StorageService
from app.core.content_fetcher import ContentFetcher
from app.core.content_generator import ContentGenerator
from app.core.channel_manager import ChannelManager


class TaskManager:
    """
    任务管理器
    - 管理任务队列
    - 后台线程异步执行任务
    - 事件回调通知 UI 更新
    """

    def __init__(self, storage: StorageService, channel_manager: ChannelManager, app_config):
        self.storage = storage
        self.channel_manager = channel_manager
        self.app_config = app_config
        self.tasks: list[Task] = []
        self._fetcher = ContentFetcher()
        self._generator = ContentGenerator(app_config)
        self._queue: Queue = Queue()
        self._worker_thread = None
        self._running = False
        self._listeners: list[callable] = []
        self._load_tasks()

    def _load_tasks(self):
        self.tasks = self.storage.get_all_tasks()

    def add_listener(self, callback: callable):
        """添加任务状态变更监听器（用于驱动 UI 更新）"""
        self._listeners.append(callback)

    def _notify(self, task: Task):
        for cb in self._listeners:
            try:
                cb(task)
            except Exception as e:
                logger.error(f"通知监听器失败：{e}")

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
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                if target_ids is None or task.id in target_ids:
                    self._queue.put(task)
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
            task.status = TaskStatus.PROCESSING
            self._update_task(task)
            logger.info(f"处理任务：{task.id}，URL={task.url}")

            # 1. 抓取原文（如果有则跳过）
            if not task.original_content:
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

            task.generated_content = generated
            task.status = TaskStatus.COMPLETED
            from datetime import datetime
            task.completed_at = datetime.now()
            self._update_task(task)
            logger.info(f"任务完成：{task.id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self._update_task(task)
            logger.error(f"任务失败：{task.id}，错误：{e}")

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

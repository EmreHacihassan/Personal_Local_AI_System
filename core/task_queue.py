"""
Async Task Queue System
=======================

Endüstri standartlarında asenkron görev kuyruğu sistemi.
Uzun süren işlemler için background task yönetimi sağlar.

Features:
- Priority-based task scheduling
- Task retry with exponential backoff
- Task cancellation
- Progress tracking
- Task persistence
- Concurrent worker pool
"""

import asyncio
import uuid
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import traceback
from functools import wraps

from .logger import get_logger

logger = get_logger("task_queue")


class TaskStatus(Enum):
    """Task durumları"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task öncelikleri"""
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class TaskResult:
    """Task sonucu"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time
        }


@dataclass
class Task:
    """Task tanımı"""
    id: str
    name: str
    func_name: str
    args: tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    retry_count: int = 0
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: Optional[float] = None  # seconds
    progress: float = 0.0  # 0.0 - 1.0
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "func_name": self.func_name,
            "status": self.status.value,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result.to_dict() if self.result else None,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "progress": self.progress,
            "metadata": self.metadata
        }


class TaskRegistry:
    """Callable task fonksiyonlarının registry'si"""
    
    def __init__(self):
        self._tasks: Dict[str, Callable] = {}
    
    def register(self, name: Optional[str] = None):
        """Task fonksiyonunu kaydet (decorator)"""
        def decorator(func: Callable):
            task_name = name or func.__name__
            self._tasks[task_name] = func
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    def get(self, name: str) -> Optional[Callable]:
        """Task fonksiyonunu al"""
        return self._tasks.get(name)
    
    def list_tasks(self) -> List[str]:
        """Kayıtlı task isimlerini listele"""
        return list(self._tasks.keys())


# Global registry
task_registry = TaskRegistry()


class TaskQueue:
    """
    Asenkron görev kuyruğu
    
    Features:
    - Priority queue
    - Concurrent workers
    - Retry mechanism
    - Progress tracking
    - Persistence
    """
    
    def __init__(
        self,
        db_path: Optional[Path] = None,
        max_workers: int = 4,
        persist: bool = True
    ):
        self.db_path = db_path or Path("data/task_queue.db")
        self.max_workers = max_workers
        self.persist = persist
        
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._lock = asyncio.Lock()
        self._callbacks: Dict[str, List[Callable]] = {
            "on_start": [],
            "on_complete": [],
            "on_error": [],
            "on_progress": []
        }
        
        if self.persist:
            self._init_db()
    
    def _init_db(self):
        """SQLite veritabanını başlat"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                func_name TEXT NOT NULL,
                args TEXT,
                kwargs TEXT,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                result TEXT,
                retry_count INTEGER DEFAULT 0,
                max_retries INTEGER DEFAULT 3,
                progress REAL DEFAULT 0.0,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_task_priority ON tasks(priority DESC)
        """)
        
        conn.commit()
        conn.close()
        
        logger.info("Task queue database initialized")
    
    def _save_task(self, task: Task):
        """Task'ı veritabanına kaydet"""
        if not self.persist:
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO tasks
            (id, name, func_name, args, kwargs, status, priority,
             created_at, started_at, completed_at, result,
             retry_count, max_retries, progress, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            task.id,
            task.name,
            task.func_name,
            json.dumps(task.args),
            json.dumps(task.kwargs),
            task.status.value,
            task.priority.value,
            task.created_at.isoformat(),
            task.started_at.isoformat() if task.started_at else None,
            task.completed_at.isoformat() if task.completed_at else None,
            json.dumps(task.result.to_dict()) if task.result else None,
            task.retry_count,
            task.max_retries,
            task.progress,
            json.dumps(task.metadata)
        ))
        
        conn.commit()
        conn.close()
    
    def _load_pending_tasks(self):
        """Pending task'ları veritabanından yükle"""
        if not self.persist or not self.db_path.exists():
            return
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM tasks
            WHERE status IN ('pending', 'retrying')
            ORDER BY priority DESC, created_at ASC
        """)
        
        for row in cursor.fetchall():
            task = Task(
                id=row[0],
                name=row[1],
                func_name=row[2],
                args=tuple(json.loads(row[3] or "[]")),
                kwargs=json.loads(row[4] or "{}"),
                status=TaskStatus(row[5]),
                priority=TaskPriority(row[6]),
                created_at=datetime.fromisoformat(row[7]),
                retry_count=row[11],
                max_retries=row[12],
                progress=row[13],
                metadata=json.loads(row[14] or "{}")
            )
            
            self._tasks[task.id] = task
            # Priority queue: (negative priority for max-heap behavior, created_at, task_id)
            asyncio.create_task(
                self._queue.put((-task.priority.value, task.created_at, task.id))
            )
        
        conn.close()
        
        logger.info(f"Loaded {len(self._tasks)} pending tasks from database")
    
    async def submit(
        self,
        func_name: str,
        *args,
        name: Optional[str] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        metadata: Optional[Dict] = None,
        **kwargs
    ) -> str:
        """
        Task'ı kuyruğa ekle
        
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]
        
        task = Task(
            id=task_id,
            name=name or func_name,
            func_name=func_name,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            metadata=metadata or {}
        )
        
        async with self._lock:
            self._tasks[task_id] = task
            await self._queue.put((-priority.value, task.created_at, task_id))
        
        self._save_task(task)
        
        logger.info(f"Task submitted: {task_id} ({task.name})")
        
        return task_id
    
    async def cancel(self, task_id: str) -> bool:
        """Task'ı iptal et"""
        async with self._lock:
            if task_id not in self._tasks:
                return False
            
            task = self._tasks[task_id]
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                return False
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            
            self._save_task(task)
        
        logger.info(f"Task cancelled: {task_id}")
        
        return True
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Task bilgisini al"""
        return self._tasks.get(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Task durumunu al"""
        task = self._tasks.get(task_id)
        return task.status if task else None
    
    def get_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Task sonucunu al"""
        task = self._tasks.get(task_id)
        return task.result if task else None
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None,
        poll_interval: float = 0.1
    ) -> Optional[TaskResult]:
        """Task'ın tamamlanmasını bekle"""
        start_time = datetime.now()
        
        while True:
            task = self._tasks.get(task_id)
            
            if not task:
                return None
            
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                return task.result
            
            if timeout:
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed > timeout:
                    return None
            
            await asyncio.sleep(poll_interval)
    
    def update_progress(self, task_id: str, progress: float):
        """Task progress'ini güncelle"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.progress = max(0.0, min(1.0, progress))
            
            # Trigger callbacks
            for callback in self._callbacks["on_progress"]:
                try:
                    callback(task)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
    
    def on(self, event: str, callback: Callable):
        """Event callback ekle"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    async def _execute_task(self, task: Task) -> TaskResult:
        """Task'ı çalıştır"""
        func = task_registry.get(task.func_name)
        
        if not func:
            return TaskResult(
                success=False,
                error=f"Task function not found: {task.func_name}"
            )
        
        start_time = datetime.now()
        
        try:
            # Timeout ile çalıştır
            if task.timeout:
                result = await asyncio.wait_for(
                    self._run_func(func, task.args, task.kwargs),
                    timeout=task.timeout
                )
            else:
                result = await self._run_func(func, task.args, task.kwargs)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return TaskResult(
                success=True,
                data=result,
                execution_time=execution_time
            )
        
        except asyncio.TimeoutError:
            return TaskResult(
                success=False,
                error=f"Task timed out after {task.timeout}s",
                execution_time=task.timeout
            )
        
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            return TaskResult(
                success=False,
                error=f"{type(e).__name__}: {str(e)}",
                execution_time=execution_time
            )
    
    async def _run_func(self, func: Callable, args: tuple, kwargs: dict) -> Any:
        """Fonksiyonu çalıştır (async veya sync)"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Sync fonksiyonları thread pool'da çalıştır
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))
    
    async def _worker(self, worker_id: int):
        """Worker coroutine"""
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                # Get next task (with timeout to check running flag)
                try:
                    priority, created_at, task_id = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                async with self._lock:
                    if task_id not in self._tasks:
                        continue
                    
                    task = self._tasks[task_id]
                    
                    # Skip cancelled tasks
                    if task.status == TaskStatus.CANCELLED:
                        continue
                    
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now()
                
                # Trigger on_start callbacks
                for callback in self._callbacks["on_start"]:
                    try:
                        callback(task)
                    except Exception as e:
                        logger.error(f"Start callback error: {e}")
                
                logger.info(f"Worker {worker_id} executing: {task_id} ({task.name})")
                
                # Execute task
                result = await self._execute_task(task)
                
                async with self._lock:
                    task.result = result
                    
                    if result.success:
                        task.status = TaskStatus.COMPLETED
                        task.progress = 1.0
                        
                        # Trigger on_complete callbacks
                        for callback in self._callbacks["on_complete"]:
                            try:
                                callback(task)
                            except Exception as e:
                                logger.error(f"Complete callback error: {e}")
                    
                    else:
                        # Retry logic
                        if task.retry_count < task.max_retries:
                            task.retry_count += 1
                            task.status = TaskStatus.RETRYING
                            
                            # Exponential backoff
                            delay = task.retry_delay * (2 ** (task.retry_count - 1))
                            
                            logger.warning(
                                f"Task {task_id} failed, retrying in {delay}s "
                                f"({task.retry_count}/{task.max_retries})"
                            )
                            
                            # Schedule retry
                            await asyncio.sleep(delay)
                            await self._queue.put((-task.priority.value, datetime.now(), task_id))
                        
                        else:
                            task.status = TaskStatus.FAILED
                            
                            # Trigger on_error callbacks
                            for callback in self._callbacks["on_error"]:
                                try:
                                    callback(task)
                                except Exception as e:
                                    logger.error(f"Error callback error: {e}")
                    
                    task.completed_at = datetime.now()
                
                self._save_task(task)
                
                logger.info(f"Task {task_id} {task.status.value}: {result.execution_time:.2f}s")
            
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}\n{traceback.format_exc()}")
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def start(self):
        """Task queue'yu başlat"""
        if self._running:
            return
        
        self._running = True
        
        # Load pending tasks from database
        self._load_pending_tasks()
        
        # Start workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        
        logger.info(f"Task queue started with {self.max_workers} workers")
    
    async def stop(self, wait: bool = True):
        """Task queue'yu durdur"""
        self._running = False
        
        if wait:
            # Wait for workers to finish
            await asyncio.gather(*self._workers, return_exceptions=True)
        
        self._workers.clear()
        
        logger.info("Task queue stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """Queue istatistiklerini al"""
        stats = {
            "total_tasks": len(self._tasks),
            "queue_size": self._queue.qsize(),
            "workers": len(self._workers),
            "running": self._running,
            "by_status": {}
        }
        
        for status in TaskStatus:
            count = sum(1 for t in self._tasks.values() if t.status == status)
            stats["by_status"][status.value] = count
        
        return stats
    
    def get_recent_tasks(
        self,
        limit: int = 10,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Son task'ları getir"""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        # Sort by created_at descending
        tasks.sort(key=lambda t: t.created_at, reverse=True)
        
        return tasks[:limit]


# Global task queue instance
task_queue = TaskQueue()


# ========================
# Built-in Tasks
# ========================

@task_registry.register("document_index")
async def index_document(file_path: str, **kwargs) -> Dict:
    """Döküman indexleme task'ı"""
    # Bu fonksiyon rag modülü tarafından override edilebilir
    return {"status": "indexed", "file": file_path}


@task_registry.register("batch_embed")
async def batch_embed_texts(texts: List[str], **kwargs) -> Dict:
    """Toplu embedding task'ı"""
    return {"status": "embedded", "count": len(texts)}


@task_registry.register("cleanup_cache")
async def cleanup_cache(max_age_hours: int = 24, **kwargs) -> Dict:
    """Cache temizleme task'ı"""
    return {"status": "cleaned", "max_age_hours": max_age_hours}


@task_registry.register("generate_report")
async def generate_analytics_report(
    days: int = 7,
    report_type: str = "summary",
    **kwargs
) -> Dict:
    """Analytics raporu oluşturma task'ı"""
    return {
        "status": "generated",
        "days": days,
        "type": report_type
    }


@task_registry.register("knowledge_graph_update")
async def update_knowledge_graph(document_ids: List[str], **kwargs) -> Dict:
    """Knowledge graph güncelleme task'ı"""
    return {"status": "updated", "documents": len(document_ids)}


# ========================
# Convenience Functions
# ========================

async def submit_task(
    func_name: str,
    *args,
    **kwargs
) -> str:
    """Convenience function for submitting tasks"""
    return await task_queue.submit(func_name, *args, **kwargs)


async def get_task_status(task_id: str) -> Optional[str]:
    """Convenience function for getting task status"""
    status = task_queue.get_task_status(task_id)
    return status.value if status else None


__all__ = [
    "TaskQueue",
    "Task",
    "TaskResult",
    "TaskStatus",
    "TaskPriority",
    "TaskRegistry",
    "task_queue",
    "task_registry",
    "submit_task",
    "get_task_status"
]

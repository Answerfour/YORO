"""ThreadPool Utility Module - Provides background task execution capabilities"""
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Optional
from threading import Event


class TaskFuture:
    """Task future wrapper"""
    
    def __init__(self, future: Future, cancel_event: Event):
        self._future = future
        self._cancel_event = cancel_event
    
    def cancel(self) -> bool:
        self._cancel_event.set()
        return self._future.cancel()
    
    @property
    def done(self) -> bool:
        return self._future.done()
    
    @property
    def cancelled(self) -> bool:
        return self._future.cancelled()
    
    def result(self, timeout: Optional[float] = None) -> Any:
        return self._future.result(timeout)
    
    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class ThreadPool:
    """Thread pool manager - Singleton pattern"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_workers: int = 4):
        if self._initialized:
            return
        self._initialized = True
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._tasks: dict[str, TaskFuture] = {}
    
    def submit(self, task_id: str, func: Callable, *args, **kwargs) -> TaskFuture:
        cancel_event = Event()
        
        def wrapped_func():
            if cancel_event.is_set():
                return None
            return func(*args, **kwargs)
        
        future = self._executor.submit(wrapped_func)
        task_future = TaskFuture(future, cancel_event)
        self._tasks[task_id] = task_future
        return task_future
    
    def cancel(self, task_id: str) -> bool:
        if task_id in self._tasks:
            return self._tasks[task_id].cancel()
        return False
    
    def cancel_all(self):
        for task_id in list(self._tasks.keys()):
            self.cancel(task_id)
    
    def get_task(self, task_id: str) -> Optional[TaskFuture]:
        return self._tasks.get(task_id)
    
    def remove_task(self, task_id: str):
        if task_id in self._tasks:
            del self._tasks[task_id]
    
    def shutdown(self, wait: bool = True):
        self._executor.shutdown(wait=wait)
    
    @staticmethod
    def get_instance() -> 'ThreadPool':
        return ThreadPool()
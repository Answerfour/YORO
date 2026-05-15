"""核心抽象基类定义 - 提供模块通用接口"""
from abc import ABC, abstractmethod
from typing import Optional, List, Tuple
import tkinter as tk
from tkinter import ttk


class TaskExecutor(ABC):
    """任务执行器抽象基类"""
    
    @abstractmethod
    def execute(self, **kwargs) -> bool:
        """执行任务，返回是否成功"""
        pass
    
    @abstractmethod
    def cancel(self) -> None:
        """取消任务"""
        pass
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """任务是否正在运行"""
        pass


class FileProcessor(ABC):
    """文件处理器抽象基类"""
    
    @abstractmethod
    def process_file(self, file_path: str) -> bool:
        """处理单个文件，返回是否成功"""
        pass
    
    @abstractmethod
    def process_batch(self, file_paths: List[str]) -> Tuple[int, int]:
        """批量处理文件，返回 (成功数, 失败数)"""
        pass


class BaseModule(ABC):
    """模块基类 - 定义模块通用接口"""
    
    def __init__(self, parent_window: Optional[tk.Tk] = None):
        self.parent = parent_window
        self._enabled = True
        self._widgets: Optional[ttk.Frame] = None
    
    @abstractmethod
    def get_name(self) -> str:
        """获取模块名称"""
        pass
    
    @abstractmethod
    def get_widgets(self) -> ttk.Frame:
        """获取模块的GUI组件"""
        pass
    
    @abstractmethod
    def validate_inputs(self) -> Tuple[bool, List[str]]:
        """验证输入，返回 (是否有效, 错误信息列表)"""
        pass
    
    @abstractmethod
    def on_activate(self) -> None:
        """模块被激活时调用"""
        pass
    
    @abstractmethod
    def on_deactivate(self) -> None:
        """模块被停用时调用"""
        pass
    
    def enable(self) -> None:
        self._enabled = True
        
    def disable(self) -> None:
        self._enabled = False
        
    @property
    def is_enabled(self) -> bool:
        return self._enabled
    
    def reset(self) -> None:
        """重置模块状态"""
        pass

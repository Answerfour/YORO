"""Core Abstract Base Classes - Provide module common interfaces"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional


class TaskExecutor(ABC):
    """Abstract base class for task executors"""
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the task and return whether it succeeded"""
        pass
    
    @abstractmethod
    def cancel(self):
        """Cancel the task"""
        pass
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Whether the task is currently running"""
        pass


class FileProcessor(ABC):
    """Abstract base class for file processors"""
    
    @abstractmethod
    def process_file(self, file_path: str) -> bool:
        """Process a single file, return whether it succeeded"""
        pass
    
    @abstractmethod
    def process_batch(self, file_paths: List[str]) -> Tuple[int, int]:
        """Process multiple files in batch, return (success_count, failure_count)"""
        pass


class BaseModule(ABC):
    """Base class for modules - defines common module interface"""
    
    def __init__(self):
        self._is_active = False
    
    @abstractmethod
    def get_name(self) -> str:
        """Get module name"""
        pass
    
    @abstractmethod
    def get_gui_component(self, parent) -> 'BaseModule':
        """Get the GUI component for this module"""
        pass
    
    @abstractmethod
    def validate_input(self) -> Tuple[bool, List[str]]:
        """Validate input, return (is_valid, error_messages)"""
        pass
    
    def activate(self):
        """Called when module is activated"""
        self._is_active = True
    
    def deactivate(self):
        """Called when module is deactivated"""
        self._is_active = False
    
    @property
    def is_active(self) -> bool:
        return self._is_active
    
    def reset(self):
        """Reset module state"""
        pass
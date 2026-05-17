"""Persistence Utility Module - Provides automatic configuration saving and loading functionality"""
import json
import os
from typing import TypeVar, Generic, Type, Optional, Any
from dataclasses import asdict, is_dataclass
from threading import Lock
from pathlib import Path


T = TypeVar('T')


class PersistenceManager:
    """Configuration persistence manager - Singleton pattern"""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._file_locks: dict[str, Lock] = {}
        self._config_dir = self._get_config_dir()
    
    def _get_config_dir(self) -> str:
        config_dir = Path(__file__).parent.parent / "config_data"
        config_dir.mkdir(exist_ok=True)
        return str(config_dir)
    
    def _get_file_lock(self, file_path: str) -> Lock:
        if file_path not in self._file_locks:
            self._file_locks[file_path] = Lock()
        return self._file_locks[file_path]
    
    def save(self, data: Any, file_path: Optional[str] = None, auto_named: bool = False) -> bool:
        if file_path is None and auto_named:
            file_path = os.path.join(self._config_dir, f"{type(data).__name__}.json")
        
        if not file_path:
            return False
        
        with self._get_file_lock(file_path):
            try:
                os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
                
                if is_dataclass(data):
                    save_data = asdict(data)
                elif hasattr(data, '__dict__'):
                    save_data = vars(data)
                else:
                    save_data = data
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(save_data, f, ensure_ascii=False, indent=2)
                return True
            except Exception as e:
                print(f"Failed to save config {file_path}: {e}")
                return False
    
    def load(self, file_path: str, default_factory: Optional[Type[T]] = None) -> Optional[Any]:
        if not os.path.exists(file_path):
            return default_factory() if default_factory else None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if default_factory and is_dataclass(default_factory):
                return default_factory(**data)
            elif default_factory:
                instance = default_factory()
                for k, v in data.items():
                    if hasattr(instance, k):
                        setattr(instance, k, v)
                return instance
            else:
                return data
        except Exception as e:
            print(f"Failed to load config {file_path}: {e}")
            return default_factory() if default_factory else None
    
    def exists(self, file_path: str) -> bool:
        return os.path.exists(file_path)
    
    @staticmethod
    def get_instance() -> 'PersistenceManager':
        return PersistenceManager()
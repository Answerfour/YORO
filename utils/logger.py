"""Logger Utility Module - Provides unified logging functionality"""
import tkinter as tk
from datetime import datetime
from typing import Optional, Callable
from threading import Lock


class Logger:
    """Thread-safe logger with UI component integration support"""
    
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
        self._text_widget: Optional[tk.Text] = None
        self._status_var: Optional[tk.StringVar] = None
        self._root: Optional[tk.Wm] = None
        self._log_callback: Optional[Callable[[str, str], None]] = None
    
    def bind_ui(self, text_widget: tk.Text, status_var: Optional[tk.StringVar] = None, root: Optional[tk.Wm] = None):
        self._text_widget = text_widget
        self._status_var = status_var
        self._root = root
    
    def set_log_callback(self, callback: Callable[[str, str], None]):
        self._log_callback = callback
    
    def log(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = {"info": "ℹ", "warning": "⚠", "error": "✗", "success": "✓"}.get(level, "•")
        formatted_msg = f"[{timestamp}] {prefix} {message}"
        
        if self._text_widget:
            self._text_widget.insert(tk.END, formatted_msg + "\n")
            self._text_widget.see(tk.END)
        
        if self._root:
            self._root.update_idletasks()
        
        if self._log_callback:
            self._log_callback(formatted_msg, level)
    
    def info(self, message: str):
        self.log(message, "info")
    
    def warning(self, message: str):
        self.log(message, "warning")
    
    def error(self, message: str):
        self.log(message, "error")
    
    def success(self, message: str):
        self.log(message, "success")
    
    def set_status(self, message: str):
        if self._status_var:
            self._status_var.set(message)
        if self._root:
            self._root.update_idletasks()
    
    def clear(self):
        if self._text_widget:
            self._text_widget.delete(1.0, tk.END)
    
    @staticmethod
    def get_instance() -> 'Logger':
        return Logger()
"""UI Components Module - Provides common UI components"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional, Callable


class FileSelectionFrame(ttk.Frame):
    """File selection frame component"""
    
    def __init__(self, parent, label_text: str, button_text: str = "Browse...",
                 file_types: Optional[list] = None, mode: str = "file", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.path_var = tk.StringVar()
        self.file_types = file_types
        self.mode = mode
        
        ttk.Label(self, text=label_text).pack(side=tk.LEFT, padx=5)
        ttk.Entry(self, textvariable=self.path_var, width=40).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(self, text=button_text, command=self.select_path).pack(side=tk.LEFT, padx=5)
        
        if mode == "folder":
            ttk.Button(self, text="Refresh", command=self.refresh_callback).pack(side=tk.LEFT, padx=2) if hasattr(self, 'refresh_callback') else None
    
    def select_path(self):
        if self.mode == "file":
            path = filedialog.askopenfilename(title="Select file", filetypes=self.file_types or [("All files", "*.*")])
        else:
            path = filedialog.askdirectory(title="Select folder")
        
        if path:
            self.path_var.set(path)
    
    def get_path(self) -> str:
        return self.path_var.get()
    
    def set_path(self, path: str):
        self.path_var.set(path)


class DirectorySelectionFrame(FileSelectionFrame):
    """Directory selection frame component"""
    
    def __init__(self, parent, label_text: str, button_text: str = "Browse...", **kwargs):
        super().__init__(parent, label_text, button_text, mode="directory", **kwargs)


class LogFrame(ttk.Frame):
    """Log display frame component"""
    
    def __init__(self, parent, height: int = 8, **kwargs):
        super().__init__(parent, **kwargs)
        
        ttk.Label(self, text="Running Log:").pack(anchor=tk.W)
        
        self.text_widget = scrolledtext.ScrolledText(
            self, height=height, wrap=tk.WORD, font=("Consolas", 9)
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_widget.insert(tk.END, f"[{timestamp}] {message}\n")
        self.text_widget.see(tk.END)
    
    def clear(self):
        self.text_widget.delete(1.0, tk.END)


class ProgressFrame(ttk.Frame):
    """Progress display frame component"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        self.label = ttk.Label(self, text="")
        self.label.pack()
    
    def update_progress(self, current: int, total: int, message: str = ""):
        if total > 0:
            self.progress_var.set(int(current / total * 100))
        if message:
            self.label.config(text=message)
    
    def reset(self):
        self.progress_var.set(0)
        self.label.config(text="")


class StatusBar(ttk.Frame):
    """Status bar component"""
    
    def __init__(self, parent, initial_text: str = "Ready", **kwargs):
        super().__init__(parent, **kwargs)
        
        self.status_var = tk.StringVar(value=initial_text)
        ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W).pack(fill=tk.X)
    
    def set_status(self, message: str):
        self.status_var.set(message)
    
    def get_status(self) -> str:
        return self.status_var.get()


class ConfirmationDialog:
    """Confirmation dialog"""
    
    @staticmethod
    def confirm(parent, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message)
    
    @staticmethod
    def warning(parent, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, icon='warning')
    
    @staticmethod
    def error(parent, title: str, message: str):
        messagebox.showerror(title, message)
    
    @staticmethod
    def info(parent, title: str, message: str):
        messagebox.showinfo(title, message)
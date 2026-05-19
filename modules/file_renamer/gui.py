"""File Renamer Module GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Tuple
from modules.file_renamer.renamer import FileRenamer
from config.schema import RenamerConfig
from ui.components import LogFrame


class FileRenamerGUI(ttk.Frame):
    """File Renamer GUI Component"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.renamer = None
        self.preview_data: List[Tuple[str, str]] = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        folder_frame = ttk.LabelFrame(self, text="1. Select Folder", padding=5)
        folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(folder_frame, text="Path:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.folder_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(folder_frame, text="Browse...", command=self._select_folder).grid(row=0, column=2, padx=5)
        
        param_frame = ttk.LabelFrame(self, text="2. Rename Settings", padding=5)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(param_frame, text="File Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_type_var = tk.StringVar(value="txt")
        ttk.Radiobutton(param_frame, text="Text (.txt)", variable=self.file_type_var, value="txt").grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(param_frame, text="Images (.jpg/.png/.gif/.bmp/.tiff/.webp)", variable=self.file_type_var, value="image").grid(row=0, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(param_frame, text="Start Number:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_number_var = tk.IntVar(value=1)
        ttk.Spinbox(param_frame, from_=1, to=999999, textvariable=self.start_number_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(param_frame, text="Digit Width:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.digit_width_var = tk.IntVar(value=6)
        ttk.Spinbox(param_frame, from_=1, to=10, textvariable=self.digit_width_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Label(param_frame, text="(e.g., width 6 → 000001)").grid(row=2, column=2, sticky=tk.W, padx=5)
        
        btn_frame = ttk.Frame(param_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="Preview Rename", command=self._preview_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Execute Rename", command=self._execute_rename).pack(side=tk.LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(self, text="3. Preview (Old → New)", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        log_frame = ttk.LabelFrame(self, text="Operation Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        self.log_frame = LogFrame(log_frame, height=8)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_frame.log("Welcome to Batch Rename Tool. Please select a folder and click Preview.")
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Files to Rename")
        if folder:
            self.folder_path_var.set(folder)
            self.log_frame.log(f"Selected folder: {folder}")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
    
    def _preview_rename(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("Warning", "Please select a folder first!")
            return
        
        config = RenamerConfig(
            file_type=self.file_type_var.get(),
            start_number=self.start_number_var.get(),
            digit_width=self.digit_width_var.get()
        )
        
        self.renamer = FileRenamer(folder, config)
        files = self.renamer.load_files()
        
        if not files:
            self.log_frame.log(f"Warning: No {'TXT' if config.file_type == 'txt' else 'image'} files found in folder.")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
            return
        
        self.preview_data = self.renamer.generate_preview()
        
        self.listbox.delete(0, tk.END)
        for old, new in self.preview_data:
            self.listbox.insert(tk.END, f"{old}  →  {new}")
        
        self.log_frame.log(f"Preview generated: {len(files)} files, start {config.start_number}, width {config.digit_width}")
    
    def _execute_rename(self):
        if not self.preview_data:
            messagebox.showwarning("Warning", "Please click Preview first to generate the rename list!")
            return
        
        if not self.renamer:
            messagebox.showerror("Error", "System error, please preview again")
            return
        
        if not messagebox.askyesno("Confirm Rename",
                                   f"About to rename {len(self.preview_data)} files.\n\nThis operation cannot be undone. Continue?"):
            self.log_frame.log("Operation cancelled.")
            return
        
        success, failed = self.renamer.execute_rename()
        
        self.log_frame.log("\n========== Rename Results ==========")
        self.log_frame.log(f"Success: {len(success)}, Failed: {len(failed)}.")
        
        if not failed:
            self.log_frame.log("All files renamed successfully!")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
        else:
            self.log_frame.log("Some files failed to rename, check the log.")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
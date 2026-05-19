"""Orphan File Cleaner Module GUI"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict
from modules.orphan_cleaner.cleaner import OrphanCleaner


class OrphanCleanerGUI(ttk.Frame):
    """Orphan File Cleaner GUI Component"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.cleaner = None
        self.analysis_result: Dict = {}
        
        self._create_widgets()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_folder_selection(main_frame)
        self._create_options(main_frame)
        self._create_buttons(main_frame)
        self._create_results(main_frame)
        self._create_log(main_frame)
        self._create_status_bar(main_frame)
    
    def _create_folder_selection(self, parent):
        folder_frame = ttk.LabelFrame(parent, text="Folder Selection", padding="10")
        folder_frame.pack(fill=tk.X, pady=10)
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Folder 1 (Images):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.folder1_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder1_path_var, width=50).grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(folder_frame, text="Browse...", command=lambda: self._select_folder(self.folder1_path_var, 1)).grid(row=0, column=2, padx=5)
        ttk.Button(folder_frame, text="Refresh", command=lambda: self._load_files(1)).grid(row=0, column=3, padx=5)
        
        ttk.Label(folder_frame, text="Folder 2 (TXT):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.folder2_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder2_path_var, width=50).grid(row=1, column=1, padx=5, sticky=(tk.W, tk.E), pady=(5, 0))
        ttk.Button(folder_frame, text="Browse...", command=lambda: self._select_folder(self.folder2_path_var, 2)).grid(row=1, column=2, padx=5, pady=(5, 0))
        ttk.Button(folder_frame, text="Refresh", command=lambda: self._load_files(2)).grid(row=1, column=3, padx=5, pady=(5, 0))
    
    def _create_options(self, parent):
        options_frame = ttk.LabelFrame(parent, text="Matching Options", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        self.pairing_mode_var = tk.StringVar(value="name")
        ttk.Radiobutton(options_frame, text="Match by Name (same filename)",
                        variable=self.pairing_mode_var, value="name").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(options_frame, text="Match by Sequence (first with first)",
                        variable=self.pairing_mode_var, value="sequence").pack(side=tk.LEFT, padx=10)
    
    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Scan and Analyze", command=self._scan_and_analyze).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Delete Orphans", command=self._delete_orphans).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Move Orphans", command=self._move_orphans).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=5)
    
    def _create_results(self, parent):
        result_frame = ttk.LabelFrame(parent, text="Analysis Results", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        columns = ("type", "filename", "status")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="tree headings", height=12)
        self.tree.heading("#0", text="Index")
        self.tree.heading("type", text="Type")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("status", text="Status")
        
        self.tree.column("#0", width=60)
        self.tree.column("type", width=100)
        self.tree.column("filename", width=350)
        self.tree.column("status", width=150)
        
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.tree.tag_configure("paired", foreground="green")
        self.tree.tag_configure("orphan1", foreground="orange")
        self.tree.tag_configure("orphan2", foreground="red")
    
    def _create_log(self, parent):
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 10))
        
        ttk.Label(log_frame, text="Operation Log:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self, parent):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)
    
    def _select_folder(self, path_var, folder_num):
        folder = filedialog.askdirectory()
        if folder:
            path_var.set(folder)
            self._load_files(folder_num)
            self._log(f"Selected folder{folder_num}: {folder}")
    
    def _load_files(self, folder_num):
        if folder_num == 1:
            folder_path = self.folder1_path_var.get()
            if folder_path and os.path.exists(folder_path):
                from core.file_operator import FileOperator
                self.folder1_files = FileOperator.get_image_files(folder_path)
                self._log(f"Folder 1 loaded: {len(self.folder1_files)} image files found")
                self.status_var.set(f"Folder 1: {len(self.folder1_files)} image files")
        else:
            folder_path = self.folder2_path_var.get()
            if folder_path and os.path.exists(folder_path):
                from core.file_operator import FileOperator
                self.folder2_files = FileOperator.get_txt_files(folder_path)
                self._log(f"Folder 2 loaded: {len(self.folder2_files)} TXT files found")
                self.status_var.set(f"Folder 2: {len(self.folder2_files)} TXT files")
    
    def _scan_and_analyze(self):
        if not hasattr(self, 'folder1_files') or not hasattr(self, 'folder2_files'):
            messagebox.showwarning("Warning", "Please select both folders and refresh!")
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self._log("=" * 60)
        self._log("Starting file pairing analysis...")
        
        folder1_path = self.folder1_path_var.get()
        folder2_path = self.folder2_path_var.get()
        
        self.cleaner = OrphanCleaner(folder1_path, folder2_path, self.pairing_mode_var.get())
        self.cleaner.folder1_files = self.folder1_files
        self.cleaner.folder2_files = self.folder2_files
        self.analysis_result = self.cleaner.analyze()
        
        paired_count = self.analysis_result['paired_count']
        orphan1_count = self.analysis_result['orphan1_count']
        orphan2_count = self.analysis_result['orphan2_count']
        
        if paired_count > 0:
            pair_item = self.tree.insert("", "end", text=f"✓ Paired ({paired_count})",
                                         values=("", "", ""), tags=("paired",))
            for name in sorted(list(self.analysis_result['paired']))[:50]:
                self.tree.insert(pair_item, "end", text="", values=("Paired", name, "Matched"))
            if paired_count > 50:
                self.tree.insert(pair_item, "end", text="", values=("...", f"... {paired_count - 50} more files", ""))
        
        if orphan1_count > 0:
            orphan1_item = self.tree.insert("", "end", text=f"⚠ Orphan Images ({orphan1_count})",
                                            values=("", "", ""), tags=("orphan1",))
            for name in sorted(list(self.analysis_result['orphan1']))[:50]:
                self.tree.insert(orphan1_item, "end", text="", values=("Orphan Image", name, "No matching TXT"))
            if orphan1_count > 50:
                self.tree.insert(orphan1_item, "end", text="", values=("...", f"... {orphan1_count - 50} more files", ""))
        
        if orphan2_count > 0:
            orphan2_item = self.tree.insert("", "end", text=f"⚠ Orphan TXT ({orphan2_count})",
                                            values=("", "", ""), tags=("orphan2",))
            for name in sorted(list(self.analysis_result['orphan2']))[:50]:
                self.tree.insert(orphan2_item, "end", text="", values=("Orphan TXT", name, "No matching image"))
            if orphan2_count > 50:
                self.tree.insert(orphan2_item, "end", text="", values=("...", f"... {orphan2_count - 50} more files", ""))
        
        self._log(f"Analysis completed! Paired:{paired_count} Orphan Images:{orphan1_count} Orphan TXT:{orphan2_count}")
        self.status_var.set(f"Analysis completed - Paired:{paired_count} Orphan Images:{orphan1_count} Orphan TXT:{orphan2_count}")
    
    def _delete_orphans(self):
        if not self.analysis_result:
            messagebox.showwarning("Warning", "Please scan and analyze first!")
            return
        
        orphan1_count = self.analysis_result['orphan1_count']
        orphan2_count = self.analysis_result['orphan2_count']
        total = orphan1_count + orphan2_count
        
        if total == 0:
            messagebox.showinfo("Info", "No orphan files found!")
            return
        
        if messagebox.askyesno("Confirm Delete",
                               f"About to delete {orphan1_count} orphan images and {orphan2_count} orphan TXT files.\n\nContinue?",
                               icon='warning'):
            deleted_count, logs = self.cleaner.delete_orphans(
                self.analysis_result['orphan1'],
                self.analysis_result['orphan2']
            )
            
            for log in logs:
                self._log(log)
            
            self._log(f"Completed! {deleted_count} orphan files deleted")
            messagebox.showinfo("Completed", f"Successfully deleted {deleted_count} orphan files")
            
            self._load_files(1)
            self._load_files(2)
            self._scan_and_analyze()
    
    def _move_orphans(self):
        if not self.analysis_result:
            messagebox.showwarning("Warning", "Please scan and analyze first!")
            return
        
        total = self.analysis_result['orphan1_count'] + self.analysis_result['orphan2_count']
        
        if total == 0:
            messagebox.showinfo("Info", "No orphan files found!")
            return
        
        backup_folder = filedialog.askdirectory(title="Select Backup Folder")
        if not backup_folder:
            return
        
        moved_count, logs = self.cleaner.move_orphans(
            self.analysis_result['orphan1'],
            self.analysis_result['orphan2'],
            backup_folder
        )
        
        for log in logs:
            self._log(log)
        
        self._log(f"Completed! {moved_count} orphan files moved")
        messagebox.showinfo("Completed", f"Successfully moved {moved_count} orphan files to backup")
        
        self._load_files(1)
        self._load_files(2)
        self._scan_and_analyze()
    
    def _clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self._log("Log cleared")
    
    def _log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()
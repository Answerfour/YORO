"""孤立文件清理模块GUI"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict
from modules.orphan_cleaner.cleaner import OrphanCleaner


class OrphanCleanerGUI(ttk.Frame):
    """孤立文件清理GUI组件"""
    
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
        folder_frame = ttk.LabelFrame(parent, text="文件夹选择", padding="10")
        folder_frame.pack(fill=tk.X, pady=10)
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="文件夹1 (图片):").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.folder1_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder1_path_var, width=50).grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(folder_frame, text="浏览...", command=lambda: self._select_folder(self.folder1_path_var, 1)).grid(row=0, column=2, padx=5)
        ttk.Button(folder_frame, text="刷新", command=lambda: self._load_files(1)).grid(row=0, column=3, padx=5)
        
        ttk.Label(folder_frame, text="文件夹2 (TXT):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.folder2_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder2_path_var, width=50).grid(row=1, column=1, padx=5, sticky=(tk.W, tk.E), pady=(5, 0))
        ttk.Button(folder_frame, text="浏览...", command=lambda: self._select_folder(self.folder2_path_var, 2)).grid(row=1, column=2, padx=5, pady=(5, 0))
        ttk.Button(folder_frame, text="刷新", command=lambda: self._load_files(2)).grid(row=1, column=3, padx=5, pady=(5, 0))
    
    def _create_options(self, parent):
        options_frame = ttk.LabelFrame(parent, text="配对选项", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        self.pairing_mode_var = tk.StringVar(value="name")
        ttk.Radiobutton(options_frame, text="按文件名配对 (同名文件配对)",
                        variable=self.pairing_mode_var, value="name").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(options_frame, text="按序号配对 (第一个与第一个配对)",
                        variable=self.pairing_mode_var, value="sequence").pack(side=tk.LEFT, padx=10)
    
    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="扫描并分析", command=self._scan_and_analyze, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="删除孤立文件", command=self._delete_orphans, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="移动孤立文件", command=self._move_orphans, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="清空日志", command=self._clear_log, width=12).pack(side=tk.LEFT, padx=5)
    
    def _create_results(self, parent):
        result_frame = ttk.LabelFrame(parent, text="分析结果", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        columns = ("type", "filename", "status")
        self.tree = ttk.Treeview(result_frame, columns=columns, show="tree headings", height=12)
        self.tree.heading("#0", text="序号")
        self.tree.heading("type", text="类型")
        self.tree.heading("filename", text="文件名")
        self.tree.heading("status", text="状态")
        
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
        
        ttk.Label(log_frame, text="操作日志:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def _create_status_bar(self, parent):
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)
    
    def _select_folder(self, path_var, folder_num):
        folder = filedialog.askdirectory()
        if folder:
            path_var.set(folder)
            self._load_files(folder_num)
            self._log(f"已选择文件夹{folder_num}: {folder}")
    
    def _load_files(self, folder_num):
        if folder_num == 1:
            folder_path = self.folder1_path_var.get()
            if folder_path and os.path.exists(folder_path):
                from core.file_operator import FileOperator
                self.folder1_files = FileOperator.get_image_files(folder_path)
                self._log(f"文件夹1加载完成: 找到 {len(self.folder1_files)} 个图片文件")
                self.status_var.set(f"文件夹1: {len(self.folder1_files)} 个图片文件")
        else:
            folder_path = self.folder2_path_var.get()
            if folder_path and os.path.exists(folder_path):
                from core.file_operator import FileOperator
                self.folder2_files = FileOperator.get_txt_files(folder_path)
                self._log(f"文件夹2加载完成: 找到 {len(self.folder2_files)} 个TXT文件")
                self.status_var.set(f"文件夹2: {len(self.folder2_files)} 个TXT文件")
    
    def _scan_and_analyze(self):
        if not hasattr(self, 'folder1_files') or not hasattr(self, 'folder2_files'):
            messagebox.showwarning("警告", "请先选择两个文件夹并刷新！")
            return
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self._log("=" * 60)
        self._log("开始分析文件配对...")
        
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
            pair_item = self.tree.insert("", "end", text=f"✓ 配对文件 ({paired_count})",
                                         values=("", "", ""), tags=("paired",))
            for name in sorted(list(self.analysis_result['paired']))[:50]:
                self.tree.insert(pair_item, "end", text="", values=("配对", name, "已配对"))
            if paired_count > 50:
                self.tree.insert(pair_item, "end", text="", values=("...", f"... 还有 {paired_count - 50} 个文件", ""))
        
        if orphan1_count > 0:
            orphan1_item = self.tree.insert("", "end", text=f"⚠ 孤立图片 ({orphan1_count})",
                                            values=("", "", ""), tags=("orphan1",))
            for name in sorted(list(self.analysis_result['orphan1']))[:50]:
                self.tree.insert(orphan1_item, "end", text="", values=("孤立图片", name, "无配对TXT"))
            if orphan1_count > 50:
                self.tree.insert(orphan1_item, "end", text="", values=("...", f"... 还有 {orphan1_count - 50} 个文件", ""))
        
        if orphan2_count > 0:
            orphan2_item = self.tree.insert("", "end", text=f"⚠ 孤立TXT ({orphan2_count})",
                                            values=("", "", ""), tags=("orphan2",))
            for name in sorted(list(self.analysis_result['orphan2']))[:50]:
                self.tree.insert(orphan2_item, "end", text="", values=("孤立TXT", name, "无配对图片"))
            if orphan2_count > 50:
                self.tree.insert(orphan2_item, "end", text="", values=("...", f"... 还有 {orphan2_count - 50} 个文件", ""))
        
        self._log(f"分析完成！配对:{paired_count} 孤立图片:{orphan1_count} 孤立TXT:{orphan2_count}")
        self.status_var.set(f"分析完成 - 配对:{paired_count} 孤立图片:{orphan1_count} 孤立TXT:{orphan2_count}")
    
    def _delete_orphans(self):
        if not self.analysis_result:
            messagebox.showwarning("警告", "请先进行扫描分析！")
            return
        
        orphan1_count = self.analysis_result['orphan1_count']
        orphan2_count = self.analysis_result['orphan2_count']
        total = orphan1_count + orphan2_count
        
        if total == 0:
            messagebox.showinfo("提示", "没有发现孤立文件！")
            return
        
        if messagebox.askyesno("确认删除",
                               f"即将删除 {orphan1_count} 个孤立图片和 {orphan2_count} 个孤立TXT文件。\n\n是否继续？",
                               icon='warning'):
            deleted_count, logs = self.cleaner.delete_orphans(
                self.analysis_result['orphan1'],
                self.analysis_result['orphan2']
            )
            
            for log in logs:
                self._log(log)
            
            self._log(f"完成！共删除 {deleted_count} 个孤立文件")
            messagebox.showinfo("完成", f"成功删除 {deleted_count} 个孤立文件")
            
            self._load_files(1)
            self._load_files(2)
            self._scan_and_analyze()
    
    def _move_orphans(self):
        if not self.analysis_result:
            messagebox.showwarning("警告", "请先进行扫描分析！")
            return
        
        total = self.analysis_result['orphan1_count'] + self.analysis_result['orphan2_count']
        
        if total == 0:
            messagebox.showinfo("提示", "没有发现孤立文件！")
            return
        
        backup_folder = filedialog.askdirectory(title="选择备份文件夹")
        if not backup_folder:
            return
        
        moved_count, logs = self.cleaner.move_orphans(
            self.analysis_result['orphan1'],
            self.analysis_result['orphan2'],
            backup_folder
        )
        
        for log in logs:
            self._log(log)
        
        self._log(f"完成！共移动 {moved_count} 个孤立文件")
        messagebox.showinfo("完成", f"成功移动 {moved_count} 个孤立文件到:\n{logs[0].replace('备份目录: ', '')}")
        
        self._load_files(1)
        self._load_files(2)
        self._scan_and_analyze()
    
    def _clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self._log("日志已清空")
    
    def _log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

"""无标注文件处理器GUI组件"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from modules.unlabeled_processor.processor import UnlabeledProcessor
from datetime import datetime
import threading


class UnlabeledProcessorGUI(ttk.Frame):
    """无标注文件处理器GUI组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.processor = None
        self.processing = False
        
        self._create_widgets()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_folder_selection(main_frame)
        self._create_process_options(main_frame)
        self._create_buttons(main_frame)
        self._create_progress(main_frame)
        self._create_results(main_frame)
        self._create_log(main_frame)
    
    def _create_folder_selection(self, parent):
        folder_frame = ttk.LabelFrame(parent, text="1. 选择主文件夹", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        dir_row = ttk.Frame(folder_frame)
        dir_row.pack(fill=tk.X)
        
        ttk.Label(dir_row, text="主文件夹路径:").pack(side=tk.LEFT, padx=5)
        self.folder_path_var = tk.StringVar()
        ttk.Entry(dir_row, textvariable=self.folder_path_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_row, text="浏览", command=self._select_folder).pack(side=tk.RIGHT, padx=5)
        
        self.folder_status_label = ttk.Label(folder_frame, text="", foreground="blue")
        self.folder_status_label.pack(anchor=tk.W, pady=5)
    
    def _create_process_options(self, parent):
        options_frame = ttk.LabelFrame(parent, text="2. 处理选项", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.process_mode = tk.StringVar(value="move")
        
        ttk.Radiobutton(options_frame, text="移动模式 - 将文件移到 unlabeled_files 目录",
                        variable=self.process_mode, value="move").pack(anchor=tk.W, padx=5)
        ttk.Radiobutton(options_frame, text="删除模式 - 直接删除文件（需要确认）",
                        variable=self.process_mode, value="delete").pack(anchor=tk.W, padx=5)
        
        self.auto_save_report = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="自动保存处理报告",
                        variable=self.auto_save_report).pack(anchor=tk.W, padx=5)
    
    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶ 开始处理", command=self._start_process, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(button_frame, text="取消", command=self._cancel_process, width=8, state="disabled")
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(button_frame, text="刷新扫描", command=self._scan_files, width=10)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_progress(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="处理进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(pady=5)
    
    def _create_results(self, parent):
        result_frame = ttk.LabelFrame(parent, text="处理结果", padding="10")
        result_frame.pack(fill=tk.X, pady=5)
        
        result_grid = ttk.Frame(result_frame)
        result_grid.pack(fill=tk.X)
        
        ttk.Label(result_grid, text="空标签文件:").grid(row=0, column=0, padx=10)
        self.empty_count_label = ttk.Label(result_grid, text="0", foreground="orange", font=('TkDefaultFont', 10, 'bold'))
        self.empty_count_label.grid(row=0, column=1, padx=10)
        
        ttk.Label(result_grid, text="成功处理:").grid(row=0, column=2, padx=10)
        self.success_count_label = ttk.Label(result_grid, text="0", foreground="green", font=('TkDefaultFont', 10, 'bold'))
        self.success_count_label.grid(row=0, column=3, padx=10)
        
        ttk.Label(result_grid, text="处理失败:").grid(row=0, column=4, padx=10)
        self.failed_count_label = ttk.Label(result_grid, text="0", foreground="red", font=('TkDefaultFont', 10, 'bold'))
        self.failed_count_label.grid(row=0, column=5, padx=10)
    
    def _create_log(self, parent):
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self._log("欢迎使用无标注文件处理器")
        self._log("请选择主文件夹，系统将自动识别 images 和 labels 子目录")
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="选择主文件夹（需包含 images 和 labels 子目录）")
        if folder:
            self.folder_path_var.set(folder)
            self._scan_files()
    
    def _scan_files(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择主文件夹")
            return
        
        processor = UnlabeledProcessor(folder)
        valid, msg = processor.validate_folders()
        
        if not valid:
            self.folder_status_label.config(text=f"❌ {msg}", foreground="red")
            self.empty_count_label.config(text="0")
            self._log(f"错误: {msg}")
            return
        
        self.folder_status_label.config(text=f"✅ 文件夹结构有效", foreground="green")
        
        empty_labels = processor.find_empty_labels()
        self.empty_count_label.config(text=str(len(empty_labels)))
        
        self._log(f"扫描完成: 找到 {len(empty_labels)} 个空标签文件")
        
        for label in empty_labels[:10]:
            self._log(f"  - {label}")
        
        if len(empty_labels) > 10:
            self._log(f"  ... 还有 {len(empty_labels) - 10} 个文件")
    
    def _start_process(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择主文件夹")
            return
        
        if self.process_mode.get() == "delete":
            if not messagebox.askyesno("确认删除",
                                       "⚠️ 警告：此操作将永久删除空标签文件及其对应图片！\n\n"
                                       "此操作不可逆，确定要继续吗？",
                                       icon='warning'):
                return
        
        self.processing = True
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.refresh_btn.config(state="disabled")
        
        self.log_text.delete(1.0, tk.END)
        self._log("开始处理...")
        
        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()
    
    def _process_worker(self):
        folder = self.folder_path_var.get()
        self.processor = UnlabeledProcessor(folder)
        
        valid, msg = self.processor.validate_folders()
        if not valid:
            self.after(0, lambda: self._log(f"错误: {msg}"))
            self._finish_process(0, 0)
            return
        
        self.processor.find_empty_labels()
        total = len(self.processor.empty_labels)
        self.after(0, lambda: self._log(f"共发现 {total} 个空标签文件"))
        
        if self.process_mode.get() == "move":
            processed, failed, logs = self.processor.process_move()
        else:
            processed, failed, logs = self.processor.process_delete()
        
        for log in logs:
            self.after(0, lambda l=log: self._log(l))
        
        self._finish_process(processed, failed)
    
    def _finish_process(self, processed, failed):
        self.success_count_label.config(text=str(processed))
        self.failed_count_label.config(text=str(failed))
        
        self._log(f"\n处理完成！")
        self._log(f"成功: {processed} | 失败: {failed}")
        
        if self.auto_save_report.get() and self.processor:
            report = self.processor.generate_report(processed, failed)
            success, path = self.processor.save_report(report)
            if success:
                self._log(f"报告已保存: {path}")
            else:
                self._log(f"报告保存失败: {path}")
        
        self.processing = False
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.refresh_btn.config(state="normal")
        
        self.progress_var.set(0)
        self.progress_label.config(text="")
    
    def _cancel_process(self):
        if self.processor:
            self.processor.cancel()
            self._log("正在取消操作...")
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

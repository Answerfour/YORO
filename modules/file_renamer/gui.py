"""文件重命名模块GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from typing import List, Tuple
from modules.file_renamer.renamer import FileRenamer
from config.schema import RenamerConfig
from ui.components import LogFrame


class FileRenamerGUI(ttk.Frame):
    """文件重命名GUI组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.renamer = None
        self.preview_data: List[Tuple[str, str]] = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        folder_frame = ttk.LabelFrame(self, text="1. 选择文件夹", padding=5)
        folder_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(folder_frame, text="路径：").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.folder_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.folder_path_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(folder_frame, text="浏览...", command=self._select_folder).grid(row=0, column=2, padx=5)
        
        param_frame = ttk.LabelFrame(self, text="2. 设置重命名参数", padding=5)
        param_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(param_frame, text="文件类型：").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.file_type_var = tk.StringVar(value="txt")
        ttk.Radiobutton(param_frame, text="TXT 文件 (.txt)", variable=self.file_type_var, value="txt").grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(param_frame, text="图片文件 (jpg/png/gif/bmp/tiff/webp)", variable=self.file_type_var, value="image").grid(row=0, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(param_frame, text="起始编号：").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.start_number_var = tk.IntVar(value=1)
        ttk.Spinbox(param_frame, from_=1, to=999999, textvariable=self.start_number_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(param_frame, text="数字宽度：").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.digit_width_var = tk.IntVar(value=6)
        ttk.Spinbox(param_frame, from_=1, to=10, textvariable=self.digit_width_var, width=10).grid(row=2, column=1, sticky=tk.W, padx=5)
        ttk.Label(param_frame, text="(例：宽度6 → 000001)").grid(row=2, column=2, sticky=tk.W, padx=5)
        
        btn_frame = ttk.Frame(param_frame)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=10)
        ttk.Button(btn_frame, text="预览重命名效果", command=self._preview_rename).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="执行重命名", command=self._execute_rename).pack(side=tk.LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(self, text="3. 预览结果 (原文件名 → 新文件名)", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Consolas", 9))
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        log_frame = ttk.LabelFrame(self, text="操作日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        self.log_frame = LogFrame(log_frame, height=8)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_frame.log("欢迎使用批量重命名工具。请选择文件夹并设置参数后点击「预览」。")
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="选择包含需要重命名文件的文件夹")
        if folder:
            self.folder_path_var.set(folder)
            self.log_frame.log(f"已选择文件夹：{folder}")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
    
    def _preview_rename(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择文件夹！")
            return
        
        config = RenamerConfig(
            file_type=self.file_type_var.get(),
            start_number=self.start_number_var.get(),
            digit_width=self.digit_width_var.get()
        )
        
        self.renamer = FileRenamer(folder, config)
        files = self.renamer.load_files()
        
        if not files:
            self.log_frame.log(f"警告：文件夹中没有找到 {'TXT' if config.file_type == 'txt' else '图片'} 文件。")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
            return
        
        self.preview_data = self.renamer.generate_preview()
        
        self.listbox.delete(0, tk.END)
        for old, new in self.preview_data:
            self.listbox.insert(tk.END, f"{old}  →  {new}")
        
        self.log_frame.log(f"预览生成完成：共 {len(files)} 个文件，起始编号 {config.start_number}，宽度 {config.digit_width}")
    
    def _execute_rename(self):
        if not self.preview_data:
            messagebox.showwarning("警告", "请先点击「预览重命名效果」生成待处理列表！")
            return
        
        if not self.renamer:
            messagebox.showerror("错误", "系统错误，请重新预览")
            return
        
        if not messagebox.askyesno("确认重命名",
                                   f"即将对 {len(self.preview_data)} 个文件进行重命名。\n\n此操作不可撤销，是否继续？"):
            self.log_frame.log("操作已取消。")
            return
        
        success, failed = self.renamer.execute_rename()
        
        self.log_frame.log("\n========== 重命名执行结果 ==========")
        self.log_frame.log(f"成功：{len(success)} 个，失败：{len(failed)} 个。")
        
        if not failed:
            self.log_frame.log("所有文件重命名成功！")
            self.preview_data = []
            self.listbox.delete(0, tk.END)
        else:
            self.log_frame.log("部分文件重命名失败，请查看日志。")
            self.preview_data = []
            self.listbox.delete(0, tk.END)

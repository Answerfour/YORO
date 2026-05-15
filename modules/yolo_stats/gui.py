"""YOLO统计模块GUI"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List
from config.schema import ClassMappingConfig
from modules.yolo_stats.counter import YOLOCounter
from ui.components import LogFrame
from utils.persistence import PersistenceManager


class YOLOStatsGUI(ttk.Frame):
    """YOLO统计GUI组件"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.persistence = PersistenceManager.get_instance()
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config_data", "class_mapping.json")
        
        self.class_mapping = self._load_mapping()
        self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
        
        self._create_widgets()
        self._refresh_mapping_table()
    
    def _load_mapping(self) -> Dict[int, str]:
        """加载类别映射"""
        default = {
            0: "开水器",
            1: "纸杯",
            2: "厕所",
            3: "灭火器",
            4: "马桶",
            5: "水槽"
        }
        
        data = self.persistence.load(self.config_file)
        if data:
            return {int(k): v for k, v in data.items()}
        return default
    
    def _save_mapping(self):
        """保存类别映射"""
        self.persistence.save(self.class_mapping, self.config_file, auto_named=False)
    
    def _create_widgets(self):
        top_frame = ttk.LabelFrame(self, text="1. 选择统计目录", padding=5)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(top_frame, text="目录路径：").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.folder_path_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.folder_path_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(top_frame, text="浏览...", command=self._select_folder).grid(row=0, column=2, padx=5)
        
        mapping_frame = ttk.LabelFrame(self, text="2. 类别映射管理 (可增删改)", padding=5)
        mapping_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        table_frame = ttk.Frame(mapping_frame)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("ID", "类别名称")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        self.tree.heading("ID", text="类别 ID")
        self.tree.heading("类别名称", text="类别名称")
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("类别名称", width=150)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        edit_frame = ttk.Frame(mapping_frame)
        edit_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        
        ttk.Label(edit_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_id = ttk.Entry(edit_frame, width=10)
        self.entry_id.grid(row=0, column=1, pady=2)
        
        ttk.Label(edit_frame, text="名称:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_name = ttk.Entry(edit_frame, width=15)
        self.entry_name.grid(row=1, column=1, pady=2)
        
        ttk.Button(edit_frame, text="添加/修改", command=self._add_or_update_class).grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(edit_frame, text="删除选中", command=self._delete_selected_class).grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(edit_frame, text="重置默认", command=self._reset_default_mapping).grid(row=4, column=0, columnspan=2, pady=5)
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Button(bottom_frame, text="开始统计", command=self._start_count).pack(pady=5)
        
        result_label = ttk.Label(bottom_frame, text="统计结果：", anchor=tk.W)
        result_label.pack(fill=tk.X)
        
        result_frame = ttk.Frame(bottom_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_tree = ttk.Treeview(result_frame, columns=("ID", "名称", "数量"), show="headings", height=10)
        self.result_tree.heading("ID", text="类别 ID")
        self.result_tree.heading("名称", text="类别名称")
        self.result_tree.heading("数量", text="目标数量")
        self.result_tree.column("ID", width=80, anchor=tk.CENTER)
        self.result_tree.column("名称", width=150)
        self.result_tree.column("数量", width=100, anchor=tk.CENTER)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        result_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=result_scroll.set)
        
        log_label = ttk.Label(bottom_frame, text="日志信息：", anchor=tk.W)
        log_label.pack(fill=tk.X, pady=(5, 0))
        self.log_frame = LogFrame(bottom_frame, height=6)
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="选择包含 YOLO 标注 txt 文件的文件夹")
        if folder:
            self.folder_path_var.set(folder)
            self.log_frame.log(f"已选择目录: {folder}")
    
    def _refresh_mapping_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for cls_id, name in sorted(self.class_mapping.items()):
            self.tree.insert("", tk.END, values=(cls_id, name))
    
    def _add_or_update_class(self):
        try:
            cls_id = int(self.entry_id.get())
            name = self.entry_name.get().strip()
            if not name:
                messagebox.showwarning("警告", "类别名称不能为空")
                return
            self.class_mapping[cls_id] = name
            self._refresh_mapping_table()
            self._save_mapping()
            self.log_frame.log(f"已添加/修改类别: ID={cls_id}, 名称={name}")
            self.entry_id.delete(0, tk.END)
            self.entry_name.delete(0, tk.END)
            self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
        except ValueError:
            messagebox.showerror("错误", "类别 ID 必须是整数")
    
    def _delete_selected_class(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选中要删除的行")
            return
        item = self.tree.item(selected[0])
        cls_id = item['values'][0]
        if messagebox.askyesno("确认删除", f"确定要删除类别 {cls_id} ({self.class_mapping[cls_id]}) 吗？"):
            del self.class_mapping[cls_id]
            self._refresh_mapping_table()
            self._save_mapping()
            self.log_frame.log(f"已删除类别 ID={cls_id}")
            self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
    
    def _reset_default_mapping(self):
        self.class_mapping = {
            0: "开水器",
            1: "纸杯",
            2: "厕所",
            3: "灭火器",
            4: "马桶",
            5: "水槽"
        }
        self._refresh_mapping_table()
        self._save_mapping()
        self.log_frame.log("已重置类别映射为默认值")
        self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
    
    def _start_count(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("警告", "请先选择要统计的目录")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("错误", "目录不存在")
            return
        
        counts, warnings = self.counter.count_in_folder(folder)
        
        for row in self.result_tree.get_children():
            self.result_tree.delete(row)
        
        total = 0
        for cls_id, name, num in self.counter.get_results_list():
            self.result_tree.insert("", tk.END, values=(cls_id, name, num))
            total += num
        
        self.result_tree.insert("", tk.END, values=("", "总计", total), tags=("total",))
        self.result_tree.tag_configure("total", background="#f0f0f0", font=("TkDefaultFont", 10, "bold"))
        
        self.log_frame.log("\n========== 统计完成 ==========")
        self.log_frame.log(f"目录: {folder}")
        self.log_frame.log(f"涉及类别: {len(self.class_mapping)} 个")
        if warnings:
            self.log_frame.log("警告信息：")
            for w in warnings:
                self.log_frame.log(f"  {w}")
        else:
            self.log_frame.log("无警告")
        self.log_frame.log(f"总计目标数量: {total}")

"""YOLO Statistics Module GUI"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Dict, List
from config.schema import ClassMappingConfig
from modules.yolo_stats.counter import YOLOCounter
from ui.components import LogFrame
from utils.persistence import PersistenceManager


class YOLOStatsGUI(ttk.Frame):
    """YOLO Statistics GUI Component"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.persistence = PersistenceManager.get_instance()
        self.config_file = os.path.join(os.path.dirname(__file__), "..", "..", "config_data", "class_mapping.json")
        
        self.class_mapping = self._load_mapping()
        self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
        
        self._create_widgets()
        self._refresh_mapping_table()
    
    def _load_mapping(self) -> Dict[int, str]:
        """Load class mapping"""
        default = {
            0: "water_heater",
            1: "paper_cup",
            2: "toilet",
            3: "fire_extinguisher",
            4: "commode",
            5: "sink"
        }
        
        data = self.persistence.load(self.config_file)
        if data:
            return {int(k): v for k, v in data.items()}
        return default
    
    def _save_mapping(self):
        """Save class mapping"""
        self.persistence.save(self.class_mapping, self.config_file, auto_named=False)
    
    def _create_widgets(self):
        top_frame = ttk.LabelFrame(self, text="1. Select Directory", padding=5)
        top_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(top_frame, text="Directory Path:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.folder_path_var = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.folder_path_var, width=60).grid(row=0, column=1, padx=5)
        ttk.Button(top_frame, text="Browse...", command=self._select_folder).grid(row=0, column=2, padx=5)
        
        mapping_frame = ttk.LabelFrame(self, text="2. Class Mapping (Add/Edit/Delete)", padding=5)
        mapping_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        table_frame = ttk.Frame(mapping_frame)
        table_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("ID", "ClassName")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        self.tree.heading("ID", text="Class ID")
        self.tree.heading("ClassName", text="Class Name")
        self.tree.column("ID", width=80, anchor=tk.CENTER)
        self.tree.column("ClassName", width=150)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        edit_frame = ttk.Frame(mapping_frame)
        edit_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=5)
        
        ttk.Label(edit_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_id = ttk.Entry(edit_frame, width=10)
        self.entry_id.grid(row=0, column=1, pady=2)
        
        ttk.Label(edit_frame, text="Name:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_name = ttk.Entry(edit_frame, width=15)
        self.entry_name.grid(row=1, column=1, pady=2)
        
        ttk.Button(edit_frame, text="Add/Update", command=self._add_or_update_class).grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(edit_frame, text="Delete Selected", command=self._delete_selected_class).grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(edit_frame, text="Reset Default", command=self._reset_default_mapping).grid(row=4, column=0, columnspan=2, pady=5)
        
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        ttk.Button(bottom_frame, text="Start Count", command=self._start_count).pack(pady=5)
        
        result_label = ttk.Label(bottom_frame, text="Statistics Results:", anchor=tk.W)
        result_label.pack(fill=tk.X)
        
        result_frame = ttk.Frame(bottom_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_tree = ttk.Treeview(result_frame, columns=("ID", "Name", "Count"), show="headings", height=10)
        self.result_tree.heading("ID", text="Class ID")
        self.result_tree.heading("Name", text="Class Name")
        self.result_tree.heading("Count", text="Object Count")
        self.result_tree.column("ID", width=80, anchor=tk.CENTER)
        self.result_tree.column("Name", width=150)
        self.result_tree.column("Count", width=100, anchor=tk.CENTER)
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        result_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        result_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.result_tree.configure(yscrollcommand=result_scroll.set)
        
        log_label = ttk.Label(bottom_frame, text="Log Info:", anchor=tk.W)
        log_label.pack(fill=tk.X, pady=(5, 0))
        self.log_frame = LogFrame(bottom_frame, height=6)
        self.log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with YOLO annotation txt files")
        if folder:
            self.folder_path_var.set(folder)
            self.log_frame.log(f"Selected directory: {folder}")
    
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
                messagebox.showwarning("Warning", "Class name cannot be empty")
                return
            self.class_mapping[cls_id] = name
            self._refresh_mapping_table()
            self._save_mapping()
            self.log_frame.log(f"Added/Updated class: ID={cls_id}, Name={name}")
            self.entry_id.delete(0, tk.END)
            self.entry_name.delete(0, tk.END)
            self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
        except ValueError:
            messagebox.showerror("Error", "Class ID must be an integer")
    
    def _delete_selected_class(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a row to delete")
            return
        item = self.tree.item(selected[0])
        cls_id = item['values'][0]
        if messagebox.askyesno("Confirm Delete", f"Are you sure to delete class {cls_id} ({self.class_mapping[cls_id]})?"):
            del self.class_mapping[cls_id]
            self._refresh_mapping_table()
            self._save_mapping()
            self.log_frame.log(f"Deleted class ID={cls_id}")
            self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
    
    def _reset_default_mapping(self):
        self.class_mapping = {
            0: "water_heater",
            1: "paper_cup",
            2: "toilet",
            3: "fire_extinguisher",
            4: "commode",
            5: "sink"
        }
        self._refresh_mapping_table()
        self._save_mapping()
        self.log_frame.log("Reset class mapping to default values")
        self.counter = YOLOCounter(ClassMappingConfig.from_dict(self.class_mapping))
    
    def _start_count(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("Warning", "Please select a directory to count")
            return
        if not os.path.isdir(folder):
            messagebox.showerror("Error", "Directory does not exist")
            return
        
        counts, warnings = self.counter.count_in_folder(folder)
        
        for row in self.result_tree.get_children():
            self.result_tree.delete(row)
        
        total = 0
        for cls_id, name, num in self.counter.get_results_list():
            self.result_tree.insert("", tk.END, values=(cls_id, name, num))
            total += num
        
        self.result_tree.insert("", tk.END, values=("", "Total", total), tags=("total",))
        self.result_tree.tag_configure("total", background="#f0f0f0", font=("TkDefaultFont", 10, "bold"))
        
        self.log_frame.log("\n========== Count Completed ==========")
        self.log_frame.log(f"Directory: {folder}")
        self.log_frame.log(f"Classes involved: {len(self.class_mapping)}")
        if warnings:
            self.log_frame.log("Warnings:")
            for w in warnings:
                self.log_frame.log(f"  {w}")
        else:
            self.log_frame.log("No warnings")
        self.log_frame.log(f"Total objects counted: {total}")
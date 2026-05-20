"""Validation Set Extractor Module GUI"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import List, Dict
from modules.valid_extractor.extractor import ValidExtractor, ClassBasedExtractor
from config.schema import ValidExtractorConfig
from utils.persistence import PersistenceManager


class ValidExtractorGUI(ttk.Frame):
    """Validation Set Extractor GUI Component"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.extractor = None
        self.class_extractor = None
        self.match_report: Dict = {}
        self.selected_files: List[str] = []
        self.all_paired_files: List[str] = []
        self.class_selections: Dict[int, float] = {}
        
        self.config = ValidExtractorConfig()
        self.persistence = PersistenceManager.get_instance()
        
        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_folder_selection(main_frame)
        self._create_operation_options(main_frame)
        self._create_extraction_mode(main_frame)
        self._create_class_selection_panel(main_frame)
        self._create_file_list(main_frame)
        self._create_preview_panel(main_frame)
        self._create_buttons(main_frame)
        self._create_log(main_frame)
        self._create_status_bar(main_frame)

    def _create_folder_selection(self, parent):
        folder_frame = ttk.LabelFrame(parent, text="Source Directories", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        folder_frame.columnconfigure(1, weight=1)
        
        ttk.Label(folder_frame, text="Images Directory:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.images_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.images_path_var, width=50).grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        ttk.Button(folder_frame, text="Browse...", command=self._select_images_folder).grid(row=0, column=2, padx=5)
        
        ttk.Label(folder_frame, text="Labels Directory:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.labels_path_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.labels_path_var, width=50).grid(row=1, column=1, padx=5, sticky=(tk.W, tk.E), pady=(5, 0))
        ttk.Button(folder_frame, text="Browse...", command=self._select_labels_folder).grid(row=1, column=2, padx=5, pady=(5, 0))

    def _create_operation_options(self, parent):
        options_frame = ttk.LabelFrame(parent, text="Operation Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.operation_var = tk.StringVar(value="copy")
        ttk.Radiobutton(options_frame, text="Copy files",
                        variable=self.operation_var, value="copy").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(options_frame, text="Move files",
                        variable=self.operation_var, value="move").pack(side=tk.LEFT, padx=10)
        
        ttk.Label(options_frame, text="Output Directory:").pack(side=tk.LEFT, padx=10)
        self.output_dir_var = tk.StringVar(value="")
        ttk.Entry(options_frame, textvariable=self.output_dir_var, width=30).pack(side=tk.LEFT, padx=5)
        ttk.Button(options_frame, text="Browse...", command=self._select_output_folder).pack(side=tk.LEFT, padx=5)

    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="Select Output Directory")
        if folder:
            self.output_dir_var.set(folder)
            self._log(f"Selected output directory: {folder}")

    def _create_extraction_mode(self, parent):
        mode_frame = ttk.LabelFrame(parent, text="Extraction Mode", padding="10")
        mode_frame.pack(fill=tk.X, pady=5)
        mode_frame.columnconfigure(2, weight=1)
        
        self.mode_var = tk.StringVar(value="ratio")
        
        ttk.Radiobutton(mode_frame, text="By Ratio:",
                        variable=self.mode_var, value="ratio", command=self._update_mode_widgets).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.ratio_var = tk.DoubleVar(value=0.2)
        self.ratio_spin = ttk.Spinbox(mode_frame, from_=0.01, to=1.0, increment=0.01, 
                                       textvariable=self.ratio_var, width=8)
        self.ratio_spin.grid(row=0, column=1, padx=5)
        ttk.Label(mode_frame, text="(e.g., 0.2 = 20%)").grid(row=0, column=2, sticky=tk.W, padx=2)
        
        ttk.Radiobutton(mode_frame, text="By Count:",
                        variable=self.mode_var, value="count", command=self._update_mode_widgets).grid(row=1, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        self.count_var = tk.IntVar(value=50)
        self.count_spin = ttk.Spinbox(mode_frame, from_=1, to=99999, 
                                       textvariable=self.count_var, width=8)
        self.count_spin.grid(row=1, column=1, padx=5, pady=(5, 0))
        
        ttk.Radiobutton(mode_frame, text="Manual Selection:",
                        variable=self.mode_var, value="manual", command=self._update_mode_widgets).grid(row=2, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        
        ttk.Radiobutton(mode_frame, text="By Class:",
                        variable=self.mode_var, value="class", command=self._update_mode_widgets).grid(row=3, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        
        self.seed_var = tk.IntVar(value=42)
        ttk.Label(mode_frame, text="Random Seed:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=(5, 0))
        ttk.Entry(mode_frame, textvariable=self.seed_var, width=10).grid(row=4, column=1, padx=5, pady=(5, 0))

    def _update_mode_widgets(self):
        mode = self.mode_var.get()
        self.ratio_spin.config(state='normal' if mode == 'ratio' else 'disabled')
        self.count_spin.config(state='normal' if mode == 'count' else 'disabled')
        
        if hasattr(self, 'class_selection_frame'):
            self.class_selection_frame.pack(fill=tk.BOTH if mode == 'class' else tk.NONE)

    def _create_class_selection_panel(self, parent):
        self.class_selection_frame = ttk.LabelFrame(parent, text="Class Selection (for Class-based Extraction)", padding="10")
        
        class_panel = ttk.Frame(self.class_selection_frame)
        class_panel.pack(fill=tk.BOTH, expand=True)
        
        self.class_tree = ttk.Treeview(class_panel, columns=("ID", "Name", "Count", "Ratio", "Select"), show="headings", height=8)
        self.class_tree.heading("ID", text="Class ID")
        self.class_tree.heading("Name", text="Class Name")
        self.class_tree.heading("Count", text="Image Count")
        self.class_tree.heading("Ratio", text="Extract Ratio")
        self.class_tree.heading("Select", text="Select")
        
        self.class_tree.column("ID", width=60, anchor=tk.CENTER)
        self.class_tree.column("Name", width=120)
        self.class_tree.column("Count", width=80, anchor=tk.CENTER)
        self.class_tree.column("Ratio", width=100, anchor=tk.CENTER)
        self.class_tree.column("Select", width=80, anchor=tk.CENTER)
        
        scrollbar = ttk.Scrollbar(class_panel, orient="vertical", command=self.class_tree.yview)
        self.class_tree.configure(yscrollcommand=scrollbar.set)
        
        self.class_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        class_button_frame = ttk.Frame(self.class_selection_frame)
        class_button_frame.pack(fill=tk.X, pady=5)
        ttk.Button(class_button_frame, text="Select All", command=self._select_all_classes).pack(side=tk.LEFT, padx=5)
        ttk.Button(class_button_frame, text="Deselect All", command=self._deselect_all_classes).pack(side=tk.LEFT, padx=5)
        ttk.Button(class_button_frame, text="Set Same Ratio", command=self._set_same_ratio).pack(side=tk.LEFT, padx=5)
        ttk.Button(class_button_frame, text="Analyze Labels", command=self._analyze_labels).pack(side=tk.RIGHT, padx=5)
        
        self.class_ratio_entries: Dict[int, ttk.Spinbox] = {}
        self.class_checkboxes: Dict[int, tk.BooleanVar] = {}
        
        self._update_mode_widgets()

    def _populate_class_tree(self, stats: Dict):
        for item in self.class_tree.get_children():
            self.class_tree.delete(item)
        
        self.class_ratio_entries.clear()
        self.class_checkboxes.clear()
        
        for cls_id, cls_stats in sorted(stats.get('class_stats', {}).items()):
            self.class_checkboxes[cls_id] = tk.BooleanVar(value=False)
            cb = ttk.Checkbutton(None, variable=self.class_checkboxes[cls_id])
            
            self.class_ratio_entries[cls_id] = ttk.Spinbox(None, from_=0.0, to=1.0, increment=0.05, width=8)
            self.class_ratio_entries[cls_id].set(0.2)
            
            self.class_tree.insert("", "end", values=(
                cls_id,
                cls_stats['name'],
                cls_stats['count'],
                "",
                ""
            ))
            
        for i, item in enumerate(self.class_tree.get_children()):
            cls_id = int(self.class_tree.item(item, "values")[0])
            self.class_tree.set(item, "Ratio", "")
            
        self.class_tree.bind("<Map>", self._update_class_widgets)

    def _update_class_widgets(self, event=None):
        for item in self.class_tree.get_children():
            cls_id = int(self.class_tree.item(item, "values")[0])
            if cls_id in self.class_ratio_entries:
                self.class_ratio_entries[cls_id].destroy()
                
        self.class_ratio_entries.clear()
        
        for item in self.class_tree.get_children():
            cls_id = int(self.class_tree.item(item, "values")[0])
            if cls_id in self.class_checkboxes:
                cb = ttk.Checkbutton(self.class_tree, variable=self.class_checkboxes[cls_id])
                self.class_tree.set(item, "Select", "")
                self.class_tree.item(item, tags=(str(cls_id),))
                
                ratio_spin = ttk.Spinbox(self.class_tree, from_=0.0, to=1.0, increment=0.05, width=6)
                ratio_spin.set(0.2)
                self.class_ratio_entries[cls_id] = ratio_spin
                
                def update_ratio(event, cid=cls_id):
                    self.class_selections[cid] = float(self.class_ratio_entries[cid].get())
                
                ratio_spin.bind("<KeyRelease>", update_ratio)

    def _select_all_classes(self):
        for cls_id, var in self.class_checkboxes.items():
            var.set(True)
            if cls_id in self.class_ratio_entries:
                self.class_selections[cls_id] = float(self.class_ratio_entries[cls_id].get())

    def _deselect_all_classes(self):
        for cls_id, var in self.class_checkboxes.items():
            var.set(False)
            self.class_selections.pop(cls_id, None)

    def _set_same_ratio(self):
        try:
            ratio = float(self.ratio_var.get())
            for cls_id, entry in self.class_ratio_entries.items():
                entry.set(ratio)
                if self.class_checkboxes[cls_id].get():
                    self.class_selections[cls_id] = ratio
            self._log(f"Set all class ratios to {ratio:.2f}")
        except ValueError:
            messagebox.showwarning("Warning", "Please enter a valid ratio")

    def _analyze_labels(self):
        labels_dir = self.labels_path_var.get()
        
        if not labels_dir:
            messagebox.showwarning("Warning", "Please select labels directory first")
            return
        
        self._log("=" * 60)
        self._log("Analyzing labels for class distribution...")
        
        self.class_extractor = ClassBasedExtractor(labels_dir, project_root=os.getcwd())
        config_path = os.path.join(os.getcwd(), "config_data", "class_mapping.json")
        success = self.class_extractor.load_class_mapping(config_path)
        
        if success:
            self._log(f"Loaded class mapping from {config_path}")
        else:
            self._log("Using default class mapping")
        
        stats = self.class_extractor.analyze_labels()
        
        self._log(f"Total images analyzed: {stats['total_images']}")
        self._log(f"Total objects found: {stats['total_objects']}")
        self._log(f"Number of classes: {stats['class_count']}")
        
        self._populate_class_tree(stats)
        
        self.status_var.set(f"Analyzed: {stats['total_images']} images, {stats['class_count']} classes")

    def _create_file_list(self, parent):
        file_frame = ttk.LabelFrame(parent, text="Paired Files", padding="10")
        file_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)
        
        columns = ("name", "status")
        self.file_tree = ttk.Treeview(file_frame, columns=columns, show="tree headings", height=10)
        self.file_tree.heading("#0", text="Index")
        self.file_tree.heading("name", text="Filename")
        self.file_tree.heading("status", text="Status")
        
        self.file_tree.column("#0", width=60)
        self.file_tree.column("name", width=400)
        self.file_tree.column("status", width=100)
        
        scrollbar = ttk.Scrollbar(file_frame, orient="vertical", command=self.file_tree.yview)
        self.file_tree.configure(yscrollcommand=scrollbar.set)
        
        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.file_tree.tag_configure("selected", background="#a8d8ea")
        self.file_tree.bind("<Double-1>", self._toggle_file_selection)
        
        select_frame = ttk.Frame(file_frame)
        select_frame.grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Button(select_frame, text="Select All", command=self._select_all_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Deselect All", command=self._deselect_all_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(select_frame, text="Random Select", command=self._random_select_files).pack(side=tk.LEFT, padx=5)

    def _create_preview_panel(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="Extraction Preview", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)
        
        self.preview_text = scrolledtext.ScrolledText(preview_frame, height=6, wrap=tk.WORD, font=("Consolas", 9))
        self.preview_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        preview_info_frame = ttk.Frame(preview_frame)
        preview_info_frame.grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(preview_info_frame, text="Selected:").pack(side=tk.LEFT, padx=5)
        self.selected_count_var = tk.StringVar(value="0")
        ttk.Label(preview_info_frame, textvariable=self.selected_count_var, foreground="blue").pack(side=tk.LEFT)
        
        ttk.Button(preview_info_frame, text="Show Report", command=self._show_extraction_report).pack(side=tk.RIGHT, padx=5)

    def _show_extraction_report(self):
        if not self.class_extractor:
            messagebox.showwarning("Warning", "Please analyze labels first")
            return
        
        report = self.class_extractor.generate_extraction_report()
        
        report_window = tk.Toplevel(self)
        report_window.title("Extraction Report")
        report_window.geometry("800x600")
        
        text = scrolledtext.ScrolledText(report_window, wrap=tk.WORD, font=("Consolas", 9))
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, report)
        text.config(state='disabled')
        
        save_btn = ttk.Button(report_window, text="Save Report", command=lambda: self._save_report(report))
        save_btn.pack(pady=10)

    def _save_report(self, report: str):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Extraction Report"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(report)
                self._log(f"Report saved to {file_path}")
                messagebox.showinfo("Success", "Report saved successfully")
            except Exception as e:
                self._log(f"Failed to save report: {e}")
                messagebox.showerror("Error", f"Failed to save report: {e}")

    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        
        ttk.Button(button_frame, text="Scan Directories", command=self._scan_directories).grid(row=0, column=0, sticky=tk.EW, padx=3)
        ttk.Button(button_frame, text="Generate Preview", command=self._generate_preview).grid(row=0, column=1, sticky=tk.EW, padx=3)
        ttk.Button(button_frame, text="Execute", command=self._execute_extraction).grid(row=0, column=2, sticky=tk.EW, padx=3)
        ttk.Button(button_frame, text="Validate", command=self._validate_extraction).grid(row=0, column=3, sticky=tk.EW, padx=3)
        
        btn2_frame = ttk.Frame(button_frame)
        btn2_frame.grid(row=1, column=0, columnspan=4, sticky=tk.EW, pady=(5, 0))
        
        ttk.Button(btn2_frame, text="Save Config", command=self._save_config).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn2_frame, text="Load Config", command=self._load_config).pack(side=tk.LEFT, padx=3)
        ttk.Button(btn2_frame, text="Clear Log", command=self._clear_log).pack(side=tk.LEFT, padx=3)

    def _create_log(self, parent):
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(0, 5))
        
        ttk.Label(log_frame, text="Operation Log:").pack(anchor=tk.W)
        self.log_text = scrolledtext.ScrolledText(log_frame, height=6, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _create_status_bar(self, parent):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(parent, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X)

    def _select_images_folder(self):
        folder = filedialog.askdirectory(title="Select Images Directory")
        if folder:
            self.images_path_var.set(folder)
            self._log(f"Selected images directory: {folder}")

    def _select_labels_folder(self):
        folder = filedialog.askdirectory(title="Select Labels Directory")
        if folder:
            self.labels_path_var.set(folder)
            self._log(f"Selected labels directory: {folder}")

    def _scan_directories(self):
        images_dir = self.images_path_var.get()
        labels_dir = self.labels_path_var.get()
        
        if not images_dir or not labels_dir:
            messagebox.showwarning("Warning", "Please select both images and labels directories")
            return
        
        self._log("=" * 60)
        self._log("Scanning directories...")
        
        self.extractor = ValidExtractor(images_dir, labels_dir, project_root=os.getcwd())
        img_count, lbl_count = self.extractor.scan_directories()
        self.match_report = self.extractor.get_match_report()
        
        self._log(f"Found {img_count} image files in {images_dir}")
        self._log(f"Found {lbl_count} label files in {labels_dir}")
        self._log(f"Paired files: {self.match_report['paired_count']}")
        self._log(f"Unpaired images: {self.match_report['unpaired_images_count']}")
        self._log(f"Unpaired labels: {self.match_report['unpaired_labels_count']}")
        
        self._populate_file_list()
        
        if self.match_report['unpaired_images_count'] > 0:
            self._log(f"Warning: {self.match_report['unpaired_images_count']} images have no matching labels")
        if self.match_report['unpaired_labels_count'] > 0:
            self._log(f"Warning: {self.match_report['unpaired_labels_count']} labels have no matching images")
        
        self.status_var.set(f"Scanned: {img_count} images, {lbl_count} labels, {self.match_report['paired_count']} paired")

    def _populate_file_list(self):
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        
        self.all_paired_files = self.match_report.get('paired_names', [])
        self.selected_files = []
        
        for i, name in enumerate(self.all_paired_files):
            self.file_tree.insert("", "end", text=str(i+1), values=(name, "Unselected"))

    def _toggle_file_selection(self, event):
        if self.mode_var.get() != "manual":
            messagebox.showwarning("Warning", "Please switch to Manual Selection mode")
            return
        
        item = self.file_tree.selection()[0]
        filename = self.file_tree.item(item, "values")[0]
        
        if filename in self.selected_files:
            self.selected_files.remove(filename)
            self.file_tree.item(item, values=(filename, "Unselected"))
            self.file_tree.detach(item)
            self.file_tree.reattach(item, "", "end")
        else:
            self.selected_files.append(filename)
            self.file_tree.item(item, values=(filename, "Selected"))
            self.file_tree.detach(item)
            self.file_tree.reattach(item, "", 0)
        
        self.selected_count_var.set(str(len(self.selected_files)))

    def _select_all_files(self):
        if self.mode_var.get() != "manual":
            messagebox.showwarning("Warning", "Please switch to Manual Selection mode")
            return
        
        self.selected_files = list(self.all_paired_files)
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            self.file_tree.item(item, values=(values[0], "Selected"))
        
        self.selected_count_var.set(str(len(self.selected_files)))

    def _deselect_all_files(self):
        self.selected_files = []
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            self.file_tree.item(item, values=(values[0], "Unselected"))
        
        self.selected_count_var.set("0")

    def _random_select_files(self):
        if self.mode_var.get() != "manual":
            messagebox.showwarning("Warning", "Please switch to Manual Selection mode")
            return
        
        if not self.extractor:
            messagebox.showwarning("Warning", "Please scan directories first")
            return
        
        ratio = self.ratio_var.get()
        count = max(1, int(len(self.all_paired_files) * ratio))
        self.selected_files = self.extractor.select_by_count(count, seed=self.seed_var.get())
        
        for item in self.file_tree.get_children():
            values = self.file_tree.item(item, "values")
            status = "Selected" if values[0] in self.selected_files else "Unselected"
            self.file_tree.item(item, values=(values[0], status))
        
        self.selected_count_var.set(str(len(self.selected_files)))

    def _generate_preview(self):
        if not self.extractor:
            messagebox.showwarning("Warning", "Please scan directories first")
            return
        
        selected = self._get_selected_files()
        
        if not selected:
            messagebox.showwarning("Warning", "No files selected for extraction")
            return
        
        preview = self.extractor.generate_preview(selected)
        
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, f"=== Extraction Preview ({len(selected)} files) ===\n")
        self.preview_text.insert(tk.END, f"Operation: {'Copy' if self.operation_var.get() == 'copy' else 'Move'}\n")
        target_dir = self.output_dir_var.get() or os.path.join(os.getcwd(), 'valid')
        self.preview_text.insert(tk.END, f"Target: {target_dir}\n")
        self.preview_text.insert(tk.END, "-" * 50 + "\n")
        
        for name, img_path, lbl_path in preview[:20]:
            self.preview_text.insert(tk.END, f"{name}\n")
        
        if len(preview) > 20:
            self.preview_text.insert(tk.END, f"... and {len(preview) - 20} more files\n")
        
        self._log(f"Generated preview for {len(selected)} files")

    def _get_selected_files(self) -> List[str]:
        mode = self.mode_var.get()
        
        if mode == "manual":
            return self.selected_files
        elif mode == "ratio":
            if not self.extractor:
                return []
            return self.extractor.select_by_ratio(self.ratio_var.get(), seed=self.seed_var.get())
        elif mode == "count":
            if not self.extractor:
                return []
            return self.extractor.select_by_count(self.count_var.get(), seed=self.seed_var.get())
        elif mode == "class":
            return self._get_class_based_selection()
        return []

    def _get_class_based_selection(self) -> List[str]:
        if not self.class_extractor:
            messagebox.showwarning("Warning", "Please analyze labels first")
            return []
        
        self.class_selections = {}
        for cls_id, var in self.class_checkboxes.items():
            if var.get():
                ratio = float(self.class_ratio_entries.get(cls_id, 0.2))
                self.class_selections[cls_id] = ratio
        
        if not self.class_selections:
            messagebox.showwarning("Warning", "Please select at least one class")
            return []
        
        return self.class_extractor.extract_by_classes(self.class_selections, seed=self.seed_var.get())

    def _execute_extraction(self):
        if not self.extractor:
            messagebox.showwarning("Warning", "Please scan directories first")
            return
        
        selected = self._get_selected_files()
        
        if not selected:
            messagebox.showwarning("Warning", "No files selected for extraction")
            return
        
        operation = self.operation_var.get()
        target_dir = self.output_dir_var.get() or os.path.join(os.getcwd(), 'valid')
        
        confirm_msg = f"About to {'copy' if operation == 'copy' else 'move'} {len(selected)} file pairs to:\n{target_dir}\n\nContinue?"
        if not messagebox.askyesno("Confirm Extraction", confirm_msg, icon='warning'):
            return
        
        self._log("=" * 60)
        self._log(f"Starting {'copy' if operation == 'copy' else 'move'} operation...")
        self._log(f"Source images: {self.extractor.images_dir}")
        self._log(f"Source labels: {self.extractor.labels_dir}")
        self._log(f"Target: {target_dir}")
        self._log(f"Files to process: {len(selected)}")
        
        success_count, failure_count, errors = self.extractor.execute_extraction(
            selected, operation=operation, valid_dir=target_dir
        )
        
        self._log(f"Extraction completed!")
        self._log(f"Success: {success_count} file pairs")
        self._log(f"Failed: {failure_count} file pairs")
        
        if errors:
            self._log("--- Errors ---")
            for error in errors[:10]:
                self._log(f"  {error['file']}: {error['error']}")
            if len(errors) > 10:
                self._log(f"  ... and {len(errors) - 10} more errors")
        
        if self.class_extractor:
            report = self.class_extractor.generate_extraction_report()
            self._log("\n--- Extraction Report ---")
            for line in report.split('\n')[:15]:
                self._log(line)
            self._log("... (full report available via Show Report button)")
        
        messagebox.showinfo(
            "Extraction Completed",
            f"Successfully {'copied' if operation == 'copy' else 'moved'} {success_count} file pairs.\n"
            f"Failed: {failure_count} file pairs.\n\n"
            f"Check log for details."
        )
        
        self.status_var.set(f"Extraction done: {success_count} success, {failure_count} failed")

    def _validate_extraction(self):
        target_dir = self.output_dir_var.get() or os.path.join(os.getcwd(), 'valid')
        
        if not self.extractor:
            extractor = ValidExtractor(project_root=target_dir)
        else:
            extractor = ValidExtractor(
                images_dir=self.extractor.images_dir,
                labels_dir=self.extractor.labels_dir,
                project_root=target_dir
            )
        
        result = extractor.validate_extraction(valid_dir=target_dir)
        
        if not result['images_dir_exists'] or not result['labels_dir_exists']:
            messagebox.showwarning("Warning", f"valid/ directory does not exist in {target_dir}")
            return
        
        report = f"=== Validation Report ===\n"
        report += f"Target Directory: {target_dir}\n"
        report += f"Images directory: {'OK' if result['images_dir_exists'] else 'MISSING'}\n"
        report += f"Labels directory: {'OK' if result['labels_dir_exists'] else 'MISSING'}\n"
        report += f"\nImage files: {result['image_count']}\n"
        report += f"Label files: {result['label_count']}\n"
        report += f"Paired files: {result['paired_count']}\n"
        
        if result['missing_labels']:
            report += f"\nImages without labels ({len(result['missing_labels'])}):\n"
            for name in result['missing_labels'][:5]:
                report += f"  - {name}\n"
            if len(result['missing_labels']) > 5:
                report += f"  ... and {len(result['missing_labels']) - 5} more\n"
        
        if result['missing_images']:
            report += f"\nLabels without images ({len(result['missing_images'])}):\n"
            for name in result['missing_images'][:5]:
                report += f"  - {name}\n"
            if len(result['missing_images']) > 5:
                report += f"  ... and {len(result['missing_images']) - 5} more\n"
        
        report += f"\nTotal image size: {self._format_size(result['total_image_size'])}\n"
        report += f"Total label size: {self._format_size(result['total_label_size'])}\n"
        report += f"\nValidation: {'PASS' if result['valid'] else 'FAIL'}"
        
        self._log("Validation report generated")
        messagebox.showinfo("Validation Result", report)

    def _format_size(self, size_bytes: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def _save_config(self):
        self.config.images_dir = self.images_path_var.get()
        self.config.labels_dir = self.labels_path_var.get()
        self.config.extraction_method = self.mode_var.get()
        self.config.extraction_ratio = self.ratio_var.get()
        self.config.extraction_count = self.count_var.get()
        self.config.file_operation = self.operation_var.get()
        self.config.random_seed = self.seed_var.get()
        self.config.manual_selection = self.selected_files
        
        success = self.persistence.save(self.config, auto_named=True)
        
        if success:
            self._log("Configuration saved successfully")
            messagebox.showinfo("Success", "Configuration saved successfully")
        else:
            self._log("Failed to save configuration")
            messagebox.showerror("Error", "Failed to save configuration")

    def _load_config(self):
        loaded = self.persistence.load("ValidExtractorConfig.json")
        
        if loaded:
            if hasattr(loaded, 'images_dir'):
                self.images_path_var.set(loaded.images_dir)
            if hasattr(loaded, 'labels_dir'):
                self.labels_path_var.set(loaded.labels_dir)
            if hasattr(loaded, 'extraction_method'):
                self.mode_var.set(loaded.extraction_method)
            if hasattr(loaded, 'extraction_ratio'):
                self.ratio_var.set(loaded.extraction_ratio)
            if hasattr(loaded, 'extraction_count'):
                self.count_var.set(loaded.extraction_count)
            if hasattr(loaded, 'file_operation'):
                self.operation_var.set(loaded.file_operation)
            if hasattr(loaded, 'random_seed'):
                self.seed_var.set(loaded.random_seed)
            
            self._update_mode_widgets()
            self._log("Configuration loaded successfully")
            messagebox.showinfo("Success", "Configuration loaded successfully")
        else:
            self._log("No saved configuration found")
            messagebox.showinfo("Info", "No saved configuration found")

    def _clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self._log("Log cleared")

    def _log(self, message: str):
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()
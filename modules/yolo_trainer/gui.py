"""YOLO Trainer Module GUI"""
import os
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from modules.yolo_trainer.trainer import YOLOTrainer


class YOLOTrainerGUI(ttk.Frame):
    """YOLO Trainer GUI Component"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.trainer = YOLOTrainer()
        self.trainer.register_callback(self._on_training_message)
        
        self.is_training = False
        self.training_thread = None
        
        self.model_var = tk.StringVar(value="yolo12s.pt")
        self.data_var = tk.StringVar(value="data.yaml")
        self.epochs_var = tk.IntVar(value=100)
        self.batch_var = tk.IntVar(value=24)
        self.imgsz_var = tk.StringVar(value="640")
        self.amp_var = tk.BooleanVar(value=True)
        self.cache_var = tk.BooleanVar(value=False)
        self.device_var = tk.StringVar(value="auto")
        self.workers_var = tk.IntVar(value=8)
        self.project_var = tk.StringVar(value="output/train_model")
        self.name_var = tk.StringVar(value="detect_model")
        self.resume_var = tk.BooleanVar(value=False)
        
        self.status_var = tk.StringVar(value="Ready")
        
        self.log_messages = []
        
        self._create_widgets()

    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding=(10, 10, 10, 0))
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_param_panel(left_frame)
        self._build_log_panel(right_frame)

        status_bar = ttk.Label(self, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W, padding=(5, 2))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_param_panel(self, parent):
        canvas = tk.Canvas(parent, width=420, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        row = 0

        sec = ttk.LabelFrame(scrollable, text="Model & Data", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = self._add_file_row(sec, row, "Model File:", self.model_var, "*.pt", self._on_model_changed)
        row = self._add_file_row(sec, row, "Data Config:", self.data_var, "*.yaml *.yml")
        ttk.Button(sec, text="Create data.yaml", command=self._create_data_yaml).grid(
            row=row, column=1, columnspan=2, sticky=tk.EW, pady=(2, 5))
        row += 1

        sec = ttk.LabelFrame(scrollable, text="Training Parameters", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = 0
        row = self._add_spin_row(sec, row, "Epochs:", self.epochs_var, 1, 1000, "epochs")
        row = self._add_spin_row(sec, row, "Batch Size:", self.batch_var, 1, 256, "batch")
        row = self._add_combo_row(sec, row, "Image Size:", self.imgsz_var,
                                  ["320", "416", "512", "640", "768", "1024", "1280"])

        sec = ttk.LabelFrame(scrollable, text="Performance Settings", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = 0
        row = self._add_check_row(sec, row, "Mixed Precision (AMP):", self.amp_var, 
                                  "Accelerate training & save memory")
        row = self._add_check_row(sec, row, "Cache Images:", self.cache_var, 
                                  "Requires sufficient RAM")
        row = self._add_combo_row(sec, row, "Device:", self.device_var,
                                  ["auto", "cuda", "cpu"])
        row = self._add_spin_row(sec, row, "Workers:", self.workers_var, 1, 32, "workers")

        sec = ttk.LabelFrame(scrollable, text="Output Settings", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = 0
        row = self._add_dir_row(sec, row, "Output Dir:", self.project_var)
        row = self._add_entry_row(sec, row, "Run Name:", self.name_var,
                                  "Subdirectory for weights & logs")
        row = self._add_check_row(sec, row, "Resume Training:", self.resume_var,
                                  "Continue from checkpoint")

        btn_frame = ttk.Frame(scrollable)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        self.start_btn = ttk.Button(btn_frame, text="Start Training", command=self._start_training)
        self.start_btn.grid(row=0, column=0, sticky=tk.EW, padx=2)

        self.validate_btn = ttk.Button(btn_frame, text="Validate Params", command=self._validate_params)
        self.validate_btn.grid(row=0, column=1, sticky=tk.EW, padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="Stop", command=self._stop_training, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, sticky=tk.EW, padx=2)

    def _build_log_panel(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Training Log", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        control_frame = ttk.Frame(log_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_entry = ttk.Entry(control_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.search_entry.bind('<KeyRelease>', self._search_log)
        
        ttk.Button(control_frame, text="Search", command=self._search_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Clear", command=self._clear_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="Copy", command=self._copy_log).pack(side=tk.LEFT, padx=(0, 5))
        
        filter_frame = ttk.Frame(log_frame)
        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.log_filter_var = tk.StringVar(value="all")
        ttk.Radiobutton(filter_frame, text="All", variable=self.log_filter_var, 
                        value="all", command=self._apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Info", variable=self.log_filter_var, 
                        value="INFO", command=self._apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Warning", variable=self.log_filter_var, 
                        value="WARN", command=self._apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(filter_frame, text="Error", variable=self.log_filter_var, 
                        value="ERROR", command=self._apply_filter).pack(side=tk.LEFT, padx=5)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 9),
                                state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4",
                                insertbackground="white")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                   command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log_text.tag_configure("INFO", foreground="#4ec9b0")
        self.log_text.tag_configure("WARN", foreground="#dcdcaa")
        self.log_text.tag_configure("ERROR", foreground="#f14c4c")
        self.log_text.tag_configure("timestamp", foreground="#6b7280")

        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(info_frame, text="Device Info:").pack(side=tk.LEFT)
        self.device_info_label = ttk.Label(info_frame, text="Detecting...", foreground="gray")
        self.device_info_label.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(info_frame, text="Refresh", command=self._refresh_device_info).pack(side=tk.RIGHT)

        self._refresh_device_info()

    def _add_file_row(self, parent, row, label, var, filetypes, callback=None):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=2)
        if callback:
            var.trace_add("write", callback)
        ttk.Button(parent, text="Browse", width=6,
                   command=lambda: self._browse_file(var, filetypes)).grid(
            row=row, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _add_dir_row(self, parent, row, label, var):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        ttk.Entry(parent, textvariable=var).grid(
            row=row, column=1, sticky=tk.EW, pady=2)
        ttk.Button(parent, text="Browse", width=6,
                   command=lambda: self._browse_dir(var)).grid(
            row=row, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _add_spin_row(self, parent, row, label, var, vmin, vmax, unit):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        ttk.Spinbox(parent, from_=vmin, to=vmax, textvariable=var, width=10).grid(
            row=row, column=1, sticky=tk.W, pady=2)
        ttk.Label(parent, text=unit, foreground="gray").grid(
            row=row, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        return row + 1

    def _add_combo_row(self, parent, row, label, var, values):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        ttk.Combobox(parent, textvariable=var, values=values, width=10,
                     state="readonly").grid(row=row, column=1, sticky=tk.W, pady=2)
        return row + 1

    def _add_check_row(self, parent, row, label, var, hint):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        ttk.Checkbutton(parent, variable=var).grid(
            row=row, column=1, sticky=tk.W, pady=2)
        ttk.Label(parent, text=hint, foreground="gray", font=("Arial", 8)).grid(
            row=row, column=2, sticky=tk.W, pady=2, padx=(2, 0))
        return row + 1

    def _add_entry_row(self, parent, row, label, var, hint):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        ttk.Entry(parent, textvariable=var).grid(
            row=row, column=1, sticky=tk.EW, pady=2)
        ttk.Label(parent, text=hint, foreground="gray", font=("Arial", 8)).grid(
            row=row, column=2, sticky=tk.W, pady=2, padx=(2, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _browse_file(self, var, filetypes_str):
        path = filedialog.askopenfilename(
            filetypes=[("Supported Files", filetypes_str), ("All Files", "*.*")])
        if path:
            var.set(path)
            self._log(f"Selected: {os.path.basename(path)}")

    def _browse_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)
            self._log(f"Selected directory: {path}")

    def _on_model_changed(self, *args):
        model_path = self.model_var.get()
        if model_path and os.path.exists(model_path):
            self._log(f"Model file selected: {os.path.basename(model_path)}")

    def _refresh_device_info(self):
        device_info = self.trainer.get_device_info()
        if device_info['device_type'] == 'cuda':
            self.device_info_label.config(
                text=f"{device_info['name']} ({device_info['memory_gb']:.1f} GB)", foreground="green")
        else:
            self.device_info_label.config(
                text="CPU only", foreground="orange")

    def _create_data_yaml(self):
        from pathlib import Path
        default_path = str(Path("output") / "train")
        if os.path.exists(default_path) and os.path.exists(os.path.join(default_path, "images")):
            dataset_path = default_path
        else:
            dataset_path = filedialog.askdirectory(title="Select Dataset Root Directory")
            if not dataset_path:
                return

        yaml_content = self.trainer.create_data_yaml(dataset_path)

        save_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML Files", "*.yaml"), ("All Files", "*.*")],
            initialfile="data.yaml",
            title="Save data.yaml"
        )
        if save_path:
            success = self.trainer.save_data_yaml(yaml_content, save_path)
            if success:
                self.data_var.set(save_path)
                self._log(f"data.yaml created: {save_path}")
                messagebox.showinfo("Success", f"data.yaml saved to:\n{save_path}")
            else:
                messagebox.showerror("Error", "Failed to save data.yaml")

    def _validate_params(self):
        params = self._get_params()
        is_valid, errors = self.trainer.validate_parameters(params)

        if errors:
            messagebox.showwarning("Parameter Validation Failed",
                                   "Please fix the following issues:\n\n" + "\n".join(f"  - {e}" for e in errors))
            return False

        self._log_separator()
        self._log("Parameter validation passed", level="INFO")

        self._log(f"  Model: {params['model']}", level="INFO")
        self._log(f"  Data: {params['data']}", level="INFO")
        self._log(f"  Device: {params['device']}", level="INFO")
        self._log(f"  Epochs: {params['epochs']}", level="INFO")
        self._log(f"  Batch Size: {params['batch']}", level="INFO")
        self._log(f"  Image Size: {params['imgsz']}", level="INFO")
        self._log(f"  AMP: {'Enabled' if params['amp'] else 'Disabled'}", level="INFO")
        self._log(f"  Cache: {'Enabled' if params['cache'] else 'Disabled'}", level="INFO")
        self._log(f"  Workers: {params['workers']}", level="INFO")
        self._log(f"  Output: {params['project']}/{params['name']}", level="INFO")
        messagebox.showinfo("Validation Passed", "All parameters are valid. Ready to start training.")
        return True

    def _get_params(self):
        return {
            'model': self.model_var.get(),
            'data': self.data_var.get(),
            'epochs': self.epochs_var.get(),
            'batch': self.batch_var.get(),
            'imgsz': int(self.imgsz_var.get()),
            'amp': self.amp_var.get(),
            'cache': self.cache_var.get(),
            'device': self.device_var.get(),
            'workers': self.workers_var.get(),
            'project': self.project_var.get(),
            'name': self.name_var.get(),
            'resume': self.resume_var.get()
        }

    def _start_training(self):
        if self.is_training:
            return

        if not self._validate_params():
            return

        self.is_training = True
        self.start_btn.config(state=tk.DISABLED)
        self.validate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Training...")

        self._log_separator()
        self._log("Starting training", level="INFO")

        self.training_thread = threading.Thread(target=self._run_training, daemon=True)
        self.training_thread.start()

    def _stop_training(self):
        if not self.is_training:
            return
        self.is_training = False
        self._log("Stopping training...", level="WARN")
        self.status_var.set("Stopped")

    def _run_training(self):
        params = self._get_params()
        results = self.trainer.train(params)
        
        self._root().after(0, lambda: self._on_training_complete(results))

    def _on_training_complete(self, results):
        if results['success']:
            elapsed = results['elapsed_time']
            messagebox.showinfo("Training Complete",
                               f"Training completed!\nTime: {elapsed:.0f} seconds\n"
                               f"Model: {results['output_dir']}/weights/best.pt")
        else:
            self._log(results.get('error', 'Unknown error'), level="ERROR")
            messagebox.showerror("Training Failed", str(results.get('error', 'Unknown error')))
        
        self._on_training_end()

    def _on_training_message(self, message):
        self._root().after(0, lambda: self._log(message))

    def _on_training_end(self):
        self.is_training = False
        self.start_btn.config(state=tk.NORMAL)
        self.validate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Ready")

    def _log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_messages.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
        self.log_text.config(state=tk.NORMAL)
        
        self.log_text.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.log_text.insert(tk.END, f"[{level}] ", level)
        self.log_text.insert(tk.END, f"{message}\n")
        
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _log_separator(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, "-" * 70 + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        self.log_messages = []
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        self._log("Log cleared", level="INFO")

    def _copy_log(self):
        self.log_text.clipboard_clear()
        log_content = "\n".join([f"[{m['timestamp']}] [{m['level']}] {m['message']}" 
                                for m in self.log_messages])
        self.log_text.clipboard_append(log_content)
        messagebox.showinfo("Success", "Log content copied to clipboard")

    def _search_log(self, event=None):
        search_term = self.search_entry.get().lower()
        
        self.log_text.tag_remove(tk.SEL, 1.0, tk.END)
        
        if not search_term:
            return
        
        start = 1.0
        while True:
            pos = self.log_text.search(search_term, start, stopindex=tk.END, nocase=True)
            if not pos:
                break
            end = pos + f"+{len(search_term)}c"
            self.log_text.tag_add(tk.SEL, pos, end)
            start = end
        
        self.log_text.tag_config(tk.SEL, background="yellow", foreground="black")

    def _apply_filter(self):
        filter_level = self.log_filter_var.get()
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for msg in self.log_messages:
            if filter_level == "all" or msg['level'] == filter_level:
                self.log_text.insert(tk.END, f"[{msg['timestamp']}] ", "timestamp")
                self.log_text.insert(tk.END, f"[{msg['level']}] ", msg['level'])
                self.log_text.insert(tk.END, f"{msg['message']}\n")
        
        self.log_text.config(state=tk.DISABLED)

    def _root(self):
        """Get the root window"""
        return self.winfo_toplevel()
from ultralytics import YOLO
import torch
import os
import threading
import time
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


class TrainGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("YOLO 训练参数配置")
        self.root.geometry("1050x680")
        self.root.minsize(900, 580)

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

        self.status_var = tk.StringVar(value="就绪")

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=(10, 10, 10, 0))
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_param_panel(left_frame)
        self._build_log_panel(right_frame)

        status_bar = ttk.Label(self.root, textvariable=self.status_var,
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

        sec = ttk.LabelFrame(scrollable, text="模型与数据", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = self._add_file_row(sec, row, "模型文件:", self.model_var, "*.pt", self._on_model_changed)
        row = self._add_file_row(sec, row, "数据配置:", self.data_var, "*.yaml *.yml")
        ttk.Button(sec, text="创建 data.yaml", command=self._create_data_yaml).grid(
            row=row, column=1, columnspan=2, sticky=tk.EW, pady=(2, 5))
        row += 1

        sec = ttk.LabelFrame(scrollable, text="训练参数", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = 0
        row = self._add_spin_row(sec, row, "训练轮数:", self.epochs_var, 1, 1000, "epochs")
        row = self._add_spin_row(sec, row, "批次大小:", self.batch_var, 1, 256, "batch")
        row = self._add_combo_row(sec, row, "图像尺寸:", self.imgsz_var,
                                  ["320", "416", "512", "640", "768", "1024", "1280"])

        sec = ttk.LabelFrame(scrollable, text="性能设置", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = 0
        row = self._add_check_row(sec, row, "混合精度 (AMP):", self.amp_var, "启用可加速训练并节省显存")
        row = self._add_check_row(sec, row, "缓存图像:", self.cache_var, "将图像缓存到内存，需要足够RAM")
        row = self._add_combo_row(sec, row, "计算设备:", self.device_var,
                                  ["auto", "cuda", "cpu"])
        row = self._add_spin_row(sec, row, "工作线程:", self.workers_var, 1, 32, "workers")

        sec = ttk.LabelFrame(scrollable, text="输出设置", padding="10 5")
        sec.pack(fill=tk.X, pady=(0, 10))
        row = 0
        row = self._add_dir_row(sec, row, "输出目录:", self.project_var)
        row = self._add_entry_row(sec, row, "运行名称:", self.name_var,
                                  "模型权重与日志保存子目录名")
        row = self._add_check_row(sec, row, "断点续训:", self.resume_var,
                                  "从上次中断处继续训练")

        btn_frame = ttk.Frame(scrollable)
        btn_frame.pack(fill=tk.X, pady=(5, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        self.start_btn = ttk.Button(btn_frame, text="开始训练", command=self._start_training)
        self.start_btn.grid(row=0, column=0, sticky=tk.EW, padx=2)

        self.validate_btn = ttk.Button(btn_frame, text="验证参数", command=self._validate_params)
        self.validate_btn.grid(row=0, column=1, sticky=tk.EW, padx=2)

        self.stop_btn = ttk.Button(btn_frame, text="停止", command=self._stop_training, state=tk.DISABLED)
        self.stop_btn.grid(row=0, column=2, sticky=tk.EW, padx=2)

    def _build_log_panel(self, parent):
        log_frame = ttk.LabelFrame(parent, text="训练日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_text = tk.Text(log_frame, wrap=tk.WORD, font=("Consolas", 9),
                                state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4",
                                insertbackground="white")
        log_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL,
                                   command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        info_frame = ttk.Frame(parent)
        info_frame.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(info_frame, text="设备信息:").pack(side=tk.LEFT)
        self.device_info_label = ttk.Label(info_frame, text="检测中...", foreground="gray")
        self.device_info_label.pack(side=tk.LEFT, padx=(5, 0))
        ttk.Button(info_frame, text="刷新", command=self._refresh_device_info).pack(side=tk.RIGHT)

        self._refresh_device_info()

    def _add_file_row(self, parent, row, label, var, filetypes, callback=None):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        entry = ttk.Entry(parent, textvariable=var)
        entry.grid(row=row, column=1, sticky=tk.EW, pady=2)
        if callback:
            var.trace_add("write", callback)
        ttk.Button(parent, text="浏览", width=6,
                   command=lambda: self._browse_file(var, filetypes)).grid(
            row=row, column=2, sticky=tk.W, pady=2, padx=(5, 0))
        parent.columnconfigure(1, weight=1)
        return row + 1

    def _add_dir_row(self, parent, row, label, var):
        ttk.Label(parent, text=label, width=12, anchor=tk.E).grid(
            row=row, column=0, sticky=tk.W, pady=2, padx=(0, 5))
        ttk.Entry(parent, textvariable=var).grid(
            row=row, column=1, sticky=tk.EW, pady=2)
        ttk.Button(parent, text="浏览", width=6,
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
            filetypes=[("支持的文件", filetypes_str), ("所有文件", "*.*")])
        if path:
            var.set(path)
            self.log(f"已选择: {os.path.basename(path)}")

    def _browse_dir(self, var):
        path = filedialog.askdirectory()
        if path:
            var.set(path)
            self.log(f"已选择目录: {path}")

    def _on_model_changed(self, *args):
        model_path = self.model_var.get()
        if model_path and os.path.exists(model_path):
            self.log(f"模型文件已选择: {os.path.basename(model_path)}")

    def _refresh_device_info(self):
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory / 1e9
            self.device_info_label.config(
                text=f"{gpu_name} ({mem:.1f} GB)", foreground="green")
        else:
            self.device_info_label.config(
                text="CPU only", foreground="orange")

    def _create_data_yaml(self):
        default_path = str(Path("output") / "train")
        if os.path.exists(default_path) and os.path.exists(os.path.join(default_path, "images")):
            dataset_path = default_path
        else:
            dataset_path = filedialog.askdirectory(title="选择数据集根目录")
            if not dataset_path:
                return

        class_names = []
        label_dir = os.path.join(dataset_path, "labels")
        if os.path.exists(label_dir):
            for f in os.listdir(label_dir):
                if f.endswith(".txt"):
                    with open(os.path.join(label_dir, f), 'r') as lf:
                        for line in lf:
                            cls_id = line.strip().split()[0] if line.strip() else None
                            if cls_id and cls_id not in class_names:
                                class_names.append(cls_id)

        if not class_names:
            class_names = [str(i) for i in range(80)]

        yaml_content = f"path: {os.path.abspath(dataset_path)}\n"
        yaml_content += "train: images\n"
        yaml_content += "val: images\n\n"
        yaml_content += f"nc: {len(class_names)}\n"
        yaml_content += "names:\n"
        for i, name in enumerate(class_names):
            yaml_content += f"  {i}: {name}\n"

        save_path = filedialog.asksaveasfilename(
            defaultextension=".yaml",
            filetypes=[("YAML文件", "*.yaml"), ("所有文件", "*.*")],
            initialfile="data.yaml",
            title="保存 data.yaml"
        )
        if save_path:
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            self.data_var.set(save_path)
            self.log(f"data.yaml 已创建: {save_path}")
            messagebox.showinfo("成功", f"data.yaml 已保存到:\n{save_path}")

    def _validate_params(self):
        errors = []

        model_path = self.model_var.get().strip()
        if not model_path:
            errors.append("模型文件路径不能为空")

        data_path = self.data_var.get().strip()
        if not data_path:
            errors.append("数据配置文件路径不能为空")
        elif not os.path.exists(data_path):
            errors.append(f"数据配置文件不存在: {data_path}")

        try:
            epochs = self.epochs_var.get()
            if epochs < 1 or epochs > 1000:
                errors.append(f"训练轮数应在 1-1000 之间，当前值: {epochs}")
        except Exception:
            errors.append("训练轮数必须是有效整数")

        try:
            batch = self.batch_var.get()
            if batch < 1 or batch > 256:
                errors.append(f"批次大小应在 1-256 之间，当前值: {batch}")
        except Exception:
            errors.append("批次大小必须是有效整数")

        try:
            imgsz = int(self.imgsz_var.get())
            if imgsz < 32 or imgsz > 2048:
                errors.append(f"图像尺寸应在 32-2048 之间，当前值: {imgsz}")
        except ValueError:
            errors.append("图像尺寸必须是有效整数")

        try:
            workers = self.workers_var.get()
            if workers < 0 or workers > 64:
                errors.append(f"工作线程应在 0-64 之间，当前值: {workers}")
        except Exception:
            errors.append("工作线程必须是有效整数")

        project = self.project_var.get().strip()
        if not project:
            errors.append("输出目录不能为空")

        name = self.name_var.get().strip()
        if not name:
            errors.append("运行名称不能为空")
        elif not name.replace("_", "").replace("-", "").isalnum():
            errors.append("运行名称只能包含字母、数字、下划线和连字符")

        if errors:
            messagebox.showwarning("参数验证失败",
                                   "请修正以下问题:\n\n" + "\n".join(f"  - {e}" for e in errors))
            return False

        self._log_separator()
        self.log("参数验证通过")

        self.log(f"  模型: {model_path}")
        self.log(f"  数据: {data_path}")
        self.log(f"  设备: {self.device_var.get()}")
        self.log(f"  训练轮数: {epochs}")
        self.log(f"  批次大小: {batch}")
        self.log(f"  图像尺寸: {imgsz}")
        self.log(f"  AMP: {'启用' if self.amp_var.get() else '禁用'}")
        self.log(f"  缓存: {'启用' if self.cache_var.get() else '禁用'}")
        self.log(f"  工作线程: {workers}")
        self.log(f"  输出: {project}/{name}")
        messagebox.showinfo("验证通过", "所有参数验证通过，可以开始训练。")
        return True

    def _start_training(self):
        if self.is_training:
            return

        if not self._validate_params():
            return

        self.is_training = True
        self.start_btn.config(state=tk.DISABLED)
        self.validate_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("训练中...")

        self._log_separator()
        self.log("开始训练")

        self.training_thread = threading.Thread(target=self._run_training, daemon=True)
        self.training_thread.start()

    def _stop_training(self):
        if not self.is_training:
            return
        self.is_training = False
        self.log("正在停止训练...")
        self.status_var.set("已停止")

    def _run_training(self):
        try:
            model_path = self.model_var.get().strip()
            data_path = self.data_var.get().strip()
            epochs = self.epochs_var.get()
            batch = self.batch_var.get()
            imgsz = int(self.imgsz_var.get())
            amp = self.amp_var.get()
            cache = self.cache_var.get()
            device = self.device_var.get()
            workers = self.workers_var.get()
            project = self.project_var.get().strip()
            name = self.name_var.get().strip()
            resume = self.resume_var.get()

            self._log_separator()
            self.log("初始化训练环境...")

            resolved_device = device
            if device == "auto":
                resolved_device = "cuda" if torch.cuda.is_available() else "cpu"
                self.log(f"自动选择设备: {resolved_device}")
            elif device == "cuda" and not torch.cuda.is_available():
                self.log("CUDA 不可用，回退到 CPU")
                resolved_device = "cpu"

            if resolved_device == "cuda":
                self.log(f"GPU: {torch.cuda.get_device_name(0)}")
                mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                self.log(f"显存: {mem:.1f} GB")
            else:
                self.log("使用 CPU 训练")

            self.log(f"加载模型: {model_path}")
            model = YOLO(model_path)

            workers_val = min(workers, os.cpu_count() or 1)
            if workers_val != workers:
                self.log(f"工作线程调整为: {workers_val} (CPU核心数限制)")

            self.log(f"数据配置: {data_path}")
            self.log(f"训练轮数: {epochs}")
            self.log(f"批次大小: {batch}")
            self.log(f"图像尺寸: {imgsz}")
            self.log(f"输出目录: {project}/{name}")
            self.log("开始模型训练...")
            self._log_separator()

            start_time = time.time()

            results = model.train(
                data=data_path,
                epochs=epochs,
                batch=batch,
                imgsz=imgsz,
                amp=amp,
                cache=cache,
                device=resolved_device,
                workers=workers_val,
                project=project,
                name=name,
                verbose=True,
                resume=resume
            )

            elapsed = time.time() - start_time
            self._log_separator()
            self.log(f"训练完成! 耗时: {elapsed:.0f} 秒 ({elapsed/60:.1f} 分钟)")
            self.log(f"模型保存在: {project}/{name}/")

            results_csv = os.path.join(project, name, "results.csv")
            if os.path.exists(results_csv):
                self.log("生成训练结果图表...")
                try:
                    from ultralytics.utils.plotting import plot_results
                    plot_results(file=results_csv)
                    self.log("训练结果图表已生成")
                except Exception as e:
                    self.log(f"图表生成失败: {e}")
            else:
                self.log(f"未找到结果文件: {results_csv}")

            self.root.after(0, lambda: messagebox.showinfo("训练完成",
                                                           f"训练已完成!\n耗时: {elapsed:.0f}秒\n"
                                                           f"模型: {project}/{name}/weights/best.pt"))

        except Exception as e:
            self.log(f"训练出错: {e}")
            import traceback
            self.log(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror("训练失败", str(e)))
        finally:
            self.root.after(0, self._on_training_end)

    def _on_training_end(self):
        self.is_training = False
        self.start_btn.config(state=tk.NORMAL)
        self.validate_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("就绪")

    def log(self, message):
        self.root.after(0, self._append_log, message)

    def _append_log(self, message):
        self.log_text.config(state=tk.NORMAL)
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _log_separator(self):
        self.log("-" * 50)

    def run(self):
        self._refresh_device_info()
        self.root.mainloop()


if __name__ == "__main__":
    print("=" * 60)
    print("YOLO 训练参数配置 GUI")
    print("=" * 60)
    print("功能:")
    print("  - 图形化配置所有训练参数")
    print("  - 参数类型与范围验证")
    print("  - 自动创建 data.yaml")
    print("  - 实时训练日志显示")
    print("  - 自动检测 GPU 设备")
    print("  - 文件选择对话框")
    print("=" * 60)

    app = TrainGUI()
    app.run()
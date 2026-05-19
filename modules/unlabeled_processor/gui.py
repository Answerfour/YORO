"""Unlabeled File Processor GUI Component"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from modules.unlabeled_processor.processor import UnlabeledProcessor
from datetime import datetime
import threading


class UnlabeledProcessorGUI(ttk.Frame):
    """Unlabeled File Processor GUI Component"""
    
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
        folder_frame = ttk.LabelFrame(parent, text="1. Select Main Folder", padding="10")
        folder_frame.pack(fill=tk.X, pady=5)
        
        dir_row = ttk.Frame(folder_frame)
        dir_row.pack(fill=tk.X)
        
        ttk.Label(dir_row, text="Main Folder Path:").pack(side=tk.LEFT, padx=5)
        self.folder_path_var = tk.StringVar()
        ttk.Entry(dir_row, textvariable=self.folder_path_var, width=60).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_row, text="Browse", command=self._select_folder).pack(side=tk.RIGHT, padx=5)
        
        self.folder_status_label = ttk.Label(folder_frame, text="", foreground="blue")
        self.folder_status_label.pack(anchor=tk.W, pady=5)
    
    def _create_process_options(self, parent):
        options_frame = ttk.LabelFrame(parent, text="2. Process Options", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        
        self.process_mode = tk.StringVar(value="move")
        
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(mode_frame, text="Move: Move files to unlabeled_files/", variable=self.process_mode, value="move").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(mode_frame, text="Delete: Remove files directly (requires confirmation)", variable=self.process_mode, value="delete").pack(side=tk.LEFT, padx=10)
        
        self.auto_save_report = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_frame, text="Auto save processing report",
                        variable=self.auto_save_report).pack(anchor=tk.W, padx=5)
    
    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(button_frame, text="▶ Start Processing", command=self._start_process)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self._cancel_process, state="disabled")
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(button_frame, text="Refresh Scan", command=self._scan_files)
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
    
    def _create_progress(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="Processing Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(progress_frame, text="")
        self.progress_label.pack(pady=5)
    
    def _create_results(self, parent):
        result_frame = ttk.LabelFrame(parent, text="Processing Results", padding="10")
        result_frame.pack(fill=tk.X, pady=5)
        
        result_grid = ttk.Frame(result_frame)
        result_grid.pack(fill=tk.X)
        
        ttk.Label(result_grid, text="Empty Labels:").grid(row=0, column=0, padx=10)
        self.empty_count_label = ttk.Label(result_grid, text="0", foreground="orange", font=('TkDefaultFont', 10, 'bold'))
        self.empty_count_label.grid(row=0, column=1, padx=10)
        
        ttk.Label(result_grid, text="Success:").grid(row=0, column=2, padx=10)
        self.success_count_label = ttk.Label(result_grid, text="0", foreground="green", font=('TkDefaultFont', 10, 'bold'))
        self.success_count_label.grid(row=0, column=3, padx=10)
        
        ttk.Label(result_grid, text="Failed:").grid(row=0, column=4, padx=10)
        self.failed_count_label = ttk.Label(result_grid, text="0", foreground="red", font=('TkDefaultFont', 10, 'bold'))
        self.failed_count_label.grid(row=0, column=5, padx=10)
    
    def _create_log(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Operation Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, wrap=tk.WORD, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self._log("Welcome to Unlabeled File Processor")
        self._log("Please select main folder. System will auto-detect images and labels subdirectories")
    
    def _select_folder(self):
        folder = filedialog.askdirectory(title="Select Main Folder (must contain images and labels subdirectories)")
        if folder:
            self.folder_path_var.set(folder)
            self._scan_files()
    
    def _scan_files(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("Warning", "Please select main folder first")
            return
        
        processor = UnlabeledProcessor(folder)
        valid, msg = processor.validate_folders()
        
        if not valid:
            self.folder_status_label.config(text=f"❌ {msg}", foreground="red")
            self.empty_count_label.config(text="0")
            self._log(f"Error: {msg}")
            return
        
        self.folder_status_label.config(text=f"✅ Folder structure valid", foreground="green")
        
        empty_labels = processor.find_empty_labels()
        self.empty_count_label.config(text=str(len(empty_labels)))
        
        self._log(f"Scan completed: Found {len(empty_labels)} empty label files")
        
        for label in empty_labels[:10]:
            self._log(f"  - {label}")
        
        if len(empty_labels) > 10:
            self._log(f"  ... {len(empty_labels) - 10} more files")
    
    def _start_process(self):
        folder = self.folder_path_var.get()
        if not folder:
            messagebox.showwarning("Warning", "Please select main folder first")
            return
        
        if self.process_mode.get() == "delete":
            if not messagebox.askyesno("Confirm Delete",
                                       "⚠️ Warning: This operation will permanently delete empty label files and their corresponding images!\n\n"
                                       "This operation cannot be undone. Continue?",
                                       icon='warning'):
                return
        
        self.processing = True
        self.start_btn.config(state="disabled")
        self.cancel_btn.config(state="normal")
        self.refresh_btn.config(state="disabled")
        
        self.log_text.delete(1.0, tk.END)
        self._log("Processing started...")
        
        thread = threading.Thread(target=self._process_worker, daemon=True)
        thread.start()
    
    def _process_worker(self):
        folder = self.folder_path_var.get()
        self.processor = UnlabeledProcessor(folder)
        
        valid, msg = self.processor.validate_folders()
        if not valid:
            self.after(0, lambda: self._log(f"Error: {msg}"))
            self._finish_process(0, 0)
            return
        
        self.processor.find_empty_labels()
        total = len(self.processor.empty_labels)
        self.after(0, lambda: self._log(f"Found {total} empty label files"))
        
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
        
        self._log(f"\nProcessing completed!")
        self._log(f"Success: {processed} | Failed: {failed}")
        
        if self.auto_save_report.get() and self.processor:
            report = self.processor.generate_report(processed, failed)
            success, path = self.processor.save_report(report)
            if success:
                self._log(f"Report saved: {path}")
            else:
                self._log(f"Failed to save report: {path}")
        
        self.processing = False
        self.start_btn.config(state="normal")
        self.cancel_btn.config(state="disabled")
        self.refresh_btn.config(state="normal")
        
        self.progress_var.set(0)
        self.progress_label.config(text="")
    
    def _cancel_process(self):
        if self.processor:
            self.processor.cancel()
            self._log("Cancelling operation...")
    
    def _log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.update_idletasks()
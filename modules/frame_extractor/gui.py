"""Video Frame Extraction Module GUI"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
from typing import Optional
from datetime import datetime
from modules.frame_extractor.extractor import FrameExtractor
from config.schema import FrameExtractorConfig
from utils.logger import Logger
from utils.thread_pool import ThreadPool
import threading


class FrameExtractorGUI(ttk.Frame):
    """Video Frame Extraction GUI Component"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.logger = Logger.get_instance()
        self.thread_pool = ThreadPool.get_instance()
        
        self.video_list = []
        self.videos_info = {}
        self.extraction_running = False
        self.current_video_index = 0
        
        self._create_widgets()
    
    def _create_widgets(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self._create_video_list(left_frame)
        self._create_settings(right_frame)
        self._create_progress(right_frame)
        self._create_buttons(right_frame)
        self._create_log(right_frame)
    
    def _create_video_list(self, parent):
        list_frame = ttk.LabelFrame(parent, text="Video List", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        btn_bar = ttk.Frame(list_frame)
        btn_bar.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Button(btn_bar, text="Add Videos", command=self._add_videos).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Add Folder", command=self._add_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Clear List", command=self._clear_list).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_bar, text="Remove Selected", command=self._remove_selected).pack(side=tk.LEFT, padx=2)
        
        self.video_info_label = ttk.Label(list_frame, text="0 videos", foreground="blue")
        self.video_info_label.pack(fill=tk.X, pady=(0, 5))
        
        scroll_y = ttk.Scrollbar(list_frame)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_listbox = tk.Listbox(list_frame, yscrollcommand=scroll_y.set,
                                        selectmode=tk.EXTENDED, height=12)
        self.video_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll_y.config(command=self.video_listbox.yview)
    
    def _create_settings(self, parent):
        output_frame = ttk.LabelFrame(parent, text="Output Settings", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        dir_row = ttk.Frame(output_frame)
        dir_row.pack(fill=tk.X, pady=5)
        ttk.Label(dir_row, text="Output Directory:").pack(side=tk.LEFT, padx=5)
        self.output_dir_var = tk.StringVar()
        ttk.Entry(dir_row, textvariable=self.output_dir_var, width=25).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(dir_row, text="Browse", command=self._select_output_dir).pack(side=tk.RIGHT, padx=5)
        
        time_frame = ttk.LabelFrame(parent, text="Time Range (seconds)", padding="10")
        time_frame.pack(fill=tk.X, pady=5)
        
        time_row = ttk.Frame(time_frame)
        time_row.pack()
        ttk.Label(time_row, text="Start:").pack(side=tk.LEFT, padx=5)
        self.start_time_var = tk.StringVar(value="0")
        ttk.Entry(time_row, textvariable=self.start_time_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(time_row, text="End:").pack(side=tk.LEFT, padx=5)
        self.end_time_var = tk.StringVar(value="10")
        ttk.Entry(time_row, textvariable=self.end_time_var, width=8).pack(side=tk.LEFT, padx=5)
        
        quick_frame = ttk.Frame(time_frame)
        quick_frame.pack(pady=5)
        ttk.Button(quick_frame, text="First 10s", command=lambda: self._set_time(0, 10)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="First 30s", command=lambda: self._set_time(0, 30)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="First 60s", command=lambda: self._set_time(0, 60)).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_frame, text="Full Video", command=self._set_full_time).pack(side=tk.LEFT, padx=2)
        
        param_frame = ttk.LabelFrame(parent, text="Extraction Parameters", padding="10")
        param_frame.pack(fill=tk.X, pady=5)
        
        param_row = ttk.Frame(param_frame)
        param_row.pack()
        ttk.Label(param_row, text="Sample FPS (frames/sec):").pack(side=tk.LEFT, padx=5)
        self.sample_fps_var = tk.StringVar(value="1")
        ttk.Entry(param_row, textvariable=self.sample_fps_var, width=8).pack(side=tk.LEFT, padx=5)
        
        format_row = ttk.Frame(param_frame)
        format_row.pack(pady=5)
        ttk.Label(format_row, text="Image Format:").pack(side=tk.LEFT, padx=5)
        self.output_format_var = tk.StringVar(value="jpg")
        ttk.Combobox(format_row, textvariable=self.output_format_var, values=["jpg", "png"], width=8, state="readonly").pack(side=tk.LEFT, padx=5)
        ttk.Label(format_row, text="JPEG Quality:").pack(side=tk.LEFT, padx=5)
        self.quality_var = tk.IntVar(value=95)
        ttk.Scale(format_row, from_=50, to=100, variable=self.quality_var, orient=tk.HORIZONTAL, length=120).pack(side=tk.LEFT, padx=5)
        ttk.Label(format_row, textvariable=self.quality_var, width=3).pack(side=tk.LEFT)
        
        naming_frame = ttk.LabelFrame(parent, text="File Naming Settings", padding="10")
        naming_frame.pack(fill=tk.X, pady=5)
        
        mode_frame = ttk.Frame(naming_frame)
        mode_frame.pack(fill=tk.X, pady=5)
        ttk.Label(mode_frame, text="Naming Mode:").pack(side=tk.LEFT, padx=5)
        self.naming_mode_var = tk.StringVar(value="sequence")
        ttk.Radiobutton(mode_frame, text="Sequence", variable=self.naming_mode_var, value="sequence").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Timestamp", variable=self.naming_mode_var, value="timestamp").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Custom Prefix", variable=self.naming_mode_var, value="custom").pack(side=tk.LEFT, padx=5)
        
        self.example_label = ttk.Label(naming_frame, text="Example: 000001.jpg", foreground="blue")
        self.example_label.pack(pady=5)
    
    def _create_progress(self, parent):
        progress_frame = ttk.LabelFrame(parent, text="Progress", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.IntVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X)
        
        self.current_video_label = ttk.Label(progress_frame, text="")
        self.current_video_label.pack(pady=5)
        
        self.status_text = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_text)
        self.status_label.pack()
    
    def _create_buttons(self, parent):
        button_frame = ttk.Frame(parent)
        button_frame.pack(pady=10)
        
        self.extract_btn = ttk.Button(button_frame, text="▶ Start Extraction", command=self._start_extraction, width=15)
        self.extract_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Stop", command=self._stop_extraction, width=8).pack(side=tk.LEFT, padx=5)
    
    def _create_log(self, parent):
        log_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        from ui.components import LogFrame
        self.log_frame = LogFrame(log_frame, height=8)
        self.log_frame.pack(fill=tk.BOTH, expand=True)
    
    def _add_videos(self):
        paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"), ("All Files", "*.*")]
        )
        for path in paths:
            if path not in self.video_list:
                self.video_list.append(path)
                self.video_listbox.insert(tk.END, os.path.basename(path))
                self._load_video_info_async(path)
        
        self._update_video_info_label()
    
    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        if folder:
            video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg'}
            added_count = 0
            for file in os.listdir(folder):
                if os.path.splitext(file)[1].lower() in video_extensions:
                    path = os.path.join(folder, file)
                    if path not in self.video_list:
                        self.video_list.append(path)
                        self.video_listbox.insert(tk.END, os.path.basename(path))
                        self._load_video_info_async(path)
                        added_count += 1
            
            self._update_video_info_label()
            self.log_frame.log(f"Added {added_count} videos from folder")
    
    def _load_video_info_async(self, path):
        def load():
            try:
                import cv2
            except ImportError:
                self.after(0, lambda: self.log_frame.log("Warning: OpenCV not installed, cannot load video info"))
                return
            
            try:
                cap = cv2.VideoCapture(path)
                if cap.isOpened():
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    duration = total_frames / fps if fps > 0 else 0
                    cap.release()
                    self.videos_info[path] = {'total_frames': total_frames, 'fps': fps, 'duration': duration}
                    self.after(0, lambda: self.log_frame.log(f"Loaded: {os.path.basename(path)} (Duration: {duration:.1f}s)"))
            except:
                pass
        
        threading.Thread(target=load, daemon=True).start()
    
    def _clear_list(self):
        self.video_list.clear()
        self.video_listbox.delete(0, tk.END)
        self.videos_info.clear()
        self._update_video_info_label()
        self.log_frame.log("Video list cleared")
    
    def _remove_selected(self):
        selected = self.video_listbox.curselection()
        for i in reversed(selected):
            path = self.video_list[i]
            self.video_list.pop(i)
            self.video_listbox.delete(i)
            if path in self.videos_info:
                del self.videos_info[path]
        self._update_video_info_label()
    
    def _update_video_info_label(self):
        count = len(self.video_list)
        total_duration = sum(info.get('duration', 0) for info in self.videos_info.values())
        self.video_info_label.config(text=f"{count} videos | Total Duration: {total_duration:.1f} sec")
    
    def _select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            self.log_frame.log(f"Output Directory: {directory}")
    
    def _set_time(self, start, end):
        self.start_time_var.set(str(start))
        self.end_time_var.set(str(end))
    
    def _set_full_time(self):
        if self.video_list and self.current_video_index < len(self.video_list):
            video_path = self.video_list[self.current_video_index]
            if video_path in self.videos_info:
                duration = self.videos_info[video_path]['duration']
                self.end_time_var.set(str(int(duration)))
                self.log_frame.log(f"Set to full duration: {duration:.1f}s")
    
    def _start_extraction(self):
        if not self.video_list:
            messagebox.showerror("Error", "Please add videos first")
            return
        
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("Error", "Please select output directory")
            return
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            test_file = os.path.join(output_dir, "_test.txt")
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            messagebox.showerror("Error", f"Output directory is not writable: {e}")
            return
        
        self.extraction_running = True
        self.extract_btn.config(state="disabled")
        threading.Thread(target=self._extraction_worker, daemon=True).start()
    
    def _extraction_worker(self):
        total_videos = len(self.video_list)
        total_frames_extracted = 0
        
        for i, video_path in enumerate(self.video_list):
            if not self.extraction_running:
                break
            
            self.after(0, lambda idx=i: self.current_video_label.config(text=f"Processing video {idx + 1}/{total_videos}"))
            
            config = FrameExtractorConfig(
                start_time=float(self.start_time_var.get()),
                end_time=float(self.end_time_var.get()),
                sample_fps=float(self.sample_fps_var.get()),
                output_format=self.output_format_var.get(),
                quality=self.quality_var.get(),
                naming_mode=self.naming_mode_var.get(),
                create_subfolder=True
            )
            
            extractor = FrameExtractor(video_path, config, self.output_dir_var.get())
            extractor.set_progress_callback(lambda c, t, m: self.after(0, lambda: self.progress_var.set(int(c/t*100) if t > 0 else 0)))
            extractor.set_message_callback(lambda m, l: self.after(0, lambda: self.log_frame.log(m)))
            
            success, count, errors = extractor.execute()
            total_frames_extracted += count
        
        self.after(0, lambda: self.extract_btn.config(state="normal"))
        self.after(0, lambda: self.extraction_running and self.log_frame.log(f"All completed! Total frames extracted: {total_frames_extracted}"))
        self.extraction_running = False
    
    def _stop_extraction(self):
        if self.extraction_running:
            self.extraction_running = False
            self.log_frame.log("⚠ Stop requested")
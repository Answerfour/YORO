"""Video Frame Extraction Module GUI - Workspace Style"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
from typing import Optional
from datetime import datetime

from modules.frame_extractor.extractor import FrameExtractor
from config.schema import FrameExtractorConfig
from ui.theme import Theme
from ui.enhanced_log import EnhancedLogFrame
from ui.task_overview import TaskOverviewBar
from ui.monitor_panel import MonitorPanel


# Status constants
STATUS_WAITING = 'waiting'
STATUS_RUNNING = 'running'
STATUS_DONE = 'done'
STATUS_ERROR = 'error'

STATUS_ICONS = {
    STATUS_WAITING: '○',
    STATUS_RUNNING: '▶',
    STATUS_DONE:   '✓',
    STATUS_ERROR:  '✗',
}


class FrameExtractorGUI(ttk.Frame):
    """Video Frame Extraction Workspace - Task-oriented UI"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # Data
        self.video_list = []          # List of full video paths
        self.videos_info = {}         # {path: {total_frames, fps, duration, width, height}}
        self.video_states = {}        # {path: {status, progress, frames_extracted}}
        self.extraction_running = False
        self.current_video_index = -1
        self._left_panel_visible = True
        
        self._create_widgets()
    
    # =========================================================================
    # UI CREATION
    # =========================================================================
    
    def _create_widgets(self):
        """Build the workspace layout"""
        c = Theme.DARK_COLORS
        
        # === TOP: Task Overview Bar ===
        self.task_overview = TaskOverviewBar(self)
        self.task_overview.pack(fill=tk.X, padx=0, pady=0)
        
        # === Separator ===
        tk.Frame(self, bg=c['border'], height=1).pack(fill=tk.X)
        
        # === MAIN VERTICAL PANED WINDOW (workspace top + log bottom) ===
        self.main_split = ttk.PanedWindow(self, orient=tk.VERTICAL)
        self.main_split.pack(fill=tk.BOTH, expand=True)
        
        # --- UPPER SECTION: Three-column workspace ---
        upper_frame = tk.Frame(self.main_split, bg=c['bg_primary'])
        
        self.workspace = ttk.PanedWindow(upper_frame, orient=tk.HORIZONTAL)
        self.workspace.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Video Task List
        self._left_panel = tk.Frame(self.workspace, bg=c['bg_primary'], width=220)
        self._build_video_list_panel(self._left_panel)
        self.workspace.add(self._left_panel, weight=1)
        
        # Center panel: Main Workspace
        self._center_panel = tk.Frame(self.workspace, bg=c['bg_primary'])
        self._build_main_workspace(self._center_panel)
        self.workspace.add(self._center_panel, weight=3)
        
        # Right panel: Monitor Dashboard
        self.monitor_panel = MonitorPanel(self.workspace)
        self.workspace.add(self.monitor_panel, weight=1)
        
        self.main_split.add(upper_frame, weight=7)
        
        # --- LOWER SECTION: Enhanced Log Area (30% default) ---
        self.log_panel = EnhancedLogFrame(self.main_split, height=12)
        self.main_split.add(self.log_panel, weight=3)
    
    # ---- LEFT PANEL: Video Task List ----
    
    def _build_video_list_panel(self, parent):
        """Build the left video task list panel"""
        c = Theme.DARK_COLORS
        
        # Header with collapse toggle
        header = tk.Frame(parent, bg=c['bg_secondary'], height=32)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="  Video Tasks", bg=c['bg_secondary'],
                fg=c['fg_primary'], font=Theme.FONTS['bold']).pack(side=tk.LEFT, padx=4)
        
        self._collapse_btn = tk.Button(
            header, text="◀", bg=c['bg_secondary'], fg=c['fg_secondary'],
            relief='flat', font=('Segoe UI', 8), cursor='hand2',
            activebackground=c['bg_hover'], activeforeground=c['fg_primary'],
            command=self._toggle_left_panel)
        self._collapse_btn.pack(side=tk.RIGHT, padx=4)
        
        # Search box
        search_frame = tk.Frame(parent, bg=c['bg_primary'])
        search_frame.pack(fill=tk.X, padx=6, pady=4)
        
        self._search_var = tk.StringVar()
        self._search_var.trace_add('write', lambda *_: self._filter_video_list())
        tk.Entry(search_frame, textvariable=self._search_var,
                bg=c['bg_tertiary'], fg=c['fg_primary'],
                insertbackground=c['fg_primary'], relief='flat',
                font=Theme.FONTS['normal']).pack(fill=tk.X, ipady=3)
        
        # Status filter
        filter_frame = tk.Frame(parent, bg=c['bg_primary'])
        filter_frame.pack(fill=tk.X, padx=6, pady=(0, 4))
        
        self._filter_var = tk.StringVar(value='All')
        filter_cb = ttk.Combobox(filter_frame, textvariable=self._filter_var,
                                values=['All', 'Waiting', 'Running', 'Done', 'Error'],
                                state='readonly', width=12)
        filter_cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        filter_cb.bind('<<ComboboxSelected>>', lambda e: self._filter_video_list())
        
        # Video count label
        self._video_count_label = tk.Label(parent, text="0 videos",
                                          bg=c['bg_primary'], fg=c['fg_secondary'],
                                          font=Theme.FONTS['normal'], anchor=tk.W)
        self._video_count_label.pack(fill=tk.X, padx=8, pady=(0, 2))
        
        # Treeview for video list
        tree_frame = tk.Frame(parent, bg=c['bg_primary'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=4)
        
        tree_style = ttk.Style()
        tree_style.configure('Video.Treeview',
                            background=c['bg_secondary'],
                            foreground=c['fg_primary'],
                            fieldbackground=c['bg_secondary'],
                            bordercolor=c['border'],
                            rowheight=30,
                            font=Theme.FONTS['normal'])
        tree_style.configure('Video.Treeview.Heading',
                            background=c['bg_tertiary'],
                            foreground=c['fg_primary'],
                            font=Theme.FONTS['bold'])
        tree_style.map('Video.Treeview',
                      background=[('selected', c['selection'])],
                      foreground=[('selected', c['selection_fg'])])
        
        self.video_tree = ttk.Treeview(
            tree_frame,
            columns=('status', 'progress'),
            show='tree headings',
            style='Video.Treeview',
            selectmode='browse',
            height=10
        )
        
        self.video_tree.heading('#0', text='Video', anchor=tk.W)
        self.video_tree.heading('status', text='Status', anchor=tk.CENTER)
        self.video_tree.heading('progress', text='Progress', anchor=tk.CENTER)
        
        self.video_tree.column('#0', width=140, minwidth=80, anchor=tk.W)
        self.video_tree.column('status', width=55, minwidth=50, anchor=tk.CENTER)
        self.video_tree.column('progress', width=50, minwidth=40, anchor=tk.CENTER)
        
        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=vsb.set)
        
        self.video_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.video_tree.bind('<<TreeviewSelect>>', self._on_video_select)
        
        # Bottom buttons
        btn_frame = tk.Frame(parent, bg=c['bg_primary'])
        btn_frame.pack(fill=tk.X, padx=4, pady=6)
        
        btn_row1 = tk.Frame(btn_frame, bg=c['bg_primary'])
        btn_row1.pack(fill=tk.X, pady=2)
        
        tk.Button(btn_row1, text="+ Add Videos", bg=c['bg_tertiary'], fg=c['fg_primary'],
                 relief='flat', padx=6, pady=3, font=Theme.FONTS['normal'], cursor='hand2',
                 activebackground=c['bg_hover'], command=self._add_videos
                 ).pack(side=tk.LEFT, padx=1, fill=tk.X, expand=True)
        
        tk.Button(btn_row1, text="+ Folder", bg=c['bg_tertiary'], fg=c['fg_primary'],
                 relief='flat', padx=6, pady=3, font=Theme.FONTS['normal'], cursor='hand2',
                 activebackground=c['bg_hover'], command=self._add_folder
                 ).pack(side=tk.RIGHT, padx=1)
        
        btn_row2 = tk.Frame(btn_frame, bg=c['bg_primary'])
        btn_row2.pack(fill=tk.X, pady=2)
        
        tk.Button(btn_row2, text="Remove", bg=c['bg_tertiary'], fg=c['fg_primary'],
                 relief='flat', padx=6, pady=3, font=Theme.FONTS['normal'], cursor='hand2',
                 activebackground=c['bg_hover'], command=self._remove_selected
                 ).pack(side=tk.LEFT, padx=1)
        
        tk.Button(btn_row2, text="Clear All", bg=c['bg_tertiary'], fg=c['fg_primary'],
                 relief='flat', padx=6, pady=3, font=Theme.FONTS['normal'], cursor='hand2',
                 activebackground=c['bg_hover'], command=self._clear_list
                 ).pack(side=tk.RIGHT, padx=1)
    
    # ---- CENTER PANEL: Main Workspace ----
    
    def _build_main_workspace(self, parent):
        """Build the center main workspace panel"""
        c = Theme.DARK_COLORS
        
        # Canvas for scrolling
        canvas = tk.Canvas(parent, bg=c['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        self._center_inner = tk.Frame(canvas, bg=c['bg_primary'])
        
        self._center_inner.bind('<Configure>',
                               lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=self._center_inner, anchor=tk.NW, width=400)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        canvas.bind_all('<MouseWheel>', _on_mousewheel, add='+')
        
        inner = self._center_inner
        
        # -- Section: Current Video Header --
        video_header = tk.Frame(inner, bg=c['bg_secondary'], padx=12, pady=8)
        video_header.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        tk.Label(video_header, text="Current Video",
                bg=c['bg_secondary'], fg=c['fg_secondary'],
                font=Theme.FONTS['bold']).pack(anchor=tk.W)
        
        self._current_video_name = tk.Label(
            video_header, text="No video selected",
            bg=c['bg_secondary'], fg=c['fg_primary'],
            font=Theme.FONTS['large'], anchor=tk.W, wraplength=400)
        self._current_video_name.pack(anchor=tk.W, pady=(2, 0))
        
        # -- Section: Video Info Grid --
        info_card = tk.Frame(inner, bg=c['bg_secondary'], padx=12, pady=8)
        info_card.pack(fill=tk.X, padx=8, pady=4)
        
        tk.Label(info_card, text="Video Information",
                bg=c['bg_secondary'], fg=c['fg_secondary'],
                font=Theme.FONTS['bold']).pack(anchor=tk.W, pady=(0, 4))
        
        info_grid = tk.Frame(info_card, bg=c['bg_secondary'])
        info_grid.pack(fill=tk.X)
        
        self._info_labels = {}
        info_items = [
            ('duration',   'Duration',    '--'),
            ('fps',        'FPS',         '--'),
            ('frames',     'Total Frames','--'),
            ('resolution', 'Resolution',  '--'),
        ]
        
        for i, (key, label, default) in enumerate(info_items):
            col = i % 2
            row = i // 2
            cell = tk.Frame(info_grid, bg=c['bg_secondary'])
            cell.grid(row=row, column=col, sticky='w', padx=(0, 16), pady=2)
            
            tk.Label(cell, text=label, bg=c['bg_secondary'],
                    fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(anchor=tk.W)
            val = tk.Label(cell, text=default, bg=c['bg_secondary'],
                          fg=c['fg_primary'], font=('Consolas', 10))
            val.pack(anchor=tk.W)
            self._info_labels[key] = val
        
        # -- Section: Frame Preview --
        preview_card = tk.Frame(inner, bg=c['bg_secondary'], padx=12, pady=8)
        preview_card.pack(fill=tk.X, padx=8, pady=4)
        
        tk.Label(preview_card, text="Frame Preview",
                bg=c['bg_secondary'], fg=c['fg_secondary'],
                font=Theme.FONTS['bold']).pack(anchor=tk.W, pady=(0, 4))
        
        self._preview_canvas = tk.Canvas(preview_card, bg=c['bg_tertiary'],
                                        width=380, height=214, highlightthickness=0)
        self._preview_canvas.pack(fill=tk.X)
        self._preview_canvas.create_text(
            190, 107, text="No preview available",
            fill=c['fg_secondary'], font=Theme.FONTS['normal'])
        
        # -- Section: Settings --
        self._build_settings_section(inner)
        
        # -- Section: Action Buttons --
        action_frame = tk.Frame(inner, bg=c['bg_primary'])
        action_frame.pack(fill=tk.X, padx=8, pady=(8, 12))
        
        self.extract_btn = tk.Button(
            action_frame, text="▶  Start Extraction",
            bg=c['accent'], fg='#FFFFFF', relief='flat', padx=16, pady=8,
            font=Theme.FONTS['bold'], cursor='hand2',
            activebackground=c['accent_hover'], command=self._start_extraction)
        self.extract_btn.pack(side=tk.LEFT, padx=4)
        
        self.stop_btn = tk.Button(
            action_frame, text="■  Stop",
            bg=c['danger'], fg='#FFFFFF', relief='flat', padx=16, pady=8,
            font=Theme.FONTS['bold'], cursor='hand2',
            activebackground='#E57373', command=self._stop_extraction,
            state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=4)
    
    def _build_settings_section(self, parent):
        """Build the collapsible settings section in center panel"""
        c = Theme.DARK_COLORS
        
        settings_card = tk.Frame(parent, bg=c['bg_secondary'], padx=12, pady=8)
        settings_card.pack(fill=tk.X, padx=8, pady=4)
        
        tk.Label(settings_card, text="Extraction Settings",
                bg=c['bg_secondary'], fg=c['fg_secondary'],
                font=Theme.FONTS['bold']).pack(anchor=tk.W, pady=(0, 6))
        
        # -- Output Directory --
        out_frame = tk.Frame(settings_card, bg=c['bg_secondary'])
        out_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(out_frame, text="Output Directory:",
                bg=c['bg_secondary'], fg=c['fg_primary'],
                font=Theme.FONTS['normal']).pack(anchor=tk.W)
        
        out_row = tk.Frame(out_frame, bg=c['bg_secondary'])
        out_row.pack(fill=tk.X, pady=2)
        
        self.output_dir_var = tk.StringVar()
        tk.Entry(out_row, textvariable=self.output_dir_var,
                bg=c['bg_tertiary'], fg=c['fg_primary'],
                insertbackground=c['fg_primary'], relief='flat',
                font=Theme.FONTS['normal']).pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        
        tk.Button(out_row, text="Browse", bg=c['bg_tertiary'], fg=c['fg_primary'],
                 relief='flat', padx=8, font=Theme.FONTS['normal'], cursor='hand2',
                 activebackground=c['bg_hover'], command=self._select_output_dir
                 ).pack(side=tk.RIGHT, padx=(4, 0))
        
        # -- Time Range --
        time_frame = tk.Frame(settings_card, bg=c['bg_secondary'])
        time_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(time_frame, text="Time Range (seconds):",
                bg=c['bg_secondary'], fg=c['fg_primary'],
                font=Theme.FONTS['normal']).pack(anchor=tk.W)
        
        time_row = tk.Frame(time_frame, bg=c['bg_secondary'])
        time_row.pack(fill=tk.X, pady=2)
        
        tk.Label(time_row, text="Start:", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT)
        self.start_time_var = tk.StringVar(value="0")
        tk.Entry(time_row, textvariable=self.start_time_var, width=7,
                bg=c['bg_tertiary'], fg=c['fg_primary'],
                insertbackground=c['fg_primary'], relief='flat',
                font=Theme.FONTS['mono']).pack(side=tk.LEFT, padx=4, ipady=2)
        
        tk.Label(time_row, text="End:", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT, padx=(8, 0))
        self.end_time_var = tk.StringVar(value="10")
        tk.Entry(time_row, textvariable=self.end_time_var, width=7,
                bg=c['bg_tertiary'], fg=c['fg_primary'],
                insertbackground=c['fg_primary'], relief='flat',
                font=Theme.FONTS['mono']).pack(side=tk.LEFT, padx=4, ipady=2)
        
        # Quick time buttons
        quick_frame = tk.Frame(time_frame, bg=c['bg_secondary'])
        quick_frame.pack(fill=tk.X, pady=2)
        
        qbtn_cfg = {'bg': c['bg_tertiary'], 'fg': c['fg_secondary'], 'relief': 'flat',
                     'padx': 6, 'pady': 2, 'font': Theme.FONTS['normal'], 'cursor': 'hand2',
                     'activebackground': c['bg_hover']}
        
        tk.Button(quick_frame, text="10s", command=lambda: self._set_time(0, 10),
                 **qbtn_cfg).pack(side=tk.LEFT, padx=1)
        tk.Button(quick_frame, text="30s", command=lambda: self._set_time(0, 30),
                 **qbtn_cfg).pack(side=tk.LEFT, padx=1)
        tk.Button(quick_frame, text="60s", command=lambda: self._set_time(0, 60),
                 **qbtn_cfg).pack(side=tk.LEFT, padx=1)
        tk.Button(quick_frame, text="Full", command=self._set_full_time,
                 **qbtn_cfg).pack(side=tk.LEFT, padx=1)
        
        # -- Extraction Parameters --
        param_frame = tk.Frame(settings_card, bg=c['bg_secondary'])
        param_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(param_frame, text="Parameters:",
                bg=c['bg_secondary'], fg=c['fg_primary'],
                font=Theme.FONTS['normal']).pack(anchor=tk.W)
        
        param_row = tk.Frame(param_frame, bg=c['bg_secondary'])
        param_row.pack(fill=tk.X, pady=2)
        
        tk.Label(param_row, text="Sample FPS:", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT)
        self.sample_fps_var = tk.StringVar(value="1")
        tk.Entry(param_row, textvariable=self.sample_fps_var, width=5,
                bg=c['bg_tertiary'], fg=c['fg_primary'],
                insertbackground=c['fg_primary'], relief='flat',
                font=Theme.FONTS['mono']).pack(side=tk.LEFT, padx=4, ipady=2)
        
        tk.Label(param_row, text="Format:", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT, padx=(12, 0))
        self.output_format_var = tk.StringVar(value="jpg")
        ttk.Combobox(param_row, textvariable=self.output_format_var,
                    values=["jpg", "png"], width=5, state="readonly"
                    ).pack(side=tk.LEFT, padx=4)
        
        # Quality
        quality_row = tk.Frame(param_frame, bg=c['bg_secondary'])
        quality_row.pack(fill=tk.X, pady=2)
        
        tk.Label(quality_row, text="JPEG Quality:", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT)
        self.quality_var = tk.IntVar(value=95)
        self._quality_display = tk.Label(quality_row, textvariable=self.quality_var,
                                        bg=c['bg_secondary'], fg=c['accent'],
                                        font=('Consolas', 9), width=3)
        self._quality_display.pack(side=tk.RIGHT)
        ttk.Scale(quality_row, from_=50, to=100, variable=self.quality_var,
                 orient=tk.HORIZONTAL, length=150).pack(side=tk.RIGHT, padx=4)
        
        # -- Naming Mode --
        naming_frame = tk.Frame(settings_card, bg=c['bg_secondary'])
        naming_frame.pack(fill=tk.X, pady=3)
        
        tk.Label(naming_frame, text="File Naming:",
                bg=c['bg_secondary'], fg=c['fg_primary'],
                font=Theme.FONTS['normal']).pack(anchor=tk.W)
        
        naming_row = tk.Frame(naming_frame, bg=c['bg_secondary'])
        naming_row.pack(fill=tk.X, pady=2)
        
        self.naming_mode_var = tk.StringVar(value="sequence")
        rb_cfg = {'bg': c['bg_secondary'], 'fg': c['fg_primary'],
                 'activebackground': c['bg_secondary'], 'activeforeground': c['accent'],
                 'selectcolor': c['bg_tertiary'], 'font': Theme.FONTS['normal']}
        
        tk.Radiobutton(naming_row, text="Sequence", variable=self.naming_mode_var,
                      value="sequence", **rb_cfg).pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(naming_row, text="Timestamp", variable=self.naming_mode_var,
                      value="timestamp", **rb_cfg).pack(side=tk.LEFT, padx=2)
        tk.Radiobutton(naming_row, text="Custom", variable=self.naming_mode_var,
                      value="custom", **rb_cfg).pack(side=tk.LEFT, padx=2)
        
        self.example_label = tk.Label(naming_frame, text="Example: 000001.jpg",
                                     bg=c['bg_secondary'], fg=c['info'],
                                     font=Theme.FONTS['mono_small'])
        self.example_label.pack(anchor=tk.W, pady=(2, 0))
    
    # =========================================================================
    # VIDEO LIST OPERATIONS
    # =========================================================================
    
    def _add_videos(self):
        paths = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv"), ("All Files", "*.*")]
        )
        added = 0
        for path in paths:
            if path not in self.video_list:
                self.video_list.append(path)
                self.video_states[path] = {'status': STATUS_WAITING, 'progress': 0, 'frames': 0}
                self._add_video_to_tree(path)
                self._load_video_info_async(path)
                added += 1
        
        self._update_counts()
        if added:
            self.log_panel.log(f"Added {added} video(s) to task list", 'info')
    
    def _add_folder(self):
        folder = filedialog.askdirectory(title="Select Folder with Videos")
        if not folder:
            return
        
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg'}
        added = 0
        for file in sorted(os.listdir(folder)):
            if os.path.splitext(file)[1].lower() in video_extensions:
                path = os.path.join(folder, file)
                if path not in self.video_list:
                    self.video_list.append(path)
                    self.video_states[path] = {'status': STATUS_WAITING, 'progress': 0, 'frames': 0}
                    self._add_video_to_tree(path)
                    self._load_video_info_async(path)
                    added += 1
        
        self._update_counts()
        self.log_panel.log(f"Added {added} videos from folder", 'info')
    
    def _add_video_to_tree(self, path):
        """Add a video entry to the treeview"""
        name = os.path.basename(path)
        # Truncate long names
        if len(name) > 22:
            name = name[:10] + '...' + name[-9:]
        
        self.video_tree.insert('', tk.END, iid=path,
                              text=f" {name}",
                              values=(STATUS_ICONS[STATUS_WAITING], '0%'))
    
    def _remove_selected(self):
        selected = self.video_tree.selection()
        if not selected:
            return
        for iid in selected:
            if iid in self.video_list:
                self.video_list.remove(iid)
            self.video_states.pop(iid, None)
            self.videos_info.pop(iid, None)
            self.video_tree.delete(iid)
        self._update_counts()
        self.log_panel.log("Removed selected video(s)", 'info')
    
    def _clear_list(self):
        self.video_list.clear()
        self.videos_info.clear()
        self.video_states.clear()
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        self._update_counts()
        self._clear_video_info_display()
        self.log_panel.log("Video list cleared", 'info')
    
    def _on_video_select(self, event):
        """Handle video selection in treeview"""
        selected = self.video_tree.selection()
        if not selected:
            return
        
        path = selected[0]
        self.current_video_index = self.video_list.index(path) if path in self.video_list else -1
        self._display_video_info(path)
    
    def _display_video_info(self, path):
        """Update center panel with selected video info"""
        name = os.path.basename(path)
        self._current_video_name.config(text=name)
        
        info = self.videos_info.get(path, {})
        if info:
            duration = info.get('duration', 0)
            fps = info.get('fps', 0)
            frames = info.get('total_frames', 0)
            width = info.get('width', 0)
            height = info.get('height', 0)
            
            self._info_labels['duration'].config(text=f"{duration:.1f} sec")
            self._info_labels['fps'].config(text=f"{fps:.2f}")
            self._info_labels['frames'].config(text=f"{frames:,}")
            self._info_labels['resolution'].config(text=f"{width}x{height}" if width else "--")
        else:
            self._info_labels['duration'].config(text="Loading...")
            self._info_labels['fps'].config(text="--")
            self._info_labels['frames'].config(text="--")
            self._info_labels['resolution'].config(text="--")
    
    def _clear_video_info_display(self):
        """Clear the video info display"""
        self._current_video_name.config(text="No video selected")
        for key in self._info_labels:
            self._info_labels[key].config(text="--")
    
    def _filter_video_list(self):
        """Filter treeview based on search and status filter"""
        search = self._search_var.get().lower().strip()
        status_filter = self._filter_var.get().lower()
        
        # Detach all items first
        for item in self.video_tree.get_children():
            self.video_tree.detach(item)
        
        # Re-insert matching items
        for path in self.video_list:
            name = os.path.basename(path).lower()
            state = self.video_states.get(path, {}).get('status', STATUS_WAITING)
            
            # Search filter
            if search and search not in name:
                continue
            
            # Status filter
            if status_filter != 'all' and state != status_filter:
                continue
            
            self.video_tree.reattach(path, '', tk.END)
    
    def _update_counts(self):
        """Update all count displays"""
        total = len(self.video_list)
        running = sum(1 for s in self.video_states.values() if s['status'] == STATUS_RUNNING)
        done = sum(1 for s in self.video_states.values() if s['status'] == STATUS_DONE)
        failed = sum(1 for s in self.video_states.values() if s['status'] == STATUS_ERROR)
        
        self.task_overview.update_stats(total=total, running=running,
                                       completed=done, failed=failed)
        self._video_count_label.config(text=f"{total} video(s)")
    
    def _update_tree_item(self, path, status=None, progress=None):
        """Update a single tree item's display"""
        if not self.video_tree.exists(path):
            return
        
        current_vals = self.video_tree.item(path, 'values')
        state = self.video_states.get(path, {})
        
        s = status if status else state.get('status', STATUS_WAITING)
        p = progress if progress is not None else state.get('progress', 0)
        
        icon = STATUS_ICONS.get(s, '○')
        pct_text = f"{int(p)}%"
        
        self.video_tree.item(path, values=(icon, pct_text))
    
    # =========================================================================
    # VIDEO INFO LOADING
    # =========================================================================
    
    def _load_video_info_async(self, path):
        """Load video info in background thread"""
        def load():
            try:
                import cv2
            except ImportError:
                self.after(0, lambda: self.log_panel.log(
                    "Warning: OpenCV not installed, cannot load video info", 'warning'))
                return
            
            try:
                cap = cv2.VideoCapture(path)
                if cap.isOpened():
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    duration = total_frames / fps if fps > 0 else 0
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                    
                    info = {
                        'total_frames': total_frames, 'fps': fps,
                        'duration': duration, 'width': width, 'height': height
                    }
                    self.videos_info[path] = info
                    
                    self.after(0, lambda: self.log_panel.log(
                        f"Loaded: {os.path.basename(path)} ({duration:.1f}s, {width}x{height})",
                        'success'))
                    
                    # Update display if this video is currently selected
                    selected = self.video_tree.selection()
                    if selected and selected[0] == path:
                        self.after(0, lambda: self._display_video_info(path))
            except Exception as e:
                self.after(0, lambda: self.log_panel.log(
                    f"Failed to load info for {os.path.basename(path)}: {e}", 'error'))
        
        threading.Thread(target=load, daemon=True).start()
    
    # =========================================================================
    # EXTRACTION
    # =========================================================================
    
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
        
        # Reset states
        for path in self.video_list:
            self.video_states[path] = {'status': STATUS_WAITING, 'progress': 0, 'frames': 0}
            self._update_tree_item(path, status=STATUS_WAITING, progress=0)
        
        self.extraction_running = True
        self.extract_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.monitor_panel.set_status('running', 'Starting extraction...')
        self.log_panel.log("Starting batch extraction...", 'info')
        
        threading.Thread(target=self._extraction_worker, daemon=True).start()
    
    def _extraction_worker(self):
        total_videos = len(self.video_list)
        total_frames_extracted = 0
        videos_completed = 0
        videos_failed = 0
        
        self.after(0, lambda: self.monitor_panel.update_stats(
            extracted=0, videos_done=0, videos_total=total_videos))
        
        for i, video_path in enumerate(self.video_list):
            if not self.extraction_running:
                self.after(0, lambda: self.log_panel.log("Extraction stopped by user", 'warning'))
                break
            
            # Update current video state
            self.video_states[video_path]['status'] = STATUS_RUNNING
            self.video_states[video_path]['progress'] = 0
            
            self.after(0, lambda p=video_path: self._update_tree_item(p, STATUS_RUNNING, 0))
            self.after(0, lambda p=video_path, idx=i: self._on_extraction_video_change(p, idx))
            self.after(0, lambda p=video_path, idx=i, t=total_videos:
                      self.monitor_panel.set_status('running',
                                                   f"Processing {idx+1}/{t}: {os.path.basename(p)}"))
            self.after(0, lambda idx=i, t=total_videos:
                      self.task_overview.update_stats(running=1, completed=videos_completed,
                                                     failed=videos_failed))
            
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
            
            # Progress callback
            def on_progress(current, total, msg, vp=video_path):
                if total > 0:
                    pct = int(current / total * 100)
                    self.video_states[vp]['progress'] = pct
                    self.after(0, lambda c=current, t=total, p=pct, v=vp:
                              self._update_extraction_progress(c, t, p, v))
            
            # Message callback
            def on_message(msg, level, vp=video_path):
                self.after(0, lambda m=msg, l=level: self.log_panel.log(m, l))
            
            extractor.set_progress_callback(on_progress)
            extractor.set_message_callback(on_message)
            
            success, count, errors = extractor.execute()
            
            total_frames_extracted += count
            
            if success:
                self.video_states[video_path]['status'] = STATUS_DONE
                self.video_states[video_path]['progress'] = 100
                self.video_states[video_path]['frames'] = count
                videos_completed += 1
                self.after(0, lambda p=video_path: self._update_tree_item(p, STATUS_DONE, 100))
                self.after(0, lambda c=count: self.log_panel.log(
                    f"Completed: {count} frames extracted", 'success'))
            else:
                self.video_states[video_path]['status'] = STATUS_ERROR
                videos_failed += 1
                self.after(0, lambda p=video_path: self._update_tree_item(p, STATUS_ERROR, 0))
                self.after(0, lambda errs=errors: self.log_panel.log(
                    f"Failed: {errs[0] if errs else 'Unknown error'}", 'error'))
            
            self.after(0, lambda vc=videos_completed, vf=videos_failed, tv=total_videos,
                      te=total_frames_extracted:
                      self.monitor_panel.update_stats(extracted=te, videos_done=vc, videos_total=tv))
            self.after(0, lambda vc=videos_completed, vf=videos_failed:
                      self.task_overview.update_stats(running=0, completed=vc, failed=vf))
        
        # Final state
        self.extraction_running = False
        self.after(0, lambda: self.extract_btn.config(state=tk.NORMAL))
        self.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
        
        if videos_completed > 0:
            self.after(0, lambda vc=videos_completed, te=total_frames_extracted:
                      self.monitor_panel.set_status('completed',
                                                   f"{vc} videos done, {te} frames total"))
            self.after(0, lambda te=total_frames_extracted:
                      self.log_panel.log(f"Batch complete! Total: {te} frames from {videos_completed} videos",
                                        'success'))
        elif not self.extraction_running:
            self.after(0, lambda: self.monitor_panel.set_status('stopped', 'User interrupted'))
        else:
            self.after(0, lambda: self.monitor_panel.set_status('error', 'All tasks failed'))
    
    def _on_extraction_video_change(self, path, index):
        """Update UI when starting a new video in batch"""
        self._display_video_info(path)
    
    def _update_extraction_progress(self, current, total, pct, video_path):
        """Update progress displays during extraction"""
        self.monitor_panel.update_progress(current, total)
        self._update_tree_item(video_path, progress=pct)
    
    def _stop_extraction(self):
        if self.extraction_running:
            self.extraction_running = False
            self.log_panel.log("Stop requested - will halt after current video", 'warning')
            self.stop_btn.config(state=tk.DISABLED)
    
    # =========================================================================
    # SETTINGS HELPERS
    # =========================================================================
    
    def _select_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
            self.log_panel.log(f"Output directory: {directory}", 'info')
    
    def _set_time(self, start, end):
        self.start_time_var.set(str(start))
        self.end_time_var.set(str(end))
    
    def _set_full_time(self):
        if self.video_list and self.current_video_index >= 0:
            video_path = self.video_list[self.current_video_index]
            if video_path in self.videos_info:
                duration = self.videos_info[video_path]['duration']
                self.end_time_var.set(str(int(duration)))
                self.log_panel.log(f"Set to full duration: {duration:.1f}s", 'info')
    
    # =========================================================================
    # LEFT PANEL TOGGLE
    # =========================================================================
    
    def _toggle_left_panel(self):
        """Toggle visibility of the left video list panel"""
        if self._left_panel_visible:
            self.workspace.forget(self._left_panel)
            self._left_panel_visible = False
            self._collapse_btn.config(text="▶")
        else:
            self.workspace.insert(0, self._left_panel, weight=1)
            self._left_panel_visible = True
            self._collapse_btn.config(text="◀")
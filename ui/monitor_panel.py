"""Monitor Panel - Right-side dashboard with status, progress, stats, and system info"""
import tkinter as tk
from tkinter import ttk
from ui.theme import Theme
import time


class MonitorPanel(tk.Frame):
    """Right-side monitoring dashboard panel"""
    
    def __init__(self, parent, **kwargs):
        c = Theme.DARK_COLORS
        super().__init__(parent, bg=c['bg_primary'], **kwargs)
        
        # Internal state
        self._start_time = None
        self._total_frames = 0
        self._processed_frames = 0
        
        # Optional psutil
        self._psutil_available = False
        try:
            import psutil
            self._psutil_available = True
        except ImportError:
            pass
        
        self._create_ui()
        
        # Start system monitor update loop
        if self._psutil_available:
            self._update_system_stats()
    
    def _create_ui(self):
        """Create the dashboard UI"""
        c = Theme.DARK_COLORS
        
        # Title
        title_frame = tk.Frame(self, bg=c['bg_primary'])
        title_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
        
        tk.Label(title_frame, text="Task Monitor",
                bg=c['bg_primary'], fg=c['accent'],
                font=Theme.FONTS['bold']).pack(side=tk.LEFT)
        
        # Status indicator dot
        self._status_dot = tk.Label(title_frame, text="●", 
                                   bg=c['bg_primary'], fg=c['waiting'],
                                   font=('Segoe UI', 10))
        self._status_dot.pack(side=tk.RIGHT, padx=4)
        self._status_text = tk.Label(title_frame, text="Idle",
                                    bg=c['bg_primary'], fg=c['fg_secondary'],
                                    font=Theme.FONTS['normal'])
        self._status_text.pack(side=tk.RIGHT)
        
        # Scrollable content area
        content = tk.Frame(self, bg=c['bg_primary'])
        content.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        # Create cards
        self._status_card = self._create_status_card(content)
        self._status_card.pack(fill=tk.X, padx=4, pady=4)
        
        self._progress_card = self._create_progress_card(content)
        self._progress_card.pack(fill=tk.X, padx=4, pady=4)
        
        self._stats_card = self._create_stats_card(content)
        self._stats_card.pack(fill=tk.X, padx=4, pady=4)
        
        if self._psutil_available:
            self._system_card = self._create_system_card(content)
            self._system_card.pack(fill=tk.X, padx=4, pady=4)
        
        # Spacer to push cards to top
        tk.Frame(content, bg=c['bg_primary']).pack(fill=tk.BOTH, expand=True)
    
    def _create_card_frame(self, parent, title: str):
        """Create a styled card frame"""
        c = Theme.DARK_COLORS
        
        card = tk.Frame(parent, bg=c['bg_secondary'], padx=10, pady=8)
        
        # Card title
        tk.Label(card, text=title,
                bg=c['bg_secondary'], fg=c['fg_secondary'],
                font=Theme.FONTS['bold']).pack(anchor=tk.W, pady=(0, 6))
        
        # Separator
        tk.Frame(card, bg=c['border'], height=1).pack(fill=tk.X, pady=(0, 6))
        
        return card
    
    def _create_status_card(self, parent):
        """Status card - shows current running state"""
        c = Theme.DARK_COLORS
        card = self._create_card_frame(parent, "Status")
        
        # Status display
        status_row = tk.Frame(card, bg=c['bg_secondary'])
        status_row.pack(fill=tk.X, pady=2)
        
        self._status_icon = tk.Label(status_row, text="○",
                                    bg=c['bg_secondary'], fg=c['waiting'],
                                    font=('Segoe UI', 16))
        self._status_icon.pack(side=tk.LEFT, padx=(0, 8))
        
        status_info = tk.Frame(status_row, bg=c['bg_secondary'])
        status_info.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self._status_label = tk.Label(status_info, text="Waiting",
                                     bg=c['bg_secondary'], fg=c['fg_primary'],
                                     font=Theme.FONTS['large'])
        self._status_label.pack(anchor=tk.W)
        
        self._status_detail = tk.Label(status_info, text="No active task",
                                      bg=c['bg_secondary'], fg=c['fg_secondary'],
                                      font=Theme.FONTS['normal'])
        self._status_detail.pack(anchor=tk.W)
        
        return card
    
    def _create_progress_card(self, parent):
        """Progress card - frame progress with bar"""
        c = Theme.DARK_COLORS
        card = self._create_card_frame(parent, "Progress")
        
        # Frame counter
        frame_row = tk.Frame(card, bg=c['bg_secondary'])
        frame_row.pack(fill=tk.X, pady=2)
        
        tk.Label(frame_row, text="Current Frame",
                bg=c['bg_secondary'], fg=c['fg_secondary'],
                font=Theme.FONTS['normal']).pack(anchor=tk.W)
        
        self._frame_label = tk.Label(frame_row, text="0 / 0",
                                    bg=c['bg_secondary'], fg=c['fg_primary'],
                                    font=('Consolas', 12, 'bold'))
        self._frame_label.pack(anchor=tk.W)
        
        # Progress bar
        bar_frame = tk.Frame(card, bg=c['bg_secondary'])
        bar_frame.pack(fill=tk.X, pady=(6, 2))
        
        self._progress_var = tk.DoubleVar(value=0)
        self._progress_bar = ttk.Progressbar(bar_frame, variable=self._progress_var,
                                            maximum=100, length=200)
        self._progress_bar.pack(fill=tk.X, side=tk.LEFT, expand=True)
        
        self._progress_pct = tk.Label(bar_frame, text="0%",
                                     bg=c['bg_secondary'], fg=c['accent'],
                                     font=Theme.FONTS['bold'], width=5)
        self._progress_pct.pack(side=tk.RIGHT, padx=(6, 0))
        
        return card
    
    def _create_stats_card(self, parent):
        """Stats card - extraction statistics"""
        c = Theme.DARK_COLORS
        card = self._create_card_frame(parent, "Statistics")
        
        # Stats rows
        self._stat_labels = {}
        stats_items = [
            ('extracted', 'Frames Extracted', '0'),
            ('videos_done', 'Videos Completed', '0 / 0'),
            ('elapsed', 'Elapsed Time', '00:00:00'),
            ('remaining', 'Est. Remaining', '--:--:--'),
        ]
        
        for key, label, default in stats_items:
            row = tk.Frame(card, bg=c['bg_secondary'])
            row.pack(fill=tk.X, pady=1)
            
            tk.Label(row, text=label,
                    bg=c['bg_secondary'], fg=c['fg_secondary'],
                    font=Theme.FONTS['normal']).pack(side=tk.LEFT)
            
            val_label = tk.Label(row, text=default,
                               bg=c['bg_secondary'], fg=c['fg_primary'],
                               font=('Consolas', 9, 'bold'))
            val_label.pack(side=tk.RIGHT)
            self._stat_labels[key] = val_label
        
        return card
    
    def _create_system_card(self, parent):
        """System card - CPU/Memory usage"""
        c = Theme.DARK_COLORS
        card = self._create_card_frame(parent, "System")
        
        # CPU
        cpu_row = tk.Frame(card, bg=c['bg_secondary'])
        cpu_row.pack(fill=tk.X, pady=1)
        tk.Label(cpu_row, text="CPU", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT)
        self._cpu_label = tk.Label(cpu_row, text="--%", bg=c['bg_secondary'],
                                  fg=c['fg_primary'], font=('Consolas', 9, 'bold'))
        self._cpu_label.pack(side=tk.RIGHT)
        
        # Memory
        mem_row = tk.Frame(card, bg=c['bg_secondary'])
        mem_row.pack(fill=tk.X, pady=1)
        tk.Label(mem_row, text="Memory", bg=c['bg_secondary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT)
        self._mem_label = tk.Label(mem_row, text="-- / -- GB", bg=c['bg_secondary'],
                                  fg=c['fg_primary'], font=('Consolas', 9, 'bold'))
        self._mem_label.pack(side=tk.RIGHT)
        
        return card
    
    # ---- Public API ----
    
    def set_status(self, status: str, detail: str = ""):
        """Update task status display"""
        c = Theme.DARK_COLORS
        
        status_lower = status.lower()
        color_map = {
            'idle': (c['waiting'], '○', 'Idle'),
            'waiting': (c['waiting'], '○', 'Waiting'),
            'running': (c['running'], '▶', 'Running'),
            'processing': (c['running'], '▶', 'Processing'),
            'completed': (c['success'], '✓', 'Completed'),
            'success': (c['success'], '✓', 'Completed'),
            'failed': (c['danger'], '✗', 'Failed'),
            'error': (c['danger'], '✗', 'Error'),
            'stopped': (c['warning'], '■', 'Stopped'),
            'warning': (c['warning'], '⚠', 'Warning'),
        }
        
        color, icon, display_text = color_map.get(status_lower, (c['waiting'], '○', status))
        
        self._status_icon.config(text=icon, fg=color)
        self._status_label.config(text=display_text, fg=color)
        self._status_dot.config(fg=color)
        self._status_text.config(text=display_text)
        
        if detail:
            self._status_detail.config(text=detail)
        
        if status_lower == 'running':
            self._start_time = time.time()
    
    def update_progress(self, current: int, total: int):
        """Update frame progress"""
        self._processed_frames = current
        self._total_frames = total
        
        self._frame_label.config(text=f"{current:,} / {total:,}")
        
        if total > 0:
            pct = (current / total) * 100
            self._progress_var.set(pct)
            self._progress_pct.config(text=f"{pct:.0f}%")
        else:
            self._progress_var.set(0)
            self._progress_pct.config(text="0%")
        
        # Update elapsed and remaining
        if self._start_time:
            elapsed = time.time() - self._start_time
            self._stat_labels['elapsed'].config(text=self._format_time(elapsed))
            
            if current > 0 and current < total:
                rate = current / elapsed
                remaining = (total - current) / rate
                self._stat_labels['remaining'].config(text=self._format_time(remaining))
            elif current >= total and total > 0:
                self._stat_labels['remaining'].config(text="Done")
    
    def update_stats(self, extracted: int = None, videos_done: int = None,
                     videos_total: int = None):
        """Update extraction statistics"""
        if extracted is not None:
            self._stat_labels['extracted'].config(text=f"{extracted:,}")
        
        if videos_done is not None and videos_total is not None:
            self._stat_labels['videos_done'].config(text=f"{videos_done} / {videos_total}")
        elif videos_done is not None:
            current = self._stat_labels['videos_done'].cget('text')
            total = current.split('/')[-1].strip() if '/' in current else '?'
            self._stat_labels['videos_done'].config(text=f"{videos_done} / {total}")
    
    def reset(self):
        """Reset all monitor values"""
        self._start_time = None
        self._total_frames = 0
        self._processed_frames = 0
        
        self.set_status('idle', 'No active task')
        self.update_progress(0, 0)
        self._stat_labels['extracted'].config(text='0')
        self._stat_labels['videos_done'].config(text='0 / 0')
        self._stat_labels['elapsed'].config(text='00:00:00')
        self._stat_labels['remaining'].config(text='--:--:--')
    
    def _update_system_stats(self):
        """Periodically update system stats using psutil"""
        if not self._psutil_available:
            return
        
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            mem = psutil.virtual_memory()
            
            self._cpu_label.config(text=f"{cpu:.0f}%")
            
            # Color code CPU
            c = Theme.DARK_COLORS
            if cpu > 80:
                self._cpu_label.config(fg=c['danger'])
            elif cpu > 60:
                self._cpu_label.config(fg=c['warning'])
            else:
                self._cpu_label.config(fg=c['fg_primary'])
            
            used_gb = mem.used / (1024**3)
            total_gb = mem.total / (1024**3)
            self._mem_label.config(text=f"{used_gb:.1f} / {total_gb:.1f} GB")
            
            if mem.percent > 85:
                self._mem_label.config(fg=c['danger'])
            elif mem.percent > 70:
                self._mem_label.config(fg=c['warning'])
            else:
                self._mem_label.config(fg=c['fg_primary'])
        except Exception:
            pass
        
        # Update every 2 seconds
        self.after(2000, self._update_system_stats)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to HH:MM:SS"""
        if seconds < 0:
            return '--:--:--'
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"

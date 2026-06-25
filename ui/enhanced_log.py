"""Enhanced Log Component - Full-featured log display with filtering, search, and fullscreen"""
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Optional


class EnhancedLogFrame(tk.Frame):
    """Enhanced log display frame with level coloring, search, and fullscreen support"""
    
    # Log level color mapping (dark theme compatible)
    LEVEL_COLORS = {
        'info':    '#29B6F6',   # Blue
        'success': '#4CAF50',   # Green
        'warning': '#FF9800',   # Orange
        'error':   '#F44336',   # Red
        'debug':   '#9E9E9E',   # Gray
    }
    
    LEVEL_TAGS = {
        'info':    '[INFO]',
        'success': '[ OK ]',
        'warning': '[WARN]',
        'error':   '[ERR ]',
        'debug':   '[DBG ]',
    }
    
    MAX_LINES = 5000
    
    def __init__(self, parent, height: int = 12, **kwargs):
        # Use bg from dark theme
        from ui.theme import Theme
        bg = Theme.DARK_COLORS['bg_secondary']
        super().__init__(parent, bg=bg, **kwargs)
        
        self.auto_scroll = True
        self.line_count = 0
        self._fullscreen_window = None
        self._fullscreen_text = None
        
        self._create_toolbar()
        self._create_text_widget(height)
    
    def _create_toolbar(self):
        """Create log toolbar with search, controls"""
        from ui.theme import Theme
        c = Theme.DARK_COLORS
        
        toolbar = tk.Frame(self, bg=c['bg_tertiary'], height=32)
        toolbar.pack(fill=tk.X, padx=1, pady=(1, 0))
        toolbar.pack_propagate(False)
        
        # Title
        tk.Label(toolbar, text="  Real-time Log", bg=c['bg_tertiary'],
                fg=c['fg_primary'], font=Theme.FONTS['bold']).pack(side=tk.LEFT, padx=(4, 8))
        
        # Search entry
        search_frame = tk.Frame(toolbar, bg=c['bg_tertiary'])
        search_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4)
        
        tk.Label(search_frame, text="Search:", bg=c['bg_tertiary'],
                fg=c['fg_secondary'], font=Theme.FONTS['normal']).pack(side=tk.LEFT, padx=(0, 4))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *_: self._highlight_search())
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                                    bg=c['bg_primary'], fg=c['fg_primary'],
                                    insertbackground=c['fg_primary'],
                                    relief='flat', font=Theme.FONTS['mono'])
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=2, padx=2)
        
        # Separator
        tk.Frame(toolbar, bg=c['border'], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=4)
        
        # Control buttons
        btn_config = {'bg': c['bg_tertiary'], 'fg': c['fg_primary'], 
                     'relief': 'flat', 'padx': 6, 'pady': 2,
                     'activebackground': c['bg_hover'], 'activeforeground': c['fg_primary'],
                     'font': Theme.FONTS['normal'], 'cursor': 'hand2'}
        
        self.scroll_btn = tk.Button(toolbar, text="|| Pause Scroll",
                                   command=self._toggle_scroll, **btn_config)
        self.scroll_btn.pack(side=tk.LEFT, padx=1)
        
        tk.Button(toolbar, text="Copy", command=self._copy_selected, **btn_config).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="Clear", command=self.clear, **btn_config).pack(side=tk.LEFT, padx=1)
        tk.Button(toolbar, text="Fullscreen", command=self._toggle_fullscreen, **btn_config).pack(side=tk.LEFT, padx=1)
    
    def _create_text_widget(self, height: int):
        """Create the main text widget for log display"""
        from ui.theme import Theme
        c = Theme.DARK_COLORS
        
        text_frame = tk.Frame(self, bg=c['border'])
        text_frame.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
        
        self.text_widget = tk.Text(
            text_frame,
            height=height,
            wrap=tk.WORD,
            bg=c['bg_primary'],
            fg=c['fg_primary'],
            insertbackground=c['fg_primary'],
            selectbackground=c['selection'],
            selectforeground=c['selection_fg'],
            font=Theme.FONTS['mono'],
            relief='flat',
            borderwidth=0,
            state=tk.DISABLED,
            padx=6,
            pady=4
        )
        
        scrollbar = ttk.Scrollbar(text_frame, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure color tags for log levels
        self.text_widget.tag_configure('timestamp', foreground=c['fg_secondary'])
        for level, color in self.LEVEL_COLORS.items():
            self.text_widget.tag_configure(f'level_{level}', foreground=color)
        self.text_widget.tag_configure('search_highlight',
                                      background=c['warning'],
                                      foreground='#000000')
    
    def log(self, message: str, level: str = "info"):
        """Add a log entry with level-based coloring"""
        level = level.lower() if level else 'info'
        if level not in self.LEVEL_COLORS:
            level = 'info'
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        level_tag = self.LEVEL_TAGS.get(level, '[INFO]')
        
        self.text_widget.configure(state=tk.NORMAL)
        
        # Insert timestamp
        self.text_widget.insert(tk.END, f"  {timestamp}  ", 'timestamp')
        # Insert level tag with color
        self.text_widget.insert(tk.END, f"{level_tag} ", f'level_{level}')
        # Insert message with level color
        self.text_widget.insert(tk.END, f"{message}\n", f'level_{level}')
        
        self.line_count += 1
        
        # Trim old lines if exceeding max
        if self.line_count > self.MAX_LINES:
            trim_count = self.line_count - self.MAX_LINES
            self.text_widget.delete('1.0', f'{trim_count}.0')
            self.line_count = self.MAX_LINES
        
        self.text_widget.configure(state=tk.DISABLED)
        
        # Auto-scroll if enabled
        if self.auto_scroll:
            self.text_widget.see(tk.END)
        
        # Also update fullscreen window if open
        if self._fullscreen_text and self._fullscreen_text.winfo_exists():
            self._update_fullscreen(timestamp, level_tag, level, message)
    
    def clear(self):
        """Clear all log entries"""
        self.text_widget.configure(state=tk.NORMAL)
        self.text_widget.delete('1.0', tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        self.line_count = 0
        
        # Clear fullscreen too
        if self._fullscreen_text and self._fullscreen_text.winfo_exists():
            self._fullscreen_text.configure(state=tk.NORMAL)
            self._fullscreen_text.delete('1.0', tk.END)
            self._fullscreen_text.configure(state=tk.DISABLED)
    
    def _toggle_scroll(self):
        """Toggle auto-scroll on/off"""
        self.auto_scroll = not self.auto_scroll
        if self.auto_scroll:
            self.scroll_btn.config(text="|| Pause Scroll")
            self.text_widget.see(tk.END)
        else:
            self.scroll_btn.config(text="▶ Resume Scroll")
    
    def _copy_selected(self):
        """Copy selected text to clipboard"""
        try:
            selected = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected:
                self.clipboard_clear()
                self.clipboard_append(selected)
        except tk.TclError:
            # No selection - copy all
            self.text_widget.configure(state=tk.NORMAL)
            content = self.text_widget.get('1.0', tk.END)
            self.text_widget.configure(state=tk.DISABLED)
            if content.strip():
                self.clipboard_clear()
                self.clipboard_append(content)
    
    def _highlight_search(self):
        """Highlight search matches in the text widget"""
        from ui.theme import Theme
        c = Theme.DARK_COLORS
        
        self.text_widget.configure(state=tk.NORMAL)
        
        # Remove existing highlights
        self.text_widget.tag_remove('search_highlight', '1.0', tk.END)
        
        query = self.search_var.get().strip()
        if query:
            start_pos = '1.0'
            while True:
                start_pos = self.text_widget.search(query, start_pos, stopindex=tk.END, nocase=True)
                if not start_pos:
                    break
                end_pos = f"{start_pos}+{len(query)}c"
                self.text_widget.tag_add('search_highlight', start_pos, end_pos)
                start_pos = end_pos
        
        self.text_widget.configure(state=tk.DISABLED)
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen log view"""
        if self._fullscreen_window and self._fullscreen_window.winfo_exists():
            self._fullscreen_window.destroy()
            self._fullscreen_window = None
            self._fullscreen_text = None
            return
        
        from ui.theme import Theme
        c = Theme.DARK_COLORS
        
        self._fullscreen_window = tk.Toplevel(self)
        self._fullscreen_window.title("Log - Fullscreen View")
        self._fullscreen_window.geometry("1200x800")
        self._fullscreen_window.configure(bg=c['bg_primary'])
        
        # Toolbar
        fs_toolbar = tk.Frame(self._fullscreen_window, bg=c['bg_tertiary'], height=36)
        fs_toolbar.pack(fill=tk.X)
        fs_toolbar.pack_propagate(False)
        
        tk.Label(fs_toolbar, text="  Log - Fullscreen", bg=c['bg_tertiary'],
                fg=c['fg_primary'], font=Theme.FONTS['bold']).pack(side=tk.LEFT, padx=8)
        
        tk.Button(fs_toolbar, text="Close", bg=c['bg_tertiary'], fg=c['fg_primary'],
                 relief='flat', padx=12, command=lambda: self._fullscreen_window.destroy()
                 ).pack(side=tk.RIGHT, padx=4)
        
        # Text widget
        fs_text_frame = tk.Frame(self._fullscreen_window, bg=c['border'])
        fs_text_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        
        self._fullscreen_text = tk.Text(
            fs_text_frame,
            wrap=tk.WORD,
            bg=c['bg_primary'],
            fg=c['fg_primary'],
            insertbackground=c['fg_primary'],
            selectbackground=c['selection'],
            selectforeground=c['selection_fg'],
            font=Theme.FONTS['mono'],
            relief='flat',
            state=tk.DISABLED,
            padx=8,
            pady=6
        )
        
        fs_scroll = ttk.Scrollbar(fs_text_frame, command=self._fullscreen_text.yview)
        self._fullscreen_text.configure(yscrollcommand=fs_scroll.set)
        
        fs_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._fullscreen_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Copy existing tags
        self._fullscreen_text.tag_configure('timestamp', foreground=c['fg_secondary'])
        for level, color in self.LEVEL_COLORS.items():
            self._fullscreen_text.tag_configure(f'level_{level}', foreground=color)
        
        # Copy existing content
        self.text_widget.configure(state=tk.NORMAL)
        content = self.text_widget.get('1.0', tk.END)
        self.text_widget.configure(state=tk.DISABLED)
        
        self._fullscreen_text.configure(state=tk.NORMAL)
        self._fullscreen_text.insert('1.0', content)
        self._fullscreen_text.configure(state=tk.DISABLED)
        self._fullscreen_text.see(tk.END)
        
        self._fullscreen_window.protocol("WM_DELETE_WINDOW", self._on_fullscreen_close)
    
    def _on_fullscreen_close(self):
        """Handle fullscreen window close"""
        if self._fullscreen_window:
            self._fullscreen_window.destroy()
        self._fullscreen_window = None
        self._fullscreen_text = None
    
    def _update_fullscreen(self, timestamp, level_tag, level, message):
        """Update fullscreen text widget with new log entry"""
        if not self._fullscreen_text or not self._fullscreen_text.winfo_exists():
            return
        self._fullscreen_text.configure(state=tk.NORMAL)
        self._fullscreen_text.insert(tk.END, f"  {timestamp}  ", 'timestamp')
        self._fullscreen_text.insert(tk.END, f"{level_tag} ", f'level_{level}')
        self._fullscreen_text.insert(tk.END, f"{message}\n", f'level_{level}')
        self._fullscreen_text.configure(state=tk.DISABLED)
        self._fullscreen_text.see(tk.END)

"""Task Overview Bar - Top statistics dashboard showing task summary"""
import tkinter as tk
from tkinter import ttk
from ui.theme import Theme


class TaskOverviewBar(tk.Frame):
    """Top bar displaying task overview statistics"""
    
    def __init__(self, parent, **kwargs):
        c = Theme.DARK_COLORS
        super().__init__(parent, bg=c['bg_secondary'], **kwargs)
        
        # Stats tracking
        self._stats = {
            'total': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
        }
        
        self._cards = {}
        self._create_cards()
    
    def _create_cards(self):
        """Create the 4 stat cards"""
        c = Theme.DARK_COLORS
        
        # Inner container with padding
        inner = tk.Frame(self, bg=c['bg_secondary'])
        inner.pack(fill=tk.X, padx=8, pady=6)
        
        # Configure grid for 4 equal columns
        for i in range(4):
            inner.columnconfigure(i, weight=1, uniform='card')
        
        # Card definitions
        cards_config = [
            ('total',     'Total',     c['accent'],   '0'),
            ('running',   'Running',   c['running'],  '0'),
            ('completed', 'Completed', c['success'],  '0'),
            ('failed',    'Failed',    c['danger'],   '0'),
        ]
        
        for col, (key, label, color, default_val) in enumerate(cards_config):
            card = self._create_card(inner, key, label, color, default_val)
            card.grid(row=0, column=col, sticky='ew', padx=4, pady=2)
            self._cards[key] = card
    
    def _create_card(self, parent, key: str, label: str, accent_color: str, value: str):
        """Create a single stat card"""
        c = Theme.DARK_COLORS
        
        # Card container
        card = tk.Frame(parent, bg=c['bg_tertiary'], padx=12, pady=8)
        
        # Top color indicator bar
        indicator = tk.Frame(card, bg=accent_color, height=3)
        indicator.pack(fill=tk.X, pady=(0, 6))
        
        # Value + Label row
        content = tk.Frame(card, bg=c['bg_tertiary'])
        content.pack(fill=tk.X)
        
        # Number label
        number_label = tk.Label(content, text=value,
                               bg=c['bg_tertiary'], fg=accent_color,
                               font=Theme.FONTS['card_number'])
        number_label.pack(side=tk.LEFT)
        
        # Text label
        text_frame = tk.Frame(content, bg=c['bg_tertiary'])
        text_frame.pack(side=tk.LEFT, padx=(8, 0))
        
        tk.Label(text_frame, text=label,
                bg=c['bg_tertiary'], fg=c['fg_secondary'],
                font=Theme.FONTS['card_label']).pack(anchor=tk.W)
        
        # Store references for updates
        card._number_label = number_label
        card._accent_color = accent_color
        card._key = key
        
        return card
    
    def update_stats(self, total: int = None, running: int = None,
                     completed: int = None, failed: int = None):
        """Update one or more stat values"""
        c = Theme.DARK_COLORS
        
        if total is not None:
            self._stats['total'] = total
        if running is not None:
            self._stats['running'] = running
        if completed is not None:
            self._stats['completed'] = completed
        if failed is not None:
            self._stats['failed'] = failed
        
        for key, card in self._cards.items():
            value = self._stats[key]
            card._number_label.config(text=str(value))
            
            # Pulse effect for running count
            if key == 'running' and value > 0:
                card._number_label.config(fg=c['running'])
            elif key == 'running':
                card._number_label.config(fg=c['fg_secondary'])
    
    def reset(self):
        """Reset all stats to 0"""
        self.update_stats(total=0, running=0, completed=0, failed=0)
    
    def get_stats(self) -> dict:
        """Get current stats"""
        return self._stats.copy()

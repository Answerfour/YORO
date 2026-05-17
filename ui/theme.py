"""Theme Styles Module - Provides unified UI themes"""
from tkinter import ttk


class Theme:
    """UI theme manager"""
    
    COLORS = {
        'primary': '#0078D4',
        'secondary': '#F3F3F3',
        'success': '#107C10',
        'warning': '#FFB900',
        'danger': '#E81123',
        'info': '#0078D4',
        'light': '#FFFFFF',
        'dark': '#323130',
        'border': '#D2D0CE',
    }
    
    FONTS = {
        'normal': ('Segoe UI', 9),
        'bold': ('Segoe UI', 9, 'bold'),
        'large': ('Segoe UI', 11),
        'title': ('Segoe UI', 14, 'bold'),
        'mono': ('Consolas', 9),
    }
    
    @staticmethod
    def apply_default_style():
        """Apply default theme styles"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        
        style.configure('TFrame', background='#FFFFFF')
        style.configure('TLabelframe', background='#FFFFFF', bordercolor='#D2D0CE')
        style.configure('TLabelframe.Label', background='#FFFFFF', foreground='#323130')
        style.configure('TLabel', background='#FFFFFF', foreground='#323130')
        style.configure('TButton', padding=6, relief='flat', background='#0078D4')
        style.configure('TEntry', padding=4)
        style.configure('TCombobox', padding=4)
        style.configure('TRadiobutton', background='#FFFFFF')
        style.configure('TCheckbutton', background='#FFFFFF')
        style.configure('Treeview', background='#FFFFFF', foreground='#323130', fieldbackground='#FFFFFF')
        style.configure('Treeview.Heading', font=('Segoe UI', 9, 'bold'))
    
    @staticmethod
    def configure_button_style(style_name: str, **kwargs):
        """Configure button styles"""
        style = ttk.Style()
        style.configure(f'{style_name}.TButton', **kwargs)
    
    @staticmethod
    def configure_treeview_colors():
        """Configure Treeview colors"""
        style = ttk.Style()
        style.map('Treeview',
                  background=[('selected', '#0078D4')],
                  foreground=[('selected', '#FFFFFF')])
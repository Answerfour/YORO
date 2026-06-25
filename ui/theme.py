"""Theme Styles Module - Provides unified UI themes with dark mode support"""
from tkinter import ttk


class Theme:
    """UI theme manager with dark mode support"""
    
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
    
    # Dark theme color palette - Industrial software style
    DARK_COLORS = {
        'bg_primary': '#1E1E2E',      # Main background
        'bg_secondary': '#2D2D3F',    # Card/panel background
        'bg_tertiary': '#383850',     # Input/highlight background
        'bg_hover': '#45455A',        # Hover state
        'fg_primary': '#E0E0E0',      # Primary text
        'fg_secondary': '#A0A0B0',    # Secondary text
        'fg_disabled': '#606070',     # Disabled text
        'accent': '#5B8DEF',          # Accent (buttons/selection)
        'accent_hover': '#7BA5F7',    # Accent hover
        'success': '#4CAF50',         # Success green
        'warning': '#FF9800',         # Warning orange
        'danger': '#F44336',          # Error red
        'info': '#29B6F6',            # Info blue
        'border': '#404055',          # Border
        'waiting': '#9E9E9E',         # Waiting gray
        'running': '#5B8DEF',         # Running blue
        'scrollbar': '#505065',       # Scrollbar
        'selection': '#5B8DEF',       # Selection background
        'selection_fg': '#FFFFFF',    # Selection foreground
    }
    
    # Status color mapping
    STATUS_COLORS = {
        'waiting': '#9E9E9E',    # Gray
        'running': '#5B8DEF',    # Blue
        'success': '#4CAF50',    # Green
        'warning': '#FF9800',    # Orange
        'error': '#F44336',      # Red
        'idle': '#9E9E9E',       # Gray
    }
    
    FONTS = {
        'normal': ('Segoe UI', 9),
        'bold': ('Segoe UI', 9, 'bold'),
        'large': ('Segoe UI', 11),
        'title': ('Segoe UI', 14, 'bold'),
        'subtitle': ('Segoe UI', 10),
        'mono': ('Consolas', 9),
        'mono_small': ('Consolas', 8),
        'card_number': ('Segoe UI', 18, 'bold'),
        'card_label': ('Segoe UI', 8),
    }
    
    _dark_theme_applied = False
    
    @staticmethod
    def apply_default_style():
        """Apply default theme styles (light mode - kept for compatibility)"""
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
    
    @classmethod
    def apply_dark_theme(cls):
        """Apply dark industrial theme - primary theme for workspace"""
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except:
            pass
        
        c = cls.DARK_COLORS
        
        # Core widget styles
        style.configure('.', 
                       background=c['bg_primary'],
                       foreground=c['fg_primary'],
                       bordercolor=c['border'],
                       arrowcolor=c['fg_primary'],
                       darkcolor=c['bg_primary'],
                       lightcolor=c['bg_primary'],
                       troughcolor=c['bg_secondary'],
                       selectbackground=c['selection'],
                       selectforeground=c['selection_fg'],
                       font=cls.FONTS['normal'])
        
        # Frame styles
        style.configure('TFrame', background=c['bg_primary'])
        style.configure('Card.TFrame', background=c['bg_secondary'])
        style.configure('Secondary.TFrame', background=c['bg_secondary'])
        
        # Label styles
        style.configure('TLabel', 
                       background=c['bg_primary'],
                       foreground=c['fg_primary'])
        style.configure('Card.TLabel',
                       background=c['bg_secondary'],
                       foreground=c['fg_primary'])
        style.configure('Secondary.TLabel',
                       foreground=c['fg_secondary'])
        style.configure('Title.TLabel',
                       font=cls.FONTS['title'],
                       foreground=c['fg_primary'])
        style.configure('Subtitle.TLabel',
                       font=cls.FONTS['subtitle'],
                       foreground=c['fg_secondary'])
        style.configure('CardNumber.TLabel',
                       font=cls.FONTS['card_number'],
                       foreground=c['accent'])
        style.configure('CardLabel.TLabel',
                       font=cls.FONTS['card_label'],
                       foreground=c['fg_secondary'])
        
        # LabelFrame styles
        style.configure('TLabelframe',
                       background=c['bg_secondary'],
                       bordercolor=c['border'],
                       relief='flat')
        style.configure('TLabelframe.Label',
                       background=c['bg_secondary'],
                       foreground=c['accent'],
                       font=cls.FONTS['bold'])
        style.configure('Card.TLabelframe',
                       background=c['bg_secondary'],
                       bordercolor=c['border'],
                       relief='flat')
        
        # Button styles
        style.configure('TButton',
                       background=c['bg_tertiary'],
                       foreground=c['fg_primary'],
                       bordercolor=c['border'],
                       padding=6,
                       relief='flat',
                       font=cls.FONTS['normal'])
        style.map('TButton',
                 background=[('active', c['bg_hover']),
                           ('pressed', c['bg_hover']),
                           ('disabled', c['bg_primary'])],
                 foreground=[('disabled', c['fg_disabled'])])
        
        # Primary (accent) button
        style.configure('Accent.TButton',
                       background=c['accent'],
                       foreground='#FFFFFF',
                       font=cls.FONTS['bold'],
                       padding=8)
        style.map('Accent.TButton',
                 background=[('active', c['accent_hover']),
                           ('pressed', c['accent_hover']),
                           ('disabled', c['bg_tertiary'])],
                 foreground=[('disabled', c['fg_disabled'])])
        
        # Danger button
        style.configure('Danger.TButton',
                       background=c['danger'],
                       foreground='#FFFFFF',
                       font=cls.FONTS['bold'],
                       padding=8)
        style.map('Danger.TButton',
                 background=[('active', '#E57373'),
                           ('pressed', '#E57373')])
        
        # Entry style
        style.configure('TEntry',
                       fieldbackground=c['bg_tertiary'],
                       foreground=c['fg_primary'],
                       bordercolor=c['border'],
                       insertcolor=c['fg_primary'],
                       padding=4)
        style.map('TEntry',
                 fieldbackground=[('focus', c['bg_hover'])],
                 bordercolor=[('focus', c['accent'])])
        
        # Combobox style
        style.configure('TCombobox',
                       fieldbackground=c['bg_tertiary'],
                       foreground=c['fg_primary'],
                       bordercolor=c['border'],
                       arrowcolor=c['fg_primary'],
                       padding=4)
        style.map('TCombobox',
                 fieldbackground=[('readonly', c['bg_tertiary']),
                                ('focus', c['bg_hover'])])
        
        # Radiobutton and Checkbutton
        style.configure('TRadiobutton',
                       background=c['bg_secondary'],
                       foreground=c['fg_primary'])
        style.configure('TCheckbutton',
                       background=c['bg_secondary'],
                       foreground=c['fg_primary'])
        
        # Progressbar
        style.configure('TProgressbar',
                       background=c['accent'],
                       troughcolor=c['bg_tertiary'],
                       bordercolor=c['border'],
                       lightcolor=c['accent'],
                       darkcolor=c['accent'])
        style.configure('Success.Horizontal.TProgressbar',
                       background=c['success'])
        style.configure('Warning.Horizontal.TProgressbar',
                       background=c['warning'])
        style.configure('Danger.Horizontal.TProgressbar',
                       background=c['danger'])
        
        # Treeview styles
        style.configure('Treeview',
                       background=c['bg_secondary'],
                       foreground=c['fg_primary'],
                       fieldbackground=c['bg_secondary'],
                       bordercolor=c['border'],
                       rowheight=28)
        style.configure('Treeview.Heading',
                       background=c['bg_tertiary'],
                       foreground=c['fg_primary'],
                       bordercolor=c['border'],
                       font=cls.FONTS['bold'])
        style.map('Treeview',
                 background=[('selected', c['selection'])],
                 foreground=[('selected', c['selection_fg'])])
        
        # Notebook styles
        style.configure('TNotebook',
                       background=c['bg_primary'],
                       bordercolor=c['border'])
        style.configure('TNotebook.Tab',
                       background=c['bg_secondary'],
                       foreground=c['fg_secondary'],
                       padding=[12, 6],
                       bordercolor=c['border'])
        style.map('TNotebook.Tab',
                 background=[('selected', c['bg_primary'])],
                 foreground=[('selected', c['accent'])],
                 expand=[('selected', [0, 0, 0, 2])])
        
        # PanedWindow
        style.configure('TPanedwindow',
                       background=c['border'])
        
        # Scrollbar
        style.configure('TScrollbar',
                       background=c['scrollbar'],
                       troughcolor=c['bg_secondary'],
                       bordercolor=c['bg_secondary'],
                       arrowcolor=c['fg_primary'])
        style.map('TScrollbar',
                 background=[('active', c['bg_hover']),
                           ('pressed', c['accent'])])
        
        # Scale (slider)
        style.configure('TScale',
                       background=c['bg_secondary'],
                       troughcolor=c['bg_tertiary'],
                       bordercolor=c['border'])
        
        # Separator
        style.configure('TSeparator',
                       background=c['border'])
        
        cls._dark_theme_applied = True
    
    @classmethod
    def get_color(cls, name: str) -> str:
        """Get dark theme color by name"""
        return cls.DARK_COLORS.get(name, '#000000')
    
    @classmethod
    def get_status_color(cls, status: str) -> str:
        """Get status indicator color"""
        return cls.STATUS_COLORS.get(status.lower(), cls.STATUS_COLORS['waiting'])
    
    @classmethod
    def is_dark_theme(cls) -> bool:
        """Check if dark theme is currently applied"""
        return cls._dark_theme_applied
    
    @staticmethod
    def configure_button_style(style_name: str, **kwargs):
        """Configure custom button styles"""
        style = ttk.Style()
        style.configure(f'{style_name}.TButton', **kwargs)
    
    @staticmethod
    def configure_treeview_colors():
        """Configure Treeview colors (for compatibility)"""
        style = ttk.Style()
        c = Theme.DARK_COLORS
        style.map('Treeview',
                  background=[('selected', c['selection'])],
                  foreground=[('selected', c['selection_fg'])])
# src/gui/theme.py
"""Gestion des thèmes (clair/sombre/système)."""
import tkinter as tk
from tkinter import ttk
from src.config import get_config

# Couleurs pour les thèmes
THEMES = {
    'light': {
        'bg': '#ffffff',
        'fg': '#000000',
        'select_bg': '#0078d4',
        'select_fg': '#ffffff',
        'entry_bg': '#ffffff',
        'entry_fg': '#000000',
        'button_bg': '#f3f3f3',
        'button_fg': '#000000',
        'frame_bg': '#f0f0f0',
        'border': '#cccccc',
        'text_bg': '#ffffff',
        'text_fg': '#000000',
        'disabled_fg': '#666666',
        'tab_bg': '#f3f3f3',
        'tab_fg': '#000000',
        'tab_selected_bg': '#0078d4',
        'tab_selected_fg': '#ffffff',
    },
    'dark': {
        'bg': '#1e1e1e',
        'fg': '#ffffff',
        'select_bg': '#0078d4',
        'select_fg': '#ffffff',
        'entry_bg': '#2d2d2d',
        'entry_fg': '#ffffff',
        'button_bg': '#333333',
        'button_fg': '#ffffff',
        'frame_bg': '#252525',
        'border': '#444444',
        'text_bg': '#1e1e1e',
        'text_fg': '#ffffff',
        'disabled_fg': '#888888',
        'tab_bg': '#333333',
        'tab_fg': '#ffffff',
        'tab_selected_bg': '#0078d4',
        'tab_selected_fg': '#ffffff',
    }
}

_current_theme = 'system'


def get_system_theme() -> str:
    """Détecte le thème système (Windows 10/11)."""
    try:
        import winreg
        registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
        key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return 'light' if value == 1 else 'dark'
    except Exception:
        return 'light'


def get_current_theme() -> str:
    """Retourne le thème actuellement actif."""
    global _current_theme
    if _current_theme == 'system':
        return get_system_theme()
    return _current_theme


def apply_theme(theme_name: str = None):
    """Applique un thème à l'application."""
    global _current_theme
    
    if theme_name is None:
        config = get_config()
        theme_name = config.get('gui.theme', 'system')
    
    _current_theme = theme_name
    actual_theme = get_current_theme()
    colors = THEMES.get(actual_theme, THEMES['light'])
    
    style = ttk.Style()
    
    # Configurer les styles ttk
    style.configure('.', 
        background=colors['bg'],
        foreground=colors['fg'],
        fieldbackground=colors['entry_bg'],
        selectbackground=colors['select_bg'],
        selectforeground=colors['select_fg'],
    )
    
    style.configure('TFrame', background=colors['frame_bg'])
    style.configure('TLabel', background=colors['frame_bg'], foreground=colors['fg'])
    style.configure('TButton', background=colors['button_bg'], foreground=colors['button_fg'])
    style.configure('TEntry', fieldbackground=colors['entry_bg'], foreground=colors['entry_fg'])
    style.configure('TCombobox', fieldbackground=colors['entry_bg'], foreground=colors['entry_fg'])
    style.configure('TSpinbox', fieldbackground=colors['entry_bg'], foreground=colors['entry_fg'])
    style.configure('TCheckbutton', background=colors['frame_bg'], foreground=colors['fg'])
    style.configure('TRadiobutton', background=colors['frame_bg'], foreground=colors['fg'])
    style.configure('TLabelFrame', background=colors['frame_bg'], foreground=colors['fg'])
    style.configure('TLabelFrame.Label', background=colors['frame_bg'], foreground=colors['fg'])
    style.configure('TNotebook', background=colors['frame_bg'], borderwidth=0)
    style.configure('TNotebook.Tab', background=colors['tab_bg'], foreground=colors['tab_fg'],
                    padding=(10, 5))
    style.configure('TSeparator', background=colors['border'])
    style.configure('TProgressbar', background=colors['select_bg'], troughcolor=colors['frame_bg'])
    style.configure('TScrollbar', background=colors['button_bg'], troughcolor=colors['frame_bg'],
                    bordercolor=colors['border'], arrowcolor=colors['fg'])
    
    # Map pour les états
    style.map('TButton',
        background=[('active', colors['select_bg']), ('disabled', colors['frame_bg'])],
        foreground=[('active', colors['select_fg']), ('disabled', colors['disabled_fg'])]
    )
    style.map('TCheckbutton',
        background=[('active', colors['frame_bg'])],
        foreground=[('disabled', colors['disabled_fg'])]
    )
    style.map('TRadiobutton',
        background=[('active', colors['frame_bg'])],
        foreground=[('disabled', colors['disabled_fg'])]
    )
    style.map('TNotebook.Tab',
        background=[('selected', colors['tab_selected_bg'])],
        foreground=[('selected', colors['tab_selected_fg'])]
    )
    style.map('TEntry',
        fieldbackground=[('disabled', colors['frame_bg'])],
        foreground=[('disabled', colors['disabled_fg'])]
    )
    
    # Mettre à jour les widgets Tk natifs (Text, etc.)
    try:
        root = tk._default_root
        if root:
            _apply_to_tk_widgets(root, colors)
    except Exception:
        pass
    
    # Sauvegarder
    try:
        config = get_config()
        config.update_gui(theme=theme_name)
    except Exception:
        pass


def _apply_to_tk_widgets(widget, colors):
    """Applique les couleurs aux widgets Tk natifs récursivement."""
    try:
        widget_class = widget.winfo_class()
        
        if widget_class in ('Text', 'Listbox', 'Entry'):
            widget.configure(
                bg=colors['text_bg'],
                fg=colors['text_fg'],
                insertbackground=colors['fg'],  # curseur
                selectbackground=colors['select_bg'],
                selectforeground=colors['select_fg'],
                highlightbackground=colors['border'],
                highlightcolor=colors['select_bg'],
            )
        elif widget_class in ('Frame', 'Labelframe', 'Toplevel', 'Tk'):
            widget.configure(bg=colors['frame_bg'])
        elif widget_class == 'Label':
            widget.configure(bg=colors['frame_bg'], fg=colors['fg'])
        elif widget_class == 'Button':
            widget.configure(bg=colors['button_bg'], fg=colors['button_fg'],
                           activebackground=colors['select_bg'], activeforeground=colors['select_fg'])
        elif widget_class == 'Menu':
            widget.configure(bg=colors['frame_bg'], fg=colors['fg'],
                           activebackground=colors['select_bg'], activeforeground=colors['select_fg'])
        elif widget_class == 'Canvas':
            widget.configure(bg=colors['text_bg'], highlightbackground=colors['border'])
    except Exception:
        pass
    
    # Récursif sur les enfants
    try:
        for child in widget.winfo_children():
            _apply_to_tk_widgets(child, colors)
    except Exception:
        pass


def refresh_theme():
    """Rafraîchit le thème actuel (après changement de langue par ex)."""
    apply_theme(_current_theme)
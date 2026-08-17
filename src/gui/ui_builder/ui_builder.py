# src/gui/ui_builder/ui_builder.py
import tkinter as tk
from tkinter import ttk
from .menus import build_menus
from .widgets import build_widgets
from src.config import config
from src.i18n import _

def build_ui(parent):
    ui = {}

    ui['folder_path_var'] = tk.StringVar()
    ui['progress_var'] = tk.DoubleVar()
    ui['status_var'] = tk.StringVar(value=_("Prêt"))

    cfg = config.get_all()
    
    ui['include_subdirs'] = tk.BooleanVar(value=cfg.extraction.include_subdirs)
    ui['show_file_paths'] = tk.BooleanVar(value=cfg.extraction.show_file_paths)
    ui['include_json'] = tk.BooleanVar(value=cfg.extraction.include_json)
    ui['include_txt'] = tk.BooleanVar(value=cfg.extraction.include_txt)
    ui['include_po'] = tk.BooleanVar(value=cfg.extraction.include_po)
    ui['include_mo'] = tk.BooleanVar(value=cfg.extraction.include_mo)
    ui['include_html'] = tk.BooleanVar(value=cfg.extraction.include_html)
    ui['include_css'] = tk.BooleanVar(value=cfg.extraction.include_css)
    ui['include_js'] = tk.BooleanVar(value=cfg.extraction.include_js)
    ui['include_structure'] = tk.BooleanVar(value=cfg.extraction.include_structure)
    ui['ignore_init'] = tk.BooleanVar(value=cfg.extraction.ignore_init)
    ui['ignore_git'] = tk.BooleanVar(value=cfg.extraction.ignore_git)         # NOUVEAU
    ui['ignore_pycache'] = tk.BooleanVar(value=cfg.extraction.ignore_pycache) # NOUVEAU
    ui['include_statistics'] = tk.BooleanVar(value=cfg.extraction.include_statistics)
    ui['include_file_metadata'] = tk.BooleanVar(value=cfg.extraction.include_file_metadata)
    
    ui['archive_old'] = tk.BooleanVar(value=False)
    ui['log_visible'] = tk.BooleanVar(value=True)

    build_menus(parent, ui)
    build_widgets(parent, ui)

    return ui
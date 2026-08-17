# src/gui/ui_builder/ui_builder.py
import tkinter as tk
from tkinter import ttk
from .menus import build_menus
from .widgets import build_widgets
from .ui_widgets import UIWidgets, create_ui_widgets
from src.config import get_config
from src.i18n import _


def build_ui(parent) -> UIWidgets:
    """Build the UI and return a typed UIWidgets container."""
    ui = create_ui_widgets(get_config())
    
    build_menus(parent, ui)
    build_widgets(parent, ui)
    
    return ui
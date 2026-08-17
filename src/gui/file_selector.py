# src/gui/file_selector.py
from src.gui.selection import SelectionDialog

def select_files(parent, folder_path, options):
    """
    options est un dict avec les clés include_json, include_txt, etc.
    On s'assure qu'il contient ignore_git et ignore_pycache.
    """
    # Le contrôleur (BaseController.get_include_options) ne renvoie pas encore ces nouvelles options.
    # Il faut mettre à jour BaseController.get_include_options (étape 14).
    # Ici, on suppose que 'options' les contient.
    dialog = SelectionDialog(parent, folder_path, options)
    parent.wait_window(dialog.window)
    return dialog.get_selected()
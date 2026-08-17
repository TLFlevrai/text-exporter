# src/gui/ui_builder/menus.py
import tkinter as tk
import json
from pathlib import Path
import os
from src.i18n import _, pgettext, change_language as i18n_change_language, register_reload_callback, unregister_reload_callback
from src.gui.recent_files import load_recent_folders, clear_recent_folders
from .ui_widgets import UIWidgets


def build_menus(parent, ui: UIWidgets):
    """Construit la barre de menus et enregistre le callback de rechargement i18n."""
    menubar = tk.Menu(parent)
    parent.config(menu=menubar)
    ui.menubar = menubar
    ui._menu_items = {}

    _rebuild_all_menus(parent, ui)

    # Enregistrer callback pour rechargement à chaud
    def refresh_menus():
        _rebuild_all_menus(parent, ui)
    
    register_reload_callback(refresh_menus)
    ui._i18n_menu_refresh_callback = refresh_menus


def _rebuild_all_menus(parent, ui: UIWidgets):
    """Reconstruit tous les menus avec la langue actuelle."""
    menubar = ui.menubar
    menubar.delete(0, tk.END)
    menu_items = ui._menu_items

    # --- Menu Fichier ---
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=pgettext("menu", "Fichier"), menu=file_menu)
    menu_items['file_menu'] = file_menu
    menu_items['file_cascade_index'] = 0

    file_menu.add_command(
        label=_("Exporter en PDF"),
        command=lambda: _export_to_pdf(parent, ui)
    )
    file_menu.add_separator()

    file_menu.add_command(label=_("Quitter"), command=parent.destroy, accelerator="Ctrl+Q")
    parent.bind_all("<Control-q>", lambda e: parent.destroy())

    # Sous-menu "Emplacements récents"
    recent_menu = tk.Menu(file_menu, tearoff=0)
    file_menu.add_cascade(label=_("Emplacements récents"), menu=recent_menu)
    menu_items['recent_menu'] = recent_menu
    menu_items['recent_cascade_index'] = 1

    # Fonction pour mettre à jour le sous-menu
    def update_recent_menu():
        recent_menu.delete(0, tk.END)
        folders = load_recent_folders()
        if not folders:
            recent_menu.add_command(label=_("Aucun"), state='disabled')
        else:
            for f in folders:
                label = f"{os.path.basename(f)} ({f})"
                recent_menu.add_command(
                    label=label,
                    command=lambda path=f: _select_recent_folder(parent, ui, path)
                )
            recent_menu.add_separator()
            recent_menu.add_command(label=_("Effacer la liste"), command=_clear_recent)
    ui.update_recent_menu = update_recent_menu

    def _clear_recent():
        clear_recent_folders()
        if ui.update_recent_menu:
            ui.update_recent_menu()

    update_recent_menu()

    # --- Menu Options ---
    options_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Options"), menu=options_menu)
    menu_items['options_menu'] = options_menu
    menu_items['options_cascade_index'] = 1

    # Stocker les items d'options pour mise à jour des labels
    option_items = []
    option_items.append(('include_subdirs', _("Inclure les sous-dossiers")))
    option_items.append(('show_file_paths', _("Afficher les chemins des fichiers")))
    option_items.append(('sep1', None))  # separator
    option_items.append(('include_json', _("Inclure les fichiers JSON")))
    option_items.append(('include_txt', _("Inclure les fichiers TXT")))
    option_items.append(('include_po', _("Inclure les fichiers .po (traductions)")))
    option_items.append(('include_mo', _("Inclure les fichiers .mo (compilés)")))
    option_items.append(('include_html', _("Inclure les fichiers HTML")))
    option_items.append(('include_css', _("Inclure les fichiers CSS")))
    option_items.append(('include_js', _("Inclure les fichiers JavaScript")))
    option_items.append(('sep2', None))
    option_items.append(('include_structure', _("Inclure la structure du projet")))
    option_items.append(('ignore_init', _("Ignorer les fichiers __init__.py")))
    option_items.append(('ignore_git', _("Ignorer le dossier .git")))
    option_items.append(('ignore_pycache', _("Ignorer les dossiers __pycache__")))
    option_items.append(('sep3', None))
    option_items.append(('include_statistics', _("Inclure les statistiques")))
    option_items.append(('include_file_metadata', _("Métadonnées détaillées par fichier")))

    menu_items['option_items'] = option_items
    
    for i, (key, label) in enumerate(option_items):
        if label is None:
            options_menu.add_separator()
        else:
            var = getattr(ui, key, None)
            if var:
                options_menu.add_checkbutton(label=label, variable=var)
            else:
                options_menu.add_command(label=label, state='disabled')

    # --- Menu Langue ---
    lang_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Langue"), menu=lang_menu)
    menu_items['lang_menu'] = lang_menu
    menu_items['lang_cascade_index'] = 2
    
    lang_menu.add_command(label="Français", command=lambda: _change_language_hot(ui, "fr"))
    lang_menu.add_command(label="English", command=lambda: _change_language_hot(ui, "en"))

    # --- Menu Outils ---
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Outils"), menu=tools_menu)
    menu_items['tools_menu'] = tools_menu
    menu_items['tools_cascade_index'] = 3
    tools_menu.add_command(label=_("Gestionnaire de versions"), command=lambda: _open_version_explorer(parent, ui))
    ui.open_version_explorer_index = 0

    # --- Menu Vue ---
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Vue"), menu=view_menu)
    menu_items['view_menu'] = view_menu
    menu_items['view_cascade_index'] = 4
    view_menu.add_checkbutton(label=_("Afficher le journal"), variable=ui.log_visible)
    ui.view_menu = view_menu


def _change_language_hot(ui: UIWidgets, lang_code):
    """Change la langue à chaud sans redémarrer l'application."""
    success = i18n_change_language(lang_code)
    if success:
        # Les callbacks register_reload_callback s'occupent du rafraîchissement
        pass


def _export_to_pdf(parent, ui: UIWidgets):
    """Exporte le code du projet sélectionné en PDF."""
    controller = ui.controller
    if controller:
        controller.export_to_pdf()
    else:
        folder = ui.folder_path_var.get()
        if not folder:
            tk.messagebox.showwarning(_("Attention"), _("Veuillez d'abord sélectionner un dossier"))
            return
        tk.messagebox.showerror(_("Erreur"), _("Contrôleur non disponible pour l'export PDF"))


def _select_recent_folder(parent, ui: UIWidgets, folder_path):
    """Sélectionne un dossier récent via le contrôleur."""
    controller = ui.controller
    if controller:
        controller.select_recent_folder(folder_path)
    else:
        ui.folder_path_var.set(folder_path)
        ui.extract_btn.config(state='normal')


def _open_version_explorer(parent, ui: UIWidgets):
    """Ouvre le gestionnaire de versions via le contrôleur."""
    controller = ui.controller
    if controller:
        controller.open_version_explorer()
    else:
        from src.gui.version_explorer import VersionExplorerDialog
        VersionExplorerDialog(parent)


def unregister_menu_refresh(ui: UIWidgets):
    """Désenregistre le callback de rafraîchissement des menus."""
    callback = ui._i18n_menu_refresh_callback
    if callback:
        unregister_reload_callback(callback)
        ui._i18n_menu_refresh_callback = None
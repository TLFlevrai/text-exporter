# src/gui/ui_builder/menus.py
import tkinter as tk
from src.config import config
import json
from pathlib import Path
import sys
import subprocess
import os
from src.i18n import _
from src.gui.recent_files import load_recent_folders, clear_recent_folders

def build_menus(parent, ui):
    menubar = tk.Menu(parent)
    parent.config(menu=menubar)
    ui['menubar'] = menubar

    # --- Menu Fichier ---
    file_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Fichier"), menu=file_menu)

    # Option "Exporter en PDF"
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
    ui['recent_menu'] = recent_menu

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
    ui['update_recent_menu'] = update_recent_menu

    # Définition locale de _clear_recent pour avoir accès à ui
    def _clear_recent():
        """Efface la liste des dossiers récents et rafraîchit le menu."""
        clear_recent_folders()
        if 'update_recent_menu' in ui:
            ui['update_recent_menu']()

    # Remplir initialement
    update_recent_menu()

    # --- Menu Options ---
    options_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Options"), menu=options_menu)
    options_menu.add_checkbutton(label=_("Inclure les sous-dossiers"), variable=ui['include_subdirs'])
    options_menu.add_checkbutton(label=_("Afficher les chemins des fichiers"), variable=ui['show_file_paths'])
    options_menu.add_separator()
    options_menu.add_checkbutton(label=_("Inclure les fichiers JSON"), variable=ui['include_json'])
    options_menu.add_checkbutton(label=_("Inclure les fichiers TXT"), variable=ui['include_txt'])
    options_menu.add_checkbutton(label=_("Inclure les fichiers .po (traductions)"), variable=ui['include_po'])
    options_menu.add_checkbutton(label=_("Inclure les fichiers .mo (compilés)"), variable=ui['include_mo'])
    options_menu.add_checkbutton(label=_("Inclure les fichiers HTML"), variable=ui['include_html'])
    options_menu.add_checkbutton(label=_("Inclure les fichiers CSS"), variable=ui['include_css'])
    options_menu.add_checkbutton(label=_("Inclure les fichiers JavaScript"), variable=ui['include_js'])
    options_menu.add_separator()
    options_menu.add_checkbutton(label=_("Inclure la structure du projet"), variable=ui['include_structure'])
    options_menu.add_checkbutton(label=_("Ignorer les fichiers __init__.py"), variable=ui['ignore_init'])
    
    # NOUVELLES OPTIONS
    options_menu.add_checkbutton(label=_("Ignorer le dossier .git"), variable=ui['ignore_git'])
    options_menu.add_checkbutton(label=_("Ignorer les dossiers __pycache__"), variable=ui['ignore_pycache'])
    
    options_menu.add_separator()
    options_menu.add_checkbutton(label=_("Inclure les statistiques"), variable=ui['include_statistics'])
    options_menu.add_checkbutton(label=_("Métadonnées détaillées par fichier"), variable=ui['include_file_metadata'])

    # --- Menu Langue ---
    lang_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Langue"), menu=lang_menu)
    lang_menu.add_command(label="Français", command=lambda: change_language(parent, "fr"))
    lang_menu.add_command(label="English", command=lambda: change_language(parent, "en"))

    # --- Menu Outils ---
    tools_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Outils"), menu=tools_menu)
    tools_menu.add_command(label=_("Gestionnaire de versions"), command=lambda: _open_version_explorer(parent, ui))
    ui['tools_menu'] = tools_menu
    ui['open_version_explorer_index'] = 0

    # --- Menu Vue ---
    view_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label=_("Vue"), menu=view_menu)
    view_menu.add_checkbutton(label=_("Afficher le journal"), variable=ui['log_visible'])
    ui['view_menu'] = view_menu

    # REMARQUE : Le menu "Transfert" a été supprimé car remplacé par le bouton "🌐 Réseau..."
    # dans la barre d'outils principale.


def _export_to_pdf(parent, ui):
    """Exporte le code du projet sélectionné en PDF."""
    controller = ui.get('controller')
    if controller:
        controller.export_to_pdf()
    else:
        # Fallback
        folder = ui['folder_path_var'].get()
        if not folder:
            tk.messagebox.showwarning(_("Attention"), _("Veuillez d'abord sélectionner un dossier"))
            return
        tk.messagebox.showerror(_("Erreur"), _("Contrôleur non disponible pour l'export PDF"))


def _select_recent_folder(parent, ui, folder_path):
    """Sélectionne un dossier récent via le contrôleur."""
    controller = ui.get('controller')
    if controller:
        controller.select_recent_folder(folder_path)
    else:
        # Fallback
        ui['folder_path_var'].set(folder_path)
        ui['extract_btn'].config(state='normal')


def _open_version_explorer(parent, ui):
    """Ouvre le gestionnaire de versions via le contrôleur."""
    controller = ui.get('controller')
    if controller:
        controller.open_version_explorer()
    else:
        # Fallback direct
        from src.gui.version_explorer import VersionExplorerDialog
        VersionExplorerDialog(parent)


def change_language(parent, lang_code):
    """
    Change la langue de l'application.
    Écrit la nouvelle langue dans config.json, puis redémarre l'application
    proprement en utilisant sys.executable et sys.argv pour fonctionner
    quel que soit le mode d'exécution (script direct, python -m, ou exécutable).
    """
    # Déterminer le chemin du fichier config.json
    config_path = Path(__file__).parent.parent.parent / "config.json"
    if not config_path.exists():
        # Fallback si le chemin relatif ne fonctionne pas
        config_path = Path("config.json")
        if not config_path.exists():
            tk.messagebox.showerror(
                "Erreur",
                f"Fichier config.json introuvable.\nRecherché dans :\n{config_path}"
            )
            return

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['language'] = lang_code
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Redémarrer l'application avec les mêmes arguments
        parent.destroy()
        # Attendre que la fenêtre soit réellement détruite pour éviter les conflits
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)
    except Exception as e:
        tk.messagebox.showerror("Erreur", f"Impossible de changer la langue : {e}")
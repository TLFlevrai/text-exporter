# src/gui/gui.py
import os
import tkinter as tk
from tkinter import filedialog
from src.gui.ui_builder.ui_builder import build_ui
from src.gui.extraction_controller import ExtractionController
from src.i18n import _, register_reload_callback, unregister_reload_callback
from src.network.server import ReceiveServer
from src.network.discovery import DiscoveryService
from src.config import get_config
from src.gui.theme import apply_theme
from .ui_builder.ui_widgets import UIWidgets


class PythonCodeExtractor:
    def __init__(
        self,
        root,
        server: ReceiveServer,
        discovery: DiscoveryService,
        extraction_service
    ):
        self.root = root
        self.server = server
        self.discovery = discovery
        self.service = extraction_service
        self.config = get_config()

        # Appliquer le thème au démarrage
        apply_theme()

        self._setup_window_title()
        self._setup_window_geometry()
        self.root.resizable(True, True)

        # Construire l'interface
        self.ui: UIWidgets = build_ui(root)

        # Contrôleur avec service injecté
        self.controller = ExtractionController(root, self.ui, service=self.service)
        self.ui.controller = self.controller

        # Transmettre les instances réseau au contrôleur (déjà démarrées)
        self.controller.set_server(self.server)
        self.controller.set_discovery(self.discovery)

        # Lier les boutons
        self._bind_buttons()

        # Raccourcis clavier
        self._bind_shortcuts()

        # Drag & drop pour le dossier
        self._setup_drag_drop()

        # Enregistrer callback pour mise à jour titre fenêtre au changement de langue
        self._register_i18n_callbacks()

        # Sauvegarder la géométrie à la fermeture
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _setup_window_title(self):
        """Configure le titre initial de la fenêtre."""
        self.root.title(_("Extracteur de code"))
        self._set_window_icon()

    def _setup_window_geometry(self):
        """Restaure la géométrie de la fenêtre depuis la config."""
        gui = self.config.get_all().gui
        width = gui.window_width
        height = gui.window_height
        x = gui.window_x
        y = gui.window_y

        if x >= 0 and y >= 0:
            self.root.geometry(f"{width}x{height}+{x}+{y}")
        else:
            # Centrer sur l'écran
            self.root.geometry(f"{width}x{height}")
            self.root.update_idletasks()
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            x = (screen_w - width) // 2
            y = (screen_h - height) // 2
            self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _save_window_geometry(self):
        """Sauvegarde la géométrie actuelle de la fenêtre."""
        try:
            self.config.update_gui(
                window_width=self.root.winfo_width(),
                window_height=self.root.winfo_height(),
                window_x=self.root.winfo_x(),
                window_y=self.root.winfo_y(),
            )
        except Exception:
            pass

    def _set_window_icon(self):
        """Définit l'icône de la fenêtre depuis un SVG."""
        try:
            from PIL import Image, ImageTk
            icon_path = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "logo.svg")
            icon_path = os.path.abspath(icon_path)
            if os.path.exists(icon_path):
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.root.iconphoto(True, photo)
                self.root._icon_photo = photo
        except Exception:
            pass

    def _register_i18n_callbacks(self):
        """Enregistre les callbacks pour mise à jour UI au changement de langue."""
        def refresh_window_title():
            self.root.title(_("Extracteur de code"))
        
        register_reload_callback(refresh_window_title)
        self._i18n_window_title_callback = refresh_window_title

    def _unregister_i18n_callbacks(self):
        """Désenregistre les callbacks i18n (à appeler à la fermeture)."""
        if hasattr(self, '_i18n_window_title_callback'):
            unregister_reload_callback(self._i18n_window_title_callback)
            delattr(self, '_i18n_window_title_callback')

    def _bind_buttons(self):
        """Lier les boutons de l'interface principale."""
        self.ui.browse_btn.config(command=self.controller.browse_folder)
        self.ui.clear_btn.config(command=self.controller.clear_info)
        self.ui.extract_btn.config(command=self.controller.extract_code)
        self.ui.select_btn.config(command=self.controller.open_selection_dialog)
        self.ui.version_btn.config(command=self.controller.open_version_explorer)
        self.ui.network_btn.config(command=self.controller.open_network_center)

    def _bind_shortcuts(self):
        """Configure les raccourcis clavier globaux."""
        # Ctrl+E : Extraire
        self.root.bind_all("<Control-e>", lambda e: self.controller.extract_code() if self.ui.extract_btn['state'] == 'normal' else None)
        # Ctrl+O : Parcourir (ouvrir dossier)
        self.root.bind_all("<Control-o>", lambda e: self.controller.browse_folder())
        # Ctrl+L : Effacer le journal
        self.root.bind_all("<Control-l>", lambda e: self.controller.clear_info())
        # Ctrl+Q : Quitter
        self.root.bind_all("<Control-q>", lambda e: self.on_close())
        # F5 : Rafraîchir (dans le gestionnaire de versions)
        self.root.bind_all("<F5>", lambda e: self._trigger_version_refresh())

    def _trigger_version_refresh(self):
        """Déclenche un rafraîchissement si le gestionnaire de versions est ouvert."""
        # Le contrôleur de version gère son propre F5 si ouvert
        pass

    def _setup_drag_drop(self):
        """Active le glisser-déposer de dossier sur le champ de saisie."""
        try:
            # Tkinter natif ne supporte pas le drag & drop nativement sur Windows sans tkdnd
            # On simule avec un clic droit sur le champ -> "Coller chemin" ou double-clic
            # Alternative: bind sur <Double-Button-1> pour ouvrir le sélecteur
            self.ui.folder_entry = self.root.nametowidget(self.ui.folder_path_var._name) if hasattr(self.ui.folder_path_var, '_name') else None
        except Exception:
            pass
        
        # Double-clic sur le champ dossier = ouvrir sélecteur
        def on_folder_double_click(event):
            self.controller.browse_folder()
        
        # Trouver le widget Entry associé à folder_path_var
        for child in self.ui.main_frame.winfo_children():
            if isinstance(child, tk.Entry) and child.cget('textvariable') == str(self.ui.folder_path_var):
                child.bind("<Double-Button-1>", on_folder_double_click)
                child.config(cursor="hand2")
                break

    def on_close(self):
        """Nettoyage à la fermeture."""
        self._save_window_geometry()
        self._unregister_i18n_callbacks()
        # Désenregistrer aussi les callbacks des menus et widgets
        from src.gui.ui_builder.menus import unregister_menu_refresh
        from src.gui.ui_builder.widgets import unregister_refresh_callback
        unregister_menu_refresh(self.ui)
        unregister_refresh_callback(self.ui)
        self.root.destroy()
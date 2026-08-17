# src/gui/gui.py
import tkinter as tk
from src.gui.ui_builder.ui_builder import build_ui
from src.gui.extraction_controller import ExtractionController
from src.i18n import _, register_reload_callback, unregister_reload_callback
from src.network.server import ReceiveServer
from src.network.discovery import DiscoveryService
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

        self._setup_window_title()
        width = 700
        height = 600
        self.root.geometry(f"{width}x{height}")
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

        # Enregistrer callback pour mise à jour titre fenêtre au changement de langue
        self._register_i18n_callbacks()

    def _setup_window_title(self):
        """Configure le titre initial de la fenêtre."""
        self.root.title(_("Extracteur de code"))

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

    def on_close(self):
        """Nettoyage à la fermeture."""
        self._unregister_i18n_callbacks()
        # Désenregistrer aussi les callbacks des menus et widgets
        from src.gui.ui_builder.menus import unregister_menu_refresh
        from src.gui.ui_builder.widgets import unregister_refresh_callback
        unregister_menu_refresh(self.ui)
        unregister_refresh_callback(self.ui)
# src/gui/gui.py
import tkinter as tk
from src.gui.ui_builder.ui_builder import build_ui
from src.gui.extraction_controller import ExtractionController
from src.services.extraction_service import ExtractionService
from src.i18n import _
from src.network.server import ReceiveServer
from src.network.discovery import DiscoveryService


class PythonCodeExtractor:
    def __init__(
        self,
        root,
        server: ReceiveServer,
        discovery: DiscoveryService,
        extraction_service: ExtractionService
    ):
        self.root = root
        self.server = server
        self.discovery = discovery
        self.service = extraction_service

        self.root.title(_("Extracteur de code"))
        width = 700
        height = 600
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(True, True)

        # Construire l'interface
        self.ui = build_ui(root)

        # Contrôleur avec service injecté
        self.controller = ExtractionController(root, self.ui, service=self.service)
        self.ui['controller'] = self.controller

        # Transmettre les instances réseau au contrôleur (déjà démarrées)
        self.controller.set_server(self.server)
        self.controller.set_discovery(self.discovery)

        # Lier les boutons
        self._bind_buttons()

    def _bind_buttons(self):
        """Lier les boutons de l'interface principale."""
        self.ui['browse_btn'].config(command=self.controller.browse_folder)
        self.ui['clear_btn'].config(command=self.controller.clear_info)
        self.ui['extract_btn'].config(command=self.controller.extract_code)
        self.ui['select_btn'].config(command=self.controller.open_selection_dialog)
        self.ui['version_btn'].config(command=self.controller.open_version_explorer)
        self.ui['network_btn'].config(command=self.controller.open_network_center)
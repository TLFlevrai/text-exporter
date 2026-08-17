# src/gui/controller/base_controller.py
import tkinter as tk
from src.services.extraction_service import ExtractionService
from src.logger import setup_logger
from src.i18n import _

logger = setup_logger(__name__)

class BaseController:
    """Classe de base contenant les dépendances partagées."""
    
    def __init__(self, root, ui_widgets, service=None):
        self.root = root
        self.ui = ui_widgets
        self.service = service or ExtractionService()
        # Utiliser un attribut privé pour éviter les conflits avec les setters
        self._selected_folder = ""
        self.selected_files = []
        self._is_extracting = False
        self.ui['controller'] = self

    @property
    def selected_folder(self):
        return self._selected_folder

    @selected_folder.setter
    def selected_folder(self, value):
        self._selected_folder = value

    @property
    def is_extracting(self):
        return self._is_extracting

    @is_extracting.setter
    def is_extracting(self, value):
        self._is_extracting = value

    def add_info(self, message):
        """Ajoute un message au journal."""
        self.ui['info_text'].insert(tk.END, message + "\n")
        self.ui['info_text'].see(tk.END)
        self.root.update_idletasks()

    def clear_info(self):
        """Efface le journal."""
        self.ui['info_text'].delete(1.0, tk.END)

    def update_status(self, message):
        """Met à jour la barre de statut."""
        self.ui['status_var'].set(message)

    def set_extracting(self, extracting):
        """Active/désactive l'état d'extraction."""
        self._is_extracting = extracting
        state = 'disabled' if extracting else 'normal'
        self.ui['extract_btn'].config(state=state)

    def get_include_options(self):
        """Retourne les options d'inclusion (pour la boîte de dialogue de sélection)."""
        return {
            'include_json': self.ui['include_json'].get(),
            'include_txt': self.ui['include_txt'].get(),
            'include_po': self.ui['include_po'].get(),
            'include_mo': self.ui['include_mo'].get(),
            'include_html': self.ui['include_html'].get(),
            'include_css': self.ui['include_css'].get(),
            'include_js': self.ui['include_js'].get(),
            'ignore_git': self.ui['ignore_git'].get(),         # NOUVEAU
            'ignore_pycache': self.ui['ignore_pycache'].get()  # NOUVEAU
        }

    def get_extraction_options(self):
        """Retourne toutes les options d'extraction (pour le moteur d'extraction)."""
        return {
            'include_json': self.ui['include_json'].get(),
            'include_subdirs': self.ui['include_subdirs'].get(),
            'show_file_paths': self.ui['show_file_paths'].get(),
            'include_structure': self.ui['include_structure'].get(),
            'include_txt': self.ui['include_txt'].get(),
            'include_po': self.ui['include_po'].get(),
            'include_mo': self.ui['include_mo'].get(),
            'include_html': self.ui['include_html'].get(),
            'include_css': self.ui['include_css'].get(),
            'include_js': self.ui['include_js'].get(),
            'ignore_init': self.ui['ignore_init'].get(),
            'ignore_git': self.ui['ignore_git'].get(),         # NOUVEAU
            'ignore_pycache': self.ui['ignore_pycache'].get(), # NOUVEAU
            'include_statistics': self.ui['include_statistics'].get(),
            'include_file_metadata': self.ui['include_file_metadata'].get()
        }

    def reset_selection(self):
        """Réinitialise la sélection de fichiers."""
        self.selected_files = []
        self.update_status(_("Prêt"))
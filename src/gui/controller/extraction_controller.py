# src/gui/controller/extraction_controller.py
import threading
from tkinter import messagebox
from .base_controller import BaseController
from src.gui.extraction_runner import run_extraction
from src.gui.recent_files import add_recent_folder
from src.i18n import _
from src.logger import setup_logger

logger = setup_logger(__name__)

class ExtractionController(BaseController):
    """Orchestration de l'extraction de code."""
    
    def open_selection_dialog(self):
        """Ouvre le dialogue de sélection des fichiers."""
        if not self._selected_folder:
            messagebox.showwarning(_("Attention"), _("Veuillez d'abord sélectionner un dossier"))
            return

        from src.gui.file_selector import select_files
        options = self.get_include_options()
        selected = select_files(self.root, self._selected_folder, options)

        if selected is not None:
            self.selected_files = selected
            count = len(selected)
            self.add_info(_("Sélection mise à jour : {} fichier(s) sélectionné(s)").format(count))
            self.update_status(_("Sélection : {} fichier(s)").format(count))
        else:
            self.add_info(_("Sélection annulée"))

    def extract_code(self, export_pdf=False):
        """Lance l'extraction du code, optionnellement avec export PDF."""
        if not self._selected_folder:
            messagebox.showwarning(_("Attention"), _("Veuillez d'abord sélectionner un dossier"))
            return

        if self.is_extracting:
            return

        self.set_extracting(True)
        self._do_extraction(export_pdf)

    def _do_extraction(self, export_pdf=False):
        """Exécute l'extraction dans un thread séparé."""
        options = self.get_extraction_options()
        selected = self.selected_files if self.selected_files else None

        self.update_status(_("Extraction en cours..."))
        self.add_info(_("\n--- Extraction en cours ---") + (" (PDF)" if export_pdf else ""))

        def progress_callback(current, total):
            if total > 0:
                progress = (current / total) * 100
                self.root.after(0, lambda: self.ui['progress_var'].set(progress))

        def log_callback(msg):
            self.root.after(0, lambda: self.add_info(msg))

        def extraction_thread():
            try:
                success, output_filename, stats = run_extraction(
                    controller=self,
                    service=self.service,
                    selected_folder=self._selected_folder,
                    options=options,
                    selected_files=selected,
                    progress_callback=progress_callback,
                    log_callback=log_callback,
                    export_pdf=export_pdf
                )

                self.root.after(0, lambda: self._extraction_finished(success, output_filename, stats))
            except Exception as e:
                logger.error(f"Erreur dans le thread d'extraction : {e}")
                self.root.after(0, lambda: self._extraction_error(e))

        threading.Thread(target=extraction_thread, daemon=True).start()

    def _extraction_finished(self, success, output_filename, stats):
        """Appelé après la fin de l'extraction."""
        self.ui['progress_var'].set(0)
        self.set_extracting(False)

        if success:
            self.update_status(_("Extraction terminée"))
            add_recent_folder(self._selected_folder)
            if 'update_recent_menu' in self.ui:
                self.ui['update_recent_menu']()
        else:
            self.update_status(_("Extraction échouée"))

    def _extraction_error(self, error):
        """Appelé en cas d'erreur dans le thread d'extraction."""
        self.ui['progress_var'].set(0)
        self.set_extracting(False)
        self.update_status(_("Extraction échouée"))
        messagebox.showerror(_("Erreur"), _("Une erreur est survenue : {}").format(error))

    def export_to_pdf(self):
        """Lance l'extraction et génère un PDF."""
        if not self._selected_folder:
            messagebox.showwarning(_("Attention"), _("Veuillez d'abord sélectionner un dossier"))
            return

        if self.is_extracting:
            return

        self.set_extracting(True)
        self._do_extraction(export_pdf=True)
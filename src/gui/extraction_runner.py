# src/gui/extraction_runner.py
import os
from tkinter import messagebox
from pathlib import Path
from src.i18n import _
from src.logger import setup_logger
from src.services.pdf_service import PDFService  # <-- nouveau

logger = setup_logger(__name__)

def run_extraction(controller, service, selected_folder, options, selected_files,
                   progress_callback, log_callback, export_pdf=False):  # <-- nouveau paramètre
    """
    Exécute l'extraction via le service et gère les mises à jour de l'UI.
    Retourne (success, output_filename, stats) ou (False, None, None)
    Si export_pdf est True, génère également un PDF.
    """
    try:
        success, output_filename, stats = service.extract_folder(
            selected_folder,
            options,
            progress_callback=progress_callback,
            log_callback=log_callback,
            selected_files=selected_files
        )

        if not success:
            controller.ui['status_var'].set(_("Extraction échouée"))
            controller.ui['progress_var'].set(0)
            messagebox.showerror(_("Erreur"), _("Échec de l'extraction (voir journal)"))
            return False, None, None

        # Succès
        controller.ui['status_var'].set(_("Extraction terminée"))
        controller.ui['progress_var'].set(0)
        controller.add_info(_("\n--- Extraction terminée avec succès ---"))
        controller.add_info(_("Fichier créé : {}").format(output_filename))
        controller.add_info(_("Emplacement : {}").format(os.path.abspath(output_filename)))
        controller.add_info(_("Fichiers extraits : {} (Python: {}, JSON: {}, TXT: {}, PO: {}, MO: {}, HTML: {}, CSS: {}, JS: {})").format(
            stats['total_files'], stats['py_count'], stats['json_count'], stats['txt_count'],
            stats['po_count'], stats['mo_count'], stats['html_count'], stats['css_count'], stats['js_count']
        ))

        # --- Génération du PDF si demandé ---
        pdf_path = None
        if export_pdf:
            txt_path = Path(output_filename)
            pdf_path = txt_path.with_suffix('.pdf')
            controller.add_info(_("Génération du PDF en cours..."))
            try:
                PDFService.convert_to_pdf(txt_path, pdf_path)
                controller.add_info(_("PDF généré : {}").format(pdf_path))
                controller.add_info(_("Emplacement : {}").format(os.path.abspath(pdf_path)))
            except Exception as e:
                logger.error(f"Erreur lors de la génération du PDF : {e}")
                controller.add_info(_("Erreur de génération du PDF : {}").format(e))

        # Message de succès (inclut le PDF si généré)
        success_msg = (
            _("Extraction terminée avec succès !\n\n")
            + _("Fichier créé : {}\n").format(output_filename)
            + _("Nombre de fichiers extraits : {}\n").format(stats['total_files'])
            + _("  - Fichiers Python : {}\n").format(stats['py_count'])
            + _("  - Fichiers JSON : {}\n").format(stats['json_count'])
            + _("  - Fichiers TXT : {}\n").format(stats['txt_count'])
            + _("  - Fichiers PO : {}\n").format(stats['po_count'])
            + _("  - Fichiers MO : {}\n").format(stats['mo_count'])
            + _("  - Fichiers HTML : {}\n").format(stats['html_count'])
            + _("  - Fichiers CSS : {}\n").format(stats['css_count'])
            + _("  - Fichiers JS : {}\n").format(stats['js_count'])
            + _("Emplacement : {}").format(os.path.abspath(output_filename))
        )
        if export_pdf and pdf_path:
            success_msg += _("\n\nPDF généré : {}").format(os.path.abspath(pdf_path))
        messagebox.showinfo(_("Succès"), success_msg)
        return True, output_filename, stats

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction : {e}")
        controller.ui['status_var'].set(_("Extraction échouée"))
        controller.ui['progress_var'].set(0)
        messagebox.showerror(_("Erreur"), _("Une erreur est survenue : {}").format(e))
        return False, None, None
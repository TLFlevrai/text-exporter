# src/gui/extraction_runner.py
import os
import time
from pathlib import Path
from typing import Callable, Optional, Tuple
from src.i18n import _
from src.logger import setup_logger
from src.services.pdf_service import PDFService  # <-- nouveau
from .errors import show_error, show_info
from .toast import show_toast

logger = setup_logger(__name__)

ProgressCallback = Callable[[int, int, str], None]
LogCallback = Callable[[str], None]

# Seuil pour afficher une ETA (sinon on reste sur le simple pourcentage)
ETA_THRESHOLD_SECONDS = 1.5


def _format_eta(seconds: float) -> str:
    """Formate une durée en secondes vers 'Xmin Ys' ou 'Ys'."""
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}min {secs}s"
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins}min"


def run_extraction(controller, service, selected_folder, options, selected_files,
                    progress_callback: ProgressCallback, log_callback: LogCallback,
                    export_pdf: bool = False,
                    cancel_event=None) -> Tuple[Optional[bool], Optional[str], Optional[dict]]:
    """
    Exécute l'extraction via le service et gère les mises à jour de l'UI.
    Retourne (success, output_filename, stats) :
      - (True, file, stats) : succès
      - (False, None, None) : échec
      - (None, None, None) : annulé
    Si export_pdf est True, génère également un PDF.
    """
    # Estimation du temps restant
    eta_state = {'start_time': None, 'last_current': 0, 'eta': None}

    def enhanced_progress_callback(current: int, total: int, current_file: str = "") -> None:
        """Callback de progression enrichi : pourcentage + ETA."""
        # Démarre le chrono au premier fichier
        if eta_state['start_time'] is None:
            eta_state['start_time'] = time.monotonic()
        else:
            elapsed = time.monotonic() - eta_state['start_time']
            delta = current - eta_state['last_current']
            if current > 0 and delta > 0 and elapsed > ETA_THRESHOLD_SECONDS:
                rate = delta / elapsed
                remaining = (total - current) / rate
                eta_state['eta'] = remaining
        eta_state['last_current'] = current

        if total > 0:
            progress = (current / total) * 100
            controller.root.after(0, lambda: controller.ui.progress_var.set(progress))

        # Mettre à jour la barre de statut avec fichier + ETA
        def _update_status():
            if current_file:
                if eta_state['eta'] is not None:
                    status_msg = _("Traitement : {} ({}/{}) - ETA {}").format(
                        current_file, current, total, _format_eta(eta_state['eta']))
                else:
                    status_msg = _("Traitement : {} ({}/{})").format(current_file, current, total)
                controller.update_status(_("Extraction en cours..."), status_msg)
            else:
                controller.update_status(_("Extraction en cours..."))
        controller.root.after(0, _update_status)

    def enhanced_log_callback(msg: str) -> None:
        controller.root.after(0, lambda: controller.add_info(msg))

    try:
        success, output_filename, stats = service.extract_folder(
            selected_folder,
            options,
            progress_callback=enhanced_progress_callback,
            log_callback=enhanced_log_callback,
            selected_files=selected_files,
            cancel_event=cancel_event,
        )

        if success is None:
            # Annulée par l'utilisateur
            controller.ui.status_var.set(_("Extraction annulée"))
            controller.ui.progress_var.set(0)
            return None, None, None

        if not success:
            controller.ui.status_var.set(_("Extraction échouée"))
            controller.ui.progress_var.set(0)
            controller.root.after(0, lambda: show_error(
                _("Erreur"), _("Échec de l'extraction (voir journal)"), parent=controller.root))
            return False, None, None

        # Succès
        controller.ui.status_var.set(_("Extraction terminée"))
        controller.ui.progress_var.set(0)
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

        # Toast non-bloquant (marshalé sur le thread UI) + message de succès
        def _show_success():
            try:
                show_toast(controller.root, _("Extraction terminée avec succès"), 'success')
            except Exception:
                pass
            show_info(_("Succès"), success_msg, parent=controller.root)
        controller.root.after(0, _show_success)
        return True, output_filename, stats

    except Exception as e:
        logger.error(f"Erreur lors de l'extraction : {e}")
        controller.ui.status_var.set(_("Extraction échouée"))
        controller.ui.progress_var.set(0)
        controller.root.after(0, lambda: show_error(
            _("Erreur"), _("Une erreur est survenue : {}").format(e), parent=controller.root))
        return False, None, None
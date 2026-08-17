# src/extractor/engine.py
from pathlib import Path
from typing import Optional, Callable
from src.extractor.file_discovery import FileDiscoveryService
from src.extractor.structure_generator import generate_project_structure
from src.extractor.report_builder import ReportBuilder
from src.extractor.file_processor import FileProcessor
from src.extractor.export_writer import write_file_section
from src.extractor.context import ExtractionContext
from src.logger import setup_logger

logger = setup_logger(__name__)


class ExtractionEngine:
    def __init__(self, context: ExtractionContext):
        self.context = context
        self.discovery = FileDiscoveryService(context.options)
        self.processor = FileProcessor(context)
        self.report_builder = ReportBuilder(context)

    def run(
        self,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
    ) -> bool:
        folder = self.context.folder_path
        output_path = self.context.output_path

        # 1) Découverte unique
        all_files = self.discovery.find_files(folder)
        if not all_files:
            msg = "Aucun fichier trouvé"
            if log_callback:
                log_callback(msg)
            logger.warning(msg)
            return False

        # 2) Filtrage sélection
        if self.context.selected_files is not None:
            selected_set = self.context.selected_files
            files = [(full, rel, ext) for full, rel, ext in all_files
                     if rel.as_posix() in selected_set]
            if not files:
                msg = "Aucun fichier sélectionné ne correspond aux fichiers trouvés"
                if log_callback:
                    log_callback(msg)
                logger.warning(msg)
                return False
        else:
            files = all_files

        total_files = len(files)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as out_file:
                # En-tête
                self._write_header(out_file, folder)

                # Structure
                if self.context.options.include_structure:
                    structure = generate_project_structure(folder, self.context.options)
                    out_file.write(structure)
                    out_file.write("\n--- FIN DE LA STRUCTURE ---\n\n")
                    if log_callback:
                        log_callback("✓ Structure du projet générée")
                    logger.info("Structure du projet générée")

                # 3) Boucle : TRAITER → ÉCRIRE (séparation des responsabilités)
                for i, (full_path, rel_path, ext) in enumerate(files):
                    if progress_callback:
                        progress_callback(i + 1, total_files)

                    # TRAITEMENT pur (testable sans I/O)
                    result = self.processor.process(full_path, rel_path, ext)

                    # ÉCRITURE (déléguée à export_writer)
                    write_file_section(out_file, result)

                    if log_callback:
                        if result.read_ok:
                            log_callback(f"✓ {rel_path} extrait")
                        else:
                            log_callback(f"✗ Erreur sur {rel_path}")

                # Statistiques
                if self.context.options.include_statistics:
                    out_file.write("\n--- FIN DES FICHIERS ---\n\n")
                    self.report_builder.write_statistics(out_file)

                logger.info(f"Extraction terminée avec succès : {output_path}")
                return True

        except Exception as e:
            logger.error(f"Erreur lors de l'extraction globale : {e}")
            if log_callback:
                log_callback(f"Erreur critique : {e}")
            return False

    def _write_header(self, out_file, folder):
        from src.utils import get_current_date
        out_file.write(f"Extraction du code du dossier : {folder}\n")
        out_file.write(f"Date d'extraction : {get_current_date()}\n")
        out_file.write("=" * 80 + "\n\n")
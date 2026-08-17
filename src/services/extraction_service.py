# src/services/extraction_service.py
import shutil
from pathlib import Path
from src.extractor.extractor import CodeExtractor
from src.versioning import VersionManager
from src.logger import setup_logger
from src.config import config, ExtractionOptions   # <-- Changement ici

logger = setup_logger(__name__)

class ExtractionService:
    def __init__(self, output_dir=None, version_file=None):
        self.output_dir = Path(output_dir or config.get('output_dir', 'out'))
        self.version_manager = VersionManager(version_file or config.get('version_file', 'extractor_version.txt'))

    def extract_folder(self, folder_path, options, progress_callback=None, log_callback=None, selected_files=None):
        """
        selected_files : liste de chemins relatifs (str) à extraire.
        Si None ou vide, on extrait tous les fichiers trouvés.
        """
        folder_path = Path(folder_path)
        default_options = config.get_all().extraction  # récupère l'objet ExtractionOptions
        # Fusionner avec les options de l'interface (dict)
        merged_dict = default_options.dict()
        merged_dict.update(options)
        extractor_options = ExtractionOptions(**merged_dict)

        extractor = CodeExtractor(options=extractor_options)

        folder_name = folder_path.name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        next_version = self.version_manager.get_next_version(folder_name, output_dir=self.output_dir)
        output_filename = self.output_dir / f"{folder_name}v{next_version}.txt"

        success, py_count, json_count, txt_count, po_count, mo_count, html_count, css_count, js_count = extractor.extract_all(
            folder_path,
            output_filename,
            progress_callback=progress_callback,
            log_callback=log_callback,
            selected_files=selected_files
        )

        if success:
            self.version_manager.use_version(folder_name, next_version)
            stats = {
                'py_count': py_count,
                'json_count': json_count,
                'txt_count': txt_count,
                'po_count': po_count,
                'mo_count': mo_count,
                'html_count': html_count,
                'css_count': css_count,
                'js_count': js_count,
                'total_files': py_count + json_count + txt_count + po_count + mo_count + html_count + css_count + js_count,
                'output_filename': str(output_filename)
            }
            logger.info(f"Extraction réussie : {output_filename}")
            return True, str(output_filename), stats
        else:
            logger.error("Échec de l'extraction")
            return False, None, None

    def clean_versions(self, archive=False):
        if archive:
            archive_dir = self.output_dir / config.get('archive_subdir', 'old_out')
            archive_dir.mkdir(parents=True, exist_ok=True)
            moved_files = []
            for item in self.output_dir.iterdir():
                if item.is_file() and item.suffix == '.txt':
                    try:
                        shutil.move(str(item), str(archive_dir / item.name))
                        moved_files.append(item.name)
                    except Exception as e:
                        logger.error(f"Erreur archivage {item} : {e}")
                        raise
            logger.info(f"Archivés : {', '.join(moved_files)}")

        self.version_manager.reset()
        logger.info("Historique des versions réinitialisé.")
        return "Nettoyage terminé" + (" (fichiers archivés)" if archive else "")
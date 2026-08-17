# src/services/extraction_service.py
import shutil
from pathlib import Path
from typing import Optional, List, Callable, Tuple
from src.config import ExtractionOptions
from src.versioning import VersionManager
from src.logger import setup_logger
from src.services.interfaces import ICodeExtractor, IVersionManager

logger = setup_logger(__name__)


class ExtractionService:
    """
    Service d'extraction (couche Use-Case).
    
    Ne connaît que les interfaces (protocoles), pas les implémentations concrètes.
    L'injection de dépendances se fait via le constructeur.
    """
    
    def __init__(
        self,
        extractor: ICodeExtractor,
        version_manager: IVersionManager,
        output_dir: Path
    ):
        self.extractor = extractor
        self.version_manager = version_manager
        self.output_dir = output_dir

    def extract_folder(
        self,
        folder_path: str | Path,
        options: dict,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        log_callback: Optional[Callable[[str], None]] = None,
        selected_files: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[dict]]:
        """
        selected_files : liste de chemins relatifs (str) à extraire.
        Si None ou vide, on extrait tous les fichiers trouvés.
        
        Retourne : (success, output_filename, stats_dict)
        """
        folder_path = Path(folder_path)
        
        # Fusionner options par défaut + options UI
        default_options = ExtractionOptions()
        merged_dict = default_options.model_dump()
        merged_dict.update(options)
        extractor_options = ExtractionOptions(**merged_dict)
        
        # Reconfigurer l'extracteur avec les nouvelles options
        # (CodeExtractor accepte les options au constructeur)
        self.extractor = self._create_extractor_with_options(extractor_options)

        folder_name = folder_path.name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        next_version = self.version_manager.get_next_version(folder_name, output_dir=self.output_dir)
        output_filename = self.output_dir / f"{folder_name}v{next_version}.txt"

        success, py_count, json_count, txt_count, po_count, mo_count, html_count, css_count, js_count = self.extractor.extract_all(
            str(folder_path),
            str(output_filename),
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

    def _create_extractor_with_options(self, options: ExtractionOptions) -> ICodeExtractor:
        """
        Crée un nouvel extracteur avec les options données.
        Note: comme CodeExtractor n'a pas de setter pour options, on recrée l'instance.
        Dans une vraie clean arch, l'extracteur serait stateless ou aurait un setter.
        """
        from src.extractor.extractor import CodeExtractor
        return CodeExtractor(options=options)

    def clean_versions(self, archive: bool = False) -> str:
        if archive:
            from src.config import config
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
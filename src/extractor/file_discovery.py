# src/extractor/file_discovery.py
import os
from pathlib import Path
from typing import List, Tuple, Set
from src.config import ExtractionOptions
from src.logger import setup_logger

logger = setup_logger(__name__)


class FileDiscoveryService:
    """
    Service unique de découverte de fichiers avec élagage (pruning) au niveau FS.
    Ne descend JAMAIS dans .git, __pycache__ ni autres dossiers ignorés.
    """

    def __init__(self, options: ExtractionOptions):
        self.options = options
        # Noms de dossiers à ignorer complètement (pruning)
        self._ignored_dir_names: Set[str] = set()
        if options.ignore_git:
            self._ignored_dir_names.add('.git')
        if options.ignore_pycache:
            self._ignored_dir_names.add('__pycache__')
        # Extensions autorisées (calculées une fois)
        self._allowed_extensions: List[str] = self._build_extension_list()

    # --------------------------------------------------------------------- #
    # API PUBLIQUE
    # --------------------------------------------------------------------- #

    def find_files(self, folder: str) -> List[Tuple[Path, Path, str]]:
        """
        Retourne la liste des fichiers à extraire.
        Format: [(full_path, relative_path, extension), ...]
        """
        folder_path = Path(folder).resolve()
        files: List[Tuple[Path, Path, str]] = []

        # os.walk topdown=True permet de modifier 'dirs' pour élaguer
        for root, dirs, filenames in os.walk(folder_path, topdown=True):
            # --- PRUNING : supprime les dossiers ignorés AVANT la descente ---
            # On modifie 'dirs' en place (seul moyen d'élaguer avec os.walk)
            dirs[:] = [d for d in dirs if d not in self._ignored_dir_names]

            # Si include_subdirs=False, on vide dirs pour ne pas descendre
            if not self.options.include_subdirs and root != str(folder_path):
                dirs[:] = []

            root_path = Path(root)
            for fname in filenames:
                if not self._is_extractable_file(fname):
                    continue

                full_path = root_path / fname
                # Vérification __init__.py (fichier, pas dossier)
                if self.options.ignore_init and fname == '__init__.py':
                    continue

                try:
                    rel_path = full_path.relative_to(folder_path)
                except ValueError:
                    # Hors racine (symlink étrange) -> ignorer
                    continue

                files.append((full_path, rel_path, full_path.suffix))

        return files

    def find_all_paths(self, folder: str) -> Tuple[List[Tuple[Path, Path, str]], Set[Path]]:
        """
        Retourne (fichiers, dossiers_parents) pour génération de structure.
        Utilise le MÊME parcours optimisé que find_files.
        """
        folder_path = Path(folder).resolve()
        files: List[Tuple[Path, Path, str]] = []
        dirs_set: Set[Path] = set()

        for root, dirs, filenames in os.walk(folder_path, topdown=True):
            # --- PRUNING IDENTIQUE ---
            dirs[:] = [d for d in dirs if d not in self._ignored_dir_names]

            if not self.options.include_subdirs and root != str(folder_path):
                dirs[:] = []

            root_path = Path(root)
            rel_root = root_path.relative_to(folder_path)
            rel_root_str = str(rel_root) if rel_root != Path('.') else ''

            # Collecter les dossiers (pour l'affichage structure)
            for d in dirs:
                if rel_root_str:
                    dirs_set.add(Path(rel_root_str) / d)
                else:
                    dirs_set.add(Path(d))

            # Collecter les fichiers
            for fname in filenames:
                if not self._is_extractable_file(fname):
                    continue
                if self.options.ignore_init and fname == '__init__.py':
                    continue

                full_path = root_path / fname
                try:
                    rel_path = full_path.relative_to(folder_path)
                except ValueError:
                    continue

                files.append((full_path, rel_path, full_path.suffix))

                # Parents du fichier pour l'arbre
                for parent in rel_path.parents:
                    if parent != Path('.'):
                        dirs_set.add(parent)

        return files, dirs_set

    # --------------------------------------------------------------------- #
    # INTERNE
    # --------------------------------------------------------------------- #

    def _is_extractable_file(self, filename: str) -> bool:
        """Vérification rapide d'extension (pas d'allocation Path)."""
        # On suppose que la liste est petite -> tuple plus rapide que set pour < 10 items
        return any(filename.endswith(ext) for ext in self._allowed_extensions)

    def _build_extension_list(self) -> List[str]:
        extensions = ['.py']
        if self.options.include_json:
            extensions.append('.json')
        if self.options.include_txt:
            extensions.append('.txt')
        if self.options.include_po:
            extensions.append('.po')
        if self.options.include_mo:
            extensions.append('.mo')
        if self.options.include_html:
            extensions.extend(['.html', '.htm'])
        if self.options.include_css:
            extensions.append('.css')
        if self.options.include_js:
            extensions.append('.js')
        return extensions
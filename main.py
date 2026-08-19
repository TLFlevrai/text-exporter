# main.py
import tkinter as tk
from pathlib import Path
from src.gui.gui import PythonCodeExtractor
from src.i18n import setup_i18n
from src.network.server import ReceiveServer
from src.network.discovery import DiscoveryService
from src.config import config
from src.logger import setup_logger
from src.versioning import VersionManager
from src.extractor.extractor import CodeExtractor
from src.services.extraction_service import ExtractionService

logger = setup_logger(__name__)


class Application:
    """Service d'application : gère le cycle de vie des services techniques.
    
    Composition Root : instancie et connecte toutes les dépendances (Clean Architecture).
    """

    def __init__(self):
        self.root = None
        self.app = None
        self.server = None
        self.discovery = None

    def start(self):
        """Démarre l'application complète."""
        # 0. Activation High-DPI AVANT la création de la fenêtre (rendu net 4K)
        from src.gui.premium import setup_dpi_awareness
        setup_dpi_awareness()

        # 1. Initialisation i18n AVANT création GUI
        setup_i18n()

        # 2. Création fenêtre Tkinter
        self.root = tk.Tk()

        # 3. Garde-fous : crash handler global + guard des callbacks Tk
        from src.gui.app_guard import install_excepthook, install_tk_callback_guard
        from src.gui.crash_report import show_crash_dialog
        install_excepthook(on_crash=lambda details: show_crash_dialog(self.root, details))
        install_tk_callback_guard(self.root, on_crash=lambda details: show_crash_dialog(self.root, details))

        # 4. Démarrage services réseau (AVANT GUI pour éviter race conditions UI)
        self._start_network_services()

        # 5. Composition Root : créer les dépendances du domaine
        extraction_service = self._create_extraction_service()

        # 6. Création GUI avec injection des services
        self.app = PythonCodeExtractor(
            root=self.root,
            server=self.server,
            discovery=self.discovery,
            extraction_service=extraction_service
        )

        # 7. Gestion fermeture propre
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 8. Boucle principale
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Interruption clavier reçue")
        finally:
            self._stop_network_services()

    def _create_extraction_service(self) -> ExtractionService:
        """Composition Root pour le service d'extraction (Domain/Use-Case layer)."""
        output_dir = Path(config.get('output_dir', 'out'))
        version_file = config.get('version_file', 'extractor_version.txt')
        
        # Implémentations concrètes (Infrastructure layer)
        version_manager = VersionManager(version_file)
        code_extractor = CodeExtractor()  # Options seront passées à chaque extraction
        
        # Service de cas d'utilisation (Domain layer) avec injection
        return ExtractionService(
            extractor=code_extractor,
            version_manager=version_manager,
            output_dir=output_dir
        )

    def _start_network_services(self):
        """Démarre les services réseau avec configuration centralisée."""
        try:
            output_dir = Path(config.get('output_dir', 'out'))
            received_subdir = config.get('received_subdir', 'received')
            received_dir = output_dir / received_subdir

            # Serveur de réception fichiers
            self.server = ReceiveServer(
                host=config.get('network.server_host', '127.0.0.1'),
                port=config.get('network.server_port', 50000),
                received_dir=received_dir
            )
            self.server.start()
            logger.info(f"Serveur réseau démarré sur {self.server.host}:{self.server.port}")

            # Service de découverte
            self.discovery = DiscoveryService(
                listen_port=config.get('network.discovery_port', 50001)
            )
            self.discovery.start_listener()
            logger.info("Service de découverte réseau démarré")

        except Exception as e:
            logger.error(f"Erreur lors du démarrage des services réseau : {e}")
            self._stop_network_services()
            raise

    def _stop_network_services(self):
        """Arrêt propre et ordonné des services réseau."""
        logger.info("Arrêt des services réseau...")

        if self.discovery:
            try:
                self.discovery.stop_listener()
                logger.info("Service de découverte arrêté")
            except Exception as e:
                logger.error(f"Erreur arrêt discovery : {e}")

        if self.server:
            try:
                self.server.stop()
                logger.info("Serveur réseau arrêté")
            except Exception as e:
                logger.error(f"Erreur arrêt serveur : {e}")

    def _on_close(self):
        """Callback fermeture fenêtre - délègue à l'application."""
        if self.app:
            self.app.on_close()
        self._stop_network_services()
        self.root.destroy()


def main():
    """Point d'entrée principal."""
    app = Application()
    app.start()


if __name__ == "__main__":
    main()
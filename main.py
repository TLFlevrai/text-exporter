# main.py
import tkinter as tk
import sys
from pathlib import Path
from src.gui.gui import PythonCodeExtractor
from src.i18n import setup_i18n
from src.network.server import ReceiveServer
from src.network.discovery import DiscoveryService
from src.config import config
from src.logger import setup_logger

logger = setup_logger(__name__)


class Application:
    """Service d'application : gère le cycle de vie des services techniques."""

    def __init__(self):
        self.root = None
        self.app = None
        self.server = None
        self.discovery = None

    def start(self):
        """Démarre l'application complète."""
        # 1. Initialisation i18n AVANT création GUI
        setup_i18n()

        # 2. Création fenêtre Tkinter
        self.root = tk.Tk()

        # 3. Démarrage services réseau (AVANT GUI pour éviter race conditions UI)
        self._start_network_services()

        # 4. Création GUI avec injection des services
        self.app = PythonCodeExtractor(
            root=self.root,
            server=self.server,
            discovery=self.discovery
        )

        # 5. Gestion fermeture propre
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 6. Boucle principale
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            logger.info("Interruption clavier reçue")
        finally:
            self._stop_network_services()

    def _start_network_services(self):
        """Démarre les services réseau avec configuration centralisée."""
        try:
            # Récupération config en Path (config.get retourne des str)
            output_dir = Path(config.get('output_dir', 'out'))
            received_subdir = config.get('received_subdir', 'received')
            received_dir = output_dir / received_subdir

            # Serveur de réception fichiers
            self.server = ReceiveServer(
                host=config.get('network.server_host', '0.0.0.0'),
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
            # Nettoyage partiel si échec
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
        self._stop_network_services()
        self.root.destroy()


def main():
    """Point d'entrée principal."""
    app = Application()
    app.start()


if __name__ == "__main__":
    main()
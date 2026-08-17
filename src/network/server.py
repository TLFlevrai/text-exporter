# src/network/server.py
import socket
import threading
import re
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import hmac
from src.logger import setup_logger
from src.config import get_config

logger = setup_logger(__name__)


class ReceiveServer(threading.Thread):
    MAX_FILENAME_LEN = 255
    MAX_FILE_SIZE = 100 * 1024 * 1024
    # Extensions par défaut, surchargées par config
    DEFAULT_ALLOWED_EXTENSIONS = {'.txt'}

    def __init__(self, host=None, port=None, received_dir=None, max_workers=10, on_event=None):
        super().__init__(daemon=True)
        cfg = get_config()
        self.host = host or cfg.get('network.server_host', '127.0.0.1')
        self.port = port or cfg.get('network.server_port', 50000)

        output_dir = Path(cfg.get('output_dir', 'out'))
        received_subdir = cfg.get('received_subdir', 'received')
        self.received_dir = (received_dir or output_dir / received_subdir)

        # Auth config
        self.auth_enabled = cfg.get('network.auth_enabled', True)
        self.auth_token = cfg.get('network.auth_token', 'change-me-secure-random-token').encode('utf-8')
        self.allowed_extensions = set(cfg.get('network.allowed_extensions', ['.txt']))

        if self.auth_enabled and self.auth_token == b'change-me-secure-random-token':
            logger.warning("[WARN] TOKEN D'AUTHENTIFICATION PAR DEFAUT DETECTE ! Changez 'auth_token' dans config.json")

        self._stop_event = threading.Event()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="ServerWorker")
        self._observers = []
        if on_event:
            self._observers.append(on_event)

    def add_observer(self, callback):
        if callback not in self._observers:
            self._observers.append(callback)

    def remove_observer(self, callback):
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify(self, event_type, data=None):
        for cb in self._observers:
            try:
                cb(event_type, data)
            except Exception as e:
                logger.error(f"Erreur dans un observateur : {e}")

    def _verify_auth(self, conn) -> bool:
        """Vérifie le token HMAC-SHA256 envoyé par le client."""
        if not self.auth_enabled:
            return True

        try:
            # Lire la taille du token (2 bytes)
            token_len_bytes = conn.recv(2)
            if not token_len_bytes:
                return False
            token_len = int.from_bytes(token_len_bytes, 'big')
            
            if token_len > 1024:  # Protection DoS
                return False

            # Lire le token client
            client_token = conn.recv(token_len)
            if len(client_token) != token_len:
                return False

            # Vérification HMAC en temps constant
            expected = hmac.new(self.auth_token, b'PYEXTRACTOR_AUTH', 'sha256').digest()
            return hmac.compare_digest(client_token, expected)

        except Exception:
            return False

    def run(self):
        self.received_dir.mkdir(parents=True, exist_ok=True)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                server_socket.bind((self.host, self.port))
                server_socket.listen(5)
                server_socket.settimeout(1.0)
                logger.info(f"Serveur démarré sur {self.host}:{self.port} (auth={'ON' if self.auth_enabled else 'OFF'})")
                self._notify('started', {'host': self.host, 'port': self.port})
            except Exception as e:
                logger.error(f"Impossible de démarrer le serveur : {e}")
                self._notify('start_failed', {'error': str(e)})
                return

            while not self._stop_event.is_set():
                try:
                    conn, addr = server_socket.accept()
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"Erreur accept : {e}")
                    break
                self._executor.submit(self._handle_client, conn, addr)

            self._notify('stopped', {})
            logger.info("Serveur arrêté")

    def _handle_client(self, conn, addr):
        try:
            # 1. AUTHENTIFICATION (avant tout traitement)
            if not self._verify_auth(conn):
                logger.warning(f"Authentification échouée pour {addr}")
                self._notify('rejected', {'reason': 'auth_failed', 'addr': addr})
                return

            # 2. Lecture nom fichier
            name_size_bytes = conn.recv(4)
            if not name_size_bytes:
                logger.warning(f"Connexion fermée par {addr} avant le nom")
                self._notify('rejected', {'reason': 'no_name', 'addr': addr})
                return
            name_size = int.from_bytes(name_size_bytes, 'big')
            if name_size > 1024:
                logger.warning(f"Nom trop long ({name_size}) de {addr}")
                self._notify('rejected', {'reason': 'name_too_long', 'addr': addr})
                return

            raw_filename = conn.recv(name_size).decode('utf-8')
            filename = Path(raw_filename).name
            if not filename:
                logger.warning(f"Nom vide de {addr}")
                self._notify('rejected', {'reason': 'empty_name', 'addr': addr})
                return

            filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
            if len(filename) > self.MAX_FILENAME_LEN:
                filename = filename[:self.MAX_FILENAME_LEN]

            ext = Path(filename).suffix.lower()
            if ext not in self.allowed_extensions:
                logger.warning(f"Extension non autorisée '{ext}' de {addr}")
                self._notify('rejected', {'reason': 'extension_not_allowed', 'filename': filename, 'addr': addr})
                return

            # 3. Taille des données
            data_size_bytes = conn.recv(8)
            if not data_size_bytes:
                logger.warning(f"Connexion fermée par {addr} avant la taille")
                self._notify('rejected', {'reason': 'no_size', 'addr': addr})
                return
            data_size = int.from_bytes(data_size_bytes, 'big')
            if data_size > self.MAX_FILE_SIZE:
                logger.warning(f"Fichier trop gros ({data_size}) de {addr}")
                self._notify('rejected', {'reason': 'file_too_large', 'size': data_size, 'addr': addr})
                return

            # 4. Réception données + hash (streaming pour éviter OOM)
            received_hash = b''
            file_data = b''
            bytes_received = 0
            
            while bytes_received < data_size + 32:
                remaining = (data_size + 32) - bytes_received
                chunk = conn.recv(min(4096, remaining))
                if not chunk:
                    break
                
                if bytes_received + len(chunk) <= data_size:
                    file_data += chunk
                else:
                    # On a dépassé les données fichier, le reste c'est le hash
                    split_idx = data_size - bytes_received
                    if split_idx > 0:
                        file_data += chunk[:split_idx]
                    received_hash += chunk[split_idx:]
                
                bytes_received += len(chunk)

            if len(file_data) != data_size or len(received_hash) != 32:
                logger.error(f"Taille reçue incorrecte pour {filename} de {addr}")
                self._notify('rejected', {'reason': 'incomplete', 'filename': filename, 'addr': addr})
                return

            # 5. Vérification hash
            computed_hash = sha256(file_data).digest()
            if not hmac.compare_digest(computed_hash, received_hash):
                logger.error(f"Hash incorrect pour {filename} de {addr}")
                self._notify('rejected', {'reason': 'hash_mismatch', 'filename': filename, 'addr': addr})
                return

            # 6. Sauvegarde
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_name = f"{timestamp}_{filename}"
            filepath = self.received_dir / safe_name
            with open(filepath, 'wb') as f:
                f.write(file_data)

            logger.info(f"Fichier reçu de {addr}: {filepath} ({data_size} octets)")
            self._notify('file_received', {
                'filename': filename,
                'path': str(filepath),
                'size': data_size,
                'addr': addr
            })

        except Exception as e:
            logger.error(f"Erreur inattendue avec {addr} : {e}")
            self._notify('rejected', {'reason': 'exception', 'error': str(e), 'addr': addr})
        finally:
            conn.close()

    def stop(self):
        logger.info("Arrêt du serveur demandé")
        self._stop_event.set()
        self._executor.shutdown(wait=True, cancel_futures=False)
        self._notify('stopped', {})
        logger.info("Serveur arrêté")
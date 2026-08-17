# src/network/discovery.py
import socket
import threading
import time
from src.config import get_config

class DiscoveryService:
    """Découvre les autres instances du programme sur le réseau local."""

    def __init__(self, listen_port=None):
        cfg = get_config()
        self.listen_port = listen_port or cfg.get('network.discovery_port', 50001)
        self._peers = {}
        self._lock = threading.Lock()
        self.broadcast_msg = cfg.get('network.broadcast_msg', 'PYEXTRACTOR_DISCOVER').encode()
        self.reply_msg = cfg.get('network.reply_msg', 'PYEXTRACTOR_HERE').encode()
        self._stop_event = threading.Event()
        self._listener_thread = None

    def start_listener(self):
        """Démarre le thread d'écoute des messages de découverte."""
        if self._listener_thread is None or not self._listener_thread.is_alive():
            self._stop_event.clear()
            self._listener_thread = threading.Thread(target=self._listen, daemon=True)
            self._listener_thread.start()

    def stop_listener(self):
        """Arrête proprement le thread d'écoute."""
        self._stop_event.set()
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=1.0)

    def _listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', self.listen_port))
            sock.settimeout(0.5)  # pour vérifier régulièrement _stop_event
            while not self._stop_event.is_set():
                try:
                    data, addr = sock.recvfrom(1024)
                except socket.timeout:
                    continue
                except Exception:
                    break
                if data == self.broadcast_msg:
                    hostname = socket.gethostname()
                    reply = f"{self.reply_msg.decode()}:{hostname}".encode()
                    sock.sendto(reply, addr)
                elif data.startswith(self.reply_msg):
                    parts = data.decode().split(':', 1)
                    if len(parts) == 2:
                        hostname = parts[1]
                        with self._lock:
                            self._peers[addr[0]] = hostname

    def scan(self, timeout=2):
        """
        Envoie un message broadcast et attend les réponses des autres instances.
        Retourne un dictionnaire {ip: hostname}.
        """
        self._peers.clear()
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(timeout)
            sock.bind(('', 0))
            sock.sendto(self.broadcast_msg, ('<broadcast>', self.listen_port))
            start = time.time()
            while time.time() - start < timeout:
                try:
                    data, addr = sock.recvfrom(1024)
                    if data.startswith(self.reply_msg):
                        parts = data.decode().split(':', 1)
                        if len(parts) == 2:
                            hostname = parts[1]
                            with self._lock:
                                self._peers[addr[0]] = hostname
                except socket.timeout:
                    break
        with self._lock:
            return dict(self._peers)
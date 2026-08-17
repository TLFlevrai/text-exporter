# src/gui/network_center/log_tab.py
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from src.i18n import _

class LogTab(ttk.Frame):
    def __init__(self, parent, dialog):
        super().__init__(parent)
        self.dialog = dialog
        self.log_entries = []  # pour limiter

        self._create_widgets()

    def _create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(main, wrap=tk.WORD, height=20, state=tk.DISABLED)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scroll = ttk.Scrollbar(main, orient=tk.VERTICAL, command=self.text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.config(yscrollcommand=scroll.set)

        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame, text=_("Effacer"), command=self._clear).pack(side=tk.LEFT, padx=2)

    def _append(self, message):
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, message + "\n")
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)
        # Limiter à 500 lignes
        lines = self.text.get(1.0, tk.END).count('\n')
        if lines > 500:
            self.text.config(state=tk.NORMAL)
            self.text.delete(1.0, 2.0)  # supprime la première ligne
            self.text.config(state=tk.DISABLED)

    def _clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)

    def on_event(self, event_type, data):
        """Reçoit les événements du serveur et les formate."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if event_type == 'started':
            host = data.get('host', '?')
            port = data.get('port', '?')
            self._append(f"[{timestamp}] ✅ Serveur démarré sur {host}:{port}")
        elif event_type == 'stopped':
            self._append(f"[{timestamp}] ⏹ Serveur arrêté")
        elif event_type == 'file_received':
            filename = data.get('filename', '')
            size = data.get('size', 0)
            addr = data.get('addr', ('?', '?'))
            self._append(f"[{timestamp}] 📥 Fichier reçu : {filename} ({size} o) de {addr[0]}")
        elif event_type == 'rejected':
            reason = data.get('reason', 'inconnu')
            filename = data.get('filename', '')
            addr = data.get('addr', ('?', '?'))
            self._append(f"[{timestamp}] ❌ Rejeté : {reason} {filename} de {addr[0]}")
        elif event_type == 'start_failed':
            error = data.get('error', '')
            self._append(f"[{timestamp}] ❌ Échec au démarrage : {error}")
        else:
            self._append(f"[{timestamp}] ℹ️ Événement : {event_type} {data}")
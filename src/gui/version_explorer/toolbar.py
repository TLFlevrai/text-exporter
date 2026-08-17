# src/gui/version_explorer/toolbar.py
import tkinter as tk
from tkinter import ttk
from src.i18n import _, pgettext


class Toolbar:
    """Barre d'outils avec les actions principales."""

    def __init__(self, parent, controller):
        self.controller = controller
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)

        # Contexte "button" pour distinguer des messages de confirmation
        self.archive_btn = ttk.Button(frame, text=pgettext("button", "Archiver"), command=self.controller.archive_selected)
        self.archive_btn.pack(side=tk.LEFT, padx=2)

        self.restore_btn = ttk.Button(frame, text=pgettext("button", "Restaurer"), command=self.controller.restore_selected)
        self.restore_btn.pack(side=tk.LEFT, padx=2)

        self.delete_btn = ttk.Button(frame, text=pgettext("button", "Supprimer"), command=self.controller.delete_selected)
        self.delete_btn.pack(side=tk.LEFT, padx=2)

        self.open_folder_btn = ttk.Button(frame, text=pgettext("button", "Ouvrir dossier"), command=self.controller.open_folder)
        self.open_folder_btn.pack(side=tk.LEFT, padx=2)

        self.refresh_btn = ttk.Button(frame, text=_("Rafraîchir"), command=self.controller.refresh)
        self.refresh_btn.pack(side=tk.LEFT, padx=2)

        self.reset_btn = ttk.Button(frame, text=_("Réinitialiser compteur"), command=self.controller.reset_counter)
        self.reset_btn.pack(side=tk.LEFT, padx=2)

        # Boutons de sélection (ajoutés après)
        self.select_all_btn = ttk.Button(frame, text=_("Tout sélectionner"), command=self.controller.select_all)
        self.select_all_btn.pack(side=tk.LEFT, padx=2)

        self.deselect_all_btn = ttk.Button(frame, text=_("Tout désélectionner"), command=self.controller.deselect_all)
        self.deselect_all_btn.pack(side=tk.LEFT, padx=2)
# src/gui/version_explorer/version_tree.py
import tkinter as tk
from tkinter import ttk
from typing import Callable, List, Optional
from src.i18n import _
from src.utils import human_size
from src.services.version_service import VersionEntry
from .utils import parse_date_from_header, get_file_stats


class VersionTree:
    """Table des versions avec colonnes et sélection multiple."""

    def __init__(
        self,
        parent,
        on_version_select: Callable[[List[VersionEntry]], None],
        on_version_double_click: Callable[[VersionEntry], None],
    ):
        self.on_version_select = on_version_select
        self.on_version_double_click = on_version_double_click
        self.current_entries = []
        self.selected_items = set()  # pour suivre les IID sélectionnés
        self._entry_map = {}  # iid -> VersionEntry

        self.tree = ttk.Treeview(
            parent,
            columns=('version', 'date', 'size', 'files', 'lines', 'status'),
            show='tree headings',
            selectmode='extended'  # sélection multiple
        )
        self.tree.heading('#0', text=_('Sélection'))
        self.tree.heading('version', text=_('Version'))
        self.tree.heading('date', text=_('Date'))
        self.tree.heading('size', text=_('Taille'))
        self.tree.heading('files', text=_('Fichiers'))
        self.tree.heading('lines', text=_('Lignes'))
        self.tree.heading('status', text=_('Statut'))

        self.tree.column('#0', width=80, anchor='center')
        self.tree.column('version', width=80, anchor='center')
        self.tree.column('date', width=150, anchor='w')
        self.tree.column('size', width=100, anchor='e')
        self.tree.column('files', width=80, anchor='center')
        self.tree.column('lines', width=80, anchor='center')
        self.tree.column('status', width=100, anchor='w')

        # Bind events
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Double-1>', self._on_double_click)

        # Scrollbar
        scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        # Pack
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def populate(self, entries):
        """Remplit le treeview avec les entrées d'un projet."""
        self.clear()
        self.current_entries = sorted(entries, key=lambda e: e.version, reverse=True)
        for entry in self.current_entries:
            # Sélection par défaut (non sélectionné)
            select_char = '☐'
            item = self.tree.insert(
                '', 
                'end', 
                text=select_char,  # La colonne #0 est définie par 'text'
                values=(
                    f"v{entry.version}",
                    entry.date,
                    human_size(entry.size),
                    entry.file_count,
                    entry.line_count,
                    _(entry.status.capitalize())
                )
            )
            # Stocker l'entry associée à l'item
            self._entry_map[item] = entry

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.current_entries = []
        self.selected_items.clear()
        self._entry_map.clear()

    def _on_select(self, event):
        selected_iids = self.tree.selection()
        # Mettre à jour les glyphes : on garde les sélectionnés avec ☑
        for item in self.tree.get_children():
            if item in selected_iids:
                self.tree.item(item, text='☑')
                self.selected_items.add(item)
            else:
                self.tree.item(item, text='☐')
                self.selected_items.discard(item)
        # Appeler le callback avec la liste des entrées sélectionnées
        selected_entries = []
        for iid in selected_iids:
            entry = self._entry_map.get(iid)
            if entry:
                selected_entries.append(entry)
        self.on_version_select(selected_entries)

    def _on_double_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            entry = self._entry_map.get(item)
            if entry:
                self.on_version_double_click(entry)

    def get_selected_entries(self):
        """Retourne la liste des VersionEntry sélectionnés (cochés)."""
        selected = []
        for iid in self.selected_items: 
            entry = self._entry_map.get(iid)
            if entry:
                selected.append(entry)
        return selected

    def get_all_entries(self):
        return self.current_entries

    def select_all(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)
            self.tree.item(item, text='☑')
            self.selected_items.add(item)
        # Mettre à jour le callback avec toutes les entrées
        all_entries = [self._entry_map.get(item) for item in self.tree.get_children() if item in self._entry_map]
        self.on_version_select(all_entries)

    def deselect_all(self):
        for item in self.tree.get_children():
            self.tree.selection_remove(item)
            self.tree.item(item, text='☐')
            self.selected_items.discard(item)
        self.on_version_select([])

    def refresh(self):
        # Repeupler avec les mêmes entrées (les métadonnées peuvent avoir changé)
        entries = self.current_entries
        self.populate(entries)
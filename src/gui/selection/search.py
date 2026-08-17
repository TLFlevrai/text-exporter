# src/gui/selection/search.py
import tkinter as tk
from tkinter import ttk
from src.i18n import _

class SearchBar:
    def __init__(self, parent, tree, all_items):
        self.tree = tree
        self.all_items = all_items
        self.var = tk.StringVar()
        # Utilisation de trace_add (moderne) au lieu de trace
        self.var.trace_add('write', self._on_search_change)

        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(frame, text=_("Rechercher :")).pack(side=tk.LEFT, padx=(0, 5))
        entry = ttk.Entry(frame, textvariable=self.var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        entry.focus_set()

        self.entry = entry

    def _on_search_change(self, *args):
        pattern = self.var.get().strip().lower()
        if not pattern:
            for item in self.all_items:
                self.tree.reattach(item, self.tree.parent(item), self.tree.index(item))
            return
        for item in self.all_items:
            text = self.tree.item(item, "text").lower()
            if pattern in text:
                self.tree.reattach(item, self.tree.parent(item), self.tree.index(item))
            else:
                self.tree.detach(item)
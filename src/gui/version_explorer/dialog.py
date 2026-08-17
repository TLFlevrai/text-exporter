# src/gui/version_explorer/dialog.py
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from src.i18n import _, pgettext
from src.logger import setup_logger
from src.services.version_service import VersionArchiveService
from .project_panel import ProjectPanel
from .version_tree import VersionTree
from .preview_pane import PreviewPane
from .toolbar import Toolbar

logger = setup_logger(__name__)


class VersionExplorerDialog(tk.Toplevel):
    """Fenetre de gestion des versions d'export."""

    def __init__(self, parent, service=None):
        super().__init__(parent)
        self.title(_("Gestionnaire de versions"))
        self.geometry("1000x650")
        self.minsize(800, 500)
        self.transient(parent)
        self.grab_set()

        self.service = service or VersionArchiveService()
        self.projects_data = {}
        self.current_project = None
        self.preview_entry = None

        self._create_widgets()
        self._start_scan()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _create_widgets(self):
        main = ttk.Frame(self, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        self.project_panel = ProjectPanel(main, self._on_project_selected)

        right_pane = ttk.Frame(main)
        right_pane.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.version_tree = VersionTree(right_pane, self._on_versions_selected, self._on_version_double_click)

        self.preview_pane = PreviewPane(right_pane)

        self.toolbar = Toolbar(right_pane, self)

        self.status_var = tk.StringVar(value=_("Scan en cours..."))
        status_label = ttk.Label(main, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X, pady=(5, 0))

    def _start_scan(self):
        self.status_var.set(_("Scan des fichiers en cours..."))
        threading.Thread(target=self._scan_thread, daemon=True).start()

    def _scan_thread(self):
        try:
            self.projects_data = self.service.scan_projects()
        except Exception as e:
            logger.error(f"Erreur lors du scan : {e}")
            self.after(0, lambda: self._scan_error(str(e)))
            return
        self.after(0, self._scan_finished)

    def _scan_finished(self):
        self.status_var.set(_("Scan termine"))
        self.project_panel.update_projects(self.projects_data)
        if self.projects_data:
            first = list(self.projects_data.keys())[0]
            self._on_project_selected(first)

    def _scan_error(self, error_msg):
        self.status_var.set(_("Erreur de scan : {}").format(error_msg))
        messagebox.showerror(_("Erreur"), _("Impossible de scanner les fichiers : {}").format(error_msg))

    def _on_project_selected(self, project_name):
        self.current_project = project_name
        entries = self.projects_data.get(project_name, [])
        self.version_tree.populate(entries)
        self.preview_pane.show_entry(None)
        self.status_var.set(_("Projet : {} ({} versions)").format(project_name, len(entries)))

    def _on_versions_selected(self, selected_entries):
        if selected_entries:
            self.preview_entry = selected_entries[0]
            self.preview_pane.show_entry(selected_entries[0])
        else:
            self.preview_entry = None
            self.preview_pane.show_entry(None)

    def _on_version_double_click(self, entry):
        try:
            os.startfile(str(entry.path))
        except Exception as e:
            logger.error(f"Impossible d'ouvrir {entry.path} : {e}")
            messagebox.showerror(_("Erreur"), _("Impossible d'ouvrir le fichier : {}").format(e))

    def archive_selected(self):
        entries = self.version_tree.get_selected_entries()
        if not entries:
            messagebox.showinfo(_("Information"), _("Aucune version selectionnee."))
            return
        to_archive = [e for e in entries if e.status == 'active']
        if not to_archive:
            messagebox.showinfo(_("Information"), _("Les versions selectionnees sont deja archivees."))
            return
        if not messagebox.askyesno(_("Confirmation"),
                                   pgettext("confirmation", "Archiver {} version(s) ?").format(len(to_archive))):
            return

        self.status_var.set(_("Archivage en cours..."))
        threading.Thread(target=self._archive_thread, args=(to_archive,), daemon=True).start()

    def _archive_thread(self, entries):
        try:
            for entry in entries:
                self.service.archive(entry)
            self.after(0, self._refresh_after_action)
        except Exception as e:
            logger.error(f"Erreur lors de l'archivage : {e}")
            self.after(0, lambda: self._show_error(_("Erreur d'archivage"), str(e)))

    def restore_selected(self):
        entries = self.version_tree.get_selected_entries()
        if not entries:
            messagebox.showinfo(_("Information"), _("Aucune version selectionnee."))
            return
        to_restore = [e for e in entries if e.status == 'archived']
        if not to_restore:
            messagebox.showinfo(_("Information"), _("Les versions selectionnees sont deja actives."))
            return
        if not messagebox.askyesno(_("Confirmation"),
                                   pgettext("confirmation", "Restaurer {} version(s) ?").format(len(to_restore))):
            return

        self.status_var.set(_("Restauration en cours..."))
        threading.Thread(target=self._restore_thread, args=(to_restore,), daemon=True).start()

    def _restore_thread(self, entries):
        try:
            for entry in entries:
                self.service.restore(entry)
            self.after(0, self._refresh_after_action)
        except Exception as e:
            logger.error(f"Erreur lors de la restauration : {e}")
            self.after(0, lambda: self._show_error(_("Erreur de restauration"), str(e)))

    def delete_selected(self):
        entries = self.version_tree.get_selected_entries()
        if not entries:
            messagebox.showinfo(_("Information"), _("Aucune version selectionnee."))
            return
        if not messagebox.askyesno(_("Confirmation"),
                                   pgettext("confirmation", "Supprimer definitivement {} version(s) ? Cette action est irreversible.").format(len(entries))):
            return

        self.status_var.set(_("Suppression en cours..."))
        threading.Thread(target=self._delete_thread, args=(entries,), daemon=True).start()

    def _delete_thread(self, entries):
        try:
            for entry in entries:
                self.service.delete(entry)
            self.after(0, self._refresh_after_action)
        except Exception as e:
            logger.error(f"Erreur lors de la suppression : {e}")
            self.after(0, lambda: self._show_error(_("Erreur de suppression"), str(e)))

    def reset_counter(self):
        if not self.current_project:
            messagebox.showinfo(_("Information"), _("Aucun projet selectionne."))
            return
        if not messagebox.askyesno(_("Confirmation"),
                                   pgettext("confirmation", "Reinitialiser le compteur de versions pour le projet '{}' ?").format(self.current_project)):
            return
        try:
            self.service.reset_project(self.current_project)
            self.status_var.set(_("Compteur reinitialise pour {}").format(self.current_project))
            self._refresh_after_action()
        except Exception as e:
            logger.error(f"Erreur lors de la reinitialisation : {e}")
            self._show_error(_("Erreur"), str(e))

    def open_folder(self):
        if not self.current_project:
            messagebox.showinfo(_("Information"), _("Aucun projet selectionne."))
            return
        folder = self.service.output_dir
        if not folder.exists():
            messagebox.showerror(_("Erreur"), _("Le dossier de sortie n'existe pas."))
            return
        try:
            os.startfile(str(folder))
        except Exception as e:
            logger.error(f"Impossible d'ouvrir {folder} : {e}")
            messagebox.showerror(_("Erreur"), _("Impossible d'ouvrir le dossier : {}").format(e))

    def refresh(self):
        self.status_var.set(_("Rafraichissement..."))
        threading.Thread(target=self._refresh_thread, daemon=True).start()

    def _refresh_thread(self):
        try:
            self.projects_data = self.service.scan_projects()
        except Exception as e:
            logger.error(f"Erreur lors du rafraichissement : {e}")
            self.after(0, lambda: self._show_error(_("Erreur de rafraichissement"), str(e)))
            return
        self.after(0, self._refresh_after_action)

    def _refresh_after_action(self):
        try:
            self.projects_data = self.service.scan_projects()
        except Exception as e:
            logger.error(f"Erreur lors du re-scan : {e}")
            self._show_error(_("Erreur"), str(e))
            return
        self.project_panel.update_projects(self.projects_data)
        if self.current_project in self.projects_data:
            self._on_project_selected(self.current_project)
        else:
            if self.projects_data:
                first = list(self.projects_data.keys())[0]
                self._on_project_selected(first)
            else:
                self.version_tree.clear()
                self.preview_pane.show_entry(None)
        self.status_var.set(_("Mise a jour terminee"))

    def select_all(self):
        self.version_tree.select_all()

    def deselect_all(self):
        self.version_tree.deselect_all()

    def _show_error(self, title, msg):
        messagebox.showerror(title, msg)

    def _on_close(self):
        self.destroy()
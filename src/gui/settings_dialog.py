# src/gui/settings_dialog.py
"""Boîte de dialogue des paramètres avec onglets."""
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from src.i18n import _, pgettext
from src.config import get_config
from src.gui.theme_editor import open_theme_editor
from src.logger import setup_logger

logger = setup_logger(__name__)


class SettingsDialog(tk.Toplevel):
    """Dialogue des paramètres avec onglets : Formats, Filtres, Sortie, Avancé."""

    def __init__(self, parent, ui_widgets):
        super().__init__(parent)
        self.title(_("Paramètres"))
        self.geometry("550x500")
        self.minsize(500, 450)
        self.transient(parent)
        self.grab_set()

        self.ui = ui_widgets
        self.config = get_config()
        self._original_options = {}

        self._create_widgets()
        self._load_current_values()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        parent = self.master
        if parent:
            x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        main = ttk.Frame(self, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # Notebook (onglets)
        self.notebook = ttk.Notebook(main)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        # --- Onglet Formats ---
        self.formats_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.formats_frame, text=_("Formats"))
        self._create_formats_tab()

        # --- Onglet Filtres ---
        self.filters_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.filters_frame, text=_("Filtres"))
        self._create_filters_tab()

        # --- Onglet Sortie ---
        self.output_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.output_frame, text=_("Sortie"))
        self._create_output_tab()

        # --- Onglet Avancé ---
        self.advanced_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(self.advanced_frame, text=_("Avancé"))
        self._create_advanced_tab()

        # Boutons bas
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text=_("Restaurer défauts"), command=self._reset_defaults).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text=_("Annuler"), command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text=_("OK"), command=self._on_ok).pack(side=tk.RIGHT, padx=5)

    def _create_formats_tab(self):
        """Onglet Formats - quels types de fichiers inclure."""
        formats = [
            ('include_json', _("Fichiers JSON (.json)"), True),
            ('include_html', _("Fichiers HTML (.html, .htm)"), True),
            ('include_css', _("Fichiers CSS (.css)"), True),
            ('include_js', _("Fichiers JavaScript (.js)"), True),
            ('include_txt', _("Fichiers texte (.txt)"), False),
            ('include_po', _("Fichiers traduction PO (.po)"), False),
            ('include_mo', _("Fichiers traduction MO (.mo)"), False),
        ]

        for i, (key, label, default) in enumerate(formats):
            var = getattr(self.ui, key, None)
            if var:
                cb = ttk.Checkbutton(self.formats_frame, text=label, variable=var)
                cb.grid(row=i, column=0, sticky=tk.W, pady=4, padx=5)
                self._original_options[key] = var.get()

    def _create_filters_tab(self):
        """Onglet Filtres - exclusions et inclusions de dossiers/fichiers."""
        filters = [
            ('include_subdirs', _("Inclure les sous-dossiers"), True),
            ('show_file_paths', _("Afficher les chemins complets"), True),
            ('include_structure', _("Inclure la structure du projet"), True),
            ('ignore_init', _("Ignorer __init__.py"), False),
            ('ignore_git', _("Ignorer le dossier .git"), True),
            ('ignore_pycache', _("Ignorer __pycache__"), True),
        ]

        for i, (key, label, default) in enumerate(filters):
            var = getattr(self.ui, key, None)
            if var:
                cb = ttk.Checkbutton(self.filters_frame, text=label, variable=var)
                cb.grid(row=i, column=0, sticky=tk.W, pady=4, padx=5)
                self._original_options[key] = var.get()

    def _create_output_tab(self):
        """Onglet Sortie - options de sortie et métadonnées."""
        outputs = [
            ('include_statistics', _("Inclure les statistiques globales"), True),
            ('include_file_metadata', _("Métadonnées par fichier (taille, lignes)"), False),
            ('archive_old', _("Archiver les anciennes versions"), False),
        ]

        for i, (key, label, default) in enumerate(outputs):
            var = getattr(self.ui, key, None)
            if var:
                cb = ttk.Checkbutton(self.output_frame, text=label, variable=var)
                cb.grid(row=i, column=0, sticky=tk.W, pady=4, padx=5)
                self._original_options[key] = var.get()

        # Dossier de sortie
        ttk.Separator(self.output_frame, orient=tk.HORIZONTAL).grid(
            row=len(outputs), column=0, sticky=(tk.W, tk.E), pady=15)

        ttk.Label(self.output_frame, text=_("Dossier de sortie :"), font=('Arial', 9, 'bold')).grid(
            row=len(outputs)+1, column=0, sticky=tk.W, pady=2)

        output_dir_frame = ttk.Frame(self.output_frame)
        output_dir_frame.grid(row=len(outputs)+2, column=0, sticky=(tk.W, tk.E), pady=2)
        output_dir_frame.columnconfigure(0, weight=1)

        self.output_dir_var = tk.StringVar(value=self.config.get('output_dir', 'out'))
        ttk.Entry(output_dir_frame, textvariable=self.output_dir_var, state='readonly').grid(
            row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        ttk.Button(output_dir_frame, text=_("Modifier..."), command=self._change_output_dir).grid(
            row=0, column=1)

    def _create_advanced_tab(self):
        """Onglet Avancé - options moins communes."""
        # Hauteur du journal
        ttk.Label(self.advanced_frame, text=_("Hauteur du journal (lignes) :")).grid(
            row=0, column=0, sticky=tk.W, pady=8)

        self.log_height_var = tk.IntVar(value=self.config.get('gui.log_height', 12))
        log_spin = ttk.Spinbox(self.advanced_frame, from_=4, to=50, textvariable=self.log_height_var, width=10)
        log_spin.grid(row=0, column=1, sticky=tk.W, padx=10, pady=8)

        # Auto-scroll
        self.log_autoscroll_var = tk.BooleanVar(value=self.config.get('gui.log_autoscroll', True))
        ttk.Checkbutton(
            self.advanced_frame,
            text=_("Défilement automatique du journal"),
            variable=self.log_autoscroll_var
        ).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=8)

        # Langue
        ttk.Label(self.advanced_frame, text=_("Langue :")).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.lang_var = tk.StringVar(value=self.config.get('language', 'fr'))
        lang_combo = ttk.Combobox(self.advanced_frame, textvariable=self.lang_var, 
                                   values=['fr', 'en'], state='readonly', width=10)
        lang_combo.grid(row=2, column=1, sticky=tk.W, padx=10, pady=8)
        lang_combo.bind('<<ComboboxSelected>>', lambda e: self._on_language_change())

        # Thème
        ttk.Label(self.advanced_frame, text=_("Thème :")).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.theme_var = tk.StringVar(value=self.config.get('gui.theme', 'system'))
        theme_combo = ttk.Combobox(self.advanced_frame, textvariable=self.theme_var,
                                    values=['system', 'light', 'dark', 'custom'], state='readonly', width=10)
        theme_combo.grid(row=3, column=1, sticky=tk.W, padx=10, pady=8)
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self._on_theme_change())

        # Bouton éditeur de thème
        ttk.Button(self.advanced_frame, text=_("Personnaliser le thème..."), 
                   command=lambda: open_theme_editor(self)).grid(row=3, column=2, padx=10, pady=8)

        # Presets d'export
        ttk.Separator(self.advanced_frame, orient=tk.HORIZONTAL).grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)

        ttk.Label(self.advanced_frame, text=_("Preset d'export :"), font=('Arial', 9, 'bold')).grid(
            row=5, column=0, sticky=tk.W, pady=2)

        preset_frame = ttk.Frame(self.advanced_frame)
        preset_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=2)
        preset_frame.columnconfigure(1, weight=1)

        self.preset_var = tk.StringVar(value='custom')
        presets = [
            ('python_only', _("Python uniquement")),
            ('web_assets', _("Assets Web (HTML/CSS/JS)")),
            ('full', _("Complet (tout)")),
            ('minimal', _("Minimal (Python + structure)")),
            ('custom', _("Personnalisé")),
        ]
        for i, (val, label) in enumerate(presets):
            rb = ttk.Radiobutton(preset_frame, text=label, variable=self.preset_var, value=val,
                                  command=self._apply_preset)
            rb.grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=2)

        ttk.Button(preset_frame, text=_("Enregistrer comme preset..."), 
                   command=self._save_preset).grid(row=3, column=0, columnspan=2, pady=8)

    def _load_current_values(self):
        """Charge les valeurs actuelles depuis l'UI et la config."""
        pass  # Les variables sont déjà liées aux widgets

    def _change_output_dir(self):
        """Change le dossier de sortie."""
        from tkinter import filedialog
        path = filedialog.askdirectory(title=_("Choisir le dossier de sortie"))
        if path:
            self.output_dir_var.set(path)

    def _on_language_change(self):
        """Change la langue à chaud."""
        from src.i18n import change_language
        change_language(self.lang_var.get())

    def _on_theme_change(self):
        """Change le thème."""
        from src.gui.theme import apply_theme
        apply_theme(self.theme_var.get())

    def _apply_preset(self):
        """Applique un preset prédéfini."""
        preset = self.preset_var.get()
        
        presets = {
            'python_only': {
                'include_json': False, 'include_html': False, 'include_css': False,
                'include_js': False, 'include_txt': False, 'include_po': False,
                'include_mo': False, 'include_structure': True,
            },
            'web_assets': {
                'include_json': True, 'include_html': True, 'include_css': True,
                'include_js': True, 'include_txt': False, 'include_po': False,
                'include_mo': False, 'include_structure': True,
            },
            'full': {
                'include_json': True, 'include_html': True, 'include_css': True,
                'include_js': True, 'include_txt': True, 'include_po': True,
                'include_mo': True, 'include_structure': True,
                'include_statistics': True, 'include_file_metadata': True,
            },
            'minimal': {
                'include_json': False, 'include_html': False, 'include_css': False,
                'include_js': False, 'include_txt': False, 'include_po': False,
                'include_mo': False, 'include_structure': True,
                'include_statistics': True,
            },
        }
        
        if preset in presets:
            for key, value in presets[preset].items():
                var = getattr(self.ui, key, None)
                if var:
                    var.set(value)

    def _save_preset(self):
        """Enregistre la config actuelle comme preset personnalisé."""
        # TODO: implémenter la sauvegarde de presets personnalisés
        messagebox.showinfo(_("Info"), _("Fonctionnalité à venir : sauvegarde de presets personnalisés"))

    def _reset_defaults(self):
        """Restaure les valeurs par défaut."""
        if messagebox.askyesno(_("Confirmation"), _("Restaurer tous les paramètres par défaut ?")):
            cfg = self.config.get_all()
            extraction = cfg.extraction
            
            defaults = {
                'include_json': extraction.include_json,
                'include_subdirs': extraction.include_subdirs,
                'show_file_paths': extraction.show_file_paths,
                'include_structure': extraction.include_structure,
                'include_txt': extraction.include_txt,
                'include_po': extraction.include_po,
                'include_mo': extraction.include_mo,
                'include_html': extraction.include_html,
                'include_css': extraction.include_css,
                'include_js': extraction.include_js,
                'ignore_init': extraction.ignore_init,
                'ignore_git': extraction.ignore_git,
                'ignore_pycache': extraction.ignore_pycache,
                'include_statistics': extraction.include_statistics,
                'include_file_metadata': extraction.include_file_metadata,
                'archive_old': cfg.gui.archive_old if hasattr(cfg.gui, 'archive_old') else False,
            }
            
            for key, value in defaults.items():
                var = getattr(self.ui, key, None)
                if var:
                    var.set(value)
            
            self.log_height_var.set(12)
            self.log_autoscroll_var.set(True)
            self.preset_var.set('custom')

    def _on_ok(self):
        """Sauvegarde et ferme."""
        # Sauvegarder les options GUI
        self.config.update_gui(
            log_height=self.log_height_var.get(),
            log_autoscroll=self.log_autoscroll_var.get(),
            theme=self.theme_var.get(),
        )
        
        # Sauvegarder le dossier de sortie
        self.config._config.output_dir = self.output_dir_var.get()
        self.config.save()
        
        # Sauvegarder la langue
        self.config._config.language = self.lang_var.get()
        self.config.save()
        
        self.destroy()


def open_settings_dialog(parent, ui_widgets):
    """Ouvre la boîte de dialogue des paramètres."""
    SettingsDialog(parent, ui_widgets)
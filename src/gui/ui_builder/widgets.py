# src/gui/ui_builder/widgets.py
import tkinter as tk
from tkinter import ttk
from src.config import get_config
from src.i18n import _, LazyString, register_reload_callback, unregister_reload_callback
from .ui_widgets import UIWidgets


def build_widgets(parent, ui: UIWidgets):
    main_frame = ttk.Frame(parent, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    ui.main_frame = main_frame

    # Titre
    title_label = ttk.Label(main_frame, text=str(LazyString("Extracteur de code Python, JSON & TXT")),
                            font=('Arial', 16, 'bold'))
    title_label.grid(row=0, column=0, columnspan=2, pady=10)
    _register_lazy_widget(ui, title_label, "Extracteur de code Python, JSON & TXT")

    # Dossier
    folder_label = ttk.Label(main_frame, text=str(LazyString("Dossier à scanner :")))
    folder_label.grid(row=1, column=0, sticky=tk.W, pady=5)
    _register_lazy_widget(ui, folder_label, "Dossier à scanner :")

    folder_entry = ttk.Entry(main_frame, textvariable=ui.folder_path_var,
                             width=60, state='readonly')
    folder_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    browse_btn = ttk.Button(main_frame, text=str(LazyString("Parcourir")))
    browse_btn.grid(row=1, column=2, padx=5, pady=5)
    ui.browse_btn = browse_btn
    _register_lazy_widget(ui, browse_btn, "Parcourir")

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=2, column=0, columnspan=3, pady=10)

    extract_btn = ttk.Button(button_frame, text=str(LazyString("Extraire le code")), state='disabled')
    extract_btn.pack(side=tk.LEFT, padx=5)
    ui.extract_btn = extract_btn
    _register_lazy_widget(ui, extract_btn, "Extraire le code")

    select_btn = ttk.Button(button_frame, text=str(LazyString("Sélectionner...")))
    select_btn.pack(side=tk.LEFT, padx=5)
    ui.select_btn = select_btn
    _register_lazy_widget(ui, select_btn, "Sélectionner...")

    version_btn = ttk.Button(button_frame, text=str(LazyString("Gérer les versions")))
    version_btn.pack(side=tk.LEFT, padx=5)
    ui.version_btn = version_btn
    _register_lazy_widget(ui, version_btn, "Gérer les versions")

    network_btn = ttk.Button(button_frame, text=str(LazyString("Réseau...")))
    network_btn.pack(side=tk.LEFT, padx=5)
    ui.network_btn = network_btn
    _register_lazy_widget(ui, network_btn, "Réseau...")

    clear_btn = ttk.Button(button_frame, text=str(LazyString("Effacer le journal")))
    clear_btn.pack(side=tk.LEFT, padx=5)
    ui.clear_btn = clear_btn
    _register_lazy_widget(ui, clear_btn, "Effacer le journal")

    progress_bar = ttk.Progressbar(main_frame, variable=ui.progress_var,
                                   maximum=100, length=500)
    progress_bar.grid(row=3, column=0, columnspan=3, pady=10)
    ui.progress_bar = progress_bar

    # Journal - LabelFrame text needs special handling
    info_frame = ttk.LabelFrame(main_frame, text=str(LazyString("Journal")), padding="5")
    info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    ui.info_frame = info_frame
    _register_lazy_labelframe(ui, info_frame, "Journal")

    log_height = get_config().get('gui.log_height', 12)
    info_text = tk.Text(info_frame, height=log_height, width=80, wrap=tk.WORD)
    info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_text.yview)
    scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    info_text.configure(yscrollcommand=scrollbar.set)
    ui.info_text = info_text

    status_bar = ttk.Label(main_frame, textvariable=ui.status_var,
                           relief=tk.SUNKEN, anchor=tk.W)
    status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
    ui.status_bar = status_bar

    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(4, weight=1)
    info_frame.columnconfigure(0, weight=1)
    info_frame.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)

    def toggle_log_visibility():
        if ui.log_visible.get():
            ui.info_frame.grid()
        else:
            ui.info_frame.grid_remove()

    view_menu = ui.view_menu
    if view_menu:
        view_menu.entryconfig(0, command=toggle_log_visibility)

    # Enregistrer le callback de rafraîchissement global
    _register_refresh_callback(ui)


def _register_lazy_widget(ui: UIWidgets, widget, msgid: str):
    """Enregistre un widget avec son message pour mise à jour ultérieure."""
    ui._lazy_widgets.append((widget, msgid, 'text'))


def _register_lazy_labelframe(ui: UIWidgets, labelframe, msgid: str):
    """Enregistre un LabelFrame avec son message pour mise à jour ultérieure."""
    ui._lazy_widgets.append((labelframe, msgid, 'label'))


def _register_refresh_callback(ui: UIWidgets):
    """Enregistre un callback pour rafraîchir tous les widgets à la volée."""
    def refresh_all_widgets():
        for widget, msgid, attr in ui._lazy_widgets:
            try:
                translated = _(msgid)
                if attr == 'text':
                    widget.config(text=translated)
                elif attr == 'label':
                    widget.config(text=translated)
            except Exception:
                pass  # Widget peut être détruit
    
    from src.i18n import register_reload_callback
    register_reload_callback(refresh_all_widgets)
    ui._i18n_refresh_callback = refresh_all_widgets


def unregister_refresh_callback(ui: UIWidgets):
    """Désenregistre le callback de rafraîchissement (à appeler à la fermeture)."""
    callback = ui._i18n_refresh_callback
    if callback:
        from src.i18n import unregister_reload_callback
        unregister_reload_callback(callback)
        ui._i18n_refresh_callback = None
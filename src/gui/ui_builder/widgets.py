# src/gui/ui_builder/widgets.py
import tkinter as tk
from tkinter import ttk
from src.config import get_config
from src.i18n import _, LazyString, register_reload_callback, unregister_reload_callback
from .ui_widgets import UIWidgets
from .tooltip import add_lazy_tooltip
from .log_widget import LogWidget


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
    ui.folder_entry = folder_entry

    browse_btn = ttk.Button(main_frame, text=str(LazyString("Parcourir")))
    browse_btn.grid(row=1, column=2, padx=5, pady=5)
    ui.browse_btn = browse_btn
    _register_lazy_widget(ui, browse_btn, "Parcourir")
    tooltip = add_lazy_tooltip(browse_btn, "Sélectionner le dossier à scanner (Ctrl+O)")
    ui._lazy_tooltips.append(tooltip)

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=2, column=0, columnspan=3, pady=10)

    extract_btn = ttk.Button(button_frame, text=str(LazyString("Extraire le code")), state='disabled')
    extract_btn.pack(side=tk.LEFT, padx=5)
    ui.extract_btn = extract_btn
    _register_lazy_widget(ui, extract_btn, "Extraire le code")
    tooltip = add_lazy_tooltip(extract_btn, "Lancer l'extraction du code (Ctrl+E)")
    ui._lazy_tooltips.append(tooltip)

    cancel_btn = ttk.Button(button_frame, text=str(LazyString("Annuler")), state='disabled')
    cancel_btn.pack(side=tk.LEFT, padx=5)
    ui.cancel_btn = cancel_btn
    _register_lazy_widget(ui, cancel_btn, "Annuler")
    tooltip = add_lazy_tooltip(cancel_btn, "Annuler l'extraction en cours")
    ui._lazy_tooltips.append(tooltip)

    select_btn = ttk.Button(button_frame, text=str(LazyString("Sélectionner...")))
    select_btn.pack(side=tk.LEFT, padx=5)
    ui.select_btn = select_btn
    _register_lazy_widget(ui, select_btn, "Sélectionner...")
    tooltip = add_lazy_tooltip(select_btn, "Choisir les fichiers spécifiques à extraire")
    ui._lazy_tooltips.append(tooltip)

    version_btn = ttk.Button(button_frame, text=str(LazyString("Gérer les versions")))
    version_btn.pack(side=tk.LEFT, padx=5)
    ui.version_btn = version_btn
    _register_lazy_widget(ui, version_btn, "Gérer les versions")
    tooltip = add_lazy_tooltip(version_btn, "Ouvrir le gestionnaire de versions d'export")
    ui._lazy_tooltips.append(tooltip)

    network_btn = ttk.Button(button_frame, text=str(LazyString("Réseau...")))
    network_btn.pack(side=tk.LEFT, padx=5)
    ui.network_btn = network_btn
    _register_lazy_widget(ui, network_btn, "Réseau...")
    tooltip = add_lazy_tooltip(network_btn, "Ouvrir le centre de transfert réseau")
    ui._lazy_tooltips.append(tooltip)

    clear_btn = ttk.Button(button_frame, text=str(LazyString("Effacer le journal")))
    clear_btn.pack(side=tk.LEFT, padx=5)
    ui.clear_btn = clear_btn
    _register_lazy_widget(ui, clear_btn, "Effacer le journal")
    tooltip = add_lazy_tooltip(clear_btn, "Vider le journal d'activité (Ctrl+L)")
    ui._lazy_tooltips.append(tooltip)

    progress_bar = ttk.Progressbar(main_frame, variable=ui.progress_var,
                                   maximum=100, length=500)
    progress_bar.grid(row=3, column=0, columnspan=3, pady=10)
    ui.progress_bar = progress_bar

    # Widget de journal (encapsule Text, recherche, barre de statut)
    log_widget = LogWidget(
        parent=main_frame,
        ui=ui,
        status_var=ui.status_var,
        log_visible_var=ui.log_visible,
    )
    ui.log_widget = log_widget

    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(4, weight=1)
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)

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
        for tooltip in ui._lazy_tooltips:
            try:
                tooltip.refresh()
            except Exception:
                pass
    
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
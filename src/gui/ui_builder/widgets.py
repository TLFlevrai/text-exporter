# src/gui/ui_builder/widgets.py
import tkinter as tk
from tkinter import ttk
from src.config import get_config
from src.i18n import _, LazyString, register_reload_callback, unregister_reload_callback
from .ui_widgets import UIWidgets
from .tooltip import add_lazy_tooltip


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

# Journal - LabelFrame text needs special handling
    info_frame = ttk.LabelFrame(main_frame, text=str(LazyString("Journal")), padding="5")
    info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    ui.info_frame = info_frame
    _register_lazy_labelframe(ui, info_frame, "Journal")

    # Barre de recherche dans le journal
    search_frame = ttk.Frame(info_frame)
    search_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 5))
    search_frame.columnconfigure(1, weight=1)

    ttk.Label(search_frame, text=_("Rechercher :")).grid(row=0, column=0, padx=(0, 5))
    ui.log_search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=ui.log_search_var, width=30)
    search_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
    search_entry.bind("<KeyRelease>", lambda e: _on_log_search(ui))
    search_entry.bind("<Return>", lambda e: _on_log_search_next(ui))
    _register_lazy_widget(ui, search_entry, "")  # Pour le placeholder si nécessaire

    ui.log_search_next_btn = ttk.Button(search_frame, text=_("Suivant"), command=lambda: _on_log_search_next(ui), width=8)
    ui.log_search_next_btn.grid(row=0, column=2, padx=2)
    _register_lazy_widget(ui, ui.log_search_next_btn, "Suivant")

    ui.log_search_prev_btn = ttk.Button(search_frame, text=_("Précédent"), command=lambda: _on_log_search_prev(ui), width=8)
    ui.log_search_prev_btn.grid(row=0, column=3, padx=2)
    _register_lazy_widget(ui, ui.log_search_prev_btn, "Précédent")

    ui.log_search_clear_btn = ttk.Button(search_frame, text=_("Effacer"), command=lambda: _on_log_search_clear(ui), width=8)
    ui.log_search_clear_btn.grid(row=0, column=4, padx=2)
    _register_lazy_widget(ui, ui.log_search_clear_btn, "Effacer")

    log_height = get_config().get('gui.log_height', 12)
    info_text = tk.Text(info_frame, height=log_height, width=80, wrap=tk.WORD)
    info_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    ui.info_text = info_text

    scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_text.yview)
    scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
    info_text.configure(yscrollcommand=lambda *args: _on_scroll(info_text, scrollbar, *args))

    # Configuration du tag pour la surbrillance
    info_text.tag_configure("search_highlight", background="yellow", foreground="black")
    
    # Stocker les positions de recherche
    ui._log_search_matches = []
    ui._log_search_current = -1

    info_frame.rowconfigure(1, weight=1)

    # Barre de statut améliorée avec détails
    status_frame = ttk.Frame(main_frame)
    status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
    status_frame.columnconfigure(1, weight=1)

    status_bar = ttk.Label(status_frame, textvariable=ui.status_var, relief=tk.SUNKEN, anchor=tk.W)
    status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
    ui.status_bar = status_bar

    # Checkbox auto-scroll à droite de la barre de statut
    ui.log_autoscroll_var = tk.BooleanVar(value=get_config().get('gui.log_autoscroll', True))
    autoscroll_cb = ttk.Checkbutton(
        status_frame,
        text=_("Auto-scroll"),
        variable=ui.log_autoscroll_var,
        command=lambda: _save_autoscroll_pref(ui)
    )
    autoscroll_cb.grid(row=0, column=1, sticky=tk.E, padx=5)
    _register_lazy_widget(ui, autoscroll_cb, "Auto-scroll")

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


def _on_scroll(text_widget, scrollbar, *args):
    """Callback de scroll - met à jour la scrollbar et gère l'auto-scroll."""
    scrollbar.set(*args)
    # Si l'utilisateur scrolle manuellement vers le haut, désactiver temporairement l'auto-scroll
    # (on ne le désactive pas définitivement, juste pour cette session de scroll)


def _save_autoscroll_pref(ui: UIWidgets):
    """Sauvegarde la préférence d'auto-scroll dans la config."""
    try:
        config = get_config()
        config.update_gui(log_autoscroll=ui.log_autoscroll_var.get())
    except Exception:
        pass


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


# --- Fonctions de recherche dans le journal ---

def _on_log_search(ui: UIWidgets):
    """Recherche dans le journal et surligne les correspondances."""
    text_widget = ui.info_text
    search_term = ui.log_search_var.get().strip()
    
    # Supprimer les surbrillances précédentes
    text_widget.tag_remove("search_highlight", "1.0", tk.END)
    ui._log_search_matches = []
    ui._log_search_current = -1
    
    if not search_term:
        return
    
    # Rechercher toutes les occurrences
    start = "1.0"
    while True:
        pos = text_widget.search(search_term, start, tk.END, nocase=True)
        if not pos:
            break
        end = f"{pos}+{len(search_term)}c"
        text_widget.tag_add("search_highlight", pos, end)
        ui._log_search_matches.append(pos)
        start = end
    
    if ui._log_search_matches:
        ui._log_search_current = 0
        _highlight_current_match(ui)


def _on_log_search_next(ui: UIWidgets):
    """Va à la correspondance suivante."""
    if not ui._log_search_matches:
        _on_log_search(ui)
        return
    
    ui._log_search_current = (ui._log_search_current + 1) % len(ui._log_search_matches)
    _highlight_current_match(ui)


def _on_log_search_prev(ui: UIWidgets):
    """Va à la correspondance précédente."""
    if not ui._log_search_matches:
        _on_log_search(ui)
        return
    
    ui._log_search_current = (ui._log_search_current - 1) % len(ui._log_search_matches)
    _highlight_current_match(ui)


def _on_log_search_clear(ui: UIWidgets):
    """Efface la recherche et les surbrillances."""
    ui.log_search_var.set("")
    ui.info_text.tag_remove("search_highlight", "1.0", tk.END)
    ui._log_search_matches = []
    ui._log_search_current = -1


def _highlight_current_match(ui: UIWidgets):
    """Surligne et fait défiler vers la correspondance courante."""
    if not ui._log_search_matches or ui._log_search_current < 0:
        return
    
    text_widget = ui.info_text
    pos = ui._log_search_matches[ui._log_search_current]
    
    # Retirer la surbrillance de toutes, puis ajouter sur la courante
    text_widget.tag_remove("search_highlight", "1.0", tk.END)
    search_term = ui.log_search_var.get().strip()
    end = f"{pos}+{len(search_term)}c"
    text_widget.tag_add("search_highlight", pos, end)
    
    # S'assurer que la correspondance est visible
    text_widget.see(pos)
    text_widget.mark_set(tk.INSERT, pos)
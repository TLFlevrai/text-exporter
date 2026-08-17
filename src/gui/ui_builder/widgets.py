# src/gui/ui_builder/widgets.py
import tkinter as tk
from tkinter import ttk
from src.config import config
from src.i18n import _

def build_widgets(parent, ui):
    main_frame = ttk.Frame(parent, padding="10")
    main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    ui['main_frame'] = main_frame

    title_label = ttk.Label(main_frame, text=_("Extracteur de code Python, JSON & TXT"),
                            font=('Arial', 16, 'bold'))
    title_label.grid(row=0, column=0, columnspan=2, pady=10)

    folder_label = ttk.Label(main_frame, text=_("Dossier à scanner :"))
    folder_label.grid(row=1, column=0, sticky=tk.W, pady=5)

    folder_entry = ttk.Entry(main_frame, textvariable=ui['folder_path_var'],
                             width=60, state='readonly')
    folder_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    browse_btn = ttk.Button(main_frame, text=_("Parcourir"))
    browse_btn.grid(row=1, column=2, padx=5, pady=5)
    ui['browse_btn'] = browse_btn

    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=2, column=0, columnspan=3, pady=10)

    extract_btn = ttk.Button(button_frame, text=_("Extraire le code"), state='disabled')
    extract_btn.pack(side=tk.LEFT, padx=5)
    ui['extract_btn'] = extract_btn

    # Bouton "Sélectionner..."
    select_btn = ttk.Button(button_frame, text=_("Sélectionner..."))
    select_btn.pack(side=tk.LEFT, padx=5)
    ui['select_btn'] = select_btn

    # Bouton "Gérer les versions"
    version_btn = ttk.Button(button_frame, text=_("🗂 Gérer les versions"))
    version_btn.pack(side=tk.LEFT, padx=5)
    ui['version_btn'] = version_btn

    # NOUVEAU : Bouton "🌐 Réseau..."
    network_btn = ttk.Button(button_frame, text=_("🌐 Réseau..."))
    network_btn.pack(side=tk.LEFT, padx=5)
    ui['network_btn'] = network_btn

    clear_btn = ttk.Button(button_frame, text=_("Effacer le journal"))
    clear_btn.pack(side=tk.LEFT, padx=5)
    ui['clear_btn'] = clear_btn

    progress_bar = ttk.Progressbar(main_frame, variable=ui['progress_var'],
                                   maximum=100, length=500)
    progress_bar.grid(row=3, column=0, columnspan=3, pady=10)
    ui['progress_bar'] = progress_bar

    info_frame = ttk.LabelFrame(main_frame, text=_("Journal"), padding="5")
    info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
    ui['info_frame'] = info_frame

    log_height = config.get('gui.log_height', 12)
    info_text = tk.Text(info_frame, height=log_height, width=80, wrap=tk.WORD)
    info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=info_text.yview)
    scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    info_text.configure(yscrollcommand=scrollbar.set)
    ui['info_text'] = info_text

    status_bar = ttk.Label(main_frame, textvariable=ui['status_var'],
                           relief=tk.SUNKEN, anchor=tk.W)
    status_bar.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
    ui['status_bar'] = status_bar

    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(4, weight=1)
    info_frame.columnconfigure(0, weight=1)
    info_frame.rowconfigure(0, weight=1)
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)

    def toggle_log_visibility():
        if ui['log_visible'].get():
            ui['info_frame'].grid()
        else:
            ui['info_frame'].grid_remove()

    view_menu = ui.get('view_menu')
    if view_menu:
        view_menu.entryconfig(0, command=toggle_log_visibility)
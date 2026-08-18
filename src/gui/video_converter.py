# src/gui/video_converter.py
"""Convertisseur vidéo vers MP3."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import subprocess
import threading
from src.i18n import _
from src.logger import setup_logger

logger = setup_logger(__name__)


class VideoToMP3Converter(tk.Toplevel):
    """Fenêtre de conversion vidéo vers MP3."""

    def __init__(self, parent):
        super().__init__(parent)
        self.title(_("Convertisseur Vidéo → MP3"))
        self.geometry("600x450")
        self.minsize(550, 400)
        self.transient(parent)
        self.grab_set()

        self.video_path = None
        self.output_path = None
        self.ffmpeg_available = self._check_ffmpeg()

        self._create_widgets()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        parent = self.master
        if parent:
            x = parent.winfo_rootx() + (parent.winfo_width() - self.winfo_width()) // 2
            y = parent.winfo_rooty() + (parent.winfo_height() - self.winfo_height()) // 2
            self.geometry(f"+{x}+{y}")

    def _check_ffmpeg(self) -> bool:
        """Vérifie si ffmpeg est disponible."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _create_widgets(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Titre
        title = ttk.Label(main, text=_("Convertisseur Vidéo vers MP3"), font=('Arial', 14, 'bold'))
        title.pack(pady=(0, 10))

        # Avertissement ffmpeg
        if not self.ffmpeg_available:
            warning_frame = ttk.Frame(main)
            warning_frame.pack(fill=tk.X, pady=(0, 15))
            warning_label = ttk.Label(
                warning_frame,
                text=_("⚠ FFmpeg non détecté. La conversion ne fonctionnera pas.\n"
                       "Installez FFmpeg et assurez-vous qu'il est dans le PATH."),
                foreground='red',
                wraplength=500,
                justify=tk.CENTER
            )
            warning_label.pack()
            ttk.Button(warning_frame, text=_("Télécharger FFmpeg"), 
                      command=self._open_ffmpeg_download).pack(pady=5)

        # Sélection fichier vidéo
        video_frame = ttk.LabelFrame(main, text=_("Fichier vidéo source"), padding=10)
        video_frame.pack(fill=tk.X, pady=(0, 15))
        video_frame.columnconfigure(0, weight=1)

        self.video_entry = ttk.Entry(video_frame, state='readonly')
        self.video_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        video_btn = ttk.Button(video_frame, text=_("Parcourir..."), command=self._select_video)
        video_btn.grid(row=0, column=1)

        # Formats supportés
        formats_label = ttk.Label(video_frame, 
            text=_("Formats supportés : MP4, AVI, MKV, MOV, WMV, FLV, WebM, M4V, 3GP, OGV, MPEG, MPG"),
            font=('Arial', 8), foreground='gray')
        formats_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))

        # Options de conversion
        options_frame = ttk.LabelFrame(main, text=_("Options de conversion"), padding=10)
        options_frame.pack(fill=tk.X, pady=(0, 15))
        options_frame.columnconfigure(1, weight=1)

        # Qualité audio
        ttk.Label(options_frame, text=_("Qualité audio :")).grid(row=0, column=0, sticky=tk.W, pady=4)
        self.quality_var = tk.StringVar(value='192k')
        quality_combo = ttk.Combobox(options_frame, textvariable=self.quality_var,
                                      values=['64k', '128k', '192k', '256k', '320k'], 
                                      state='readonly', width=10)
        quality_combo.grid(row=0, column=1, sticky=tk.W, padx=10, pady=4)

        # Taux d'échantillonnage
        ttk.Label(options_frame, text=_("Taux d'échantillonnage :")).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.sample_rate_var = tk.StringVar(value='44100')
        sample_combo = ttk.Combobox(options_frame, textvariable=self.sample_rate_var,
                                     values=['22050', '44100', '48000'], 
                                     state='readonly', width=10)
        sample_combo.grid(row=1, column=1, sticky=tk.W, padx=10, pady=4)

        # Canaux
        ttk.Label(options_frame, text=_("Canaux :")).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.channels_var = tk.StringVar(value='stereo')
        channels_combo = ttk.Combobox(options_frame, textvariable=self.channels_var,
                                       values=['mono', 'stereo'], 
                                       state='readonly', width=10)
        channels_combo.grid(row=2, column=1, sticky=tk.W, padx=10, pady=4)

        # Volume
        ttk.Label(options_frame, text=_("Volume :")).grid(row=3, column=0, sticky=tk.W, pady=4)
        self.volume_var = tk.DoubleVar(value=1.0)
        volume_frame = ttk.Frame(options_frame)
        volume_frame.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=10, pady=4)
        volume_frame.columnconfigure(0, weight=1)
        volume_scale = ttk.Scale(volume_frame, from_=0.5, to=2.0, variable=self.volume_var, 
                                  orient=tk.HORIZONTAL, length=200)
        volume_scale.grid(row=0, column=0, sticky=(tk.W, tk.E))
        self.volume_label = ttk.Label(volume_frame, text="100%")
        self.volume_label.grid(row=0, column=1, padx=5)
        volume_scale.bind('<Motion>', lambda e: self.volume_label.config(
            text=f"{int(self.volume_var.get() * 100)}%"))

        # Fichier de sortie
        output_frame = ttk.LabelFrame(main, text=_("Fichier MP3 de sortie"), padding=10)
        output_frame.pack(fill=tk.X, pady=(0, 15))
        output_frame.columnconfigure(0, weight=1)

        self.output_entry = ttk.Entry(output_frame, state='readonly')
        self.output_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))

        output_btn = ttk.Button(output_frame, text=_("Parcourir..."), command=self._select_output)
        output_btn.grid(row=0, column=1)

        # Barre de progression
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(main, variable=self.progress_var, maximum=100, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, pady=(10, 5))

        self.status_var = tk.StringVar(value=_("Prêt") if self.ffmpeg_available else _("FFmpeg requis"))
        status_label = ttk.Label(main, textvariable=self.status_var, anchor=tk.W)
        status_label.pack(fill=tk.X)

        # Boutons d'action
        btn_frame = ttk.Frame(main)
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        self.convert_btn = ttk.Button(btn_frame, text=_("Convertir en MP3"), 
                                       command=self._start_conversion, 
                                       state='normal' if self.ffmpeg_available else 'disabled')
        self.convert_btn.pack(side=tk.RIGHT, padx=5)

        close_btn = ttk.Button(btn_frame, text=_("Fermer"), command=self.destroy)
        close_btn.pack(side=tk.RIGHT, padx=5)

    def _open_ffmpeg_download(self):
        """Ouvre la page de téléchargement FFmpeg."""
        import webbrowser
        webbrowser.open("https://ffmpeg.org/download.html")

    def _select_video(self):
        """Sélectionne le fichier vidéo source."""
        path = filedialog.askopenfilename(
            title=_("Sélectionner un fichier vidéo"),
            filetypes=[
                (_("Fichiers vidéo"), "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm *.m4v *.3gp *.ogv *.mpeg *.mpg"),
                (_("Tous les fichiers"), "*.*")
            ]
        )
        if path:
            self.video_path = Path(path)
            self.video_entry.config(state='normal')
            self.video_entry.delete(0, tk.END)
            self.video_entry.insert(0, str(self.video_path))
            self.video_entry.config(state='readonly')

            # Auto-générer le nom du fichier MP3
            mp3_path = self.video_path.with_suffix('.mp3')
            self.output_path = mp3_path
            self.output_entry.config(state='normal')
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(mp3_path))
            self.output_entry.config(state='readonly')

            self.status_var.set(_("Fichier vidéo sélectionné"))

    def _select_output(self):
        """Sélectionne le fichier MP3 de sortie."""
        path = filedialog.asksaveasfilename(
            title=_("Enregistrer le fichier MP3"),
            defaultextension=".mp3",
            filetypes=[(_("Fichiers MP3"), "*.mp3"), (_("Tous les fichiers"), "*.*")]
        )
        if path:
            self.output_path = Path(path)
            self.output_entry.config(state='normal')
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(self.output_path))
            self.output_entry.config(state='readonly')

    def _start_conversion(self):
        """Lance la conversion dans un thread séparé."""
        if not self.video_path or not self.video_path.exists():
            messagebox.showerror(_("Erreur"), _("Veuillez sélectionner un fichier vidéo valide"))
            return

        if not self.output_path:
            messagebox.showerror(_("Erreur"), _("Veuillez spécifier un fichier de sortie"))
            return

        if not self.ffmpeg_available:
            messagebox.showerror(_("Erreur"), _("FFmpeg n'est pas installé ou pas dans le PATH"))
            return

        self.convert_btn.config(state='disabled')
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start(10)
        self.status_var.set(_("Conversion en cours..."))

        thread = threading.Thread(target=self._convert_thread, daemon=True)
        thread.start()

    def _convert_thread(self):
        """Thread de conversion."""
        try:
            # Construire la commande ffmpeg
            cmd = [
                'ffmpeg', '-y',  # -y = overwrite output
                '-i', str(self.video_path),
                '-vn',  # Pas de vidéo
                '-acodec', 'libmp3lame',  # Codec MP3
                '-b:a', self.quality_var.get(),  # Bitrate
                '-ar', self.sample_rate_var.get(),  # Sample rate
            ]

            # Canaux
            if self.channels_var.get() == 'mono':
                cmd.extend(['-ac', '1'])
            else:
                cmd.extend(['-ac', '2'])

            # Volume
            volume = self.volume_var.get()
            if volume != 1.0:
                cmd.extend(['-filter:a', f'volume={volume}'])

            cmd.append(str(self.output_path))

            logger.info(f"Commande ffmpeg : {' '.join(cmd)}")

            # Exécuter avec capture de sortie pour progression
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Surveiller la progression (stderr contient les infos de progression)
            while True:
                output = process.stderr.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Parser la progression si possible
                    if 'time=' in output:
                        self.after(0, lambda: self.status_var.set(_("Conversion en cours...")))

            return_code = process.wait()

            if return_code == 0:
                self.after(0, self._conversion_success)
            else:
                stderr_output = process.stderr.read()
                logger.error(f"Erreur ffmpeg : {stderr_output}")
                self.after(0, lambda: self._conversion_error(stderr_output))

        except Exception as e:
            logger.error(f"Erreur lors de la conversion : {e}")
            self.after(0, lambda: self._conversion_error(str(e)))

    def _conversion_success(self):
        """Appelé quand la conversion réussit."""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate', value=100)
        self.status_var.set(_("Conversion terminée avec succès !"))
        self.convert_btn.config(state='normal')
        
        messagebox.showinfo(
            _("Succès"),
            _("Fichier MP3 créé : {}").format(self.output_path)
        )

    def _conversion_error(self, error_msg):
        """Appelé en cas d'erreur de conversion."""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate', value=0)
        self.status_var.set(_("Erreur lors de la conversion"))
        self.convert_btn.config(state='normal')
        
        messagebox.showerror(_("Erreur"), _("Impossible de convertir : {}").format(error_msg))


def open_video_converter(parent):
    """Ouvre le convertisseur vidéo vers MP3."""
    VideoToMP3Converter(parent)
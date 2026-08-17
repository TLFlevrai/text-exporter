# src/config/__init__.py
import json
import threading
from pathlib import Path
from .schema import AppConfig, ExtractionOptions, NetworkConfig, GuiConfig

__all__ = ['AppConfig', 'ExtractionOptions', 'NetworkConfig', 'GuiConfig', 'config']

# Chemin vers config.json à la racine du projet
CONFIG_PATH = Path(__file__).parent.parent.parent / "config.json"


class Config:
    """Chargeur de configuration centralisé (Singleton thread-safe)."""
    
    _instance = None
    _config: AppConfig = None
    _lock = threading.Lock()  # Verrou de classe pour l'initialisation

    def __new__(cls):
        # Premier check SANS verrou (performance chemin normal)
        if cls._instance is not None:
            return cls._instance
        
        # Verrou pour la création réelle
        with cls._lock:
            # Double-check APRÈS avoir acquis le verrou
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._load()  # Initialisation protégée
        return cls._instance

    @classmethod
    def _load(cls):
        """Charge la configuration depuis config.json ou utilise les valeurs par défaut.
        
        Appelée UNE SEULE FOIS sous verrou lors de la première instanciation.
        """
        default = AppConfig()
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                cls._config = AppConfig(**data)
                print(f"✅ Configuration chargée depuis {CONFIG_PATH}")
            except Exception as e:
                print(f"❌ Erreur de chargement de config.json : {e}")
                print("   → Utilisation des valeurs par défaut")
                cls._config = default
        else:
            print(f"ℹ️  Fichier {CONFIG_PATH} non trouvé, utilisation des valeurs par défaut")
            cls._config = default

    def get(self, key: str, default=None):
        """
        Récupère une valeur par chemin pointé (ex: 'network.server_port').
        
        Args:
            key: Chemin pointé (ex: 'extraction.include_json')
            default: Valeur par défaut si la clé n'existe pas
        
        Returns:
            La valeur configurée ou default
        """
        # Lecture sans verrou : _config est immuable après _load()
        keys = key.split('.')
        value = self._config
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        return value

    def get_all(self) -> AppConfig:
        """Retourne l'objet AppConfig complet (immuable)."""
        return self._config

    # --- Pour tests : reset contrôlé (optionnel) ---
    @classmethod
    def _reset_for_testing(cls):
        """Réinitialise le singleton (UNIQUEMENT pour tests unitaires)."""
        with cls._lock:
            cls._instance = None
            cls._config = None


# Instance unique (singleton) - Initialisation paresseuse thread-safe
config = Config()
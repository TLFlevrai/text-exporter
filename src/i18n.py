# src/i18n.py
import gettext
from pathlib import Path
from src.config import config
from src.logger import setup_logger

logger = setup_logger(__name__)

class Translator:
    """Wrapper mutable pour la fonction de traduction."""
    def __init__(self):
        self._func = gettext.gettext   # fallback par défaut

    def __call__(self, message):
        return self._func(message)

    def set_translation(self, func):
        """Change la fonction de traduction sous-jacente."""
        self._func = func

# Instance globale unique
_ = Translator()

def setup_i18n():
    """Configure la traduction en fonction de la langue définie dans config."""
    lang = config.get('language', 'fr')
    locale_dir = Path(__file__).parent.parent / "locale"

    try:
        translation = gettext.translation(
            'messages',
            localedir=locale_dir,
            languages=[lang],
            fallback=True
        )
        # Installe pour les appels builtins (gettext.install) si nécessaire
        translation.install()
        # Met à jour notre wrapper
        _.set_translation(translation.gettext)
        logger.info(f"Traduction chargée pour la langue '{lang}'")
    except Exception as e:
        logger.warning(
            f"Traduction non disponible pour '{lang}', utilisation du fallback : {e}"
        )
        # Installe le fallback
        gettext.install('messages', names=('ngettext',))
        _.set_translation(gettext.gettext)

    return _

def get_current_language():
    return config.get('language', 'fr')
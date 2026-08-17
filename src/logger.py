# src/logger.py
import logging
import sys

def setup_logger(name=None, level=logging.INFO):
    """Configure et retourne un logger avec un format standard."""
    logger = logging.getLogger(name or __name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger
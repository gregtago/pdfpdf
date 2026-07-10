"""Configuration de la journalisation (fichier tournant + console)."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_file: str | Path) -> logging.Logger:
    """Initialise le logger racine du service.

    Écrit à la fois dans un fichier (rotation à 2 Mo, 5 archives) et sur la
    sortie standard, ce qui reste lisible même lancé en tâche de fond.
    """
    log_file = Path(log_file)
    logger = logging.getLogger("ocr_service")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = RotatingFileHandler(
        log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # En exécutable « fenêtré » (service), sys.stdout peut être absent :
    # on n'ajoute la sortie console que si elle existe réellement.
    if sys.stdout is not None:
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)

    return logger

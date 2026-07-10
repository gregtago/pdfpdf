"""Résolution des chemins et localisation des moteurs OCR embarqués.

En mode « développement » (lancé avec Python), les chemins sont relatifs au
projet. En mode « installé » (exécutable PyInstaller), les binaires Tesseract
et Ghostscript sont embarqués dans le sous-dossier ``vendor`` à côté de l'exe,
et les données modifiables (config, journal, état) vont dans
``%ProgramData%\\OcrPdfService`` — seul emplacement fiable en écriture pour un
service Windows.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "OcrPdfService"


def is_frozen() -> bool:
    """Vrai lorsque le programme tourne en exécutable PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def app_dir() -> Path:
    """Dossier de l'application (contient l'exe et le dossier vendor)."""
    if is_frozen():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def data_dir() -> Path:
    """Dossier des données modifiables (config, journal, état)."""
    if is_frozen() and os.name == "nt":
        base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        d = base / APP_NAME
    else:
        d = app_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def default_config_path() -> Path:
    """Emplacement du config.toml : à côté de l'exe (dev) ou ProgramData."""
    local = app_dir() / "config.toml"
    if local.exists():
        return local
    return data_dir() / "config.toml"


def configure_engines() -> None:
    """Rend les moteurs OCR embarqués (vendor/) visibles pour OCRmyPDF.

    Ajoute Tesseract et Ghostscript au PATH du processus et positionne
    TESSDATA_PREFIX. Sans effet en mode développement si vendor/ est absent
    (on utilise alors les programmes installés sur le système).
    """
    vendor = app_dir() / "vendor"
    tesseract = vendor / "tesseract"
    ghostscript_bin = vendor / "gs" / "bin"

    for path in (tesseract, ghostscript_bin):
        if path.is_dir():
            os.environ["PATH"] = str(path) + os.pathsep + os.environ.get("PATH", "")

    tessdata = tesseract / "tessdata"
    if tessdata.is_dir():
        # Valeur classique : dossier CONTENANT le répertoire tessdata.
        os.environ.setdefault("TESSDATA_PREFIX", str(tesseract))

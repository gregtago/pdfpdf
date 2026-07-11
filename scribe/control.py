"""Pause/reprise partagée entre le service et l'app compagnon.

Mécanisme volontairement simple et robuste : un fichier « drapeau »
(``paused.flag``) dans le dossier de données. S'il existe, le service est en
pause. L'app de la barre des tâches crée ou supprime ce fichier ; le service
le consulte avant de traiter chaque fichier.
"""

from __future__ import annotations

from pathlib import Path

FLAG_NAME = "paused.flag"


def flag_path(data_dir: str | Path) -> Path:
    return Path(data_dir) / FLAG_NAME


def is_paused(data_dir: str | Path) -> bool:
    return flag_path(data_dir).exists()


def set_paused(data_dir: str | Path, paused: bool) -> None:
    f = flag_path(data_dir)
    if paused:
        try:
            f.write_text("paused", encoding="utf-8")
        except OSError:
            pass
    else:
        f.unlink(missing_ok=True)

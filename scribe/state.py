"""Suivi des fichiers déjà traités (évite les doublons et les boucles).

On mémorise, pour chaque PDF traité, sa taille et sa date de modification.
Après remplacement de l'original par la version OCR, on enregistre les
caractéristiques du NOUVEAU fichier : ainsi l'écriture du résultat ne
déclenche pas un nouveau traitement en boucle.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path


class ProcessedStore:
    """Petit registre persistant (JSON) des fichiers déjà traités."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._lock = threading.Lock()
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self) -> None:
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self._path)

    @staticmethod
    def _signature(pdf: Path) -> dict:
        st = pdf.stat()
        return {"size": st.st_size, "mtime": int(st.st_mtime)}

    def is_processed(self, pdf: Path) -> bool:
        """Vrai si le fichier a déjà été traité et n'a pas changé depuis."""
        key = str(pdf.resolve())
        with self._lock:
            known = self._data.get(key)
        if known is None:
            return False
        try:
            return self._signature(pdf) == {
                "size": known.get("size"),
                "mtime": known.get("mtime"),
            }
        except OSError:
            return False

    def mark(self, pdf: Path) -> None:
        """Enregistre la signature actuelle du fichier comme « traité »."""
        key = str(pdf.resolve())
        try:
            sig = self._signature(pdf)
        except OSError:
            return
        with self._lock:
            self._data[key] = sig
            self._save()

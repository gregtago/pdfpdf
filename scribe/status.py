"""Rapport d'avancement partagé entre le service et l'app compagnon.

Le service (worker) met à jour des compteurs et les écrit dans un fichier
JSON (``status.json``) placé dans le dossier de données. L'application de la
barre des tâches lit ce fichier périodiquement pour afficher la progression.

L'écriture est faite par un thread dédié, au plus une fois par seconde quand
quelque chose a changé, pour ne pas marteler le disque lors de la mise en
file initiale de centaines de fichiers.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path


class StatusReporter:
    """Compteurs d'avancement, sérialisés dans status.json."""

    def __init__(self, path: str | Path, flush_interval: float = 1.0) -> None:
        self._path = Path(path)
        self._flush_interval = flush_interval
        self._lock = threading.Lock()
        self._done = 0            # PDF traités depuis le démarrage
        self._pending = 0         # PDF en file, pas encore commencés
        self._current: str | None = None   # PDF en cours de traitement
        self._recent: deque[dict] = deque(maxlen=15)
        self._started_at = time.time()
        self._dirty = True
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._thread.start()

    # -- mutations appelées par le worker --------------------------------
    def on_enqueued(self, count: int = 1) -> None:
        with self._lock:
            self._pending += count
            self._dirty = True

    def on_start(self, pdf: Path) -> None:
        with self._lock:
            self._pending = max(0, self._pending - 1)
            self._current = str(pdf)
            self._dirty = True

    def on_done(self, pdf: Path, status: str) -> None:
        with self._lock:
            self._done += 1
            self._current = None
            self._recent.appendleft(
                {"file": pdf.name, "path": str(pdf), "status": status,
                 "at": time.strftime("%H:%M:%S")}
            )
            self._dirty = True

    # -- écriture ---------------------------------------------------------
    def _snapshot(self) -> dict:
        with self._lock:
            total = self._done + self._pending + (1 if self._current else 0)
            current = self._current
            return {
                "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
                "done": self._done,
                "pending": self._pending,
                "current": current,
                "current_name": Path(current).name if current else None,
                "total": total,
                "recent": list(self._recent),
                "started_at": self._started_at,
            }

    def _write(self) -> None:
        data = self._snapshot()
        tmp = self._path.with_suffix(".json.tmp")
        try:
            tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                           encoding="utf-8")
            tmp.replace(self._path)
        except OSError:
            pass

    def _flush_loop(self) -> None:
        while not self._stop.is_set():
            if self._dirty:
                with self._lock:
                    self._dirty = False
                self._write()
            self._stop.wait(self._flush_interval)

    def stop(self) -> None:
        self._stop.set()
        self._write()


def read_status(path: str | Path) -> dict | None:
    """Lit status.json (côté app compagnon). None si absent/illisible."""
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

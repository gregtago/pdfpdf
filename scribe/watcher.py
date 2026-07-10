"""Surveillance du dossier et file d'attente de traitement.

- Un scan initial océrise les PDF déjà présents.
- Un observateur (watchdog) détecte les nouveaux fichiers en temps réel.
- Une nouvelle analyse périodique sert de filet de sécurité.
- Un unique thread de travail traite les PDF les uns après les autres
  (l'OCR est gourmand : inutile de saturer la machine).
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver

from .config import Config
from .processor import process_pdf
from .state import ProcessedStore

logger = logging.getLogger("scribe.watcher")


def _is_candidate(path: Path, config: Config) -> bool:
    """Filtre : PDF uniquement, hors dossier de sauvegarde et fichiers temp."""
    if path.suffix.lower() != ".pdf":
        return False
    if path.name.startswith("ocr_") or path.name.endswith(".tmp"):
        return False
    if config.backup_dir and config.backup_dir in path.parts:
        return False
    return True


class _Handler(FileSystemEventHandler):
    """Met en file d'attente chaque PDF créé ou modifié."""

    def __init__(self, enqueue, config: Config) -> None:
        self._enqueue = enqueue
        self._config = config

    def _consider(self, path_str: str) -> None:
        path = Path(path_str)
        if _is_candidate(path, self._config):
            self._enqueue(path)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._consider(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._consider(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._consider(event.dest_path)


class OcrService:
    """Orchestrateur : observateur + file d'attente + thread de travail."""

    def __init__(self, config: Config, state: ProcessedStore) -> None:
        self._config = config
        self._state = state
        self._queue: queue.Queue[Path] = queue.Queue()
        self._pending: set[str] = set()
        self._pending_lock = threading.Lock()
        self._stop = threading.Event()
        self._worker: threading.Thread | None = None

    # -- mise en file d'attente ------------------------------------------
    def enqueue(self, pdf: Path) -> None:
        key = str(pdf.resolve())
        with self._pending_lock:
            if key in self._pending:
                return
            self._pending.add(key)
        self._queue.put(pdf)

    # -- attente de stabilité --------------------------------------------
    def _wait_until_stable(self, pdf: Path) -> bool:
        """Attend que la taille du fichier ne bouge plus (copie terminée)."""
        last = -1
        stable_for = 0.0
        step = 1.0
        deadline = time.monotonic() + 120  # abandon après 2 min
        while not self._stop.is_set() and time.monotonic() < deadline:
            try:
                size = pdf.stat().st_size
            except OSError:
                return False
            if size == last and size > 0:
                stable_for += step
                if stable_for >= self._config.stable_seconds:
                    return True
            else:
                stable_for = 0.0
                last = size
            time.sleep(step)
        return False

    # -- boucle de travail -----------------------------------------------
    def _work_loop(self) -> None:
        while not self._stop.is_set():
            try:
                pdf = self._queue.get(timeout=1.0)
            except queue.Empty:
                continue
            key = str(pdf.resolve())
            try:
                if not pdf.exists():
                    continue
                if self._state.is_processed(pdf):
                    continue
                if not self._wait_until_stable(pdf):
                    logger.debug("Fichier instable ou disparu : %s", pdf)
                    continue
                if self._state.is_processed(pdf):
                    continue
                try:
                    process_pdf(pdf, self._config)
                finally:
                    # Quel que soit le résultat, on mémorise la signature
                    # actuelle pour ne pas retraiter en boucle.
                    self._state.mark(pdf)
            except Exception:  # noqa: BLE001 - un fichier ne doit pas tuer le service
                logger.exception("Erreur inattendue sur %s", pdf)
            finally:
                with self._pending_lock:
                    self._pending.discard(key)
                self._queue.task_done()

    # -- scan complet -----------------------------------------------------
    def scan_all(self) -> None:
        count = 0
        for pdf in self._config.watch_dir.rglob("*.pdf"):
            if _is_candidate(pdf, self._config) and not self._state.is_processed(pdf):
                self.enqueue(pdf)
                count += 1
        if count:
            logger.info("Scan : %d fichier(s) mis en file d'attente.", count)

    # -- cycle de vie -----------------------------------------------------
    def run(self) -> None:
        logger.info("Surveillance du dossier : %s", self._config.watch_dir)
        self._worker = threading.Thread(target=self._work_loop, daemon=True)
        self._worker.start()

        # Scan initial des fichiers déjà présents.
        self.scan_all()

        handler = _Handler(self.enqueue, self._config)
        observer = PollingObserver() if self._config.use_polling else Observer()
        observer.schedule(handler, str(self._config.watch_dir), recursive=True)
        observer.start()
        logger.info(
            "Service démarré (%s).",
            "polling" if self._config.use_polling else "événements natifs",
        )

        next_rescan = time.monotonic() + self._config.rescan_seconds
        try:
            while not self._stop.is_set():
                time.sleep(1.0)
                if (
                    self._config.rescan_seconds > 0
                    and time.monotonic() >= next_rescan
                ):
                    self.scan_all()
                    next_rescan = time.monotonic() + self._config.rescan_seconds
        finally:
            observer.stop()
            observer.join(timeout=5)
            logger.info("Service arrêté.")

    def run_once(self) -> None:
        """Traite les PDF présents puis s'arrête (sans surveillance)."""
        self._worker = threading.Thread(target=self._work_loop, daemon=True)
        self._worker.start()
        self.scan_all()
        self._queue.join()
        self.stop()
        self._worker.join(timeout=5)

    def stop(self) -> None:
        self._stop.set()

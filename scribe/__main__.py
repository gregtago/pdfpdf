"""Point d'entrée du service : python -m scribe [config.toml]."""

from __future__ import annotations

import argparse
import signal
import sys
from pathlib import Path

from . import paths
from .config import load_config
from .logging_setup import setup_logging
from .state import ProcessedStore
from .watcher import OcrService

DEFAULT_CONFIG_TEMPLATE = """\
# Configuration de Scribe (générée à l'installation).
watch_dir = "{watch_dir}"
languages = ["fra"]
keep_backup = false
backup_dir = "_originaux"
optimize = 1
deskew = true
rotate_pages = true
use_polling = true
stable_seconds = 5
rescan_seconds = 300
log_file = "scribe.log"
"""


def write_default_config(watch_dir: str) -> Path:
    """Écrit un config.toml par défaut dans le dossier de données.

    Utilisé par l'installeur (option --init-config). Ne remplace pas une
    configuration déjà présente. Crée le dossier surveillé s'il manque.
    """
    cfg_path = paths.data_dir() / "config.toml"
    try:
        Path(watch_dir).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    if not cfg_path.exists():
        safe = watch_dir.replace("\\", "/")
        cfg_path.write_text(
            DEFAULT_CONFIG_TEMPLATE.format(watch_dir=safe), encoding="utf-8"
        )
    return cfg_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scribe",
        description="Service de fond : océrise les PDF d'un dossier (image -> texte).",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=None,
        help="Chemin du fichier de configuration (défaut : détecté automatiquement).",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Traite les fichiers présents puis s'arrête (pas de surveillance).",
    )
    parser.add_argument(
        "--init-config",
        metavar="DOSSIER",
        help="Écrit un config.toml par défaut pour ce dossier surveillé, puis quitte.",
    )
    args = parser.parse_args(argv)

    # Rendre les moteurs OCR embarqués (vendor/) visibles avant tout appel OCR.
    paths.configure_engines()

    if args.init_config is not None:
        cfg = write_default_config(args.init_config)
        print(f"Configuration écrite : {cfg}")
        return 0

    config_path = args.config or paths.default_config_path()
    try:
        config = load_config(config_path)
    except (FileNotFoundError, ValueError) as exc:
        print(f"Erreur de configuration : {exc}", file=sys.stderr)
        return 2

    # Journal et fichier d'état dans un emplacement fiable en écriture.
    log_path = Path(config.log_file)
    if not log_path.is_absolute():
        log_path = paths.data_dir() / log_path
    logger = setup_logging(log_path)
    logger.info("Démarrage de Scribe.")

    state = ProcessedStore(log_path.with_name(".ocr_state.json"))
    service = OcrService(config, state)

    def _handle_signal(signum, _frame):
        logger.info("Signal %s reçu, arrêt en cours...", signum)
        service.stop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _handle_signal)
        except (ValueError, OSError):
            pass  # certains contextes (thread) n'autorisent pas les signaux

    if args.once:
        service.run_once()
        logger.info("Mode --once terminé.")
        return 0

    try:
        service.run()
    except KeyboardInterrupt:
        service.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

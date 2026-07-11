"""Point d'entrée PyInstaller pour l'application de la barre des tâches."""

import multiprocessing
import sys

from scribe.tray import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())

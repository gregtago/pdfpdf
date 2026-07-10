"""Point d'entrée pour l'exécutable PyInstaller.

PyInstaller a besoin d'un script (et non d'un module -m) comme point de
départ ; ce fichier se contente d'appeler la fonction main() du paquet.
"""

import multiprocessing
import sys

from scribe.__main__ import main

if __name__ == "__main__":
    # Nécessaire quand le programme est gelé (évite les relances de process).
    multiprocessing.freeze_support()
    sys.exit(main())

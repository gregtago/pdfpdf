# -*- mode: python ; coding: utf-8 -*-
"""Spécification PyInstaller pour l'exécutable de Scribe.

Compilation (depuis la racine du dépôt) :
    pyinstaller --noconfirm build/scribe.spec

Produit dist/scribe/scribe.exe (+ dossier _internal). OCRmyPDF
importe dynamiquement de nombreux sous-modules et lit ses métadonnées de
distribution : on force donc leur collecte complète.
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

# Racine du dépôt = dossier parent de ce fichier .spec (situé dans build/).
# On la calcule en absolu et on l'ajoute au chemin d'import : sans cela, un
# 'pathex' relatif se résout par rapport au dossier courant de compilation et
# le paquet "scribe" n'est pas trouvé -> "No module named 'scribe'".
REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

datas = []
binaries = []
hiddenimports = []

# Notre propre paquet : on embarque explicitement tous ses sous-modules.
hiddenimports += collect_submodules("scribe")

# Paquets à embarquer intégralement (code, données, métadonnées).
for pkg in ("ocrmypdf", "pikepdf", "img2pdf", "pdfminer", "PIL", "reportlab", "pluggy"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# OCRmyPDF découvre ses greffons via les points d'entrée (importlib.metadata) :
# ses métadonnées doivent être présentes dans le paquet gelé.
for dist in ("ocrmypdf", "img2pdf"):
    try:
        datas += copy_metadata(dist)
    except Exception:
        pass


a = Analysis(
    [os.path.join(SPECPATH, "entrypoint.py")],
    pathex=[REPO_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="scribe",
    console=False,          # exécutable fenêtré : pas de console qui clignote
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="scribe",
)

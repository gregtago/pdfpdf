# -*- mode: python ; coding: utf-8 -*-
"""Spécification PyInstaller pour l'app de la barre des tâches (scribe-tray.exe).

Exécutable léger (pas de moteur OCR) : interface Tkinter + icône pystray.

Compilation (depuis la racine du dépôt) :
    pyinstaller --noconfirm build/scribe-tray.spec
"""

import os
import sys

from PyInstaller.utils.hooks import collect_all, collect_submodules

REPO_ROOT = os.path.abspath(os.path.join(SPECPATH, os.pardir))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

datas = []
binaries = []
hiddenimports = []

# Notre paquet + les dépendances de l'interface graphique.
hiddenimports += collect_submodules("scribe")
for pkg in ("pystray", "PIL"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# pystray choisit son backend dynamiquement : on force le backend Windows.
hiddenimports += ["pystray._win32"]


a = Analysis(
    [os.path.join(SPECPATH, "tray-entrypoint.py")],
    pathex=[REPO_ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["ocrmypdf", "pikepdf"],  # inutile côté interface : on allège
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="scribe-tray",
    console=False,          # application fenêtrée
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="scribe-tray",
)

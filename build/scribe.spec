# -*- mode: python ; coding: utf-8 -*-
"""Spécification PyInstaller pour l'exécutable de Scribe.

Compilation (depuis la racine du dépôt) :
    pyinstaller --noconfirm build/scribe.spec

Produit dist/scribe/scribe.exe (+ dossier _internal). OCRmyPDF
importe dynamiquement de nombreux sous-modules et lit ses métadonnées de
distribution : on force donc leur collecte complète.
"""

from PyInstaller.utils.hooks import collect_all, copy_metadata

datas = []
binaries = []
hiddenimports = []

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
    ["entrypoint.py"],
    pathex=[".."],
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

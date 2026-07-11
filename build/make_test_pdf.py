"""Génère un petit PDF image contenant du texte, pour tester l'OCR en CI.

Usage : python build/make_test_pdf.py <chemin_de_sortie.pdf>
"""

import sys

from PIL import Image, ImageDraw, ImageFont


def main() -> int:
    out = sys.argv[1]
    img = Image.new("RGB", (1400, 400), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 70)
    except OSError:
        font = ImageFont.load_default()
    draw.text((60, 150), "SCRIBE OCR FONCTIONNE", fill="black", font=font)
    img.save(out, "PDF", resolution=150.0)
    print(f"PDF de test écrit : {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

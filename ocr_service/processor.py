"""Traitement OCR d'un fichier PDF : image -> texte recherchable.

S'appuie sur la bibliothèque OCRmyPDF (moteur Tesseract). La reconnaissance
se fait avec l'option skip_text : les pages déjà porteuses de texte sont
laissées telles quelles, seules les pages « image » sont océrisées. Le
traitement est donc idempotent — relancer sur un PDF déjà océrisé ne
l'abîme pas.
"""

from __future__ import annotations

import logging
import shutil
import tempfile
from pathlib import Path

from .config import Config

logger = logging.getLogger("ocr_service.processor")


def _backup_original(pdf: Path, config: Config) -> None:
    """Conserve une copie de l'original avant remplacement, si demandé."""
    if not config.keep_backup:
        return

    if config.backup_dir:
        dest_dir = pdf.parent / config.backup_dir
        dest_dir.mkdir(exist_ok=True)
        dest = dest_dir / pdf.name
    else:
        dest = pdf.with_suffix(".orig.pdf")

    # Ne pas écraser une sauvegarde déjà présente.
    if not dest.exists():
        shutil.copy2(pdf, dest)
        logger.info("Sauvegarde de l'original -> %s", dest)


def process_pdf(pdf: Path, config: Config) -> bool:
    """Océrise un PDF et remplace l'original par la version recherchable.

    Renvoie True si le fichier a bien été (re)traité, False s'il a été
    ignoré (déjà entièrement textuel, chiffré, ou erreur récupérable).
    """
    logger.info("Traitement : %s", pdf)

    # Import différé : le moteur OCR (lourd, dépendances natives) n'est requis
    # qu'au moment de traiter un fichier, pas à l'import du paquet.
    import ocrmypdf

    # On écrit d'abord dans un fichier temporaire, puis on bascule de façon
    # atomique : jamais de PDF à moitié écrit à la place de l'original.
    tmp_fd = tempfile.NamedTemporaryFile(
        prefix="ocr_", suffix=".pdf", dir=str(pdf.parent), delete=False
    )
    tmp_out = Path(tmp_fd.name)
    tmp_fd.close()

    try:
        result = ocrmypdf.ocr(
            input_file=str(pdf),
            output_file=str(tmp_out),
            language=config.language_arg,
            skip_text=True,          # n'océrise que les pages sans texte
            deskew=config.deskew,
            rotate_pages=config.rotate_pages,
            optimize=config.optimize,
            progress_bar=False,
            output_type="pdf",
        )
    except ocrmypdf.exceptions.PriorOcrFoundError:
        logger.info("Déjà océrisé, ignoré : %s", pdf)
        tmp_out.unlink(missing_ok=True)
        return False
    except ocrmypdf.exceptions.EncryptedPdfError:
        logger.warning("PDF chiffré (mot de passe), ignoré : %s", pdf)
        tmp_out.unlink(missing_ok=True)
        return False
    except ocrmypdf.exceptions.MissingDependencyError as exc:
        logger.error("Dépendance manquante (Tesseract/Ghostscript ?) : %s", exc)
        tmp_out.unlink(missing_ok=True)
        raise
    except Exception as exc:  # noqa: BLE001 - on isole le fichier fautif
        logger.error("Échec de l'OCR sur %s : %s", pdf, exc)
        tmp_out.unlink(missing_ok=True)
        return False

    if result != ocrmypdf.ExitCode.ok:
        logger.warning("OCRmyPDF a renvoyé le code %s pour %s", result, pdf)
        tmp_out.unlink(missing_ok=True)
        return False

    _backup_original(pdf, config)
    # Remplacement atomique de l'original par la version océrisée.
    shutil.move(str(tmp_out), str(pdf))
    logger.info("Terminé : %s (PDF texte recherchable)", pdf)
    return True

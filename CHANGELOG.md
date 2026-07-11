# Journal des versions — Scribe

Toutes les évolutions notables de Scribe sont consignées ici.
Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/).

## [1.0.0] — 2026-07-11

Première version publiée. Scribe est un logiciel Windows qui océrise
automatiquement, en tâche de fond, les PDF scannés d'un dossier.

### Fonctionnalités
- **Service Windows** (`Scribe`) qui surveille un dossier et tous ses
  sous-dossiers et transforme les PDF « image » en PDF **texte recherchable**
  (moteur OCRmyPDF / Tesseract). L'original est **remplacé** sur place.
- **Installeur `.exe` autonome** : Tesseract (français) et Ghostscript sont
  embarqués, aucun prérequis à installer. L'assistant demande le dossier à
  surveiller et installe/démarre le service.
- **Icône dans la barre des tâches** avec **fenêtre de progression** : nombre
  de PDF traités / restants, fichier en cours, barre d'avancement et liste des
  derniers fichiers traités.
- **Priorité aux nouveaux fichiers** : un PDF déposé passe devant le lot de
  fichiers déjà présents au démarrage.
- Traitement **idempotent** (jamais de double OCR), remplacement **atomique**,
  redressement et rotation automatiques des pages, **journal** détaillé.
- Compilation automatisée et **auto-testée** sur Windows (GitHub Actions).

### Notes
- L'installeur n'est pas signé numériquement : Windows affiche un avertissement
  SmartScreen à la première exécution (voir le README, section « Installeur non
  signé »).

[1.0.0]: https://github.com/gregtago/pdfpdf/releases/tag/v1.0.0

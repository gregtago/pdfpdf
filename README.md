# Scribe — reconnaissance de texte sur PDF, en tâche de fond

**Scribe** tourne **en tâche de fond sous Windows**. Il surveille un
dossier (et **tous ses sous-dossiers**) et, dès qu'un PDF « image » (un scan)
y apparaît, il lance automatiquement une **reconnaissance de texte (OCR)** et
remplace le fichier par une version **PDF texte recherchable** — même
apparence, mais on peut désormais faire `Ctrl+F`, copier le texte et
l'indexer.

Le moteur utilisé est [OCRmyPDF](https://ocrmypdf.readthedocs.io/) (basé sur
Tesseract), la référence libre pour ce besoin.

> **Deux façons de l'utiliser :**
>
> - **Installeur autonome (recommandé)** — un `.exe` qui installe un vrai
>   **service Windows** et embarque tout le nécessaire (Tesseract, Ghostscript).
>   Rien d'autre à installer sur le poste. Voir
>   [build/README-build.md](build/README-build.md).
> - **Manuellement en Python** — pour tester ou personnaliser, voir les
>   sections ci-dessous.

---

## Version installeur (service Windows autonome)

Pour la plupart des usages, préférez l'**installeur** : il crée un service
Windows `Scribe` qui démarre automatiquement avec le PC, se relance en
cas d'incident, et n'exige aucun prérequis (Tesseract et Ghostscript sont
embarqués).

- Comment obtenir/compiler l'installeur : **[build/README-build.md](build/README-build.md)**
- La compilation est automatisée sur Windows via GitHub Actions ; l'installeur
  se télécharge dans l'onglet **Actions**.

Les sections ci-dessous décrivent l'usage **manuel en Python** (développement,
tests, ou installation sans passer par l'installeur).

---

## 1. Ce qu'il fait, concrètement

- Surveille en continu le dossier de votre choix, sous-dossiers compris.
- Détecte les nouveaux PDF **et** re-scanne périodiquement (filet de sécurité,
  utile sur les lecteurs réseau).
- N'océrise que les pages « image » : un PDF déjà textuel est laissé
  intact (traitement **idempotent**, jamais de double OCR).
- **Remplace purement et simplement l'original** par la version recherchable
  (aucune sauvegarde par défaut ; une copie reste activable si besoin).
- Corrige l'inclinaison et l'orientation des pages scannées de travers.
- Traite les fichiers **un par un** pour ne pas saturer le poste.
- **Priorité aux nouveaux fichiers** : un PDF déposé maintenant passe devant le
  lot de fichiers déjà présents au démarrage (plus d'attente derrière la file).
- **Icône dans la barre des tâches** (bas à droite) avec une **fenêtre de
  progression** : nombre de PDF traités / restants, fichier en cours, barre
  d'avancement, derniers fichiers traités. Voir la section dédiée ci-dessous.
- Tient un **journal** (`scribe.log`) de tout ce qu'il fait.

> **Comment ça marche.** Le travail d'OCR est fait par un *service Windows*
> (robuste, en fond). Comme un service ne peut pas afficher d'interface, une
> petite **application compagnon** (`scribe-tray.exe`) démarre à l'ouverture de
> session et affiche l'icône + la progression, en lisant l'état publié par le
> service. Double-cliquez l'icône pour ouvrir la fenêtre de progression.

---

## 2. Prérequis à installer (une seule fois)

Le moteur OCR a besoin de trois briques. Sous Windows :

1. **Python 3.11 ou plus** — <https://www.python.org/downloads/>
   Cochez « *Add Python to PATH* » pendant l'installation.
2. **Tesseract OCR** (avec la langue française) —
   <https://github.com/UB-Mannheim/tesseract/wiki>
   Pendant l'installation, dans « *Additional language data* », cochez
   **French**. Notez le dossier d'installation (souvent
   `C:\Program Files\Tesseract-OCR`).
3. **Ghostscript** — <https://ghostscript.com/releases/gsdnld.html>

> Astuce : la façon la plus simple d'installer les trois est
> [Chocolatey](https://chocolatey.org/), dans un PowerShell **administrateur** :
>
> ```powershell
> choco install python tesseract ghostscript -y
> choco install tesseract-lang -y   # packs de langues, dont le français
> ```

Vérifiez que Tesseract et Ghostscript sont bien dans le `PATH` (ouvrez une
**nouvelle** invite de commandes) :

```powershell
tesseract --version
gswin64c --version
```

---

## 3. Installation du service

Dans une invite de commandes, placez-vous dans le dossier `scribe` puis :

```powershell
python -m pip install -r requirements.txt
```

Copiez le modèle de configuration et adaptez-le :

```powershell
copy config.example.toml config.toml
notepad config.toml
```

L'essentiel à régler dans `config.toml` :

```toml
watch_dir = "C:/Users/VOTRE_NOM/Documents/PDF"   # le dossier à surveiller
languages = ["fra"]                              # "fra", ou ["fra","eng"]
keep_backup = false                              # remplacement pur (sans sauvegarde)
```

> Écrivez les chemins avec des barres obliques normales `/` — c'est accepté
> sous Windows et évite les soucis d'échappement.

---

## 4. Tester avant de le mettre en tâche de fond

Lancez-le dans une fenêtre pour voir ce qu'il fait :

```powershell
python -m scribe
```

Déposez un PDF scanné dans le dossier surveillé : il doit être traité en
quelques secondes (le journal s'affiche à l'écran). `Ctrl+C` pour arrêter.

Pour traiter uniquement les fichiers déjà présents puis quitter :

```powershell
python -m scribe --once
```

---

## 5. Le faire démarrer tout seul (tâche de fond)

Une tâche planifiée le lance **sans fenêtre** à chaque ouverture de session :

```powershell
powershell -ExecutionPolicy Bypass -File install\install-task.ps1
```

Puis, pour le démarrer immédiatement sans redémarrer la session :

```powershell
Start-ScheduledTask -TaskName "Scribe"
```

Pour le désinstaller :

```powershell
powershell -ExecutionPolicy Bypass -File install\uninstall-task.ps1
```

---

## 6. Réglages disponibles (`config.toml`)

| Clé              | Rôle                                                            |
|------------------|-----------------------------------------------------------------|
| `watch_dir`      | Dossier racine surveillé (sous-dossiers inclus).                |
| `languages`      | Langues Tesseract, ex. `["fra"]` ou `["fra","eng"]`.            |
| `keep_backup`    | `false` (défaut) = remplacement pur. `true` = garder une copie. |
| `backup_dir`     | Si `keep_backup=true` : sous-dossier ; vide → `<nom>.orig.pdf`. |
| `optimize`       | Compression `0`–`3` (`1` = sûr).                                |
| `deskew`         | Redresse les pages scannées de travers.                        |
| `rotate_pages`   | Remet les pages dans le bon sens.                              |
| `use_polling`    | `true` = scrutation régulière, plus fiable sur lecteur réseau. |
| `stable_seconds` | Délai de stabilité avant traitement (copie terminée).          |
| `rescan_seconds` | Ré-analyse complète périodique (`0` pour désactiver).          |
| `log_file`       | Fichier journal.                                               |

---

## 7. En cas de souci

- **« Dépendance manquante »** dans le journal → Tesseract ou Ghostscript
  n'est pas installé, ou pas dans le `PATH`. Rouvrez une invite après
  l'installation.
- **Rien ne se passe sur un lecteur réseau** → laissez `use_polling = true`.
- **PDF ignoré** → il est peut-être déjà textuel (rien à faire) ou protégé par
  mot de passe (indiqué dans le journal).
- Consultez `scribe.log` : chaque fichier traité, ignoré ou en erreur y
  est tracé.

---

## 8. Structure du projet

```
scribe/
├── scribe/
│   ├── __main__.py       # point d'entrée du service : python -m scribe
│   ├── config.py         # lecture de config.toml
│   ├── paths.py          # chemins + localisation des moteurs embarqués
│   ├── watcher.py        # surveillance + file d'attente (prioritaire)
│   ├── processor.py      # OCR d'un PDF (OCRmyPDF)
│   ├── state.py          # suivi des fichiers déjà traités
│   ├── status.py         # publication de l'avancement (status.json)
│   ├── tray.py           # app barre des tâches : icône + progression
│   └── logging_setup.py  # journalisation
├── build/                # fabrication de l'installeur
│   ├── entrypoint.py     # point d'entrée PyInstaller (service)
│   ├── tray-entrypoint.py# point d'entrée PyInstaller (barre des tâches)
│   ├── scribe.spec       # spec PyInstaller du service
│   ├── scribe-tray.spec  # spec PyInstaller de l'app barre des tâches
│   ├── fetch-vendor.ps1  # récupère Tesseract/Ghostscript/NSSM
│   ├── installer.iss     # script Inno Setup (.exe)
│   └── README-build.md   # guide de compilation
├── install/              # route manuelle (tâche planifiée)
│   ├── install-task.ps1
│   ├── uninstall-task.ps1
│   └── run.bat
├── config.example.toml
├── requirements.txt
├── pyproject.toml
└── README.md
```

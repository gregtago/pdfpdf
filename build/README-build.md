# Fabrication de l'installeur Windows

L'installeur `.exe` est **autonome** : il embarque l'application, le moteur
Tesseract (français inclus) et Ghostscript. L'utilisateur final n'a **rien
d'autre à installer**. À l'installation, un **vrai service Windows** (nommé
`Scribe`) est créé, démarré et configuré pour se lancer au démarrage du
PC, avec redémarrage automatique en cas d'arrêt inattendu (géré par NSSM).

## Le plus simple : GitHub Actions (recommandé)

Le workflow [`.github/workflows/build-windows.yml`](../.github/workflows/build-windows.yml)
compile tout sur un runner Windows. Vous n'installez aucun outil.

1. Poussez un commit, ou lancez le workflow manuellement : onglet **Actions**
   → *Build Scribe (installeur Windows)* → **Run workflow**.
2. À la fin, téléchargez l'artefact **Scribe-Setup** : il contient
   `Scribe-Setup-1.0.0.exe`.
3. Transférez ce fichier sur le poste cible et double-cliquez dessus.

## Compilation manuelle (sur un poste Windows)

Prérequis : Python 3.11+, puis les outils via [Chocolatey](https://chocolatey.org)
(PowerShell administrateur) :

```powershell
choco install tesseract ghostscript nssm innosetup -y
```

Ensuite, depuis la racine du dépôt :

```powershell
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --workpath dist/_pyiwork build/scribe.spec
powershell -ExecutionPolicy Bypass -File build/fetch-vendor.ps1
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss
```

L'installeur est produit dans `dist/installer/`.

## Ce que fait l'installeur

1. Copie l'application et le dossier `vendor/` (Tesseract + Ghostscript) dans
   `C:\Program Files\Scribe`.
2. Demande le **dossier à surveiller** (par défaut `Documents\PDF`).
3. Génère `C:\ProgramData\Scribe\config.toml`.
4. Crée le service Windows `Scribe` avec NSSM (démarrage automatique,
   redémarrage sur incident) et le lance.

Journal du service : `C:\ProgramData\Scribe\scribe.log`.

## Gestion du service (poste cible)

```powershell
Get-Service Scribe          # état
Restart-Service Scribe      # après modification du config.toml
Stop-Service Scribe
```

## Note importante — dossiers réseau

Par défaut, le service tourne sous le compte **LocalSystem**, qui n'a
généralement **pas** accès aux lecteurs réseau (`\\serveur\partage` ou lettres
mappées). Si les PDF sont sur un partage réseau, faites tourner le service sous
un compte utilisateur ayant les droits, par exemple :

```powershell
& "C:\Program Files\Scribe\nssm.exe" set Scribe ObjectName "DOMAINE\utilisateur" "MotDePasse"
Restart-Service Scribe
```

## Composants tiers

| Composant   | Rôle                         | Licence                |
|-------------|------------------------------|------------------------|
| Tesseract   | Moteur de reconnaissance     | Apache 2.0             |
| Ghostscript | Traitement PDF/PostScript    | AGPL / licence commerciale |
| NSSM        | Gestionnaire de service      | Domaine public         |
| OCRmyPDF    | Orchestration OCR (Python)   | MPL 2.0                |

> Ghostscript est distribué sous **AGPL**. Pour un usage purement interne à
> l'étude, c'est sans conséquence ; en cas de redistribution commerciale du
> logiciel, vérifiez les conditions de licence de Ghostscript.

## Publier une version (release permanente)

Le workflow crée automatiquement une **release GitHub** (téléchargement
permanent + notes de version) quand on pousse un tag `vX.Y.Z` :

```bash
# 1. Mettre à jour AppVersion dans build/installer.iss et le CHANGELOG.md
# 2. Créer et pousser le tag
git tag v1.0.0
git push origin v1.0.0
```

L'installeur est alors compilé, attaché à la release et visible dans l'onglet
**Releases**. Le corps de la release reprend `CHANGELOG.md`.

## Signature du code (supprimer l'avertissement SmartScreen)

L'installeur n'est pas signé : Windows affiche un avertissement à la première
exécution. Pour le supprimer, il faut un **certificat de signature de code**
(OV ou EV, payant, auprès de DigiCert / Sectigo / Certum…).

Une fois le certificat disponible (idéalement stocké en secret GitHub ou sur un
HSM cloud), on ajoute une étape de signature avant Inno Setup :

```powershell
# Exemple avec signtool (certificat .pfx) — à adapter :
& signtool sign /f cert.pfx /p $env:CERT_PASSWORD /tr http://timestamp.digicert.com `
    /td sha256 /fd sha256 dist\scribe\scribe.exe dist\scribe-tray\scribe-tray.exe
```

puis on signe aussi l'installeur produit par Inno Setup (`SignTool` intégré à
Inno, ou une seconde commande signtool sur le `.exe` final). Un certificat
**EV** donne une réputation SmartScreen immédiate ; un certificat **OV** la
construit progressivement.

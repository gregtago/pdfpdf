# ---------------------------------------------------------------------------
# Prépare le dossier "vendor" (moteurs OCR embarqués) et récupère NSSM.
# Suppose que Tesseract, Ghostscript et NSSM ont été installés au préalable
# (par exemple via Chocolatey dans le workflow GitHub Actions).
#
# Produit :
#   scribe/vendor/tesseract/...  (tesseract.exe + tessdata fra/eng/osd)
#   scribe/vendor/gs/bin/gswin64c.exe ...
#   scribe/build/nssm.exe
# ---------------------------------------------------------------------------

$ErrorActionPreference = "Stop"
$buildDir = $PSScriptRoot
$root     = Split-Path -Parent $buildDir          # dossier scribe
$vendor   = Join-Path $root "vendor"

New-Item -ItemType Directory -Force -Path $vendor | Out-Null

# --- Tesseract -------------------------------------------------------------
$tessSrc = "C:\Program Files\Tesseract-OCR"
if (-not (Test-Path $tessSrc)) {
    throw "Tesseract introuvable dans $tessSrc (installez-le avant : choco install tesseract)."
}
$tessDst = Join-Path $vendor "tesseract"
if (Test-Path $tessDst) { Remove-Item $tessDst -Recurse -Force }
Copy-Item $tessSrc $tessDst -Recurse -Force
Write-Host "Tesseract copié -> $tessDst"

# Données de langue de qualité (tessdata_best) : français, anglais + OSD
# (l'OSD est requis par la rotation/redressement automatique des pages).
$tessdata = Join-Path $tessDst "tessdata"
New-Item -ItemType Directory -Force -Path $tessdata | Out-Null
foreach ($lang in @("fra", "eng", "osd")) {
    $url = "https://github.com/tesseract-ocr/tessdata_best/raw/main/$lang.traineddata"
    $out = Join-Path $tessdata "$lang.traineddata"
    Write-Host "Téléchargement $lang.traineddata ..."
    Invoke-WebRequest -Uri $url -OutFile $out -UseBasicParsing
}

# --- Ghostscript -----------------------------------------------------------
$gsBase = Get-ChildItem "C:\Program Files\gs" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
if (-not $gsBase) {
    throw "Ghostscript introuvable dans C:\Program Files\gs (choco install ghostscript)."
}
$gsDst = Join-Path $vendor "gs"
if (Test-Path $gsDst) { Remove-Item $gsDst -Recurse -Force }
Copy-Item $gsBase.FullName $gsDst -Recurse -Force
Write-Host "Ghostscript copié -> $gsDst (depuis $($gsBase.Name))"

# --- NSSM ------------------------------------------------------------------
$nssm = (Get-Command nssm -ErrorAction SilentlyContinue).Source
if (-not $nssm) {
    throw "NSSM introuvable (choco install nssm)."
}
Copy-Item $nssm (Join-Path $buildDir "nssm.exe") -Force
Write-Host "NSSM copié -> $(Join-Path $buildDir 'nssm.exe')"

Write-Host "vendor prêt."

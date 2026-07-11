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
# IMPORTANT : ne PAS copier le shim Chocolatey (C:\ProgramData\chocolatey\bin\
# nssm.exe) — ce n'est qu'un lanceur qui ne fonctionne que sur cette machine.
# On copie le VRAI binaire 64 bits depuis le dossier lib de Chocolatey.
$nssmReal =
    Get-ChildItem "C:\ProgramData\chocolatey\lib" -Recurse -Filter nssm.exe -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match '\\win64\\' } | Select-Object -First 1
if (-not $nssmReal) {
    $nssmReal = Get-ChildItem "C:\ProgramData\chocolatey\lib" -Recurse -Filter nssm.exe -ErrorAction SilentlyContinue |
        Select-Object -First 1
}
if (-not $nssmReal) {
    throw "Vrai nssm.exe introuvable sous chocolatey\lib (choco install nssm ?)."
}
# Garde-fou : le shim fait quelques Ko, le vrai binaire en fait ~250+.
if ($nssmReal.Length -lt 100000) {
    throw "nssm.exe trouvé trop petit ($($nssmReal.Length) octets) : c'est probablement un shim, pas le vrai binaire."
}
Copy-Item $nssmReal.FullName (Join-Path $buildDir "nssm.exe") -Force
Write-Host "NSSM (réel) copié -> $(Join-Path $buildDir 'nssm.exe') depuis $($nssmReal.FullName)"

Write-Host "vendor prêt."

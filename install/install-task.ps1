# ---------------------------------------------------------------------------
# Installe le service OCR PDF comme tâche planifiée Windows.
# La tâche démarre automatiquement à l'ouverture de session, sans fenêtre.
#
# Utilisation (dans PowerShell, depuis le dossier du projet) :
#     powershell -ExecutionPolicy Bypass -File install\install-task.ps1
# ---------------------------------------------------------------------------

param(
    [string]$TaskName = "OCR-PDF-Service",
    [string]$PythonExe = "pythonw.exe"   # pythonw = sans fenêtre console
)

$ErrorActionPreference = "Stop"

# Dossier racine du projet (parent du dossier "install").
$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Definition
$projectDir = Split-Path -Parent $scriptDir

# Vérifie la présence de la configuration.
$configPath = Join-Path $projectDir "config.toml"
if (-not (Test-Path $configPath)) {
    Write-Warning "config.toml est absent. Copiez config.example.toml en config.toml et adaptez-le avant de démarrer."
}

$action = New-ScheduledTaskAction -Execute $PythonExe `
    -Argument "-m ocr_service" -WorkingDirectory $projectDir

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero)   # aucune limite de durée

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description "Reconnaissance de texte (OCR) automatique sur les PDF." -Force

Write-Host ""
Write-Host "Tache '$TaskName' installee." -ForegroundColor Green
Write-Host "Elle demarrera automatiquement a votre prochaine ouverture de session."
Write-Host "Pour la lancer tout de suite :" -ForegroundColor Cyan
Write-Host "    Start-ScheduledTask -TaskName $TaskName"

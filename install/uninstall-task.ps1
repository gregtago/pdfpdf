# ---------------------------------------------------------------------------
# Désinstalle la tâche planifiée du service OCR PDF.
#     powershell -ExecutionPolicy Bypass -File install\uninstall-task.ps1
# ---------------------------------------------------------------------------

param(
    [string]$TaskName = "OCR-PDF-Service"
)

$ErrorActionPreference = "Stop"

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask  -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Tache '$TaskName' desinstallee." -ForegroundColor Green
} else {
    Write-Host "Aucune tache '$TaskName' trouvee."
}

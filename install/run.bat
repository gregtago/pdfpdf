@echo off
REM Lance le service OCR PDF dans une fenetre (utile pour tester / voir les logs).
REM Double-cliquez ce fichier, ou lancez-le depuis une invite de commandes.

cd /d "%~dp0.."
python -m ocr_service %*
pause

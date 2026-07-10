@echo off
REM Lance Scribe dans une fenetre (utile pour tester / voir les logs).
REM Double-cliquez ce fichier, ou lancez-le depuis une invite de commandes.

cd /d "%~dp0.."
python -m scribe %*
pause

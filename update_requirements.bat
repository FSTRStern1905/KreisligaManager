@echo off
title Requirements aktualisieren
cd /d "%~dp0"

echo ==========================================
echo        requirements.txt aktualisieren
echo ==========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden.
    pause
    exit /b
)

call ".venv\Scripts\activate.bat"

pip freeze > requirements.txt

echo.
echo requirements.txt wurde aktualisiert.
pause
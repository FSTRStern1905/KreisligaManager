@echo off
title KreisligaManager Build
cd /d "%~dp0"

echo ==========================================
echo        Release Build
echo ==========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden.
    pause
    exit /b
)

call ".venv\Scripts\activate.bat"

echo Dieser Build-Schritt wird spaeter mit PyInstaller erweitert.
echo Aktuell ist noch kein Release-Build eingerichtet.
echo.

pause
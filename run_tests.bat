@echo off
title KreisligaManager Tests
cd /d "%~dp0"

echo ==========================================
echo        Tests ausfuehren
echo ==========================================
echo.

if not exist ".venv\Scripts\activate.bat" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden.
    pause
    exit /b
)

call ".venv\Scripts\activate.bat"

python -m unittest discover tests

echo.
pause
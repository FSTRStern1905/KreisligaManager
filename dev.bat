@echo off
title KreisligaManager DEV Center
cd /d "%~dp0"

:menu
cls
echo ==========================================
echo        KreisligaManager DEV Center
echo ==========================================
echo.
echo [1] Projekt starten
echo [2] Projektstruktur aktualisieren
echo [3] Tests ausfuehren
echo [4] requirements.txt aktualisieren
echo.
echo [5] Git Status
echo [6] Git Pull
echo [7] Git Add + Commit + Push
echo.
echo [8] Datenbank loeschen
echo [9] Datenbank neu erstellen
echo.
echo [0] Beenden
echo.
set /p choice=Auswahl: 

if "%choice%"=="1" call start.bat
if "%choice%"=="2" call projektstruktur.bat
if "%choice%"=="3" call run_tests.bat
if "%choice%"=="4" call update_requirements.bat
if "%choice%"=="5" goto gitstatus
if "%choice%"=="6" goto gitpull
if "%choice%"=="7" goto gitcommitpush
if "%choice%"=="8" goto deletedb
if "%choice%"=="9" goto recreatedb
if "%choice%"=="0" exit /b

goto menu

:gitstatus
cls
git status
echo.
pause
goto menu

:gitpull
cls
git pull
echo.
pause
goto menu

:gitcommitpush
cls
git status
echo.
set /p msg=Commit-Nachricht eingeben: 
git add .
git commit -m "%msg%"
git push
echo.
pause
goto menu

:deletedb
cls
echo Datenbank wird geloescht...
echo.
if exist "data\database\kreisligamanager.db" (
    del "data\database\kreisligamanager.db"
    echo Datenbank geloescht.
) else (
    echo Keine Datenbank gefunden.
)
echo.
pause
goto menu

:recreatedb
cls
echo Datenbank wird neu erstellt...
echo.
if not exist ".venv\Scripts\activate.bat" (
    echo FEHLER: Virtuelle Umgebung nicht gefunden.
    pause
    goto menu
)

call ".venv\Scripts\activate.bat"
python main.py
echo.
pause
goto menu
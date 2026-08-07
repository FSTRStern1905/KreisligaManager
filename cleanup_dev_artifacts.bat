@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  KreisligaManager - Finales Cleanup
echo  Entwicklungsartefakte + .gitignore
echo ============================================================
echo.
echo Es wird NICHT endgueltig geloescht.
echo debug, data\temp und alte Test-ZIPs werden gesichert.
echo.
echo KreisligaManager vorher schliessen.
echo.
pause

set "BACKUP=data\backups\cleanup_dev_artifacts_%RANDOM%"

if not exist "%BACKUP%" mkdir "%BACKUP%"
if not exist "%BACKUP%\data" mkdir "%BACKUP%\data"

echo.
echo Backup:
echo %BACKUP%
echo.

REM ------------------------------------------------------------
REM debug\
REM ------------------------------------------------------------
if exist "debug\" (
    move "debug" "%BACKUP%\debug" >nul
    echo [VERSCHOBEN] debug\
) else (
    echo [NICHT GEFUNDEN] debug\
)

REM ------------------------------------------------------------
REM data\temp\
REM ------------------------------------------------------------
if exist "data\temp\" (
    move "data\temp" "%BACKUP%\data\temp" >nul
    echo [VERSCHOBEN] data\temp\
) else (
    echo [NICHT GEFUNDEN] data\temp\
)

REM ------------------------------------------------------------
REM Alte Root-Test-ZIPs
REM ------------------------------------------------------------
if exist "02TKDR2LFG000000VS5489BUVUD1610F.zip" (
    move /Y "02TKDR2LFG000000VS5489BUVUD1610F.zip" "%BACKUP%\" >nul
    echo [VERSCHOBEN] 02TKDR2LFG000000VS5489BUVUD1610F.zip
) else (
    echo [NICHT GEFUNDEN] 02TKDR2LFG000000VS5489BUVUD1610F.zip
)

if exist "02TNB07DS8000000VS5489BUVSSD35NB.zip" (
    move /Y "02TNB07DS8000000VS5489BUVSSD35NB.zip" "%BACKUP%\" >nul
    echo [VERSCHOBEN] 02TNB07DS8000000VS5489BUVSSD35NB.zip
) else (
    echo [NICHT GEFUNDEN] 02TNB07DS8000000VS5489BUVSSD35NB.zip
)

REM ------------------------------------------------------------
REM .gitignore sicher erweitern
REM ------------------------------------------------------------
if not exist ".gitignore" (
    type nul > ".gitignore"
)

findstr /x /c:"debug/" ".gitignore" >nul 2>&1
if errorlevel 1 echo debug/>>".gitignore"

findstr /x /c:"data/temp/" ".gitignore" >nul 2>&1
if errorlevel 1 echo data/temp/>>".gitignore"

findstr /x /c:"data/backups/" ".gitignore" >nul 2>&1
if errorlevel 1 echo data/backups/>>".gitignore"

findstr /x /c:"02TKDR2LFG000000VS5489BUVUD1610F.zip" ".gitignore" >nul 2>&1
if errorlevel 1 echo 02TKDR2LFG000000VS5489BUVUD1610F.zip>>".gitignore"

findstr /x /c:"02TNB07DS8000000VS5489BUVSSD35NB.zip" ".gitignore" >nul 2>&1
if errorlevel 1 echo 02TNB07DS8000000VS5489BUVSSD35NB.zip>>".gitignore"

echo [AKTUALISIERT] .gitignore

echo.
echo ============================================================
echo Cleanup abgeschlossen.
echo ============================================================
echo.
echo 1. GUI testen:
echo.
echo     python main.py
echo.
echo 2. Danach Git kontrollieren:
echo.
echo     git status
echo.
echo Backup NICHT sofort loeschen:
echo     %BACKUP%
echo.
pause

endlocal

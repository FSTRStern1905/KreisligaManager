@echo off
setlocal EnableExtensions EnableDelayedExpansion

title KreisligaManager - Projekt ZIP

echo ============================================================
echo  KreisligaManager - Projekt ZIP erstellen
echo ============================================================
echo.

REM ============================================================
REM Projektpfad
REM ============================================================

set "PROJECT_DIR=%~dp0"

REM Abschliessenden Backslash entfernen
set "SOURCE_DIR=%PROJECT_DIR:~0,-1%"

set "PROJECT_NAME=KreisligaManager"

REM ============================================================
REM Zeitstempel
REM ============================================================

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do (
    set "TIMESTAMP=%%I"
)

set "ZIP_NAME=%PROJECT_NAME%_%TIMESTAMP%.zip"
set "ZIP_PATH=%SOURCE_DIR%\%ZIP_NAME%"

REM ============================================================
REM Temporaerer Arbeitsordner
REM ============================================================

set "STAGE_DIR=%TEMP%\KreisligaManager_ZIP_%RANDOM%_%RANDOM%"

echo Projekt:
echo %SOURCE_DIR%
echo.

echo Ziel:
echo %ZIP_PATH%
echo.

echo Folgende Ordner werden NICHT mitgenommen:
echo   .venv
echo   .git
echo   __pycache__
echo   .pytest_cache
echo   .mypy_cache
echo   .ruff_cache
echo   .idea
echo   .vscode
echo   build
echo   dist
echo   node_modules
echo.

echo Ausgeschlossen werden ausserdem:
echo   *.pyc
echo   *.pyo
echo   alte KreisligaManager ZIP-Dateien
echo.

echo Die SQLite-Datenbank bleibt enthalten.
echo.

REM ============================================================
REM Temporaeren Ordner vorbereiten
REM ============================================================

if exist "%STAGE_DIR%" (
    rmdir /S /Q "%STAGE_DIR%"
)

mkdir "%STAGE_DIR%"

if errorlevel 1 (
    echo.
    echo FEHLER:
    echo Temporaerer Ordner konnte nicht erstellt werden.
    echo.
    pause
    exit /b 1
)

REM ============================================================
REM Projekt kopieren
REM ============================================================

echo Projektdateien werden vorbereitet...
echo.

robocopy "%SOURCE_DIR%" "%STAGE_DIR%" /E /R:1 /W:1 /NFL /NDL /NJH /NJS /NP /XD ".venv" ".git" "__pycache__" ".pytest_cache" ".mypy_cache" ".ruff_cache" ".idea" ".vscode" "build" "dist" "node_modules" /XF "*.pyc" "*.pyo" "KreisligaManager_*.zip"

set "ROBOCOPY_RESULT=%ERRORLEVEL%"

REM Robocopy Exit-Codes 0 bis 7 sind OK
if %ROBOCOPY_RESULT% GEQ 8 (
    echo.
    echo ============================================================
    echo  FEHLER
    echo ============================================================
    echo.
    echo Fehler beim Kopieren der Projektdateien.
    echo Robocopy Exit-Code: %ROBOCOPY_RESULT%
    echo.

    if exist "%STAGE_DIR%" (
        rmdir /S /Q "%STAGE_DIR%"
    )

    pause
    exit /b 1
)

REM ============================================================
REM Altes Ziel entfernen
REM ============================================================

if exist "%ZIP_PATH%" (
    del /Q "%ZIP_PATH%"
)

REM ============================================================
REM ZIP erstellen
REM ============================================================

echo.
echo ZIP wird erstellt...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"Add-Type -AssemblyName System.IO.Compression.FileSystem; $source='%STAGE_DIR%'; $target='%ZIP_PATH%'; [System.IO.Compression.ZipFile]::CreateFromDirectory($source, $target, [System.IO.Compression.CompressionLevel]::Optimal, $false)"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  FEHLER
    echo ============================================================
    echo.
    echo ZIP konnte nicht erstellt werden.
    echo.

    if exist "%STAGE_DIR%" (
        rmdir /S /Q "%STAGE_DIR%"
    )

    pause
    exit /b 1
)

REM ============================================================
REM Temporaeren Ordner entfernen
REM ============================================================

if exist "%STAGE_DIR%" (
    rmdir /S /Q "%STAGE_DIR%"
)

REM ============================================================
REM Dateigroesse ermitteln
REM ============================================================

for /f "delims=" %%I in ('powershell -NoProfile -Command "$f=Get-Item -LiteralPath '%ZIP_PATH%'; [math]::Round($f.Length / 1MB, 2)"') do (
    set "ZIP_SIZE_MB=%%I"
)

for /f "delims=" %%I in ('powershell -NoProfile -Command "$f=Get-Item -LiteralPath '%ZIP_PATH%'; if ($f.Length -lt 500MB) {'OK'} else {'TOO_BIG'}"') do (
    set "SIZE_STATUS=%%I"
)

REM ============================================================
REM Ergebnis
REM ============================================================

echo.
echo ============================================================
echo  FERTIG
echo ============================================================
echo.

echo ZIP:
echo %ZIP_NAME%
echo.

echo Groesse:
echo %ZIP_SIZE_MB% MB
echo.

if "%SIZE_STATUS%"=="OK" (
    echo OK - ZIP liegt unter 500 MB.
) else (
    echo WARNUNG - ZIP ist groesser als 500 MB.
)

echo.
echo Speicherort:
echo %ZIP_PATH%
echo.

pause
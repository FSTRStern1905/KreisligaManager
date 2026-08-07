@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"

echo ============================================================
echo  KreisligaManager - Legacy Cleanup
echo ============================================================
echo.
echo Projektordner:
echo %CD%
echo.
echo WICHTIG:
echo - KreisligaManager vorher schliessen.
echo - Dateien werden NICHT endgueltig geloescht.
echo - Sie werden nach data\backups\cleanup_... verschoben.
echo.
pause

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "STAMP=%%I"

set "BACKUP_ROOT=data\backups\cleanup_%STAMP%"

echo.
echo Backup:
echo %BACKUP_ROOT%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
"$ErrorActionPreference = 'Stop';" ^
"$root = (Get-Location).Path;" ^
"$backup = Join-Path $root '%BACKUP_ROOT%';" ^
"$files = @(" ^
"'src/core/app.py'," ^
"'src/core/logger.py'," ^
"'src/core/settings.py'," ^
"'src/database/migrations.py'," ^
"'src/database/models.py'," ^
"'src/database/queries.py'," ^
"'src/database/seed.py'," ^
"'src/database/models/country.py'," ^
"'src/database/models/event.py'," ^
"'src/database/models/formation.py'," ^
"'src/database/models/player.py'," ^
"'src/database/models/referee.py'," ^
"'src/database/models/stadium.py'," ^
"'src/database/models/team.py'," ^
"'src/importer/csv_reader.py'," ^
"'src/importer/event_importer.py'," ^
"'src/importer/match_importer.py'," ^
"'src/importer/player_importer.py'," ^
"'src/importer/team_importer.py'," ^
"'src/importer/validator.py'," ^
"'src/ui/dialogs/about_dialog.py'," ^
"'src/ui/dialogs/settings_dialog.py'," ^
"'src/ui/widgets/sidebar.py'," ^
"'src/ui/widgets/statusbar.py'," ^
"'src/validator/html_match_parser.py'" ^
");" ^
"$moved = 0;" ^
"$missing = 0;" ^
"foreach ($relative in $files) {" ^
"    $source = Join-Path $root $relative;" ^
"    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {" ^
"        Write-Host ('[FEHLT]       ' + $relative) -ForegroundColor DarkGray;" ^
"        $missing++;" ^
"        continue;" ^
"    }" ^
"    $destination = Join-Path $backup $relative;" ^
"    $destinationDir = Split-Path -Parent $destination;" ^
"    New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null;" ^
"    Move-Item -LiteralPath $source -Destination $destination;" ^
"    Write-Host ('[VERSCHOBEN] ' + $relative) -ForegroundColor Green;" ^
"    $moved++;" ^
"};" ^
"Write-Host '';" ^
"Write-Host '------------------------------------------------------------';" ^
"Write-Host ('Verschoben: ' + $moved);" ^
"Write-Host ('Nicht gefunden: ' + $missing);" ^
"Write-Host ('Backup: ' + $backup);" ^
"Write-Host '------------------------------------------------------------';"

if errorlevel 1 (
    echo.
    echo FEHLER: Cleanup wurde abgebrochen.
    echo Bereits verschobene Dateien liegen im Backup-Ordner.
    echo.
    pause
    exit /b 1
)

echo.
echo Cleanup abgeschlossen.
echo.
echo Jetzt bitte testen:
echo.
echo     python main.py
echo.
echo Wenn alles funktioniert, behalten wir diesen Stand.
echo Backup-Ordner:
echo     %BACKUP_ROOT%
echo.
pause

endlocal

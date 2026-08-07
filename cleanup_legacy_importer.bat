@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  KreisligaManager - Cleanup Paket C
echo  Legacy Importer
echo ============================================================
echo.
echo Diese Dateien gehoeren zur alten Importer-Kette.
echo Sie werden NICHT geloescht, sondern ins Backup verschoben.
echo.
echo KreisligaManager vorher schliessen.
echo.
pause

set "BACKUP=data\backups\cleanup_legacy_importer"
if not exist "%BACKUP%" mkdir "%BACKUP%"

if exist "src\demo\import_demo.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\demo\import_demo.py" "%BACKUP%\src\demo\import_demo.py" >nul
    echo [VERSCHOBEN] src\demo\import_demo.py
) else (
    echo [NICHT GEFUNDEN] src\demo\import_demo.py
)

if exist "src\importer\base_importer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\base_importer.py" "%BACKUP%\src\importer\base_importer.py" >nul
    echo [VERSCHOBEN] src\importer\base_importer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\base_importer.py
)

if exist "src\importer\club_import_service.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\club_import_service.py" "%BACKUP%\src\importer\club_import_service.py" >nul
    echo [VERSCHOBEN] src\importer\club_import_service.py
) else (
    echo [NICHT GEFUNDEN] src\importer\club_import_service.py
)

if exist "src\importer\club_importer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\club_importer.py" "%BACKUP%\src\importer\club_importer.py" >nul
    echo [VERSCHOBEN] src\importer\club_importer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\club_importer.py
)

if exist "src\importer\csv_importer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\csv_importer.py" "%BACKUP%\src\importer\csv_importer.py" >nul
    echo [VERSCHOBEN] src\importer\csv_importer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\csv_importer.py
)

if exist "src\importer\import_manager.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\import_manager.py" "%BACKUP%\src\importer\import_manager.py" >nul
    echo [VERSCHOBEN] src\importer\import_manager.py
) else (
    echo [NICHT GEFUNDEN] src\importer\import_manager.py
)

if exist "src\importer\validators.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\validators.py" "%BACKUP%\src\importer\validators.py" >nul
    echo [VERSCHOBEN] src\importer\validators.py
) else (
    echo [NICHT GEFUNDEN] src\importer\validators.py
)

if exist "src\importer\fussballde\importer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\importer.py" "%BACKUP%\src\importer\fussballde\importer.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\importer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\importer.py
)

echo ============================================================
echo Cleanup Paket C abgeschlossen.
echo ============================================================
echo.
echo Jetzt testen:
echo     python main.py
echo.
echo Backup vorerst NICHT loeschen.
echo.
pause
endlocal

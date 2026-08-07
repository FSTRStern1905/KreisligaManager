@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ============================================================
echo  KreisligaManager - Cleanup Paket 3 FIXED
echo ============================================================
echo.
echo Dateien werden nur nach data\backups verschoben.
echo Es wird nichts endgueltig geloescht.
echo.
pause

set "BACKUP=data\backups\cleanup_debug_tools"
if not exist "%BACKUP%" mkdir "%BACKUP%"

if exist "src\importer\fussballde\ajax_tester.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\ajax_tester.py" "%BACKUP%\src\importer\fussballde\ajax_tester.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\ajax_tester.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\ajax_tester.py
)

if exist "src\importer\fussballde\debug_matchday.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\debug_matchday.py" "%BACKUP%\src\importer\fussballde\debug_matchday.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\debug_matchday.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\debug_matchday.py
)

if exist "src\importer\fussballde\dom_inspector.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\dom_inspector.py" "%BACKUP%\src\importer\fussballde\dom_inspector.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\dom_inspector.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\dom_inspector.py
)

if exist "src\importer\fussballde\font_inspector.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\font_inspector.py" "%BACKUP%\src\importer\fussballde\font_inspector.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\font_inspector.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\font_inspector.py
)

if exist "src\importer\fussballde\font_mapping_tester.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\font_mapping_tester.py" "%BACKUP%\src\importer\fussballde\font_mapping_tester.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\font_mapping_tester.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\font_mapping_tester.py
)

if exist "src\importer\fussballde\inspector.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\inspector.py" "%BACKUP%\src\importer\fussballde\inspector.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\inspector.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\inspector.py
)

if exist "src\importer\fussballde\liveticker_explorer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\liveticker_explorer.py" "%BACKUP%\src\importer\fussballde\liveticker_explorer.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\liveticker_explorer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\liveticker_explorer.py
)

if exist "src\importer\fussballde\liveticker_network_explorer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\liveticker_network_explorer.py" "%BACKUP%\src\importer\fussballde\liveticker_network_explorer.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\liveticker_network_explorer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\liveticker_network_explorer.py
)

if exist "src\importer\fussballde\liveticker_type_id_explorer.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\liveticker_type_id_explorer.py" "%BACKUP%\src\importer\fussballde\liveticker_type_id_explorer.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\liveticker_type_id_explorer.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\liveticker_type_id_explorer.py
)

if exist "src\importer\fussballde\match_detail_event_inspector.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\match_detail_event_inspector.py" "%BACKUP%\src\importer\fussballde\match_detail_event_inspector.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\match_detail_event_inspector.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\match_detail_event_inspector.py
)

if exist "src\importer\fussballde\match_detail_inspector.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\match_detail_inspector.py" "%BACKUP%\src\importer\fussballde\match_detail_inspector.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\match_detail_inspector.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\match_detail_inspector.py
)

if exist "src\importer\fussballde\match_detail_structure_inspector.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\match_detail_structure_inspector.py" "%BACKUP%\src\importer\fussballde\match_detail_structure_inspector.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\match_detail_structure_inspector.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\match_detail_structure_inspector.py
)

if exist "src\importer\fussballde\rendered_dom_tester.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\rendered_dom_tester.py" "%BACKUP%\src\importer\fussballde\rendered_dom_tester.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\rendered_dom_tester.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\rendered_dom_tester.py
)

if exist "src\importer\fussballde\test_browser.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\importer\fussballde\test_browser.py" "%BACKUP%\src\importer\fussballde\test_browser.py" >nul
    echo [VERSCHOBEN] src\importer\fussballde\test_browser.py
) else (
    echo [NICHT GEFUNDEN] src\importer\fussballde\test_browser.py
)

if exist "src\services\test_schedule_generator.py" (
    if not exist "%BACKUP%\." mkdir "%BACKUP%\."
    move /Y "src\services\test_schedule_generator.py" "%BACKUP%\src\services\test_schedule_generator.py" >nul
    echo [VERSCHOBEN] src\services\test_schedule_generator.py
) else (
    echo [NICHT GEFUNDEN] src\services\test_schedule_generator.py
)

echo ============================================================
echo Cleanup abgeschlossen.
echo ============================================================
echo.
echo Jetzt testen:
echo     python main.py
echo.
pause
endlocal

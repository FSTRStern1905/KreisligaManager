@echo off
cd /d "%~dp0"

echo =====================================
echo KreisligaManager - Projektstruktur
echo =====================================
echo.

REM ================================
REM Hauptordner
REM ================================

mkdir assets 2>nul
mkdir config 2>nul
mkdir data 2>nul
mkdir data\database 2>nul
mkdir docs 2>nul
mkdir exports 2>nul
mkdir imports 2>nul
mkdir tests 2>nul

REM ================================
REM SRC Ordner
REM ================================

mkdir src 2>nul
mkdir src\core 2>nul
mkdir src\database 2>nul
mkdir src\database\models 2>nul
mkdir src\importer 2>nul
mkdir src\media 2>nul
mkdir src\parser 2>nul
mkdir src\resources 2>nul
mkdir src\services 2>nul
mkdir src\statistics 2>nul
mkdir src\ui 2>nul
mkdir src\utils 2>nul

REM ================================
REM __init__.py Dateien
REM ================================

if not exist src\__init__.py type nul > src\__init__.py
if not exist src\core\__init__.py type nul > src\core\__init__.py
if not exist src\database\__init__.py type nul > src\database\__init__.py
if not exist src\database\models\__init__.py type nul > src\database\models\__init__.py
if not exist src\importer\__init__.py type nul > src\importer\__init__.py
if not exist src\media\__init__.py type nul > src\media\__init__.py
if not exist src\parser\__init__.py type nul > src\parser\__init__.py
if not exist src\resources\__init__.py type nul > src\resources\__init__.py
if not exist src\services\__init__.py type nul > src\services\__init__.py
if not exist src\statistics\__init__.py type nul > src\statistics\__init__.py
if not exist src\ui\__init__.py type nul > src\ui\__init__.py
if not exist src\utils\__init__.py type nul > src\utils\__init__.py

REM ================================
REM Core
REM ================================

if not exist src\core\app.py type nul > src\core\app.py
if not exist src\core\logger.py type nul > src\core\logger.py
if not exist src\core\settings.py type nul > src\core\settings.py

REM ================================
REM Database
REM ================================

if not exist src\database\database.py type nul > src\database\database.py
if not exist src\database\schema.py type nul > src\database\schema.py
if not exist src\database\repository.py type nul > src\database\repository.py
if not exist src\database\migrations.py type nul > src\database\migrations.py
if not exist src\database\queries.py type nul > src\database\queries.py
if not exist src\database\seed.py type nul > src\database\seed.py

REM ================================
REM Database Models
REM ================================

if not exist src\database\models\country.py type nul > src\database\models\country.py
if not exist src\database\models\association.py type nul > src\database\models\association.py
if not exist src\database\models\league.py type nul > src\database\models\league.py
if not exist src\database\models\season.py type nul > src\database\models\season.py
if not exist src\database\models\club.py type nul > src\database\models\club.py
if not exist src\database\models\team.py type nul > src\database\models\team.py
if not exist src\database\models\player.py type nul > src\database\models\player.py
if not exist src\database\models\stadium.py type nul > src\database\models\stadium.py
if not exist src\database\models\referee.py type nul > src\database\models\referee.py
if not exist src\database\models\match.py type nul > src\database\models\match.py
if not exist src\database\models\event.py type nul > src\database\models\event.py
if not exist src\database\models\formation.py type nul > src\database\models\formation.py

REM ================================
REM Importer
REM ================================

if not exist src\importer\csv_reader.py type nul > src\importer\csv_reader.py
if not exist src\importer\validator.py type nul > src\importer\validator.py
if not exist src\importer\import_manager.py type nul > src\importer\import_manager.py
if not exist src\importer\club_importer.py type nul > src\importer\club_importer.py
if not exist src\importer\team_importer.py type nul > src\importer\team_importer.py
if not exist src\importer\player_importer.py type nul > src\importer\player_importer.py
if not exist src\importer\match_importer.py type nul > src\importer\match_importer.py
if not exist src\importer\event_importer.py type nul > src\importer\event_importer.py

REM ================================
REM UI
REM ================================

if not exist src\ui\main_window.py type nul > src\ui\main_window.py
if not exist src\ui\dialogs.py type nul > src\ui\dialogs.py
if not exist src\ui\widgets.py type nul > src\ui\widgets.py
if not exist src\ui\menu.py type nul > src\ui\menu.py
if not exist src\ui\toolbar.py type nul > src\ui\toolbar.py
if not exist src\ui\statusbar.py type nul > src\ui\statusbar.py

REM ================================
REM Docs
REM ================================

if not exist docs\roadmap.md type nul > docs\roadmap.md
if not exist docs\architecture.md type nul > docs\architecture.md
if not exist docs\database.md type nul > docs\database.md
if not exist docs\importer.md type nul > docs\importer.md
if not exist docs\gui.md type nul > docs\gui.md
if not exist docs\statistics.md type nul > docs\statistics.md
if not exist docs\changelog.md type nul > docs\changelog.md
if not exist docs\coding_guidelines.md type nul > docs\coding_guidelines.md

REM ================================
REM Tests
REM ================================

if not exist tests\__init__.py type nul > tests\__init__.py
if not exist tests\test_database.py type nul > tests\test_database.py
if not exist tests\test_repository.py type nul > tests\test_repository.py
if not exist tests\test_models.py type nul > tests\test_models.py
if not exist tests\test_importer.py type nul > tests\test_importer.py

echo.
echo =====================================
echo Projektstruktur erfolgreich geprueft.
echo Fehlende Ordner und Dateien wurden erstellt.
echo Bestehende Dateien wurden nicht ueberschrieben.
echo =====================================
echo.

pause
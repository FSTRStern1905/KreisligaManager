@echo off
cd /d E:\Kreisligamanager

echo Erstelle Ordnerstruktur...

mkdir src\core
mkdir src\database
mkdir src\importer

type nul > src\core\app.py
type nul > src\core\logger.py
type nul > src\core\settings.py

type nul > src\database\repository.py

type nul > src\importer\csv_reader.py
type nul > src\importer\validator.py
type nul > src\importer\import_manager.py
type nul > src\importer\club_importer.py
type nul > src\importer\team_importer.py
type nul > src\importer\player_importer.py
type nul > src\importer\match_importer.py
type nul > src\importer\event_importer.py

type nul > src\core\__init__.py
type nul > src\importer\__init__.py

echo Fertig.
pause
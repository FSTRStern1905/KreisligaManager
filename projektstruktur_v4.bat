@echo off
cd /d "%~dp0"

echo ===============================
echo KreisligaManager Strukturupdate
echo ===============================

REM ----- Ordner -----

mkdir src\services 2>nul
mkdir src\statistics 2>nul
mkdir src\utils 2>nul
mkdir src\resources 2>nul

mkdir docs 2>nul

REM ----- UI -----

if not exist src\ui\__init__.py type nul > src\ui\__init__.py
if not exist src\ui\main_window.py type nul > src\ui\main_window.py
if not exist src\ui\dialogs.py type nul > src\ui\dialogs.py
if not exist src\ui\widgets.py type nul > src\ui\widgets.py
if not exist src\ui\menu.py type nul > src\ui\menu.py
if not exist src\ui\toolbar.py type nul > src\ui\toolbar.py
if not exist src\ui\statusbar.py type nul > src\ui\statusbar.py

REM ----- Database -----

if not exist src\database\queries.py type nul > src\database\queries.py

REM ----- Utils -----

if not exist src\utils\__init__.py type nul > src\utils\__init__.py

REM ----- Services -----

if not exist src\services\__init__.py type nul > src\services\__init__.py

REM ----- Statistics -----

if not exist src\statistics\__init__.py type nul > src\statistics\__init__.py

REM ----- Resources -----

if not exist src\resources\__init__.py type nul > src\resources\__init__.py

REM ----- Dokumentation -----

if not exist docs\database.md type nul > docs\database.md
if not exist docs\importer.md type nul > docs\importer.md
if not exist docs\gui.md type nul > docs\gui.md
if not exist docs\roadmap.md type nul > docs\roadmap.md
if not exist docs\changelog.md type nul > docs\changelog.md

echo.
echo =====================================
echo Struktur erfolgreich aktualisiert.
echo =====================================
pause
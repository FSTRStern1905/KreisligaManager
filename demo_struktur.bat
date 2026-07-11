@echo off
cd /d "%~dp0"

echo Erstelle Demo-Struktur...

mkdir src\demo 2>nul

if not exist src\demo\__init__.py type nul > src\demo\__init__.py
if not exist src\demo\demo_generator.py type nul > src\demo\demo_generator.py
if not exist src\demo\clubs.py type nul > src\demo\clubs.py
if not exist src\demo\players.py type nul > src\demo\players.py
if not exist src\demo\schedule.py type nul > src\demo\schedule.py
if not exist src\demo\matches.py type nul > src\demo\matches.py
if not exist src\demo\events.py type nul > src\demo\events.py
if not exist src\demo\names.py type nul > src\demo\names.py

echo.
echo Demo-Struktur erstellt.
pause
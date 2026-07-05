REM ================================
REM UI STRUKTUR
REM ================================

mkdir src\ui\windows 2>nul
mkdir src\ui\widgets 2>nul
mkdir src\ui\dialogs 2>nul
mkdir src\ui\resources 2>nul
mkdir src\ui\styles 2>nul

if not exist src\ui\windows\__init__.py type nul > src\ui\windows\__init__.py
if not exist src\ui\widgets\__init__.py type nul > src\ui\widgets\__init__.py
if not exist src\ui\dialogs\__init__.py type nul > src\ui\dialogs\__init__.py
if not exist src\ui\resources\__init__.py type nul > src\ui\resources\__init__.py
if not exist src\ui\styles\__init__.py type nul > src\ui\styles\__init__.py

REM ----- Windows -----

if not exist src\ui\windows\main_window.py type nul > src\ui\windows\main_window.py
if not exist src\ui\windows\dashboard.py type nul > src\ui\windows\dashboard.py

REM ----- Dialoge -----

if not exist src\ui\dialogs\about_dialog.py type nul > src\ui\dialogs\about_dialog.py
if not exist src\ui\dialogs\settings_dialog.py type nul > src\ui\dialogs\settings_dialog.py

REM ----- Widgets -----

if not exist src\ui\widgets\sidebar.py type nul > src\ui\widgets\sidebar.py
if not exist src\ui\widgets\statusbar.py type nul > src\ui\widgets\statusbar.py
if not exist src\ui\widgets\toolbar.py type nul > src\ui\widgets\toolbar.py
if not exist src\ui\widgets\info_card.py type nul > src\ui\widgets\info_card.py

REM ----- Styles -----

if not exist src\ui\styles\dark.qss type nul > src\ui\styles\dark.qss
if not exist src\ui\styles\light.qss type nul > src\ui\styles\light.qss
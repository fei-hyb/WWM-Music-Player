@echo off
echo Starting Music Player GUI...
cd /d "%~dp0"
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)
python gui_launcher.py
pause


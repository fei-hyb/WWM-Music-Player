@echo off
echo Starting Game Music Player...
cd /d "%~dp0"

echo Checking for virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Virtual environment not found, using system Python...
)

echo Running dependency test...
python test_setup.py

echo.
echo If the test passed, launching music player...
python launcher.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred. Error level: %ERRORLEVEL%
    echo Please check that Python and all dependencies are installed.
)

pause


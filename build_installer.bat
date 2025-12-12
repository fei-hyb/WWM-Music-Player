@echo off
REM build_installer.bat - Create standalone exe and optional installer for Game Music Player
REM Run from project root (same folder as gui_launcher.py). Requires Python 3.9+ and optional Inno Setup.

setlocal ENABLEDELAYEDEXPANSION

set PROJECT_ROOT=%~dp0
if "%PROJECT_ROOT:~-1%"=="\" set PROJECT_ROOT=%PROJECT_ROOT:~0,-1%
set VENV_DIR=%PROJECT_ROOT%\.venv-build
set DIST_DIR=%PROJECT_ROOT%\dist
set BUILD_DIR=%PROJECT_ROOT%\build
set PACKAGING_DIR=%PROJECT_ROOT%\packaging
set SPEC_FILE=%PACKAGING_DIR%\game_music_player.spec
set INSTALLER_SCRIPT=%PACKAGING_DIR%\game_music_player.iss
set ENTRY=gui_launcher.py
set EXE_NAME=GameMusicPlayer

if not exist "%PACKAGING_DIR%" mkdir "%PACKAGING_DIR%"

echo [1/7] Creating isolated virtual environment...
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
)

call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)

echo [2/7] Upgrading pip and installing build dependencies...
python -m pip install --upgrade pip
python -m pip install -r "%PROJECT_ROOT%\requirements.txt"
python -m pip install pyinstaller

echo [3/7] Checking PyInstaller spec...
if not exist "%SPEC_FILE%" (
    echo [ERROR] Spec file not found at %SPEC_FILE%.
    exit /b 1
)

echo [3.5/7] Cleaning previous dist/build executables...
if exist "%DIST_DIR%\%EXE_NAME%.exe" (
    echo Deleting old %EXE_NAME%.exe
    del /f /q "%DIST_DIR%\%EXE_NAME%.exe"
)
if exist "%BUILD_DIR%\%EXE_NAME%" (
    echo Removing previous build folder
    rmdir /s /q "%BUILD_DIR%\%EXE_NAME%"
)

echo [4/7] Building executable with PyInstaller...
pyinstaller "%SPEC_FILE%"
if errorlevel 1 (
    echo PyInstaller build failed.
    exit /b 1
)

if exist "%DIST_DIR%\%EXE_NAME%.exe" (
    echo [INFO] Standalone executable ready: %DIST_DIR%\%EXE_NAME%.exe
) else (
    echo [WARN] Expected exe not found at %DIST_DIR%\%EXE_NAME%.exe
)

echo [5/7] Cleaning old Inno Setup output...
if exist "%PROJECT_ROOT%\output" rmdir /s /q "%PROJECT_ROOT%\output"

echo [6/7] Building Inno Setup installer (if ISCC.exe is on PATH)...
where ISCC.exe >nul 2>&1
if errorlevel 1 (
    echo [INFO] ISCC.exe not found; skipping installer build.
) else (
    if not exist "%INSTALLER_SCRIPT%" echo [WARN] Installer script missing at %INSTALLER_SCRIPT%
    if exist "%INSTALLER_SCRIPT%" (
        ISCC.exe "%INSTALLER_SCRIPT%"
        if errorlevel 1 (
            echo [ERROR] Inno Setup build failed.
            exit /b 1
        ) else (
            echo [INFO] Installer created in %PROJECT_ROOT%\output
        )
    )
)

echo [7/7] Deactivating env and cleaning up...
call "%VENV_DIR%\Scripts\deactivate.bat" 2>nul
echo Removing temporary build venv...
rmdir /s /q "%VENV_DIR%"

echo Build pipeline finished.
exit /b 0

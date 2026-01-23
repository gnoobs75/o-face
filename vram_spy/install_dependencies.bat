@echo off
title VRAM Spy - Install Dependencies

cd /d "%~dp0"

echo ========================================
echo  VRAM Spy - Installing Dependencies
echo ========================================
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Installation failed. Please check that Python and pip are installed.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Installation complete!
echo  Run 'run_vram_spy.bat' to start.
echo ========================================
echo.
pause

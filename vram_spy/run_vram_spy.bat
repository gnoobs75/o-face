@echo off
title VRAM Spy - GPU Monitor

cd /d "%~dp0"

echo Starting VRAM Spy...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start VRAM Spy.
    echo.
    echo Make sure you have installed the dependencies:
    echo   pip install -r requirements.txt
    echo.
    pause
)

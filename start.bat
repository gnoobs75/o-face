@echo off
title o-face Terminal
cd /d "%~dp0"

echo.
echo   o-face Terminal
echo   The Unofficial Homepage of Ronin
echo.

:: Check if node_modules exists
if not exist "node_modules\" (
    echo Installing dependencies...
    echo.
    call npm install
    if errorlevel 1 (
        echo.
        echo ERROR: npm install failed. Make sure Node.js is installed.
        pause
        exit /b 1
    )
    echo.
)

echo Starting o-face...
echo.
call npm start

:: If npm start fails, pause so user can see error
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start. Check the error above.
    pause
)

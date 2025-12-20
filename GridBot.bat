@echo off
title Grid Trading Bot
cd /d "%~dp0"

echo.
echo ========================================
echo   Grid Trading Bot
echo ========================================
echo.

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo Warning: No virtual environment found
    echo Consider running: python -m venv .venv
)

echo.

REM Check if config exists
if not exist "config\config.json" (
    echo ERROR: config\config.json not found!
    echo.
    echo Please copy config\config.example.json to config\config.json
    echo and add your Kraken API keys.
    echo.
    pause
    exit /b 1
)

REM Kill any existing process on port 8080
echo Checking for existing processes on port 8080...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8080 ^| findstr LISTENING') do (
    echo Stopping existing process: %%a
    taskkill /PID %%a /F >nul 2>&1
)

echo.
echo Starting Grid Trading Bot...
echo.
echo ==========================================
echo   Dashboard: http://localhost:8080
echo ==========================================
echo.
echo Press Ctrl+C to stop the bot
echo.

REM Start the bot
python main.py --config config/config.json

if errorlevel 1 (
    echo.
    echo ==========================================
    echo   Bot exited with an error
    echo ==========================================
    echo.
    echo Check the logs folder for details.
    echo.
    pause
)

@echo off
title Grid Trading Bot
cd /d "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master"

echo.
echo ========================================
echo   Grid Trading Bot - Starting...
echo ========================================
echo.

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Check if config exists
if not exist "config\config.json" (
    echo ERROR: config\config.json not found!
    echo Please copy config\config.example.json to config\config.json
    echo and add your API keys.
    pause
    exit /b 1
)

REM Start the bot
echo Starting Grid Trading Bot...
echo Dashboard will be available at: http://localhost:8080
echo.
echo Press Ctrl+C to stop the bot
echo.

python main.py --config config/config.json

if errorlevel 1 (
    echo.
    echo Bot exited with an error. Check the logs folder for details.
    pause
)

@echo off
REM Grid Trading Bot Dashboard Launcher
REM This script opens the dashboard in your default browser

echo.
echo ========================================
echo Grid Trading Bot Dashboard
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if requests module is installed
python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing required packages...
    pip install requests
)

REM Run the dashboard launcher
echo Starting dashboard launcher...
echo.
python dashboard_launcher.py --no-tray

pause

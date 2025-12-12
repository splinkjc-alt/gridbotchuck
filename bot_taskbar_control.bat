@echo off
REM Grid Trading Bot - Taskbar Control Launcher
REM This script launches the bot taskbar control application

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║     Grid Trading Bot - Taskbar Control                     ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo.
    echo Please install Python or add it to your PATH
    pause
    exit /b 1
)

REM Check if required modules are installed
python -c "import pystray, PIL, requests" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Installing required packages...
    echo.
    pip install pystray pillow requests
    if errorlevel 1 (
        echo ❌ Failed to install packages
        pause
        exit /b 1
    )
)

REM Run the bot control application
echo ✓ Starting taskbar control application...
echo.
python bot_taskbar_control.py

if errorlevel 1 (
    echo.
    echo ❌ Error running bot control application
    pause
    exit /b 1
)

pause

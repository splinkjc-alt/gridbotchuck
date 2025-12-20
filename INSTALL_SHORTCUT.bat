@echo off
REM Grid Trading Bot - Desktop Shortcut Installer
REM Double-click this file to create a desktop shortcut

title Grid Trading Bot - Installer

echo.
echo ========================================
echo   Grid Trading Bot - Desktop Installer
echo ========================================
echo.

REM Check if PowerShell script exists
if not exist "install_desktop_shortcut.ps1" (
    echo ERROR: install_desktop_shortcut.ps1 not found!
    echo Please make sure you're running this from the grid_trading_bot folder.
    pause
    exit /b 1
)

echo Creating desktop shortcut...
echo.

REM Run PowerShell script with execution policy bypass
powershell -ExecutionPolicy Bypass -File "install_desktop_shortcut.ps1"

if errorlevel 1 (
    echo.
    echo Installation failed. See error above.
    pause
    exit /b 1
)

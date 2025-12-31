@echo off
title GridBot - Setup
color 0E

echo ========================================
echo   GridBot Portable Setup
echo ========================================
echo.
echo This will download Python and install dependencies.
echo This only needs to be run once.
echo.
pause
echo.

PowerShell -ExecutionPolicy Bypass -File "%~dp0BUILD_PORTABLE.ps1"

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next: Edit config\.env with your API keys
echo Then: Double-click START_BOT.bat to run
echo.
pause

@echo off
title GridBot EMA Trading Bot
color 0A

echo ========================================
echo   GridBot EMA 9/20 Crossover Bot
echo ========================================
echo.

REM Check if .env exists
if not exist "%~dp0config\.env" (
    echo ERROR: No API keys found!
    echo.
    echo Please edit config\.env with your Kraken API keys first.
    echo.
    pause
    exit /b 1
)

echo Starting bot...
echo Press Ctrl+C to stop
echo.

"%~dp0python\python.exe" "%~dp0scripts\run_ema_bot.py"

echo.
echo Bot stopped.
pause

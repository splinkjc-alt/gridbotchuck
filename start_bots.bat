@echo off
title Bot Launcher
cd /d D:\gridbotchuck

echo ============================================
echo          GRIDBOTCHUCK BOT LAUNCHER
echo ============================================
echo.

:: Activate virtual environment path
set PYTHON=D:\gridbotchuck\.venv\Scripts\python.exe

:: Start Watchdog in its own window
echo Starting Watchdog...
start "Watchdog" cmd /k "%PYTHON% bot_watchdog.py"
timeout /t 2 >nul

:: Start CrossKiller Paper in its own window
echo Starting CrossKiller (Paper)...
start "CrossKiller-Paper" cmd /k "%PYTHON% run_crosskiller_daytrader.py --paper"
timeout /t 2 >nul

:: Uncomment below to start Kraken bots when API is stable
:: echo Starting VET Momentum...
:: start "VET-Momentum" cmd /k "%PYTHON% run_vet_momentum.py"
:: timeout /t 2 >nul

:: echo Starting PEPE Momentum...
:: start "PEPE-Momentum" cmd /k "%PYTHON% run_pepe_momentum.py"
:: timeout /t 2 >nul

echo.
echo ============================================
echo All bots started in separate windows!
echo ============================================
echo.
echo To stop all bots: Close each window or run stop_bots.bat
echo.
pause

@echo off
title Bot Launcher - LIVE MODE
cd /d D:\gridbotchuck

echo ============================================
echo     GRIDBOTCHUCK BOT LAUNCHER - LIVE
echo ============================================
echo.
echo WARNING: This starts bots in LIVE trading mode!
echo Real money will be used.
echo.
set /p confirm="Type YES to continue: "
if /i not "%confirm%"=="YES" (
    echo Cancelled.
    pause
    exit
)

:: Activate virtual environment path
set PYTHON=D:\gridbotchuck\.venv\Scripts\python.exe

:: Start Watchdog in its own window
echo Starting Watchdog...
start "Watchdog" cmd /k "%PYTHON% bot_watchdog.py"
timeout /t 2 >nul

:: Start CrossKiller LIVE in its own window
echo Starting CrossKiller (LIVE)...
start "CrossKiller-LIVE" cmd /k "%PYTHON% run_crosskiller_daytrader.py"
timeout /t 2 >nul

echo.
echo ============================================
echo LIVE bots started!
echo ============================================
echo.
pause

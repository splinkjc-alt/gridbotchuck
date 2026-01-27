@echo off
echo ============================================
echo   GridBot Fleet Launcher
echo ============================================
echo.

:: Start Chuck
echo Starting Chuck (Grid Bot #1)...
start "Chuck - Grid Bot" cmd /k "cd /d D:\gridbotchuck && .venv\Scripts\activate && python run_smart_chuck.py"

:: Wait 5 seconds before starting Growler
echo Waiting 5 seconds...
timeout /t 5 /nobreak > nul

:: Start Growler
echo Starting Growler (Grid Bot #2)...
start "Growler - Grid Bot 2" cmd /k "cd /d D:\gridbotchuck && .venv\Scripts\activate && python run_smart_growler.py"

:: Wait 5 seconds before starting CrossKiller
echo Waiting 5 seconds...
timeout /t 5 /nobreak > nul

:: Start CrossKiller
echo Starting CrossKiller (EMA Momentum Bot)...
start "CrossKiller - EMA Bot" cmd /k "cd /d D:\gridbotchuck && .venv\Scripts\activate && python run_crosskiller.py"

echo.
echo ============================================
echo   All bots launched in separate windows!
echo ============================================
echo.
echo Chuck:      Grid trading (Kraken) - $600
echo Growler:    Grid trading (Kraken) - $600
echo CrossKiller: EMA momentum (Coinbase)
echo.
pause

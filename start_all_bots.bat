@echo off
echo ============================================
echo   GridBot Chuck - MOMENTUM STRATEGIES
echo   Updated: Jan 13, 2026
echo ============================================
echo.
echo These strategies were backtested and WORK!
echo.

cd /d D:\gridbotchuck

:: Start VET Momentum (Kraken - 15m RSI+BB)
echo [1/3] Starting VET Momentum (Kraken)...
start "VET Momentum - Kraken" cmd /k ".venv\Scripts\python.exe run_vet_momentum.py"

timeout /t 3 /nobreak > nul

:: Start PEPE Momentum (Kraken - 30m RSI+EMA)
echo [2/3] Starting PEPE Momentum (Kraken)...
start "PEPE Momentum - Kraken" cmd /k ".venv\Scripts\python.exe run_pepe_momentum.py"

timeout /t 3 /nobreak > nul

:: Start CrossKiller Daytrader (Coinbase - 5m EMA)
echo [3/3] Starting CrossKiller Daytrader (Coinbase)...
start "CrossKiller - Coinbase" cmd /k ".venv\Scripts\python.exe run_crosskiller_daytrader.py"

echo.
echo ============================================
echo   All MOMENTUM bots started!
echo ============================================
echo.
echo VET Momentum:  15m RSI+BB (backtest: +23%%)
echo PEPE Momentum: 30m RSI+EMA (backtest: +36%%)
echo CrossKiller:   5m EMA Daytrader
echo.
echo To stop: Close windows or run stop_bots.bat
echo.
pause

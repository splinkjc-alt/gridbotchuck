@echo off
echo ============================================================
echo STARTING MOMENTUM BOTS WITH VISIBLE WINDOWS
echo ============================================================
echo.

cd /d D:\gridbotchuck

echo Starting VET Momentum (Kraken - 15m RSI+BB)...
start "VET-Momentum" powershell -NoExit -Command ".venv\Scripts\python.exe run_vet_momentum.py"

timeout /t 3 /nobreak > nul

echo Starting PEPE Momentum (Kraken - 30m RSI+EMA)...
start "PEPE-Momentum" powershell -NoExit -Command ".venv\Scripts\python.exe run_pepe_momentum.py"

timeout /t 3 /nobreak > nul

echo Starting ATOM Momentum (Kraken - 15m EMA 6/25)...
start "ATOM-Momentum" powershell -NoExit -Command ".venv\Scripts\python.exe run_atom_momentum.py"

timeout /t 3 /nobreak > nul

echo Starting CrossKiller (Coinbase - 15m Scanner)...
start "CrossKiller" powershell -NoExit -Command ".venv\Scripts\python.exe run_crosskiller_daytrader.py"

echo.
echo ============================================================
echo ALL BOTS STARTED - 4 PowerShell windows opened
echo ============================================================
echo.
echo Bots running:
echo   1. VET Momentum  (Kraken)  - RSI + Bollinger Bands
echo   2. PEPE Momentum (Kraken)  - RSI + EMA(9/20)
echo   3. ATOM Momentum (Kraken)  - EMA(6/25) crossover
echo   4. CrossKiller   (Coinbase)- RSI oversold scanner
echo.
echo Close this window or press any key to exit...
pause > nul

@echo off
title Stop Bots
echo ============================================
echo          STOPPING ALL BOTS
echo ============================================
echo.

taskkill /F /FI "WINDOWTITLE eq Watchdog*" 2>nul
taskkill /F /FI "WINDOWTITLE eq CrossKiller*" 2>nul
taskkill /F /FI "WINDOWTITLE eq VET-Momentum*" 2>nul
taskkill /F /FI "WINDOWTITLE eq PEPE-Momentum*" 2>nul

:: Also kill any orphaned python processes running our scripts
taskkill /F /FI "IMAGENAME eq python.exe" 2>nul

echo.
echo All bots stopped.
echo.
pause

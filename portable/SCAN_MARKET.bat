@echo off
title GridBot - Market Scanner
color 0B

echo ========================================
echo   GridBot EMA Signal Scanner
echo ========================================
echo.
echo This shows current market signals WITHOUT trading.
echo.

"%~dp0python\python.exe" "%~dp0scripts\scan_ema_signals.py"

echo.
pause

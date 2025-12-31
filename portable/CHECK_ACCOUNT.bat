@echo off
title GridBot - Account Status
color 0E

echo ========================================
echo   GridBot Account Status
echo ========================================
echo.

"%~dp0python\python.exe" "%~dp0scripts\health_check.py"

echo.
pause

@echo off
echo Stopping all Python processes...
taskkill /F /IM python.exe 2>nul
echo Done.
timeout /t 2 >nul

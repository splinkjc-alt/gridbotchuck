@echo off
REM ============================================================
REM Grid Trading Bot - Portable Desktop Shortcut Installer
REM ============================================================
REM This is a SHAREABLE, self-contained installer.
REM Just place this file in your Grid Trading Bot folder and run it.
REM No other files required!
REM ============================================================

title Grid Trading Bot - Portable Installer
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo   Grid Trading Bot - Portable Desktop Installer
echo ========================================================
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

REM Check if main.py exists (verify we're in the right folder)
if not exist "%SCRIPT_DIR%\main.py" (
    echo [ERROR] main.py not found in this folder!
    echo.
    echo Please place this installer in your Grid Trading Bot folder
    echo and run it again.
    echo.
    pause
    exit /b 1
)

echo [OK] Found Grid Trading Bot folder: %SCRIPT_DIR%
echo.

REM Check for Python
set "PYTHON_PATH="
set "VENV_PYTHON=%SCRIPT_DIR%\.venv\Scripts\python.exe"

if exist "%VENV_PYTHON%" (
    set "PYTHON_PATH=%VENV_PYTHON%"
    echo [OK] Found virtual environment Python
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "delims=" %%i in ('where python') do set "PYTHON_PATH=%%i"
        echo [OK] Found system Python: !PYTHON_PATH!
    ) else (
        echo [ERROR] Python not found!
        echo Please install Python 3.10+ and try again.
        pause
        exit /b 1
    )
)

echo.
echo Creating launcher script...

REM Create GridBot.bat launcher
(
echo @echo off
echo title Grid Trading Bot
echo cd /d "%SCRIPT_DIR%"
echo.
echo echo.
echo echo ========================================
echo echo   Grid Trading Bot - Starting...
echo echo ========================================
echo echo.
echo.
echo REM Activate virtual environment if exists
echo if exist ".venv\Scripts\activate.bat" ^(
echo     call .venv\Scripts\activate.bat
echo ^)
echo.
echo REM Check if config exists
echo if not exist "config\config.json" ^(
echo     echo ERROR: config\config.json not found!
echo     echo Please copy config\config.example.json to config\config.json
echo     echo and add your API keys.
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Start the bot
echo echo Starting Grid Trading Bot...
echo echo Dashboard will be available at: http://localhost:8080
echo echo.
echo echo Press Ctrl+C to stop the bot
echo echo.
echo.
echo python main.py --config config/config.json
echo.
echo if errorlevel 1 ^(
echo     echo.
echo     echo Bot exited with an error. Check the logs folder for details.
echo     pause
echo ^)
) > "%SCRIPT_DIR%\GridBot.bat"

echo [OK] Created GridBot.bat launcher

REM Create desktop shortcut using PowerShell (inline)
echo.
echo Creating desktop shortcut...

set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT_NAME=Grid Trading Bot"
set "ICON_PATH=%SCRIPT_DIR%\Logo\gridbot.ico"

REM Check if icon exists
if not exist "%ICON_PATH%" (
    set "ICON_PATH=%%SystemRoot%%\System32\cmd.exe,0"
)

REM Use PowerShell to create the shortcut
powershell -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
    $s = $ws.CreateShortcut('%DESKTOP%\%SHORTCUT_NAME%.lnk'); ^
    $s.TargetPath = '%SCRIPT_DIR%\GridBot.bat'; ^
    $s.WorkingDirectory = '%SCRIPT_DIR%'; ^
    $s.Description = 'Start Grid Trading Bot with Dashboard'; ^
    $s.IconLocation = '%ICON_PATH%'; ^
    $s.Save()"

if %errorlevel% equ 0 (
    echo [OK] Created desktop shortcut: %SHORTCUT_NAME%
) else (
    echo [WARNING] Could not create desktop shortcut
)

REM Try to create Start Menu shortcut
set "STARTMENU=%APPDATA%\Microsoft\Windows\Start Menu\Programs"

powershell -ExecutionPolicy Bypass -Command ^
    "$ws = New-Object -ComObject WScript.Shell; ^
    $s = $ws.CreateShortcut('%STARTMENU%\%SHORTCUT_NAME%.lnk'); ^
    $s.TargetPath = '%SCRIPT_DIR%\GridBot.bat'; ^
    $s.WorkingDirectory = '%SCRIPT_DIR%'; ^
    $s.Description = 'Start Grid Trading Bot with Dashboard'; ^
    $s.IconLocation = '%ICON_PATH%'; ^
    $s.Save()" 2>nul

if %errorlevel% equ 0 (
    echo [OK] Created Start Menu shortcut
) else (
    echo [INFO] Start Menu shortcut skipped
)

echo.
echo ========================================================
echo   Installation Complete!
echo ========================================================
echo.
echo You can now:
echo   1. Double-click "Grid Trading Bot" on your Desktop
echo   2. Or run GridBot.bat from this folder
echo   3. Search "Grid Trading Bot" in Windows Start Menu
echo.
echo The dashboard will be at: http://localhost:8080
echo.
echo --------------------------------------------------------
echo.

REM Ask about dashboard shortcut
set /p "CREATE_DASH=Create a separate 'Open Dashboard' shortcut? (y/n): "
if /i "%CREATE_DASH%"=="y" (
    powershell -ExecutionPolicy Bypass -Command ^
        "$ws = New-Object -ComObject WScript.Shell; ^
        $s = $ws.CreateShortcut('%DESKTOP%\Grid Bot Dashboard.lnk'); ^
        $s.TargetPath = 'http://localhost:8080'; ^
        $s.Description = 'Open Grid Trading Bot Dashboard'; ^
        $s.IconLocation = '%%ProgramFiles%%\Internet Explorer\iexplore.exe,0'; ^
        $s.Save()"
    echo [OK] Created "Grid Bot Dashboard" shortcut on Desktop
)

echo.
echo To uninstall, simply delete the shortcuts from your Desktop
echo and Start Menu.
echo.
pause

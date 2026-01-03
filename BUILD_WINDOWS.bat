@echo off
:: GridBot Chuck - Windows Build Script
:: Creates a portable distribution package

setlocal enabledelayedexpansion

echo.
echo =====================================================
echo     GridBot Chuck - Windows Build Script
echo =====================================================
echo.

:: Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

:: Get version from argument or use default
set VERSION=%1
if "%VERSION%"=="" set VERSION=1.0.0

set BUILD_DIR=build\GridBotChuck-%VERSION%
set DIST_DIR=dist

echo Building version: %VERSION%
echo.

:: Clean previous build
echo [1/5] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
mkdir %BUILD_DIR%
mkdir %DIST_DIR%

:: Create directory structure
echo [2/5] Creating directory structure...
mkdir %BUILD_DIR%\config
mkdir %BUILD_DIR%\core
mkdir %BUILD_DIR%\strategies
mkdir %BUILD_DIR%\utils
mkdir %BUILD_DIR%\optimization
mkdir %BUILD_DIR%\logs
mkdir %BUILD_DIR%\data

:: Copy source files
echo [3/5] Copying source files...
xcopy /E /Y core %BUILD_DIR%\core\
xcopy /E /Y strategies %BUILD_DIR%\strategies\
xcopy /E /Y utils %BUILD_DIR%\utils\
xcopy /E /Y optimization %BUILD_DIR%\optimization\
xcopy /E /Y config\*.json %BUILD_DIR%\config\ 2>nul
xcopy /E /Y config\*.example.json %BUILD_DIR%\config\ 2>nul

:: Copy main files
copy main.py %BUILD_DIR%\
copy dashboard_launcher.py %BUILD_DIR%\
copy dashboard_launcher.bat %BUILD_DIR%\
copy dashboard_launcher.ps1 %BUILD_DIR%\
copy adaptive_scanner.py %BUILD_DIR%\
copy signal_logger.py %BUILD_DIR%\
copy requirements.txt %BUILD_DIR%\
copy README.md %BUILD_DIR%\
copy LICENSE.txt %BUILD_DIR%\ 2>nul
copy QUICK_REFERENCE.md %BUILD_DIR%\ 2>nul

:: Create launcher scripts
echo [4/5] Creating launcher scripts...

:: Create START.bat
(
echo @echo off
echo echo =====================================
echo echo   GridBot Chuck - Trading Bot
echo echo =====================================
echo echo.
echo.
echo REM Check for Python
echo python --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo ERROR: Python not found!
echo     echo Please install Python 3.11+ from python.org
echo     pause
echo     exit /b 1
echo ^)
echo.
echo REM Check for venv
echo if not exist ".venv" ^(
echo     echo Creating virtual environment...
echo     python -m venv .venv
echo     call .venv\Scripts\activate.bat
echo     pip install -r requirements.txt
echo ^) else ^(
echo     call .venv\Scripts\activate.bat
echo ^)
echo.
echo echo Starting dashboard...
echo python dashboard_launcher.py
echo pause
) > %BUILD_DIR%\START.bat

:: Create INSTALL.bat
(
echo @echo off
echo echo =====================================
echo echo   GridBot Chuck - Installation
echo echo =====================================
echo echo.
echo.
echo REM Check for Python
echo python --version ^>nul 2^>^&1
echo if errorlevel 1 ^(
echo     echo ERROR: Python not found!
echo     echo.
echo     echo Please install Python 3.11 or higher from:
echo     echo   https://www.python.org/downloads/
echo     echo.
echo     echo Make sure to check "Add Python to PATH" during installation!
echo     pause
echo     exit /b 1
echo ^)
echo.
echo echo Python found. Creating virtual environment...
echo python -m venv .venv
echo.
echo echo Activating environment...
echo call .venv\Scripts\activate.bat
echo.
echo echo Installing dependencies...
echo pip install -r requirements.txt
echo.
echo echo.
echo echo =====================================
echo echo   Installation Complete!
echo echo =====================================
echo echo.
echo echo Next steps:
echo echo 1. Copy .env.example to .env
echo echo 2. Add your exchange API keys to .env
echo echo 3. Run START.bat to launch the dashboard
echo echo.
echo pause
) > %BUILD_DIR%\INSTALL.bat

:: Create SCANNER.bat
(
echo @echo off
echo call .venv\Scripts\activate.bat 2^>nul ^|^| ^(echo Run INSTALL.bat first ^& pause ^& exit /b 1^)
echo python adaptive_scanner.py
echo pause
) > %BUILD_DIR%\SCANNER.bat

:: Create .env.example
(
echo # Exchange API Keys
echo # Get your API keys from your exchange ^(Kraken, Coinbase, Binance, etc.^)
echo.
echo EXCHANGE_API_KEY=your_api_key_here
echo EXCHANGE_SECRET_KEY=your_secret_key_here
echo.
echo # Optional: Exchange-specific keys ^(override EXCHANGE_* keys^)
echo # KRAKEN_API_KEY=your_kraken_api_key
echo # KRAKEN_SECRET_KEY=your_kraken_secret_key
echo # COINBASE_API_KEY=your_coinbase_api_key
echo # COINBASE_SECRET_KEY=your_coinbase_secret_key
) > %BUILD_DIR%\.env.example

:: Remove __pycache__
for /d /r %BUILD_DIR% %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q %BUILD_DIR%\*.pyc 2>nul

:: Create zip file
echo [5/5] Creating distribution package...
cd build
powershell -Command "Compress-Archive -Path 'GridBotChuck-%VERSION%' -DestinationPath '..\dist\GridBotChuck-%VERSION%-windows.zip' -Force"
cd ..

echo.
echo =====================================================
echo   BUILD COMPLETE!
echo =====================================================
echo.
echo Output: dist\GridBotChuck-%VERSION%-windows.zip
echo.
echo To test locally, run:
echo   cd build\GridBotChuck-%VERSION%
echo   INSTALL.bat
echo   START.bat
echo.
pause

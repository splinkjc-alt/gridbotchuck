# Grid Trading Bot - Desktop Shortcut Installer
# Run this script to create a desktop icon for Grid Trading Bot

param(
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"

# Get paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$StartMenuPath = [Environment]::GetFolderPath("StartMenu")
$ShortcutName = "Grid Trading Bot"
$ShortcutPath = Join-Path $DesktopPath "$ShortcutName.lnk"
$StartMenuShortcut = Join-Path $StartMenuPath "Programs\$ShortcutName.lnk"

# Uninstall mode
if ($Uninstall) {
    Write-Host "Removing Grid Trading Bot shortcuts..." -ForegroundColor Yellow
    
    if (Test-Path $ShortcutPath) {
        Remove-Item $ShortcutPath -Force
        Write-Host "  Removed desktop shortcut" -ForegroundColor Green
    }
    
    if (Test-Path $StartMenuShortcut) {
        Remove-Item $StartMenuShortcut -Force
        Write-Host "  Removed Start Menu shortcut" -ForegroundColor Green
    }
    
    Write-Host "`nShortcuts removed successfully!" -ForegroundColor Green
    exit 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Grid Trading Bot - Desktop Installer  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if we're in the right directory
$MainPy = Join-Path $ScriptDir "main.py"
if (-not (Test-Path $MainPy)) {
    Write-Host "ERROR: main.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from the grid_trading_bot folder." -ForegroundColor Yellow
    exit 1
}

# Check for Python
$PythonPath = $null
$VenvPython = Join-Path $ScriptDir ".venv\Scripts\python.exe"

if (Test-Path $VenvPython) {
    $PythonPath = $VenvPython
    Write-Host "Found virtual environment Python" -ForegroundColor Green
} else {
    # Try to find system Python
    $SystemPython = Get-Command python -ErrorAction SilentlyContinue
    if ($SystemPython) {
        $PythonPath = $SystemPython.Source
        Write-Host "Using system Python: $PythonPath" -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: Python not found!" -ForegroundColor Red
        Write-Host "Please install Python 3.10+ and try again." -ForegroundColor Yellow
        exit 1
    }
}

# Create the launcher batch file
$LauncherBat = Join-Path $ScriptDir "GridBot.bat"
$LauncherContent = @"
@echo off
title Grid Trading Bot
cd /d "$ScriptDir"

echo.
echo ========================================
echo   Grid Trading Bot - Starting...
echo ========================================
echo.

REM Activate virtual environment if exists
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Check if config exists
if not exist "config\config.json" (
    echo ERROR: config\config.json not found!
    echo Please copy config\config.example.json to config\config.json
    echo and add your API keys.
    pause
    exit /b 1
)

REM Start the bot
echo Starting Grid Trading Bot...
echo Dashboard will be available at: http://localhost:8080
echo.
echo Press Ctrl+C to stop the bot
echo.

python main.py --config config/config.json

if errorlevel 1 (
    echo.
    echo Bot exited with an error. Check the logs folder for details.
    pause
)
"@

Set-Content -Path $LauncherBat -Value $LauncherContent -Encoding ASCII
Write-Host "Created launcher: GridBot.bat" -ForegroundColor Green

# Create Windows shortcut
$WshShell = New-Object -ComObject WScript.Shell

# Desktop shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $LauncherBat
$Shortcut.WorkingDirectory = $ScriptDir
$Shortcut.Description = "Start Grid Trading Bot with Dashboard"
$Shortcut.WindowStyle = 1  # Normal window

# Try to set icon (use cmd.exe icon as fallback)
$IconPath = Join-Path $ScriptDir "Logo\gridbot.ico"
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
} else {
    # Use a generic icon
    $Shortcut.IconLocation = "%SystemRoot%\System32\cmd.exe,0"
}

$Shortcut.Save()
Write-Host "Created desktop shortcut: $ShortcutName" -ForegroundColor Green

# Start Menu shortcut
try {
    $StartShortcut = $WshShell.CreateShortcut($StartMenuShortcut)
    $StartShortcut.TargetPath = $LauncherBat
    $StartShortcut.WorkingDirectory = $ScriptDir
    $StartShortcut.Description = "Start Grid Trading Bot with Dashboard"
    $StartShortcut.WindowStyle = 1
    if (Test-Path $IconPath) {
        $StartShortcut.IconLocation = $IconPath
    } else {
        $StartShortcut.IconLocation = "%SystemRoot%\System32\cmd.exe,0"
    }
    $StartShortcut.Save()
    Write-Host "Created Start Menu shortcut" -ForegroundColor Green
} catch {
    Write-Host "Note: Could not create Start Menu shortcut (optional)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation Complete!                " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now:" -ForegroundColor Cyan
Write-Host "  1. Double-click 'Grid Trading Bot' on your Desktop" -ForegroundColor White
Write-Host "  2. Or run GridBot.bat from this folder" -ForegroundColor White
Write-Host ""
Write-Host "The dashboard will be at: http://localhost:8080" -ForegroundColor Yellow
Write-Host ""
Write-Host "To uninstall shortcuts, run:" -ForegroundColor Gray
Write-Host "  .\install_desktop_shortcut.ps1 -Uninstall" -ForegroundColor Gray
Write-Host ""

# Offer to open the dashboard URL in browser when bot starts
$CreateBrowserShortcut = Read-Host "Create a separate 'Open Dashboard' shortcut? (y/n)"
if ($CreateBrowserShortcut -eq 'y') {
    $DashboardShortcut = Join-Path $DesktopPath "Grid Bot Dashboard.lnk"
    $DashShortcut = $WshShell.CreateShortcut($DashboardShortcut)
    $DashShortcut.TargetPath = "http://localhost:8080"
    $DashShortcut.Description = "Open Grid Trading Bot Dashboard in Browser"
    $DashShortcut.IconLocation = "%ProgramFiles%\Internet Explorer\iexplore.exe,0"
    $DashShortcut.Save()
    Write-Host "Created 'Grid Bot Dashboard' shortcut on Desktop" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

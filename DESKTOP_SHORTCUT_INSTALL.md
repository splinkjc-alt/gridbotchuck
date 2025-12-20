# Desktop Shortcut Setup

## Quick Install

**Double-click `INSTALL_SHORTCUT.bat`** to create a desktop icon for Grid Trading Bot.

This will:
1. Create a "Grid Trading Bot" shortcut on your Desktop
2. Create a Start Menu entry
3. Optionally create a "Grid Bot Dashboard" shortcut to open the web interface

## Manual Setup

If the automatic installer doesn't work, you can manually create a shortcut:

1. Right-click on `GridBot.bat`
2. Select "Create shortcut"
3. Drag the shortcut to your Desktop
4. Rename it to "Grid Trading Bot"

## What the Shortcut Does

When you double-click the shortcut:
1. Opens a terminal window
2. Activates the Python virtual environment
3. Checks for config.json
4. Kills any existing process on port 8080
5. Starts the trading bot
6. Dashboard becomes available at http://localhost:8080

## Stopping the Bot

- Press `Ctrl+C` in the terminal window
- Or close the terminal window (may leave orphan processes)

## Troubleshooting

### "config.json not found"
Copy `config/config.example.json` to `config/config.json` and add your API keys.

### "Python not found"
Make sure Python 3.10+ is installed and in your PATH.

### "Port 8080 already in use"
The launcher automatically kills existing processes on port 8080.

## Uninstall Shortcuts

Run in PowerShell:
```powershell
.\install_desktop_shortcut.ps1 -Uninstall
```

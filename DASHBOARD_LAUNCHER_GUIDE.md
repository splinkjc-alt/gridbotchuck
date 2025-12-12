# Dashboard Launcher - Quick Start

## 🚀 Easy Ways to Open Your Dashboard

### Option 1: Batch File (Easiest for Windows)

**One-Click Launch:**
1. Double-click `dashboard_launcher.bat`
2. Dashboard opens automatically in your browser
3. Keep window open (you can minimize it)

**What it does:**
- Checks if bot API is running
- Waits for server to start
- Opens dashboard in default browser
- Shows status messages

---

### Option 2: Python Launcher (Cross-Platform)

**For Windows/Mac/Linux:**
```bash
python dashboard_launcher.py
```

**With system tray icon:**
```bash
# Install requirements first
pip install pystray pillow requests

# Run with tray
python dashboard_launcher.py
```

**With custom port:**
```bash
python dashboard_launcher.py --port 9090
```

**Without system tray:**
```bash
python dashboard_launcher.py --no-tray
```

---

### Option 3: Create Windows Shortcut

**Manual Setup:**
1. Right-click desktop → New → Shortcut
2. Location: `C:\Users\YourName\...grid_trading_bot-master\dashboard_launcher.bat`
3. Name: "Grid Trading Bot Dashboard"
4. Click Finish
5. Right-click shortcut → Properties → Advanced → Check "Run as administrator"

**Or use PowerShell to create:**
```powershell
$TargetPath = "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master\dashboard_launcher.bat"
$ShortcutPath = "$env:USERPROFILE\Desktop\Grid Trading Bot.lnk"
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $TargetPath
$Shortcut.WorkingDirectory = Split-Path $TargetPath
$Shortcut.Save()
```

---

### Option 4: Browser Bookmark

**Quick Access:**
1. Open dashboard: `http://localhost:8080`
2. Press `Ctrl+D` (or Cmd+D on Mac)
3. Name it "Trading Bot Dashboard"
4. Save to bookmarks

---

## Features

### Python Launcher (`dashboard_launcher.py`)
✅ Automatically waits for bot to start
✅ Opens dashboard in default browser
✅ Optional system tray icon
✅ Custom port support
✅ Status checking
✅ Cross-platform compatible

### Batch Launcher (`dashboard_launcher.bat`)
✅ Simple one-click launching
✅ Windows native
✅ Auto-installs requirements
✅ Shows status messages
✅ Error handling

---

## Usage Workflow

### Normal Startup:
```
1. Start bot: python main.py --config config/config.json
2. Double-click: dashboard_launcher.bat
3. Dashboard opens automatically
4. Use web interface to control bot
```

### With System Tray:
```
1. Start bot: python main.py --config config/config.json
2. Run: python dashboard_launcher.py
3. Minimize the window
4. Icon appears in system tray
5. Right-click tray icon to open dashboard anytime
```

---

## Troubleshooting

### Dashboard won't open
- Make sure bot is running
- Check console for "Bot API Server started" message
- Try accessing manually: `http://localhost:8080`

### Requirements missing
- Batch file will auto-install requests
- For Python: `pip install requests`
- For tray: `pip install pystray pillow`

### Wrong port
- If using custom port, update launcher:
  ```bash
  python dashboard_launcher.py --port 9090
  ```

### Running as administrator
- Right-click launcher → Run as administrator
- Needed for some system tray features

---

## Creating a Desktop Icon (Windows)

### Method 1: Right-Click Shortcut
1. Right-click desktop
2. New → Shortcut
3. Enter: `C:\Users\YourName\...grid_trading_bot-master\dashboard_launcher.bat`
4. Name: Grid Trading Bot
5. Finish

### Method 2: Pin to Taskbar
1. Open File Explorer
2. Navigate to: `grid_trading_bot-master`
3. Right-click `dashboard_launcher.bat`
4. Pin to Quick Access / Taskbar

### Method 3: Start Menu
1. Copy `dashboard_launcher.bat` to:
   ```
   C:\Users\YourName\AppData\Roaming\Microsoft\Windows\Start Menu\Programs
   ```
2. Search "Grid Trading Bot" in Start Menu
3. Right-click → Pin to Start

---

## Advanced Usage

### Auto-Launch on Bot Startup

**Modify main.py to auto-open:**
```python
# At end of run_bot function
import webbrowser
webbrowser.open('http://localhost:8080')
```

### Create Startup Script

**bot_startup.bat:**
```batch
@echo off
cd /d "%~dp0"
start python main.py --config config/config.json
timeout /t 3
start python dashboard_launcher.py --no-tray
```

Then double-click `bot_startup.bat` to start everything at once!

---

## Mobile Access from Launcher

**On same network:**
1. Find your IP: `ipconfig` (Windows)
2. Share link: `http://192.168.1.100:8080`
3. Open on phone browser

---

## System Requirements

### Python Launcher
- Python 3.8+
- requests module: `pip install requests`
- Optional: `pip install pystray pillow` for tray icon

### Batch Launcher
- Windows OS
- Python in PATH
- requests module (auto-installed)

---

## Features by Launcher Type

| Feature | Batch | Python | Python + Tray |
|---------|-------|--------|---------------|
| One-click launch | ✅ | ✅ | ✅ |
| Auto-wait for API | ✅ | ✅ | ✅ |
| System tray | ❌ | ❌ | ✅ |
| Custom port | ❌ | ✅ | ✅ |
| Status checking | ✅ | ✅ | ✅ |
| Cross-platform | ❌ | ✅ | ✅ |

---

## Support

**If launcher doesn't work:**
1. Make sure bot is running
2. Check console for errors
3. Verify `http://localhost:8080` loads manually
4. Try different launcher option
5. Check firewall settings

---

**Choose your preferred launcher and start using the dashboard!** 🚀

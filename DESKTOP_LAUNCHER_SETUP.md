# 🚀 Complete Desktop Launcher Setup Guide

## Your Grid Trading Bot Now Has 4 Ways to Open the Dashboard!

---

## 📋 Quick Reference

| Launcher Type | File | Command | Best For |
|---|---|---|---|
| **Batch (Simplest)** | `dashboard_launcher.bat` | Double-click | Windows users |
| **Python (Flexible)** | `dashboard_launcher.py` | `python dashboard_launcher.py` | Advanced users |
| **PowerShell** | `dashboard_launcher.ps1` | `. .\dashboard_launcher.ps1` | Modern Windows |
| **Desktop Shortcut** | Create manually | One-click | Maximum convenience |

---

## 🎯 Choose Your Launcher

### 1️⃣ Batch Launcher (RECOMMENDED)
**File:** `dashboard_launcher.bat`

**Why use it:**
- ✅ Simplest - just double-click
- ✅ Auto-installs missing packages
- ✅ No command line needed
- ✅ Windows native

**How to use:**
1. Double-click `dashboard_launcher.bat`
2. Wait for "✓ Bot API server is running!"
3. Dashboard opens automatically
4. Close window when done (optional)

**What happens:**
```
Step 1: Checks if bot is running
Step 2: Waits up to 30 seconds for API to start
Step 3: Opens dashboard in your default browser
Step 4: Shows success message
```

---

### 2️⃣ Python Launcher (MOST FLEXIBLE)
**File:** `dashboard_launcher.py`

**Why use it:**
- ✅ Works on Windows/Mac/Linux
- ✅ Custom port support
- ✅ Optional system tray icon
- ✅ Programmatic control

**Basic usage:**
```bash
python dashboard_launcher.py
```

**Advanced usage:**
```bash
# No system tray
python dashboard_launcher.py --no-tray

# Custom port
python dashboard_launcher.py --port 9090

# Longer timeout (60 seconds)
python dashboard_launcher.py --timeout 60

# Non-localhost
python dashboard_launcher.py --host 192.168.1.100
```

**With system tray icon:**
```bash
# Install dependencies first
pip install pystray pillow requests

# Run with tray
python dashboard_launcher.py
# Icon appears in bottom-right taskbar
```

---

### 3️⃣ PowerShell Launcher (MODERN WINDOWS)
**File:** `dashboard_launcher.ps1`

**Why use it:**
- ✅ Modern Windows approach
- ✅ Colorful output
- ✅ Better integration with Windows terminal
- ✅ Advanced scripting

**How to use:**
```powershell
# Run from PowerShell
.\dashboard_launcher.ps1

# With custom parameters
.\dashboard_launcher.ps1 -Port 9090 -Timeout 60
```

**Parameters:**
```powershell
-Port 8080           # API server port (default: 8080)
-Host localhost      # API server host (default: localhost)
-Timeout 30          # Wait timeout in seconds (default: 30)
```

---

### 4️⃣ Desktop Shortcut (ONE-CLICK)
**Create a shortcut to any launcher**

**Option A: Shortcut to Batch File**
1. Right-click desktop
2. New → Shortcut
3. Target: `C:\Users\YourName\...\grid_trading_bot-master\dashboard_launcher.bat`
4. Name: "Grid Trading Bot Dashboard"
5. Click Finish
6. (Optional) Right-click shortcut → Properties → Change Icon

**Option B: Shortcut to PowerShell**
1. Right-click desktop
2. New → Shortcut
3. Target: `pwsh.exe -ExecutionPolicy Bypass -File "C:\Users\YourName\...\dashboard_launcher.ps1"`
4. Name: "Grid Trading Bot"
5. Click Finish

**Option C: Shortcut to Python**
1. Right-click desktop
2. New → Shortcut
3. Target: `python C:\Users\YourName\...\dashboard_launcher.py --no-tray`
4. Name: "Grid Trading Bot"
5. Click Finish

---

## 📱 Multi-Device Access

### Same Network (Phone/Tablet)
**Access from any device on your network:**

1. Find your computer's IP address:
   ```powershell
   ipconfig
   # Look for "IPv4 Address: 192.168.x.x"
   ```

2. On phone/tablet, open browser:
   ```
   http://192.168.1.100:8080
   ```
   (Replace with your actual IP)

3. Dashboard loads and auto-refreshes
   - Works on mobile browsers
   - Touch-friendly interface
   - Real-time bot status
   - Control bot from anywhere in house

### Internet Access (Advanced)
**Access from outside your network:**

Use ngrok for secure tunneling:
```bash
pip install ngrok

# Then run ngrok
ngrok http 8080

# Share the URL: https://xxxx-xxxx-xxxx.ngrok.io
```

---

## 🔧 Setup Instructions

### Prerequisites
- ✅ Python 3.8+
- ✅ Bot in working condition
- ✅ Port 8080 available

### Step 1: Install Dependencies
```bash
pip install requests
```

### Step 2: (Optional) Install Tray Support
```bash
pip install pystray pillow
```

### Step 3: Start Your Bot
```bash
python main.py --config config/config.json
```

### Step 4: Launch Dashboard
Choose ONE:
```bash
# Option A: Double-click batch file
dashboard_launcher.bat

# Option B: Python
python dashboard_launcher.py

# Option C: PowerShell

```

### Step 5: Dashboard Opens Automatically! 🎉

---

## 🏗️ How It Works

### Architecture
```
┌──────────────────────────────────────────────────┐
│  Your Computer                                   │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │  Grid Trading Bot (main.py)             │   │
│  │  - Trading logic                        │   │
│  │  - Event bus                            │   │
│  │  - Order management                     │   │
│  └──────────────┬──────────────────────────┘   │
│                 │                               │
│         ┌───────▼────────┐                     │
│         │ API Server     │                     │
│         │ :8080          │                     │
│         └───────┬────────┘                     │
│                 │                               │
│  ┌──────────────▼──────────────────────────┐  │
│  │  Web Dashboard                           │  │
│  │  - Status monitoring                     │  │
│  │  - Bot control (start/stop/pause)       │  │
│  │  - Metrics display                      │  │
│  │  - Order history                        │  │
│  └──────────────┬──────────────────────────┘  │
│                 │                               │
│                 │ HTTP                         │
│                 │ localhost:8080               │
│                 │                               │
│  ┌──────────────▼──────────────────────────┐  │
│  │  Your Browser                            │  │
│  │  - Chrome / Firefox / Edge               │  │
│  │  - Auto-refreshes status                │  │
│  │  - Responsive design                    │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  📱 Phone/Tablet (same network)                 │
│  - Connect to: http://192.168.x.x:8080         │
│  - Monitor bot remotely                        │
└──────────────────────────────────────────────────┘
```

### Startup Sequence
```
1. User runs launcher
         ↓
2. Launcher checks if API is responding
   GET http://localhost:8080/api/bot/status
         ↓
3. If not responding, wait up to 30 seconds
   (Retry every 1 second)
         ↓
4. Once API responds (HTTP 200)
         ↓
5. Browser opens with:
   http://localhost:8080
         ↓
6. Dashboard loads and connects
         ↓
7. Real-time monitoring begins
   (Updates every 2 seconds)
```

---

## 🐛 Troubleshooting

### Issue: "Bot API server not found"

**Solution 1: Start the bot first**
```bash
python main.py --config config/config.json
```

**Solution 2: Check if API is running**
```bash
# Windows PowerShell
curl http://localhost:8080/api/bot/status

# Or use browser
# Visit: http://localhost:8080
```

**Solution 3: Check for firewall**
- Windows Defender Firewall might block port 8080
- Check: Settings → Privacy & Security → Windows Defender Firewall
- Allow Python to access network

---

### Issue: "Could not open browser"

**Solution 1: Manual access**
- Open Chrome/Firefox/Edge
- Type: `http://localhost:8080`
- Press Enter

**Solution 2: Check browser isn't blocked**
- Some antivirus software blocks browser launches
- Try different browser

**Solution 3: Use no-tray mode**
```bash
python dashboard_launcher.py --no-tray
```

---

### Issue: "Python not found"

**Solution 1: Add Python to PATH**
- Windows: Settings → System → Environment Variables
- Add Python installation folder to PATH
- Restart terminal

**Solution 2: Use full path**
```bash
C:\Python\python.exe dashboard_launcher.py
```

**Solution 3: Use batch file instead**
```bash
dashboard_launcher.bat
```
(Batch file includes Python validation)

---

### Issue: "Module not found: requests"

**Solution:**
```bash
pip install requests
```

Or let batch file auto-install it.

---

### Issue: System tray icon not working

**Solution:**
```bash
# Install required packages
pip install pystray pillow

# Then run
python dashboard_launcher.py
```

Or use without tray:
```bash
python dashboard_launcher.py --no-tray
```

---

## 📊 Dashboard Features

Once dashboard opens, you get:

### Control Section
- ✅ Start Bot button
- ✅ Stop Bot button
- ✅ Pause Bot button
- ✅ Resume Bot button

### Status Section
- ✅ Bot status (running/stopped/paused)
- ✅ Current balance
- ✅ Available balance
- ✅ Grid levels active

### Metrics Section
- ✅ Total trades executed
- ✅ Win rate percentage
- ✅ Total fees paid
- ✅ Total profit/loss
- ✅ Average trade duration

### Orders Section
- ✅ Recent order history
- ✅ Order status
- ✅ Buy/sell prices
- ✅ Quantity and fees

### Configuration Section
- ✅ Current settings
- ✅ Grid configuration
- ✅ Risk parameters

### Logs Section
- ✅ Real-time activity log
- ✅ Connection status
- ✅ Error messages

---

## 🎓 Advanced Features

### Custom Port
If port 8080 is already in use:

**Python:**
```bash
python dashboard_launcher.py --port 9090
```

**Batch:** Edit `dashboard_launcher.bat`
Find line with `python dashboard_launcher.py`
Change to:
```batch
python dashboard_launcher.py --port 9090
```

**PowerShell:**
```powershell
.\dashboard_launcher.ps1 -Port 9090
```

---

### Custom Host
Access from different machine:

**Python:**
```bash
python dashboard_launcher.py --host 192.168.1.100
```

**PowerShell:**
```powershell
.\dashboard_launcher.ps1 -Host 192.168.1.100
```

---

### Extended Timeout
If bot takes longer to start:

**Python:**
```bash
python dashboard_launcher.py --timeout 60
```

**PowerShell:**
```powershell
.\dashboard_launcher.ps1 -Timeout 60
```

---

## 📦 File Locations

```
grid_trading_bot-master/
├── dashboard_launcher.bat      ← Windows batch launcher
├── dashboard_launcher.py       ← Python launcher
├── dashboard_launcher.ps1      ← PowerShell launcher
├── DESKTOP_LAUNCHER_SETUP.md   ← This file
├── DESKTOP_LAUNCHER_SUMMARY.md ← Summary doc
├── DASHBOARD_LAUNCHER_GUIDE.md ← Full guide
├── main.py                     ← Bot entry point
├── config/
│   └── config.json             ← Bot configuration
└── web/
    └── dashboard/
        ├── index.html          ← Dashboard UI
        ├── styles.css          ← Styling
        └── script.js           ← API communication
```

---

## ✅ Checklist

Before using launcher:
- [ ] Python 3.8+ installed: `python --version`
- [ ] requests module: `pip install requests`
- [ ] Bot files in place
- [ ] Port 8080 available
- [ ] No firewall blocking
- [ ] main.py has API integration

Running launcher:
- [ ] Start bot first: `python main.py backtest --config config/config.json`
- [ ] Wait 3-5 seconds for bot to initialize
- [ ] Run launcher (double-click or command)
- [ ] Watch for "✓ Bot API server is running!"
- [ ] Dashboard opens automatically

Using dashboard:
- [ ] Dashboard loads without errors
- [ ] Status updates every 2 seconds
- [ ] Connection indicator is green
- [ ] Control buttons respond

---

## 🎉 You're All Set!

Your grid trading bot is now:
- ✅ Fully automated
- ✅ Easy to control
- ✅ Accessible from desktop
- ✅ Accessible from mobile
- ✅ Professional looking
- ✅ Real-time monitoring

### Next Steps:
1. Start your bot
2. Double-click the launcher
3. Watch it trade!
4. Monitor from phone if needed
5. Control from anywhere on network

---

**Happy trading! 🚀📈**

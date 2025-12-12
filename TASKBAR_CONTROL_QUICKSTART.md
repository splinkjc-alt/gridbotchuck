# ⚡ Quick Start: Taskbar Bot Control

## 30-Second Setup

### Step 1: Install Packages (Once Only)
```bash
pip install pystray pillow requests
```

### Step 2: Start Bot in Terminal 1
```bash
python main.py --config config/config.json
```
✅ Wait for: "Bot API Server started on http://localhost:8080"

### Step 3: Launch Taskbar Control in Terminal 2
```bash
python bot_taskbar_control.py
```
✅ Icon appears in taskbar!

### Step 4: Right-Click Icon
Choose:
- **Start** - Begin trading
- **Stop** - Stop trading
- **Pause** - Pause trading
- **Resume** - Continue trading
- **Dashboard** - Open full interface
- **Quit** - Close taskbar control

---

## Three Ways to Launch

| Method | Command |
|--------|---------|
| **Easiest** | `double-click bot_taskbar_control.bat` |
| **Python** | `python bot_taskbar_control.py` |
| **PowerShell** | `.\bot_taskbar_control.ps1` |

---

## Icon Colors

- 🟢 **Green** = Running
- 🔴 **Red** = Stopped
- 🟠 **Orange** = Paused

---

## Full Documentation

See **TASKBAR_CONTROL_GUIDE.md** for complete details.

---

**Done!** You now have a taskbar icon to control your bot! 🎮

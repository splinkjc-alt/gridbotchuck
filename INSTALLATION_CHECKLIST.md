# ✅ Bot Control System - Installation Checklist

Complete this checklist to ensure proper setup.

## 📋 Pre-Installation

- [ ] Python 3.8+ installed
- [ ] pip package manager available
- [ ] Grid trading bot repository cloned/downloaded
- [ ] Terminal/PowerShell opened in bot directory

## 📦 Dependencies

- [ ] Run: `pip install aiohttp aiohttp-cors`
- [ ] Verify: `python -c "import aiohttp; print('✓ aiohttp installed')"`
- [ ] Verify: `python -c "import aiohttp_cors; print('✓ aiohttp_cors installed')"`

## 📁 File Structure

Verify these files exist:

### Backend Files
- [ ] `core/bot_management/bot_api_server.py` (≈15KB)
- [ ] `core/bot_management/bot_api_integration.py` (≈2KB)

### Frontend Files
- [ ] `web/dashboard/index.html` (≈8KB)
- [ ] `web/dashboard/styles.css` (≈12KB)
- [ ] `web/dashboard/script.js` (≈8KB)

### Documentation Files
- [ ] `DASHBOARD_QUICKSTART.md`
- [ ] `WEB_DASHBOARD_GUIDE.md`
- [ ] `BOT_CONTROL_SYSTEM.md`
- [ ] `DASHBOARD_VISUAL_GUIDE.md`
- [ ] `API_INTEGRATION_EXAMPLE.py`
- [ ] `API_REQUIREMENTS.txt`
- [ ] `WEB_CONTROL_README.md`

## 🔧 Code Integration

### Step 1: Add Import
- [ ] Open `main.py`
- [ ] Find line: `from core.bot_management.health_check import HealthCheck`
- [ ] Add after it: `from core.bot_management.bot_api_integration import BotAPIIntegration`

### Step 2: Initialize API
- [ ] Find function: `async def run_bot(`
- [ ] Find line: `health_check = HealthCheck(bot, notification_handler, event_bus)`
- [ ] Add after it:
```python
api_integration = BotAPIIntegration(bot, event_bus, config_manager, port=8080)
await api_integration.start()
```

### Step 3: Cleanup
- [ ] Find the `finally:` block
- [ ] Find line: `await event_bus.shutdown()`
- [ ] Add before it: `await api_integration.stop()`

### Step 4: Verify Code
- [ ] Run: `python -m py_compile main.py`
- [ ] Should complete without errors

## 🚀 First Run

### Start Bot
- [ ] Run: `python main.py backtest --config config/config.json`
- [ ] Look for: "Bot API Server started on http://0.0.0.0:8080"
- [ ] Confirm: No error messages in output

### Test Dashboard
- [ ] Open browser: `http://localhost:8080`
- [ ] Dashboard should load (no blank page)
- [ ] Connection indicator should be green
- [ ] Status should show "Connected" (top right)

### Test Controls
- [ ] Click "Start Bot" button
- [ ] Status should update to "Running"
- [ ] Click "Stop Bot" button
- [ ] Status should update to "Stopped"

## 📱 Mobile Access

### Get Your IP
- [ ] Windows: Run `ipconfig` in PowerShell
- [ ] Find line: "IPv4 Address" (e.g., 192.168.1.100)
- [ ] Write down your IP: `___________`

### Test Mobile
- [ ] Get on same WiFi as computer
- [ ] On phone, open: `http://<YOUR_IP>:8080`
- [ ] Dashboard should load on phone
- [ ] Buttons should work on phone
- [ ] Status should update in real-time

## 🧪 Functionality Tests

### API Endpoints
- [ ] Test in browser/curl: `http://localhost:8080/api/health`
  - Should return: `{"status": "ok", "timestamp": "..."}`

- [ ] Test: `http://localhost:8080/api/bot/status`
  - Should return: Bot status information

- [ ] Test: `http://localhost:8080/api/bot/metrics`
  - Should return: Trading metrics

### Dashboard Features
- [ ] Status section displays correctly
- [ ] Balance shows numbers (not errors)
- [ ] Grid info displays
- [ ] Metrics section shows data
- [ ] Orders table displays (or "No orders yet")
- [ ] Status log shows entries
- [ ] Configuration shows correct values
- [ ] All buttons are clickable

## 🔍 Troubleshooting Checks

If dashboard doesn't load:
- [ ] Check browser console (F12 → Console)
- [ ] Check for JavaScript errors
- [ ] Verify API server started (see terminal output)
- [ ] Try refreshing page (Ctrl+F5)

If phone can't connect:
- [ ] Verify same WiFi network
- [ ] Use IP address, not "localhost"
- [ ] Check Windows Firewall allows port 8080
- [ ] Try `ipconfig /all` to confirm IP

If buttons don't work:
- [ ] Check browser console for fetch errors
- [ ] Verify API server is running
- [ ] Check bot logs for error messages
- [ ] Restart bot and browser

## 📊 System Verification

Run these commands:

```bash
# Verify Python version
python --version
# Should be 3.8 or higher

# Verify dependencies
pip show aiohttp aiohttp-cors
# Should show version info for both

# Verify code syntax
python -m py_compile core/bot_management/bot_api_server.py
python -m py_compile core/bot_management/bot_api_integration.py
python -m py_compile main.py
# All should complete without errors

# Verify web files exist
ls web/dashboard/
# Should list: index.html, script.js, styles.css
```

- [ ] Python version correct
- [ ] Dependencies installed
- [ ] Code syntax valid
- [ ] Web files present

## 🎯 Performance Tests

- [ ] Dashboard loads in <2 seconds
- [ ] Status updates every 2-3 seconds
- [ ] Buttons respond within 1 second
- [ ] No lag on mobile browser
- [ ] Memory usage stable (check Task Manager)

## 🔐 Security Review

- [ ] Dashboard only accessed on local network
- [ ] Port 8080 restricted to local IP
- [ ] No sensitive data exposed in logs
- [ ] Bot token/credentials not in code

## 📚 Documentation Review

- [ ] Read `DASHBOARD_QUICKSTART.md`
- [ ] Understand `BOT_CONTROL_SYSTEM.md`
- [ ] Review `WEB_DASHBOARD_GUIDE.md` for features
- [ ] Keep documentation accessible for reference

## 🎉 Completion

All items checked?

**Congratulations!** Your bot control system is ready! 🚀

### Final Verification
- [ ] Bot starts and runs successfully
- [ ] Dashboard loads and displays data
- [ ] Controls work on desktop
- [ ] Controls work on phone
- [ ] Real-time updates working
- [ ] No errors in logs

### Next Steps
1. Configure your trading settings in `config/config.json`
2. Run backtests to verify strategy
3. Deploy to paper trading for live monitoring
4. Use dashboard to monitor performance
5. Adjust settings from web interface

---

## 📞 Troubleshooting Contact

If you encounter issues:
1. Check browser console (F12)
2. Review bot console output
3. Read relevant documentation
4. Verify all files are present
5. Restart bot and refresh dashboard

---

## 📝 Notes

Use this space to record any custom setup:

```
API Port: 8080
Computer IP: _______________
Phone Access URL: _______________
Custom Settings: _______________
Notes: _______________
```

---

**Setup Complete!** Now you have full web control of your trading bot! 📈

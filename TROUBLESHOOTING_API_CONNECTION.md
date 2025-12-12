# 🔧 Troubleshooting: "Can't Reach Page" Error

## Problem
You get "Can't reach page" or "This site can't be reached" when trying to access the dashboard.

---

## Quick Fixes (Try These First)

### ✅ Fix 1: Make Sure Bot is Still Running
The **most common cause** is the bot stopped or crashed.

**In Terminal 1, check if you see:**
```
Bot API Server started on http://localhost:8080
```

If you don't see this:
1. Close Terminal 1
2. Open a new terminal
3. Run: `python main.py --config config/config.json`
4. Wait 5-10 seconds
5. Try accessing again: `http://localhost:8080`

---

### ✅ Fix 2: Check Terminal 1 for Errors
Look at the bot console for any error messages like:
- `Port 8080 already in use`
- `Configuration error`
- `Module not found`

**If you see port 8080 in use:**
```bash
python bot_taskbar_control.py --port 9090
python dashboard_launcher.py --port 9090
```

---

### ✅ Fix 3: Wait Longer
The bot takes 5-10 seconds to fully start. Try:

1. After running `python main.py --config config/config.json`
2. **Wait 10 seconds** (count slowly!)
3. Then run the dashboard launcher
4. Or manually visit: `http://localhost:8080`

---

### ✅ Fix 4: Check Windows Firewall
Windows Firewall might be blocking port 8080.

**To fix:**
1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Find Python (or add it)
4. Make sure it's checked for "Private networks"
5. Restart the bot

---

## Detailed Troubleshooting

### Step 1: Manually Test the Connection

Open PowerShell and run:
```powershell
curl http://localhost:8080/api/bot/status
```

**Expected response:**
```json
{"status":"running","balance":1000.50,...}
```

**If you get error:**
- Bot is not running
- Bot crashed
- Port is blocked

---

### Step 2: Check if Port 8080 is in Use

```powershell
netstat -ano | findstr :8080
```

**If something appears:**
- Port is in use by another process
- Try different port: `python bot_taskbar_control.py --port 9090`

**If nothing appears:**
- Port is free, but bot not responding
- Bot may have crashed

---

### Step 3: Check Bot Console Output

Look at Terminal 1 where bot is running.

**Good output looks like:**
```
[INFO] Loading configuration...
[INFO] Initializing bot...
[INFO] Bot API Server started on http://localhost:8080
[INFO] Trading bot ready
```

**Bad output might show:**
```
[ERROR] Failed to load config file
[ERROR] Port 8080 already in use
[ERROR] Exception in main loop
```

---

## Common Errors & Fixes

### Error 1: "Port 8080 already in use"
**Solution:**
- Kill the old process: `taskkill /F /IM python.exe`
- Or use different port: `--port 9090`

### Error 2: "Configuration file not found"
**Solution:**
- Make sure `config/config.json` exists
- Use full path: `python main.py --config C:\...\config\config.json`

### Error 3: "ModuleNotFoundError"
**Solution:**
```bash
pip install -r requirements.txt
# or install missing modules individually
```

### Error 4: "Binding to port failed"
**Solution:**
- Restart your computer
- Use different port: `--port 9090`

### Error 5: Bot starts but no API
**Solution:**
- Check if API integration is enabled in main.py
- Verify `bot_api_integration.py` exists
- Check for syntax errors in bot code

---

## Complete Diagnostic Procedure

Run these steps in order:

### Step 1: Clean Start
```bash
# Close all terminals
# Kill any Python processes
taskkill /F /IM python.exe

# Wait 5 seconds
# Open new terminal
```

### Step 2: Start Bot with Verbose Output
```bash
python main.py --config config/config.json
```

Wait at least 10 seconds. You should see:
```
Bot API Server started on http://localhost:8080
```

### Step 3: Test Connection (New Terminal)
```powershell
curl http://localhost:8080
```

Should get HTML response (the dashboard).

### Step 4: If Still Failing
Check these:
```bash
# Is Python working?
python --version

# Is main.py present?
dir main.py

# Is config file present?
dir config\config.json

# Try running with full paths
python "C:\...\main.py" --config "C:\...\config\config.json"
```

---

## Firewall Fix (Detailed)

### For Windows Defender Firewall:

1. Open Windows Defender Firewall
   - Type "firewall" in Windows search
   - Click "Windows Defender Firewall"

2. Click "Allow an app through firewall"

3. Look for Python in the list
   - If present: Make sure both "Private" and "Public" are checked
   - If not present: Click "Allow another app" and find Python.exe

4. Click OK

5. Restart the bot:
   ```bash
   python main.py --config config/config.json
   ```

---

## Quick Recovery Checklist

- [ ] Bot is still running (Terminal 1 open)
- [ ] You see "Bot API Server started" message
- [ ] You waited at least 10 seconds after starting bot
- [ ] You're accessing `http://localhost:8080` (not `https`)
- [ ] No firewall pop-ups were dismissed
- [ ] Port 8080 is not in use by another app
- [ ] Python is in your PATH
- [ ] main.py file exists

---

## Still Not Working?

### Option 1: Try Different Port
```bash
# Terminal 1: Start bot on port 9090
python main.py --config config/config.json

# Terminal 2: Use dashboard launcher with port 9090
python dashboard_launcher.py --port 9090

# Or manually visit:
http://localhost:9090
```

### Option 2: Direct API Test
```bash
# Test the API directly
curl http://localhost:8080/api/bot/status -v

# This shows exactly what's happening
```

### Option 3: Restart Everything
```bash
# Kill all Python processes
taskkill /F /IM python.exe

# Restart your computer
# Start fresh
python main.py --config config/config.json
```

---

## What's Happening Behind the Scenes

```
1. Bot starts (main.py)
   ↓
2. Bot initializes trading engine
   ↓
3. Bot creates API server on port 8080
   ↓ (This takes 5-10 seconds)
4. API server is ready
   ↓
5. You can now connect to http://localhost:8080
```

If you get "can't reach page" it means one of these steps didn't complete.

---

## Prevention Tips

### Keep It Running
- Don't close Terminal 1 (the bot terminal)
- Minimize it instead of closing
- Keep it visible while trading

### Monitor the Bot
- Keep watching for error messages
- Use taskbar control to check status
- Check bot console regularly

### Restart Procedure
If bot crashes:
1. Close Terminal 1
2. Wait 5 seconds
3. Open new terminal
4. Run: `python main.py --config config/config.json`
5. Wait 10 seconds
6. Try dashboard again

---

## Summary

**Most likely cause:** Bot took too long to start or crashed

**Quick fix:** 
1. Look at Terminal 1 where bot runs
2. Make sure you see "Bot API Server started"
3. Wait 10 seconds
4. Try again

**If that doesn't work:**
- Check firewall
- Try different port (9090)
- Restart everything

---

## Next Steps

1. **Check Terminal 1** - What does it say?
2. **Wait 10 seconds** - Give bot time to start
3. **Try again** - Access `http://localhost:8080`
4. **If error persists** - Share the bot console output with me

I'm here to help! Just tell me what the bot console shows. 🚀

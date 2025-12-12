# Troubleshooting Fetch Errors

## Common Issues & Solutions

### 1. "Failed to fetch" Error

**Cause:** API server not running or not accessible

**Solution:**
```bash
# Make sure dependencies are installed
pip install aiohttp aiohttp-cors

# Check that main.py has API integration (you just did this)

# Run the bot
python main.py backtest --config config/config.json

# Look for this message in console:
# "Bot API Server started on http://0.0.0.0:8080"
```

**If API server doesn't start:**
- Check console for error messages
- Verify port 8080 isn't already in use
- Try a different port: Change `port=8080` to `port=9090` in main.py

---

### 2. CORS Errors (Cross-Origin Request Blocked)

**Cause:** Browser security blocking API requests

**Solution:**
Already fixed! The bot_api_server.py uses `aiohttp_cors` to handle this.

Make sure you have:
```bash
pip install aiohttp-cors
```

---

### 3. Network Connection Errors

**For Desktop:**
- Use: `http://localhost:8080`
- Check firewall allows port 8080

**For Phone on Same WiFi:**
- Find your IP: `ipconfig` (Windows)
- Use: `http://192.168.1.100:8080` (replace with your IP)
- Same network required
- Firewall must allow port 8080

---

### 4. API Endpoint Returns 404

**Cause:** API routes not properly registered

**Solution:**
- Restart bot
- Check console for "Bot API Server started" message
- Verify endpoint URL in script.js matches API

Test with:
```bash
curl http://localhost:8080/api/health
```

Should return:
```json
{"status": "ok", "timestamp": "..."}
```

---

### 5. Dashboard HTML Doesn't Load

**Cause:** Static file serving issue (just fixed)

**Solution:**
- Files now use absolute path to find dashboard folder
- Ensure files exist: `web/dashboard/index.html`
- Restart bot

---

## Testing the Connection

### Step 1: Check API is Running
Open browser console (F12) and run:
```javascript
fetch('/api/health').then(r => r.json()).then(console.log).catch(console.error)
```

Should show:
```
{status: 'ok', timestamp: '...'}
```

### Step 2: Check Bot Status
```javascript
fetch('/api/bot/status').then(r => r.json()).then(console.log).catch(console.error)
```

Should show bot status object with running, trading_mode, etc.

### Step 3: Check Configuration
```javascript
fetch('/api/config').then(r => r.json()).then(console.log).catch(console.error)
```

Should show grid configuration.

---

## Browser Console Debugging

1. Open browser: F12 (or right-click → Inspect)
2. Go to Console tab
3. Look for error messages
4. Check Network tab to see API requests
5. Red X = failed requests

---

## Bot Console Output

When you start the bot, watch for:

✅ **Good signs:**
```
Bot API Server started on http://0.0.0.0:8080
Access dashboard at: http://localhost:8080
```

❌ **Bad signs:**
```
[Error] Failed to start API server
[Error] Port already in use
[Error] Module not found
```

---

## Quick Fixes

| Problem | Fix |
|---------|-----|
| Port 8080 in use | Change to 9090: `port=9090` in main.py |
| Module not found | `pip install aiohttp aiohttp-cors` |
| Dashboard blank | Check F12 console for errors |
| API returns 404 | Restart bot, check routes |
| Phone can't connect | Use correct IP, same WiFi |

---

## If Still Having Issues

1. **Restart everything:**
   ```bash
   # Stop the bot (Ctrl+C)
   # Close browser tab
   # Delete any .pyc files
   # Restart bot
   # Open fresh browser tab
   ```

2. **Check logs:**
   - Bot console output
   - Browser console (F12)
   - Check for error messages

3. **Verify setup:**
   - `pip list | grep aiohttp`
   - `ls web/dashboard/`
   - `python -c "from core.bot_management.bot_api_integration import BotAPIIntegration; print('OK')"`

4. **Try different port:**
   - Change main.py: `BotAPIIntegration(..., port=9090)`
   - Access at: `http://localhost:9090`

---

## Success Indicators

When working correctly:

✅ Browser opens dashboard
✅ Status shows "Connected" (green dot)
✅ Status updates every 2 seconds
✅ Balance displays numbers
✅ Buttons are clickable
✅ Click Start → Status changes to "Running"
✅ No errors in browser console (F12)
✅ No errors in bot console

---

**Your fetch error should be fixed now!** Try refreshing the browser.

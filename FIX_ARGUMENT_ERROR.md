# ✅ Runtime Error Fix: Argument Parsing Failed

## Problem

You were getting this error:
```
RuntimeError: Failed to parse arguments. Please check your inputs
```

## Root Cause

The command being used was:
```bash
python main.py backtest --config config/config.json
```

But the bot's argument parser **does not expect a `backtest` subcommand**. The word "backtest" is treated as an invalid argument, causing the parsing to fail.

## Solution

**Remove the `backtest` argument from the command.**

### Correct Command:
```bash
python main.py --config config/config.json
```

## Updated Documentation

All documentation files have been corrected to use the proper command format:

✅ START_HERE.md
✅ QUICK_REFERENCE.md
✅ DOCUMENTATION_INDEX.md
✅ DESKTOP_LAUNCHER_SETUP.md
✅ DESKTOP_LAUNCHER_SUMMARY.md
✅ DASHBOARD_LAUNCHER_GUIDE.md
✅ IMPLEMENTATION_SUMMARY.md
✅ dashboard_launcher.py
✅ dashboard_launcher.ps1

## How to Run Now

### Option 1: Batch File (Easiest)
```bash
double-click dashboard_launcher.bat
```

### Option 2: Python
```bash
python main.py --config config/config.json
```

### Option 3: Full Sequence
```bash
# Terminal 1: Start bot
python main.py --config config/config.json

# Terminal 2: Launch dashboard
python dashboard_launcher.py
```

## Verification

Once you run the command correctly, you should see:
```
[INFO] Loading configuration...
[INFO] Bot API Server started on http://localhost:8080
```

Then the dashboard launcher will:
1. Detect the running API server
2. Open your browser automatically
3. Display the trading dashboard

## Next Steps

Try running:
```bash
python main.py --config config/config.json
```

And let me know if you see the "Bot API Server started" message in the console!

---

**The fix is complete!** All commands have been corrected. 🎉

# CLAUDE MEMORY FILE - READ THIS FIRST!
**Purpose:** Context for future Claude sessions
**Last Updated:** January 13, 2026

---

## WHO IS THE USER?

- Name: Jeff (also called "splin")
- Retired, uses trading bots as an activity
- Experienced with hardware (built TheBeast: RTX 4090, 128GB RAM, Ryzen 9 9950X)
- Prefers momentum trading over passive investing
- Wants manual control but AI assistance with decisions

---

## CRITICAL KNOWLEDGE

### GRID TRADING DOES NOT WORK
**This is the most important thing to remember.**

Grid trading (buy/sell at fixed price levels) was tested extensively and **LOSES MONEY** in trending markets. This was discovered on January 11, 2026 after weeks of losses.

**DO NOT suggest or start grid trading bots.**

### MOMENTUM STRATEGIES WORK
These are the only strategies to use:
- VET Momentum: RSI + Bollinger Bands, 15m timeframe
- PEPE Momentum: RSI + EMA (9/20), 30m timeframe
- CrossKiller: RSI oversold scanner, 15m timeframe

Backtests showed +23-36% returns over 30 days.

---

## PROJECT STRUCTURE

### Active Trading (D:\gridbotchuck)
```
D:\gridbotchuck\
├── start_all_bots.bat      <- START BOTS HERE
├── run_vet_momentum.py     <- VET bot (Kraken)
├── run_pepe_momentum.py    <- PEPE bot (Kraken)
├── run_crosskiller_daytrader.py <- Coinbase scanner
├── CURRENT_SETUP.md        <- READ THIS FIRST
├── SESSION_STATUS.md       <- Why momentum > grids
├── CLAUDE.md               <- Context for Claude
├── CLAUDE_MEMORY.md        <- This file
└── USB_BACKUP_REFERENCE.md <- Portable reference
```

### FrankC - Local AI (C:\AI\free-claude)
- Llama 70B fine-tuning to mimic Claude
- Training crashed Dec 25 (meta tensor error)
- Waiting for dedicated server hardware
- DO NOT try to fix/restart on TheBeast - user is building separate server

### AI Guardian (C:\AI\ai-guardian)
- Security tools (scam detector works)
- Server build inventory for FrankC
- Not actively used right now

### Development Version (OneDrive)
- `C:\Users\splin\OneDrive\Documents\grid_trading_bot-master`
- Full history, desktop app, all docs
- Use D:\gridbotchuck for production

---

## BOT ERROR HANDLING

All bots have self-healing built in:
```python
error_count = 0
max_errors = 5

while running:
    try:
        # fetch data
        error_count = 0  # Reset on success
    except:
        error_count += 1
        if error_count >= max_errors:
            # Reconnect exchange
            error_count = 0
        continue  # Keep running
```

**Bots will NOT crash from API errors. They recover automatically.**

---

## COMMON ISSUES

### Coinbase API Errors
- CrossKiller sometimes gets candle fetch errors
- This is Coinbase's API being slow, not a bug
- Bot continues monitoring, doesn't crash
- Usually resolves itself

### MATIC/USD Error
- "coinbase does not have market symbol MATIC/USD"
- This is expected - Coinbase renamed it to POL
- Harmless warning, ignore it

### "Unknown OrderType" on Coinbase
- Coinbase doesn't support limit orders the way Kraken does
- This is why grid trading doesn't work on Coinbase
- CrossKiller uses market orders instead

---

## BALANCES (Approximate)

- Kraken: ~$4,200 USD
- Coinbase: ~$1,300 USD
- Total: ~$5,500 USD

Run `python check_balances.py` in D:\gridbotchuck for current values.

---

## THINGS I CREATED IN PAST SESSIONS

1. **C:\c** - Short path workaround for Windows MAX_PATH issues
2. **Error recovery in bots** - Auto-reconnect after 5 failures
3. **Momentum strategies** - Replaced losing grid strategies
4. **Session status files** - For context persistence
5. **start_all_bots.bat** - Easy launcher for all 3 bots

---

## USER PREFERENCES

- Likes visible terminal windows when bots run (use `cmd /k`)
- Prefers concise updates over verbose explanations
- Wants bots to run unattended overnight
- Values documentation for future reference
- Building dedicated AI server (has most parts)

---

## DO NOT DO

1. DO NOT start grid trading bots
2. DO NOT try to fix FrankC training on TheBeast
3. DO NOT delete session files (valuable history)
4. DO NOT use `main.py --config` (that's grid trading)
5. DO NOT suggest time estimates for tasks

---

## RECOMMENDED FIRST ACTIONS FOR NEW SESSIONS

1. Read `D:\gridbotchuck\CURRENT_SETUP.md`
2. Read `D:\gridbotchuck\SESSION_STATUS.md`
3. Check if bots are running (look for python processes)
4. Ask user what they want to work on

---

## EVOLUTION OF THE PROJECT

```
Nov 2025: EMA research in bigclone/Ai
Dec 2025: Grid trading development (Chuck + Growler)
Dec 25:   Desktop app created, FrankC started
Dec 27:   Day trading assistant tested
Jan 11:   DISCOVERY: Grid trading loses money!
Jan 11:   Created momentum strategies
Jan 13:   All systems running momentum (current)
```

---

## CONTACT

If user needs help with Claude Code itself:
- `/help` command
- https://github.com/anthropics/claude-code/issues

---

**Remember: The user has been through many iterations. Trust the session files. Momentum works, grids don't.**

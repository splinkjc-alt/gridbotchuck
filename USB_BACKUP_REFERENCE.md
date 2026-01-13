# USB BACKUP REFERENCE - GridBot Chuck & AI Projects
**Last Updated:** January 13, 2026
**Machine:** TheBeast (RTX 4090, 128GB RAM, Ryzen 9 9950X)

---

## QUICK START - GET BOTS RUNNING

```batch
cd D:\gridbotchuck
start_all_bots.bat
```

This starts 3 momentum bots:
1. **VET Momentum** (Kraken) - 15m RSI+BB
2. **PEPE Momentum** (Kraken) - 30m RSI+EMA
3. **CrossKiller** (Coinbase) - 15m RSI scanner

---

## CRITICAL LESSONS LEARNED

### DO USE (Momentum Strategies):
- `run_vet_momentum.py` - +23.56% backtest
- `run_pepe_momentum.py` - +36.41% backtest
- `run_crosskiller_daytrader.py` - RSI oversold scanner

### DO NOT USE (Grid Trading LOSES MONEY):
- `run_smart_chuck.py` - Grid trading
- `run_smart_growler.py` - Grid trading
- `main.py --config` - Grid trading
- Any `config_*_grid.json` files

**Why?** Grid trading loses money in trending markets (up or down). Momentum strategies work better.

---

## PROJECT LOCATIONS

| Project | Location | Purpose |
|---------|----------|---------|
| **GridBot Chuck (Production)** | `D:\gridbotchuck` | Active trading bots |
| **GridBot Chuck (Dev)** | `C:\Users\splin\OneDrive\Documents\grid_trading_bot-master` | Full development version |
| **FrankC (Local AI)** | `C:\AI\free-claude` | Llama 70B fine-tuning (waiting for server) |
| **AI Guardian** | `C:\AI\ai-guardian` | Security tools (scam detector) |
| **EMA Research** | `C:\Users\splin\OneDrive\Documents\bigclone\clone\Ai` | Original backtesting work |
| **Backup** | `D:\gridbotchuck_backup_20260102` | Full backup |

---

## API KEYS LOCATION

- **Kraken:** `D:\gridbotchuck\.env`
- **Coinbase:** `D:\gridbotchuck\.env`

```
KRAKEN_API_KEY=xxx
KRAKEN_SECRET_KEY=xxx
COINBASE_API_KEY=xxx
COINBASE_API_SECRET=xxx
```

---

## BOT CONFIGURATIONS

### VET Momentum (Kraken)
- Timeframe: 15m
- Indicators: RSI + Bollinger Bands
- Position Size: $200
- Take Profit: +5%
- Stop Loss: -3.5%
- Max Hold: 24h

### PEPE Momentum (Kraken)
- Timeframe: 30m
- Indicators: RSI + EMA (9/20)
- Position Size: $200
- Take Profit: +5%
- Stop Loss: -3.5%
- Max Hold: 24h

### CrossKiller Daytrader (Coinbase)
- Timeframe: 15m
- Strategy: RSI oversold scanner (< 45)
- Position Size: $350
- Take Profit: +2%
- Stop Loss: -1.5%
- Max Hold: 4h
- Scans 25 coins every 30m

---

## ERROR RECOVERY

All bots have built-in error recovery:
- Log errors but continue running
- After 5 consecutive errors, auto-reconnect to exchange
- Reset error count on successful data fetch

**Bots will NOT crash from API timeouts.**

---

## COMMANDS

### Check Balances
```bash
cd D:\gridbotchuck
python check_balances.py
```

### Stop All Bots
```batch
stop_bots.bat
```
Or close the terminal windows.

### Manual Bot Start
```bash
cd D:\gridbotchuck
.venv\Scripts\python.exe run_vet_momentum.py
.venv\Scripts\python.exe run_pepe_momentum.py
.venv\Scripts\python.exe run_crosskiller_daytrader.py
```

---

## FRANKC (LOCAL AI) STATUS

**Location:** `C:\AI\free-claude`
**Status:** Training crashed Dec 25 (meta tensor error)
**Next Step:** Waiting for dedicated server hardware

### Server Parts (Already Have):
- Ryzen 9 5900X (12c/24t)
- MSI MEG X570 Unify
- 32GB DDR4-3600
- Samsung 970 EVO + Sabrent 1TB
- Corsair 1200W Platinum PSU
- Lian Li case

### Need to Buy:
- RTX 3060 12GB (~$250)
- CPU cooler
- 2TB storage (waiting for delivery)

---

## SESSION FILES (READ FIRST!)

| File | Location | Contains |
|------|----------|----------|
| **CURRENT_SETUP.md** | `D:\gridbotchuck` | What's working NOW |
| **SESSION_STATUS.md** | `D:\gridbotchuck` | Jan 11 - Why momentum > grids |
| **CLAUDE.md** | `D:\gridbotchuck` | AI assistant context |

**ALWAYS read CURRENT_SETUP.md first in new sessions!**

---

## EVOLUTION HISTORY

```
Nov 2025: bigclone/Ai - EMA research & backtesting
    |
Dec 2025: GridBot Chuck - Grid trading (FAILED - loses money)
    |
Jan 11:   Discovery - Grid trading doesn't work in trends
    |
Jan 11+:  Momentum Strategies - RSI/EMA/BB (WORKING)
```

---

## ACCOUNT BALANCES (As of Jan 13, 2026)

- **Kraken:** ~$4,238 USD
- **Coinbase:** ~$1,290 USD
- **Total:** ~$5,528 USD

---

## HELPFUL PATHS

### Short Path Workaround (for long Windows paths)
```
C:\c\Users\splin\OneDrive\Documents\bigclone
```
Same as the full path but shorter to avoid MAX_PATH issues.

---

## IF SOMETHING BREAKS

1. Read `D:\gridbotchuck\CURRENT_SETUP.md`
2. Check bot logs in terminal windows
3. Run `check_balances.py` to verify positions
4. Restart with `start_all_bots.bat`

---

## CONTACTS & RESOURCES

- **GitHub Issues:** https://github.com/anthropics/claude-code/issues
- **Claude Code Help:** Type `/help` in Claude Code

---

**Remember:** Momentum strategies work. Grid trading loses money. Always read session files first!

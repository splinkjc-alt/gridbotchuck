# CURRENT WORKING SETUP - Jan 13, 2026

## ⚠️ IMPORTANT: USE MOMENTUM, NOT GRIDS!
Grid trading was losing money. Momentum strategies work better.

## TO START BOTS
```
Double-click: start_all_bots.bat
```

## Active Bots (MOMENTUM STRATEGIES)

### 1. VET Momentum (Kraken)
- **Script**: `run_vet_momentum.py`
- **Timeframe**: 15m
- **Indicators**: RSI + Bollinger Bands
- **Backtest**: +23.56% return
- **Stop Loss**: -3.5%, Take Profit: +5%

### 2. PEPE Momentum (Kraken)
- **Script**: `run_pepe_momentum.py`
- **Timeframe**: 30m
- **Indicators**: RSI + EMA
- **Backtest**: +36.41% return
- **Stop Loss**: -3.5%, Take Profit: +5%

### 3. CrossKiller Daytrader (Coinbase)
- **Script**: `run_crosskiller_daytrader.py`
- **Timeframe**: 5m
- **Strategy**: EMA 9/20 dip buying
- **Stop Loss**: -1.5%, Take Profit: +2%
- **Max Hold**: 4 hours

## DO NOT USE (RETIRED)
- `run_smart_chuck.py` - Grid trading, loses money
- `run_smart_growler.py` - Grid trading, loses money
- `main.py --config` - Grid trading, loses money
- Any `config_*_grid.json` files

## Quick Commands
```bash
# Check balances
python check_balances.py

# Stop all bots
stop_bots.bat
```

## Session Notes Files
- `SESSION_STATUS.md` - Jan 11 detailed notes (momentum strategy creation)
- `CLAUDE_SESSION_STATUS.md` - Earlier notes
- `CURRENT_SETUP.md` - This file

---
*Updated: Jan 13, 2026 @ 1:17 AM*
*Lesson learned: READ SESSION_STATUS.md FIRST!*

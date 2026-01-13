# GridBot Chuck Session Status
**Last Updated:** 2026-01-11 (continued session)

## Current Status: BOTS FIXED WITH AUTO-REFRESH

| Bot | Exchange | Strategy | Capital | Status |
|-----|----------|----------|---------|--------|
| **CrossKiller** | Coinbase | 5m Day Trading (SOL, ADA, LINK) | ~$800 deployed | XRP removed, auto-refresh added |
| **VET Momentum** | Kraken | 15m RSI+BB | ~$200 | Holding 17k VET |
| **PEPE Momentum** | Kraken | 30m RSI+EMA | ~$200 | Watching for entry |

## Account Balances (Approx)
- **Coinbase:** ~$1,865 total (~$1,200 in positions, ~$665 USD)
- **Kraken:** ~$2,800 total (~$200 in VET, ~$2,600 USD)
- **Total Portfolio:** ~$4,665

---

## Fixes Applied (Jan 11, 2026 - Continued Session)

1. **Removed XRP** from CrossKiller (user sold manually, now only SOL/ADA/LINK)
2. **Added auto-refresh** to CrossKiller - reconnects after 5 consecutive errors
3. **Added auto-refresh** to momentum_strategy.py - same mechanism for VET/PEPE
4. **Fixed sell orders** - CrossKiller now fetches actual balance before selling (fees reduce tracked amounts)
5. **Added cycle logging** - Shows `[SCANNING] Cycle X` every 5 cycles so you know it's alive

---

## What Was Done This Session (Jan 11, 2026 Night)

### 1. Retired Grid Trading Strategy
- Grid trading was losing money even when working correctly
- Market trending down = grid keeps buying dips that keep dipping
- Switched to momentum-based strategies

### 2. Ran Comprehensive Backtests

**Kraken (VET/PEPE) - 30 day backtest:**
| Asset | Best Timeframe | Best Indicators | Strategy | Return |
|-------|---------------|-----------------|----------|--------|
| VET | 15m | RSI + BB | momentum | +23.56% (83% win) |
| PEPE | 30m | RSI + EMA | momentum | +36.41% (54% win) |

**Coinbase - 5m Day Trading (14 day backtest):**
| Asset | Best Indicators | Strategy | Return |
|-------|-----------------|----------|--------|
| SOL | EMA 9/20 | mean_reversion | +13.91% |
| XRP | Full Suite | momentum | +13.52% |
| ADA | Full Suite | momentum | +11.41% |
| LINK | RSI+EMA | mean_reversion | +11.37% |
| UNI | - | - | LOSER (avoid) |
| ATOM | - | - | LOSER (avoid) |

### 3. Created New Momentum Bots

**CrossKiller Day Trader** (`run_crosskiller_daytrader.py`)
- Coins: SOL, XRP, ADA, LINK (winners only)
- Timeframe: 5m
- Buy signal: EMA 9 < EMA 20 (dip)
- Sell signal: EMA 9 > EMA 20 (recovery) or +2% take profit
- Stop loss: -1.5%
- Max hold: 4 hours
- Position size: $400 each, max 3 positions

**VET Momentum** (`run_vet_momentum.py`)
- Timeframe: 15m
- Indicators: RSI + Bollinger Bands
- Buy: BB lower + RSI oversold
- Sell: BB upper or +5% take profit
- Stop loss: -3.5%, Max hold: 24h

**PEPE Momentum** (`run_pepe_momentum.py`)
- Timeframe: 30m
- Indicators: RSI + EMA
- Similar momentum strategy
- Stop loss: -3.5%, Max hold: 24h

### 4. Fixed Issues
- Coinbase API errors - added error tolerance
- Wrong EMA crossover direction - flipped buy/sell logic
- Momentum strategy hanging - added debug logging
- Coinbase market buy requires price parameter

---

## New Files Created

| File | Purpose |
|------|---------|
| `run_crosskiller_daytrader.py` | 5m day trading bot for Coinbase |
| `run_vet_momentum.py` | VET momentum bot |
| `run_pepe_momentum.py` | PEPE momentum bot |
| `strategies/momentum_strategy.py` | Momentum strategy class |
| `backtest_all_combos.py` | Backtest VET/PEPE all timeframes |
| `backtest_coinbase_5m.py` | Backtest Coinbase coins 5m |
| `config/config_vet_momentum.json` | VET config |
| `config/config_pepe_momentum.json` | PEPE config |
| `liquidate_coinbase.py` | Quick liquidate Coinbase |
| `liquidate_kraken.py` | Quick liquidate Kraken |
| `check_balances.py` | Check all exchange balances |

---

## Quick Commands

```powershell
# Check all balances
cd D:\gridbotchuck
.\.venv\Scripts\python.exe check_balances.py

# Liquidate Coinbase to USD
.\.venv\Scripts\python.exe liquidate_coinbase.py

# Liquidate Kraken to USD
.\.venv\Scripts\python.exe liquidate_kraken.py

# Start bots (each in separate PowerShell window)
.\.venv\Scripts\python.exe run_crosskiller_daytrader.py
.\.venv\Scripts\python.exe run_vet_momentum.py
.\.venv\Scripts\python.exe run_pepe_momentum.py

# Check logs
Get-Content logs/crosskiller_daytrader.log -Last 20
Get-Content logs/vet_momentum.log -Last 20
Get-Content logs/pepe_momentum.log -Last 20
```

---

## Bot Logic Summary

### CrossKiller (Day Trading)
```
BUY when: EMA 9 crosses BELOW EMA 20 (dip/weakness)
SELL when: EMA 9 crosses ABOVE EMA 20 (recovery) OR +2% profit OR -1.5% loss OR 4h hold
```

### VET/PEPE (Swing Trading)
```
BUY when: Price at lower Bollinger Band + RSI oversold (VET) or EMA conditions (PEPE)
SELL when: Price at upper BB OR +5% profit OR -3.5% loss OR 24h hold
```

---

## Important Notes for Next Session

1. **Old grid bots are retired** - Chuck/Growler (`run_smart_chuck.py`, `run_smart_growler.py`) not in use
2. **Startup shortcut needs update** - `start_all_bots.bat` points to old scripts
3. **CrossKiller is day trading** - expects quick in/out on 5m, check frequently
4. **If bots hang after startup** - check if balance fetch is timing out, may need restart
5. **UNI and ATOM are losers** on 5m - CrossKiller avoids them

---

## The Bot Family (Updated)

| Bot | Script | Exchange | Strategy | Status |
|-----|--------|----------|----------|--------|
| CrossKiller | `run_crosskiller_daytrader.py` | Coinbase | 5m EMA dip/recovery | RUNNING |
| VET Momentum | `run_vet_momentum.py` | Kraken | 15m RSI+BB | RUNNING |
| PEPE Momentum | `run_pepe_momentum.py` | Kraken | 30m RSI+EMA | RUNNING |
| Chuck (old) | `run_smart_chuck.py` | Kraken | Grid | RETIRED |
| Growler (old) | `run_smart_growler.py` | Kraken | Grid | RETIRED |
| Marketbot | `stock_trading_assistant.py` | Alpaca | Stocks | Paper mode, weekdays only |

---

## Jeff's AI Ecosystem (Unchanged)

- **GridBot Chuck** (D:\gridbotchuck) - Trading bots - ACTIVE
- **FrankC** (C:\AI\free-claude) - Local Claude-trained AI - Waiting for Python 3.11
- **Screen Watcher Frank** (D:\frankc) - Context-aware help - Paused
- **AI Guardian** (C:\AI\ai-guardian) - Security suite - Working
- **TheBeast**: RTX 4090, 128GB RAM, Ryzen 9 9950X

---

*Last updated: Jan 11, 2026 @ 2:10 AM*
*Session with: Claude Opus 4.5*
*Major change: Switched from grid trading to momentum strategies based on backtests*

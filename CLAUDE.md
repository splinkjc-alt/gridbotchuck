# Claude Context File

This file helps Claude (or any AI assistant) quickly understand this project.

## Project: GridBot Chuck & The Bot Family

A suite of cryptocurrency and stock trading bots with per-asset optimization.

## Quick Start

```bash
# Activate environment
cd D:\gridbotchuck
.venv\Scripts\activate

# Run the adaptive scanner (main tool)
python adaptive_scanner.py

# Check signal accuracy
python signal_logger.py --summary

# Re-optimize all assets (weekly)
python optimization/asset_optimizer.py --optimize-all
```

## Key Files

| File | Purpose |
|------|---------|
| `adaptive_scanner.py` | Multi-asset scanner using per-coin optimal configs |
| `signal_logger.py` | Tracks signal accuracy (BUY/SELL predictions vs outcomes) |
| `optimization/asset_optimizer.py` | Backtests to find best timeframe/indicators per asset |
| `optimization/optimal_configs.json` | Saved optimal settings per asset |
| `optimization/indicator_combos.py` | Available indicator combinations |
| `config/watchlist.json` | Assets to monitor (15 crypto + 5 stocks) |
| `config/config.json` | GridBot Chuck main config |
| `main.py` | Original GridBot Chuck entry point |

## Architecture

```
D:\gridbotchuck\
├── .venv/                    # Python 3.12 environment
├── .vscode/                  # VS Code config (launch configs, settings)
├── config/                   # JSON configs
│   ├── config.json           # Main bot config
│   └── watchlist.json        # Assets to scan
├── optimization/             # Per-asset optimization module
│   ├── asset_optimizer.py    # Runs backtests
│   ├── indicator_combos.py   # Indicator definitions
│   └── optimal_configs.json  # Results
├── data/                     # Runtime data
│   └── signals.db            # Signal tracking database
├── core/                     # Trading bot core modules
├── strategies/               # Trading strategies
├── adaptive_scanner.py       # THE MAIN SCANNER
├── signal_logger.py          # Accuracy tracking
└── main.py                   # Original bot entry
```

## The Bots

1. **GridBot Chuck** - Grid trading on BTC/USD
2. **Growler** - Bearish scalping (ADA, CPOOL)
3. **Sleeping Marketbot** - Stock day trading (needs Alpaca API)
4. **Adaptive Scanner** - Multi-asset scanner with per-coin optimization (ACTIVE)

## How Optimization Works

1. For each asset, test all combinations:
   - Timeframes: 5m, 15m, 30m, 1h
   - Indicators: RSI only, RSI+BB, RSI+EMA, RSI+MACD, Full
   - Strategies: grid, mean_reversion, momentum

2. Run 30-day backtests, rank by profit %

3. Save best config per asset to `optimal_configs.json`

4. Scanner uses each asset's optimal settings

## Signal Types

| Signal | Meaning | Strength |
|--------|---------|----------|
| BUY | Oversold, strong entry | >= 60% |
| SELL | Overbought, consider exits | >= 60% |
| WATCH | Preparing, monitor closely | >= 40% |
| WAIT | No setup | < 40% |
| SLEEPING | Market closed (stocks) | N/A |

## Important Notes

- **Exchange**: Kraken (API keys in `.env`)
- **Paper Trading**: Currently paper trading, not live
- **Signal Logging**: All BUY/SELL signals logged to `data/signals.db`
- **Validation**: Run `signal_logger.py --validate` after 24h to check accuracy

## Common Tasks

### Check scanner status
```bash
python adaptive_scanner.py --show-configs
```

### Validate signal accuracy
```bash
python signal_logger.py --validate
python signal_logger.py --summary
```

### Re-optimize after market changes
```bash
python optimization/asset_optimizer.py --optimize-all
```

### View recent signals
```bash
python signal_logger.py --recent 20
```

## GitHub

Repository: https://github.com/splinkjc-alt/gridbotchuck

## Related Projects

- **Frank C**: AI companion at `C:\AI\` (screen capture + vision)
- **Notes**: `D:\frankc\notes\FRANK_C.md` has full context

---
*Last updated: Jan 2, 2026*
*Created by: Claude Opus 4.5*

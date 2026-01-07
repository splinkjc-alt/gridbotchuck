# GridBot Chuck - Live Status

> **Last Updated:** January 6, 2026 @ 9:50 PM EST
> **Operator:** @splinkjc-alt
> **Transparency Policy:** All wins AND losses reported honestly

---

## Current Bot Status

### Chuck (Smart Scanner)
**Exchange:** Kraken | **Mode:** LIVE | **Strategy:** Auto-Scanning Grid Bot

| Metric | Value |
|--------|-------|
| **Current Pair** | VET/USD |
| **Grid Score** | 80/100 |
| **Volatility** | 2.4% |
| **Grid Range** | $0.01258 - $0.01353 |
| **Rescan Interval** | Every 2 hours |
| **Status** | Active - Auto-scanning |

---

### Growler (Smart Scanner)
**Exchange:** Kraken | **Mode:** LIVE | **Strategy:** Auto-Scanning Grid Bot #2

| Metric | Value |
|--------|-------|
| **Current Pair** | PEPE/USD |
| **Grid Score** | 75/100 |
| **Volatility** | 1.4% |
| **Rescan Interval** | Every 2 hours |
| **Status** | Active - Auto-scanning |

---

### Crosskiller
**Exchange:** Coinbase | **Mode:** LIVE | **Strategy:** EMA 9/20 Crossover

| Metric | Value |
|--------|-------|
| **Max Positions** | 3 |
| **Cycle Interval** | ~4 minutes |
| **Status** | Active - Scanning |

---

### Sleeping Marketbot
**Exchange:** Alpaca | **Mode:** LIVE | **Strategy:** Mean Reversion (RSI < 40)

| Metric | Value |
|--------|-------|
| **Market Hours** | 9:30 AM - 4:00 PM ET |
| **News Analysis** | Enabled (Alpha Vantage) |
| **Status** | Sleeping (market closed) |

---

## New Features (Jan 6, 2026)

### Smart Auto-Scanning
Both Chuck and Growler now automatically:
- Scan 17+ crypto pairs every 2 hours
- Score pairs for grid trading suitability (volatility, mean reversion)
- Switch to better pairs when found (10+ score improvement)
- Avoid trading the same pair as each other

### Market Scanner Results
| Rank | Pair | Score | Return | Why |
|------|------|-------|--------|-----|
| 1 | VET/USD | 80 | 10.9% | High volatility + mean reversion |
| 2 | PEPE/USD | 75 | 15.3% | Good volatility |
| 3 | CRV/USD | 75 | 12.8% | Consistent returns |
| 4 | ADA/USD | 70 | 16.0% | Solid performer |
| ... | BTC/USD | 50 | 0.0% | Too stable for grids |

### News Analyzer
Marketbot now analyzes financial news before market opens:
- Sentiment analysis with 80+ financial terms
- Tracks which news sources are accurate
- Adjusts trading scores based on news sentiment

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Bots Running** | 4 |
| **Smart Scanners** | 2 (Chuck, Growler) |
| **Exchanges** | Kraken, Coinbase, Alpaca |

---

## Operator Notes

**January 6, 2026:**
- Upgraded Chuck and Growler to smart auto-scanning mode
- BTC scored only 50/100 - too stable for grid trading
- VET/USD scored highest (80/100) - great volatility
- Added Telegram notifications for pair switches
- News analyzer integrated with Marketbot

---

## Disclaimer

This is a personal trading project for educational purposes. Past performance does not guarantee future results. Trading cryptocurrencies involves significant risk. Never trade more than you can afford to lose.

---

## Links

- [Source Code](https://github.com/splinkjc-alt/gridbotchuck)
- [Website](https://gridbotchuck.netlify.app)
- [Documentation](https://github.com/splinkjc-alt/gridbotchuck/blob/main/README.md)

---

*Last verified by operator: January 6, 2026*

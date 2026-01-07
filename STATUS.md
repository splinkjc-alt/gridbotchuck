# GridBot Chuck - Live Status

> **Last Updated:** January 7, 2026 @ 2:00 AM EST
> **Operator:** @splinkjc-alt
> **Transparency Policy:** All wins AND losses reported honestly

---

## Current Bot Status

### Chuck (Grid Bot)
**Exchange:** Kraken | **Mode:** LIVE | **Strategy:** Grid Trading

| Metric | Value |
|--------|-------|
| **Current Pair** | ADA/USD |
| **Grid Score** | 70/100 |
| **Volatility** | 1.0% |
| **Grid Range** | $0.38 - $0.44 |
| **Current Price** | ~$0.41 |
| **Status** | Active - Healthy |

---

### Growler (Grid Bot)
**Exchange:** Kraken | **Mode:** LIVE | **Strategy:** Grid Trading

| Metric | Value |
|--------|-------|
| **Current Pair** | PEPE/USD |
| **Grid Score** | 75/100 |
| **Volatility** | 1.4% |
| **Current Price** | ~$0.00000673 |
| **Portfolio Value** | ~$1,430 |
| **Status** | Active - Healthy |

---

### Crosskiller
**Exchange:** Coinbase | **Mode:** LIVE | **Strategy:** EMA 9/20 Crossover

| Metric | Value |
|--------|-------|
| **USD Balance** | $1,150.71 |
| **Max Positions** | 3 |
| **Cycle Interval** | ~4 minutes |
| **Recent Trade** | Bought 34.5 UNI @ $6.01 |
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

## Latest Market Scanner Results (Jan 7, 2026)

| Rank | Pair | Score | Backtest Return | Notes |
|------|------|-------|-----------------|-------|
| 1 | VET/USD | 85 | 10.9% | High volatility (connection issues) |
| 2 | PEPE/USD | 75 | 16.8% | Good volatility - Growler's pick |
| 3 | CRV/USD | 75 | 12.6% | Consistent returns |
| 4 | ADA/USD | 70 | 16.2% | Solid performer - Chuck's pick |
| 5 | UNI/USD | 70 | 31.6% | High returns |
| ... | BTC/USD | 50 | 0.0% | Too stable for grids |

---

## Features

### Smart Auto-Scanning
Both Chuck and Growler can automatically:
- Scan 17+ crypto pairs every 2 hours
- Score pairs for grid trading suitability (volatility, mean reversion)
- Switch to better pairs when found (10+ score improvement)
- Avoid trading the same pair as each other

### News Analyzer
Marketbot analyzes financial news before market opens:
- Sentiment analysis with 80+ financial terms
- Tracks which news sources are accurate
- Adjusts trading scores based on news sentiment

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Bots Running** | 4 |
| **Grid Bots** | 2 (Chuck, Growler) |
| **Exchanges** | Kraken, Coinbase, Alpaca |

---

## Operator Notes

**January 7, 2026:**
- Chuck switched from VET/USD to ADA/USD due to Kraken WebSocket timeouts on VET
- Growler running strong on PEPE/USD (~$1,430 portfolio value)
- Crosskiller actively trading - bought UNI position
- All bots restarted fresh after wallet reset

**January 6, 2026:**
- Upgraded Chuck and Growler to smart auto-scanning mode
- BTC scored only 50/100 - too stable for grid trading
- VET/USD scored highest (85/100) - great volatility
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

*Last verified by operator: January 7, 2026*

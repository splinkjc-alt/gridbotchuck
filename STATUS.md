# GridBot Chuck - Live Status

> **Last Updated:** January 7, 2026 @ 7:58 PM EST
> **Operator:** @splinkjc-alt
> **Transparency Policy:** All wins AND losses reported honestly

---

## Current Bot Status

### Chuck (Grid Bot)
**Exchange:** Kraken | **Mode:** LIVE | **Strategy:** Grid Trading

| Metric | Value |
|--------|-------|
| **Current Pair** | ADA/USD |
| **Current Price** | $0.4030 |
| **Grid Range** | $0.38 - $0.44 |
| **Crypto Balance** | 452.96 ADA |
| **Open Orders** | 2 buys ($0.38, $0.391) |
| **Uptime** | 18+ hours |
| **Status** | Active - Healthy |

---

### Growler (Grid Bot)
**Exchange:** Kraken | **Mode:** LIVE | **Strategy:** Grid Trading

| Metric | Value |
|--------|-------|
| **Current Pair** | PEPE/USD |
| **Current Price** | $0.00000657 |
| **Grid Range** | $0.0000062 - $0.0000070 |
| **Crypto Balance** | 42.8M PEPE |
| **Open Orders** | 2 buys ($0.0000062, $0.00000635) |
| **Portfolio Value** | ~$1,536 |
| **Uptime** | 18+ hours |
| **Status** | Active - Healthy |

---

### Kraken Portfolio Summary

| Asset | Amount | Value |
|-------|--------|-------|
| USD | $1,511.54 | $1,511.54 |
| ADA | 452.96 | $182.54 |
| PEPE | 42.8M | $281.58 |
| **Total** | | **$1,975.66** |

---

### Crosskiller
**Exchange:** Coinbase | **Mode:** LIVE | **Strategy:** EMA 9/20 Crossover

| Metric | Value |
|--------|-------|
| **Cycle Interval** | ~4 minutes |
| **Max Positions** | 3 |
| **Uptime** | 18+ hours |
| **Status** | Active - Scanning |

---

### Marketbot (Stock Trading)
**Exchange:** Alpaca | **Mode:** LIVE | **Strategy:** Mean Reversion (RSI < 40)

| Metric | Value |
|--------|-------|
| **Account Value** | $1,006.91 |
| **Cash** | $20.23 |
| **Market Hours** | 9:30 AM - 4:00 PM ET |
| **News Analysis** | Enabled |
| **News-Market Learner** | Enabled (NEW) |
| **Watchlist** | 19 stocks |
| **Target** | 4% bounce |
| **Stop Loss** | 3% |
| **Status** | Market closed - holding positions |

**Current Positions:**
| Stock | Shares | Entry | Current | P/L |
|-------|--------|-------|---------|-----|
| MARA | 49 | $10.07 | $10.10 | +$1.47 (+0.30%) |
| COIN | 2 | $243.16 | $245.89 | +$5.45 (+1.12%) |

---

## Latest Market Scanner Results (Jan 7, 2026)

| Rank | Pair | Score | Backtest Return | Notes |
|------|------|-------|-----------------|-------|
| 1 | VET/USD | 85 | 10.9% | High volatility (connection issues) |
| 2 | PEPE/USD | 75 | 16.8% | Growler's pick |
| 3 | CRV/USD | 75 | 12.6% | Consistent returns |
| 4 | ADA/USD | 70 | 16.2% | Chuck's pick |
| 5 | UNI/USD | 70 | 31.6% | High returns |
| ... | BTC/USD | 50 | 0.0% | Too stable for grids |

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Bots Running** | 4 |
| **Grid Bots** | 2 (Chuck, Growler) |
| **EMA Bot** | 1 (Crosskiller) |
| **Stock Bot** | 1 (Marketbot) |
| **Exchanges** | Kraken, Coinbase, Alpaca |
| **Kraken Portfolio** | $1,975.66 |
| **Alpaca Portfolio** | $1,006.91 |

---

## Operator Notes

**January 7, 2026 (Evening):**
- All 4 bots running stable for 18+ hours
- Marketbot went LIVE with new Alpaca API keys
- First live trades: MARA (49 shares), COIN (2 shares) - both in green
- Added News-Market Learner - bots now learn cause/effect from news
- Kraken portfolio: $1,975.66
- Alpaca portfolio: $1,006.91 (+0.69% day 1)

**January 7, 2026 (Morning):**
- Growler grid range fixed ($0.0000062-$0.0000070) - now has orders
- Chuck on ADA/USD with healthy grid
- Marketbot configured and waiting for market open

**January 7, 2026 (Early AM):**
- Chuck switched from VET/USD to ADA/USD due to Kraken WebSocket timeouts
- Growler running on PEPE/USD
- Crosskiller actively trading on Coinbase
- All bots restarted fresh after wallet reset

**January 6, 2026:**
- Upgraded Chuck and Growler to smart auto-scanning mode
- BTC scored only 50/100 - too stable for grid trading
- Added Telegram notifications for pair switches
- News analyzer integrated with Marketbot

---

## New Feature: News-Market Learner

The bots now learn from news events:
1. Fetches live headlines during market scans
2. Records news + price at scan time
3. Tracks price movement 1h/4h/1d later
4. Learns which keywords correlate with price moves
5. Uses learned patterns to improve future predictions

Keywords tracked: upgrades, downgrades, earnings, Fed, crypto, ETF, etc.

---

## Disclaimer

This is a personal trading project for educational purposes. Past performance does not guarantee future results. Trading cryptocurrencies involves significant risk. Never trade more than you can afford to lose.

---

## Links

- [Source Code](https://github.com/splinkjc-alt/gridbotchuck)
- [Website](https://gridbotchuck.netlify.app)
- [Documentation](https://github.com/splinkjc-alt/gridbotchuck/blob/main/README.md)

---

*Last verified by operator: January 7, 2026 @ 7:58 PM EST*

# GridBot Chuck v2.0 - Multi-Strategy Trading Platform 🚀

## 🎯 What is GridBot Chuck?

GridBot Chuck is a **transparent, multi-strategy trading bot** that automates crypto and stock trading across multiple exchanges. Built with real traders in mind - no BS, no scams, just honest automated trading with proven results.

---

## ✨ What's Included in v2.0

### 3 Complete Trading Strategies

#### 1. **GridBot** - Hedged Grid Trading
- Profits from price volatility in ranging markets
- Buys low, sells high automatically using grid levels
- **PROVEN RESULTS:** +71.6% in 8.5 hours (Day 1 live on CC/USD)
- Best for: Sideways/choppy markets

#### 2. **Triple-Threat** - Multi-Strategy Combo
- Combines 3 strategies: Mean Reversion + Momentum + Breakout
- Adapts to different market conditions
- Works on: Kraken & Coinbase
- Best for: Active crypto trading

#### 3. **Stock Bot** - Mean Reversion Scanner
- Scans stocks for oversold/overbought conditions
- Integrates with Alpaca for commission-free trading
- Best for: Day trading US stocks

---

## 🔌 Multi-Exchange Support

- **Kraken** - Grid trading + Triple-Threat
- **Coinbase** - Triple-Threat strategy
- **Alpaca** - Stock trading (commission-free)

---

## 📦 Features

✅ **Paper Trading** - Test with virtual money first  
✅ **Real Trading** - Go live when you're ready  
✅ **Multi-Pair Support** - Trade multiple assets simultaneously  
✅ **Risk Management** - Position limits, stop losses, portfolio caps  
✅ **Real-Time Monitoring** - Track performance as it happens  
✅ **Database Persistence** - All trades saved to SQLite  
✅ **Detailed Logging** - Full audit trail of every action  
✅ **Configuration System** - Easy JSON-based setup  
✅ **Open Source** - MIT License, inspect the code yourself

---

## 📊 Real Performance (Verified)

**GridBot - Day 1 Live Trading (Dec 30, 2024)**
- Asset: CC/USD on Kraken
- Starting Capital: $157.00
- Time Period: 8.5 hours
- Result: **+$112.44 (+71.6%)**
- Strategy: Hedged grid trading with dynamic grid levels

**Not every day is a winner.** We track and share both wins AND losses because transparency matters.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/splinkjc-alt/gridbotchuck.git
cd gridbotchuck
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Your API Keys
```bash
# Create .env file with your exchange API keys
cp .env.example .env
# Edit .env with your keys (NEVER commit this file!)
```

### 4. Run Your First Bot
```bash
# Paper trading (safe testing)
python triple_threat_trader.py --paper

# Live trading (real money - be careful!)
python triple_threat_trader.py --live
```

---

## 📚 Documentation

- [README.md](README.md) - Complete installation & usage guide
- [MARKETING_STRATEGY.md](MARKETING_STRATEGY.md) - Our transparent approach
- [config/](config/) - Example configuration files
- [strategies/](strategies/) - Strategy implementations

---

## 🛠️ Technical Stack

- **Python 3.8+** - Core language
- **CCXT** - Multi-exchange cryptocurrency trading
- **Alpaca-py** - Stock trading API
- **SQLite** - Trade persistence
- **Pandas** - Data analysis
- **YFinance** - Free stock market data

---

## ⚠️ Important Disclaimers

**Trading involves risk. You can lose money.**

- Start with small amounts you can afford to lose
- Always test with paper trading first
- Past performance doesn't guarantee future results
- This bot is a tool, not a money printer
- You are responsible for your own trading decisions

---

## 🤝 Contributing

This is an open-source project! Contributions welcome:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details

---

## 🙏 Credits

Built with [Claude](https://claude.ai)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>

---

## 📞 Support & Community

- **Issues:** Report bugs via [GitHub Issues](https://github.com/splinkjc-alt/gridbotchuck/issues)
- **Discussions:** Ask questions in [Discussions](https://github.com/splinkjc-alt/gridbotchuck/discussions)

---

## 🎯 What's Next?

We're actively developing:
- Windows desktop app with GUI
- Android mobile app for monitoring
- Backtesting engine
- More trading strategies
- Multi-account support

**Star ⭐ this repository to stay updated!**

---

**GridBot Chuck: The Trading Bot That Shows Its Work™**

*Automation for traders who hate BS.*

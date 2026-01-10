# GridBot Chuck - Multi-Strategy Trading Bot Suite

**Automated trading across crypto and stocks with proven strategies and full transparency.**

[![Live Trading](https://img.shields.io/badge/Live%20Trading-Active-success)](https://github.com/yourusername/gridbot-chuck)
[![Paper Trading](https://img.shields.io/badge/Paper%20Trading-Supported-blue)](https://github.com/yourusername/gridbot-chuck)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 What is GridBot Chuck?

GridBot Chuck is a comprehensive trading bot suite that runs **multiple proven strategies simultaneously** across crypto and stock markets. Built with transparency and risk management at its core.

**Real Performance (Day 1 - Dec 30, 2025):**
- GridBot Live Trading: **+71.6% in 8.5 hours** ($157 → $269.58)
- Live proof: Verified Kraken transaction history
- Strategy: Hedged grid trading on CC/USD

---

## 🎯 Features

### Multi-Strategy Trading
- **Grid Trading Bot** - Profit from sideways/volatile markets (hedged grid strategy)
- **Triple-Threat Trader** - Combines 3 strategies: Mean Reversion + Momentum + Breakout
- **Stock Trading Assistant** - Mean reversion scanner for US stocks (RSI-based)

### Multi-Exchange Support
- ✅ Kraken (crypto + live grid trading)
- ✅ Coinbase Advanced Trading (crypto)
- ✅ Alpaca (US stocks - paper trading)
- ✅ Yahoo Finance (free stock market data)

### Risk Management
- Position sizing (% of capital per trade)
- Stop losses (configurable)
- Maximum concurrent trades
- Portfolio-level risk controls
- Circuit breakers

### Trading Modes
- **Paper Trading** - Test with virtual capital ($3,000 crypto, $25,000 stocks)
- **Live Trading** - Real money on Kraken (grid trading)

### Monitoring & Analytics
- Real-time WebSocket price feeds
- Health checks (bot status, system resources)
- Trade history persistence (SQLite)
- Performance analytics
- Activity monitoring (auto-switching for stuck markets)

---

## 📊 Trading Strategies Explained

### 1. Grid Trading (GridBot Chuck)
**Best for:** Sideways/ranging markets with volatility

**How it works:**
1. Sets up buy orders at lower price levels
2. Sets up sell orders at higher price levels
3. Profits from each price oscillation
4. Hedged approach protects against trends

**Example:**
- Price range: $0.1367 - $0.1511
- Grid levels: 5 levels
- Each buy→sell cycle: ~2-4% profit
- Compounds gains through multiple cycles

**Real Result:** +71.6% in 8.5 hours on CC/USD

### 2. Triple-Threat Trader
**Best for:** Diverse market conditions

**Combines 3 strategies:**

**A. Mean Reversion (40% weight)**
- Buys oversold assets (RSI < 30-40)
- Quick 3-4% bounces
- Tight 3% stop losses

**B. Momentum (30% weight)**
- Catches trending moves (RSI > 60)
- Rides 8%+ moves
- Trailing stops

**C. Breakout (30% weight)**
- Detects range breakouts
- High volume confirmation
- Risk/reward: 1:2.7

**Real Setup:**
- Scans 14 crypto pairs every 60 seconds
- Max 7 concurrent trades
- $3,000 virtual capital
- 2% risk per trade

### 3. Stock Trading Assistant
**Best for:** US market day trading (9:30 AM - 4:00 PM ET)

**Strategy:**
- Scans 19 high-volatility stocks
- RSI + Bollinger Bands analysis
- Mean reversion score (0-100)
- Targets 4% bounces with 3% stops

**Watchlist:**
- Tech: TSLA, NVDA, AMD, PLTR, HOOD
- Leveraged ETFs: TQQQ, SOXL, UPRO, SPXL
- Large caps: AAPL, MSFT, META, GOOGL, AMZN

---

## 🛠️ Tech Stack

**Core:**
- Python 3.10+
- asyncio (async/await for concurrent operations)
- SQLite (trade history persistence)

**Trading:**
- ccxt (unified exchange API)
- alpaca-py (stock trading API)
- yfinance (free stock market data)

**Data Analysis:**
- pandas (data manipulation)
- numpy (numerical computations)
- Technical indicators (RSI, Bollinger Bands, etc.)

**Monitoring:**
- WebSockets (real-time price feeds)
- Health checks (bot + system resources)
- Event-driven architecture (EventBus)

---

## 📁 Project Structure

```
grid_trading_bot-master/
├── main.py                          # GridBot Chuck launcher
├── triple_threat_trader.py          # Kraken Triple-Threat bot
├── triple_threat_trader_coinbase.py # Coinbase Triple-Threat bot
├── stock_trading_assistant.py       # Stock mean reversion scanner
│
├── config/
│   ├── config.json                  # GridBot configuration
│   ├── config_coinbase.json         # Coinbase config
│   └── config_small_capital_multi_pair.json
│
├── core/
│   ├── bot_management/
│   │   ├── grid_trading_bot.py
│   │   ├── activity_monitor.py      # Auto-switching for stuck markets
│   │   └── enhanced_multi_pair_manager.py
│   │
│   ├── order_handling/
│   │   ├── order_manager.py
│   │   ├── enhanced_order_manager.py
│   │   └── balance_tracker.py
│   │
│   ├── risk_management/
│   │   ├── circuit_breaker.py       # Auto-stop on cascading losses
│   │   └── rate_limiter.py          # Prevent API bans
│   │
│   ├── persistence/
│   │   └── order_repository.py      # SQLite database
│   │
│   └── validation/
│       └── enhanced_order_validator.py
│
├── strategies/
│   ├── pair_performance_monitor.py  # Multi-pair switching logic
│   └── grid_trading_strategy.py
│
├── .env                             # API keys (DO NOT COMMIT)
├── requirements.txt                 # Python dependencies
└── README.md                        # This file
```

---

## 🚦 Quick Start

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)
- API keys from supported exchanges

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/gridbot-chuck.git
cd gridbot-chuck
```

### 2. Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 3. Configure API Keys
Create a `.env` file in the project root:

```env
# Kraken (for crypto trading)
EXCHANGE_API_KEY=your_kraken_api_key
EXCHANGE_SECRET_KEY=your_kraken_secret_key

# Coinbase Advanced Trading (for crypto)
COINBASE_API_KEY=your_coinbase_api_key
COINBASE_SECRET_KEY=your_coinbase_private_key

# Alpaca (for stock trading - paper trading is free!)
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
```

**Get API Keys:**
- Kraken: https://www.kraken.com/u/security/api
- Coinbase: https://www.coinbase.com/settings/api
- Alpaca (free paper trading): https://app.alpaca.markets/signup

### 4. Configure Bot Settings
Edit `config/config.json` for GridBot settings:

```json
{
  "exchange": "kraken",
  "trading_mode": "paper_trading",  // Change to "live" for real money
  "pair": "CC/USD",
  "grid_levels": 5,
  "grid_range_percent": [0.03, 0.06],
  "initial_balance": 157.0
}
```

### 5. Run Bots

**GridBot Chuck (Grid Trading):**
```bash
python main.py --config config/config.json
```

**Triple-Threat Trader (Kraken):**
```bash
python triple_threat_trader.py
```

**Triple-Threat Trader (Coinbase):**
```bash
python triple_threat_trader_coinbase.py
```

**Stock Trading Assistant:**
```bash
python stock_trading_assistant.py
```

---

## ⚙️ Configuration

### Grid Trading Settings
```json
{
  "grid_levels": 5,              // Number of grid levels
  "grid_spacing": "geometric",   // "geometric" or "arithmetic"
  "grid_range_percent": [0.03, 0.06],  // Price range around current price
  "max_pairs": 2,                // Multi-pair trading
  "auto_select": true,           // Auto-select best pairs
  "activity_monitor": {
    "enabled": true,
    "check_interval_minutes": 10,
    "stale_threshold_periods": 2,
    "stagnation_exit": {
      "enabled": true,
      "max_minutes": 45,
      "min_movement_percent": 0.3
    }
  }
}
```

### Triple-Threat Settings
```python
# In triple_threat_trader.py
self.mean_reversion_threshold = 65.0  # Mean reversion score threshold
self.momentum_threshold = 65.0        # Momentum score threshold
self.breakout_threshold = 70.0        # Breakout score threshold

self.pairs = [
    "XRP/USD", "ADA/USD", "DOGE/USD", "DOT/USD",
    "LINK/USD", "ATOM/USD", "UNI/USD", "AVAX/USD",
    "FIL/USD", "NEAR/USD", "APT/USD", "ARB/USD",
    "OP/USD", "SOL/USD"
]
```

### Stock Bot Settings
```python
# In stock_trading_assistant.py
self.threshold = 60.0  # Mean reversion score threshold

self.watchlist = [
    "TSLA", "NVDA", "AMD", "PLTR", "HOOD",
    "TQQQ", "SOXL", "UPRO", "SPXL",
    "AAPL", "MSFT", "META", "GOOGL", "AMZN"
]
```

---

## 📈 Performance Tracking

### Real-Time Monitoring
Each bot logs performance updates:

```
GridBot Chuck - Status Update
CC/USD @ $0.1482
Balance: $32.54 + 173.85 CC
Portfolio Value: $269.58
Profit: +$112.51 (+71.6%)
```

### Trade History
All trades stored in SQLite database:
- Entry/exit prices
- P&L per trade
- Strategy used
- Timestamps
- Full audit trail

### Export Data
```bash
sqlite3 data/orders.db
.headers on
.mode csv
.output trades.csv
SELECT * FROM orders;
```

---

## 🔒 Security & Risk Management

**GridBot Chuck takes security seriously.** Your API keys control real money.

### Quick Security Setup (5 Minutes)

1. **Protect API Keys**
   ```bash
   cp .env.example .env
   chmod 600 .env  # Make it private
   ```

2. **Generate Dashboard API Key**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
   Add to `.env`:
   ```env
   GRIDBOT_API_KEY=your-generated-key-here
   ```

3. **Exchange Security**
   - ❌ **NEVER** use API keys with withdrawal permissions
   - ✅ **ALWAYS** enable IP whitelisting on exchange
   - ✅ **ALWAYS** enable 2FA on exchange account
   - ✅ **ALWAYS** start with paper trading

### Security Features

**Built-in Protections:**
- ✅ API Authentication (required for all endpoints)
- ✅ Rate Limiting (60 req/min per IP)
- ✅ SQL Injection Protection (parameterized queries)
- ✅ XSS Protection (Content Security Policy)
- ✅ Path Traversal Protection
- ✅ Input Validation (all user inputs)
- ✅ CORS Restrictions (localhost only by default)
- ✅ Security Headers (CSP, X-Frame-Options, etc.)

**Read Full Documentation:**
- [SECURITY_QUICKSTART.md](SECURITY_QUICKSTART.md) - 5-minute setup guide
- [SECURITY.md](SECURITY.md) - Complete security policy

### Built-in Safety Features

**Position Sizing:**
- Max 2% risk per trade (Triple-Threat)
- Max 40% portfolio per order (GridBot)
- Configurable position limits

**Stop Losses:**
- Mean Reversion: 3% stop
- Momentum: 3% stop
- Breakout: 3% stop
- Grid: Range-based stops

**Circuit Breaker:**
- Auto-stops on cascading failures
- Loss threshold monitoring
- Configurable recovery period

**Rate Limiting:**
- Prevents exchange API bans
- Request throttling
- Exponential backoff on errors

**Portfolio Validation:**
- Ensures sufficient balance
- Checks order minimums
- Validates allocation

---

## 🧪 Testing

### Paper Trading (Recommended First)
All bots support paper trading with virtual capital:

```python
# In triple_threat_trader.py
self.trading_mode = TradingMode.PAPER_TRADING
```

**Paper Trading Capital:**
- Crypto bots: $3,000 virtual
- Stock bot: $25,000 virtual

### Backtesting (Coming Soon)
- Historical data replay
- Strategy optimization
- Risk analysis

---

## 🐛 Troubleshooting

### Common Issues

**1. API Errors (401 Unauthorized)**
- Check API keys in `.env` file
- Verify API permissions (reading, trading)
- For Alpaca: Paper trading keys ≠ Live keys

**2. "MATIC/USD not found"**
- MATIC not supported on Kraken/Coinbase
- Remove from watchlist or use different pair

**3. Rate Limiting (429 errors)**
- Reduce scan frequency
- Wait 30-60 minutes
- Use rate_limiter configuration

**4. Market Closed (Stock Bot)**
- US market hours: 9:30 AM - 4:00 PM ET
- Bot automatically sleeps outside hours

**5. WebSocket Disconnects**
- Auto-reconnects after 30 seconds
- Check internet connection
- Verify exchange status

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

**Coding Standards:**
- PEP 8 style guide
- Type hints preferred
- Docstrings for all functions
- Unit tests for new features

---

## 📝 Roadmap

### Phase 1: Core Functionality ✅ (COMPLETE)
- [x] Grid trading bot
- [x] Triple-Threat strategies
- [x] Stock mean reversion
- [x] Multi-exchange support
- [x] Risk management
- [x] Paper trading

### Phase 2: Enhanced Features (IN PROGRESS)
- [ ] Windows desktop app
- [ ] Android mobile app
- [ ] Web dashboard
- [ ] Real-time notifications
- [ ] Advanced analytics

### Phase 3: Advanced (PLANNED)
- [ ] Backtesting engine
- [ ] Custom strategy builder
- [ ] API for third-party integrations
- [ ] Machine learning optimization
- [ ] Multi-account management

---

## 📜 License

MIT License

Copyright (c) 2025 GridBot Chuck

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

## ⚠️ Disclaimer

**IMPORTANT: Trading involves substantial risk of loss.**

- This software is provided for educational and research purposes
- Past performance does not guarantee future results
- You can lose money trading (including all invested capital)
- Only trade with money you can afford to lose
- The authors are not responsible for your trading losses
- This is not financial advice
- Always do your own research (DYOR)
- Test thoroughly with paper trading before risking real money

**Regulatory Compliance:**
- Ensure trading is legal in your jurisdiction
- Comply with local tax laws
- Some features may require licenses (e.g., operating as a money manager)

---

## 📞 Support & Community

- **Issues:** [GitHub Issues](https://github.com/yourusername/gridbot-chuck/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/gridbot-chuck/discussions)
- **Discord:** [Join Community](#) (Coming soon)
- **Twitter:** [@GridBotChuck](#) (Coming soon)

---

## 🙏 Acknowledgments

Built with:
- [ccxt](https://github.com/ccxt/ccxt) - Cryptocurrency exchange trading API
- [alpaca-py](https://github.com/alpacahq/alpaca-py) - Alpaca trading API
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance market data
- Python asyncio - Asynchronous I/O

Special thanks to the open-source trading community.

---

## 📊 Performance History

**Day 1 (December 30, 2025):**
- GridBot Chuck: **+71.6%** ($157 → $269.58) in 8.5 hours
- Strategy: Hedged grid on CC/USD
- Kraken live trading
- Verified transaction history available

**Full performance log:** See [PERFORMANCE.md](PERFORMANCE.md) (coming soon)

---

**Made with ❤️ and Python**

*GridBot Chuck: The Most Honest Bot You'll Ever Meet*

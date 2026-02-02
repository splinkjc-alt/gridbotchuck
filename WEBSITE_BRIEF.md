# GridBot Chuck - Website Design Brief

## 🎯 Project Overview

**Product Name:** GridBot Chuck
**Tagline:** "Professional Cryptocurrency Grid Trading Bot"
**Website URL:** gridbotchuck.netlify.app
**Target Audience:** Cryptocurrency traders, from beginners to advanced

---

## 🏆 What GridBot Chuck Does

GridBot Chuck is an automated cryptocurrency trading bot that uses **grid trading strategies** to profit from market volatility. It places buy and sell orders at preset price intervals, automatically capturing profits as prices fluctuate up and down.

### Key Value Propositions

1. **Set It & Forget It** - Runs 24/7 without manual intervention
2. **Profit From Volatility** - Makes money whether markets go up or down
3. **Smart Pair Selection** - Automatically finds the best coins to trade
4. **Risk Management Built-In** - Stop loss, take profit, circuit breakers
5. **No Coding Required** - Desktop app with setup wizard

---

## ✨ Core Features (For Feature Section)

### 🤖 Automated Grid Trading

- Multiple grid strategies (Simple Grid, Hedged Grid)
- Arithmetic or Geometric spacing options
- Customizable grid levels and ranges

### 📊 Multi-Pair Trading

- Trade multiple cryptocurrency pairs simultaneously
- Auto-select best performing pairs from exchange
- Smart rotation when pairs become stagnant

### 📈 Market Analysis

- Multi-timeframe analysis (1d, 4h, 1h)
- EMA 9/20 crossover signals
- RSI overbought/oversold detection
- Trend strength indicators

### 🎯 Strategy Types

- **HEDGED_GRID** - Pairs buy/sell orders for balanced risk
- **SIMPLE_GRID** - Independent orders at each level
- **EMA Crossover** - Trend-following with moving averages

### 🛡️ Risk Management

- Configurable stop loss & take profit
- Circuit breaker for extreme volatility
- Rate limiting to prevent API issues
- Maximum position sizing

### 🖥️ Beautiful Dashboard

- Real-time price & balance updates
- Order history with P&L tracking
- Grid visualization
- Multi-pair status panel
- Dark/Light theme

### 📱 Easy Setup

- One-click Windows installer
- Step-by-step setup wizard
- API key testing before going live
- Risk profile presets (Conservative/Balanced/Aggressive)

### 🔄 Profit Rotation Engine

- Automatic profit compounding
- Rotates capital to best opportunities
- Configurable rotation thresholds

---

## 📋 Technical Specifications

| Spec | Details |
|------|---------|
| **Supported Exchanges** | Kraken, Binance, Coinbase Pro (via CCXT) |
| **Quote Currencies** | USD, USDT |
| **Trading Modes** | Live, Paper Trading, Backtest |
| **Platform** | Windows Desktop App (Electron) |
| **Backend** | Python with aiohttp async API |
| **Dashboard** | HTML/CSS/JS served at localhost:8080 |
| **Database** | SQLite for order persistence |
| **Logging** | Comprehensive with Grafana integration |

---

## 🎨 Brand Guidelines

### Colors

- **Primary:** Electric Blue (#2563EB) - Trust, technology
- **Secondary:** Emerald Green (#10B981) - Profit, success
- **Accent:** Purple (#8B5CF6) - Premium, innovation
- **Background Dark:** #0F172A (Slate 900)
- **Background Light:** #F8FAFC (Slate 50)
- **Danger/Loss:** Red (#EF4444)
- **Success/Profit:** Green (#22C55E)

### Typography

- **Headlines:** Inter or Poppins (Bold, modern)
- **Body:** Inter or System fonts
- **Monospace:** JetBrains Mono (for code/prices)

### Visual Style

- Modern, clean, minimalist
- Dark mode preferred (crypto aesthetic)
- Gradient accents (blue to purple)
- Card-based layouts with subtle shadows
- Data visualizations with charts/grids

---

## 📄 Website Pages Needed

### 1. **Home/Landing Page**

- Hero section with tagline & CTA
- Feature highlights (4-6 cards)
- "How It Works" 3-step section
- Trading strategies explained
- Dashboard screenshot/preview
- Testimonials (if available)
- Pricing/Download CTA
- FAQ accordion

### 2. **Features Page**

- Detailed feature breakdown
- Comparison table (vs manual trading)
- Screenshots of dashboard
- Strategy explanations

### 3. **Documentation Page**

- Quick Start guide
- Configuration reference
- API integration guide
- Troubleshooting section

### 4. **Download Page**

- Windows installer download
- System requirements
- Installation instructions
- Source code (GitHub link)

### 5. **About Page**

- Project story
- Open source commitment
- Contact information
- GitHub/community links

---

## 📸 Visual Assets Available

### Screenshots Needed

- [ ] Dashboard main view
- [ ] Grid visualization
- [ ] Order history panel
- [ ] Setup wizard steps
- [ ] System tray menu
- [ ] Multi-pair trading view

### Icons/Graphics

- Trading bot mascot (optional)
- Grid pattern illustrations
- Buy/sell arrow graphics
- Exchange logos (Kraken, Binance, Coinbase)

---

## 💰 Monetization Model

Currently **FREE & Open Source** (MIT License)

Potential future options:

- Donations (already have crypto addresses)
- Premium cloud version
- Enterprise support tiers

---

## 🔗 Important Links

- **Live Website:** <https://gridbotchuck.netlify.app>
- **GitHub:** <https://github.com/splinkjc-alt/gridbotchuck>
- **Dashboard (local):** <http://localhost:8080>

---

## 📝 Copy/Content Suggestions

### Hero Headline Options

1. "Trade Smarter, Not Harder"
2. "Automated Grid Trading for Everyone"
3. "Profit From Volatility, Automatically"
4. "Your 24/7 Crypto Trading Assistant"

### Feature Headlines

- "Set Up Once, Trade Forever"
- "Smart Money Management"
- "Real-Time Market Analysis"
- "Professional-Grade Dashboard"

### CTA Buttons

- "Download Free" (primary)
- "View Documentation"
- "Star on GitHub"
- "Watch Demo"

---

## 🎯 Website Goals

1. **Primary:** Get users to download & install the bot
2. **Secondary:** Build community/GitHub stars
3. **Tertiary:** Collect feedback for improvements

---

## 📊 Key Metrics to Display

- Number of GitHub stars
- Trades executed (if trackable)
- Supported exchanges count (3+)
- Trading strategies available (4+)

---

## 🚀 Call to Action Flow

```
Landing → Learn About Features → View Dashboard Demo → Download → Install → Trade!
```

---

## 📱 Responsive Requirements

- Desktop: Full experience with all features
- Tablet: Condensed navigation, stacked cards
- Mobile: Hamburger menu, simplified layout, download CTA prominent

---

## 🔒 Trust Signals

- Open source (full code visibility)
- MIT License (free to use/modify)
- Paper trading mode (test without risk)
- Active GitHub with commits
- Comprehensive documentation

---

## Example Content Blocks

### "How It Works" Section

**Step 1: Install**
Download the Windows installer and follow the setup wizard. Enter your exchange API keys and choose your risk profile.

**Step 2: Configure**
Select your trading pair, set your grid range, and choose between Conservative, Balanced, or Aggressive strategies.

**Step 3: Profit**
The bot runs 24/7, automatically buying low and selling high as prices fluctuate within your grid.

### FAQ Examples

**Q: Is this safe?**
A: Yes! You control your own API keys, can start with paper trading, and have full access to the source code.

**Q: How much money do I need?**
A: You can start with as little as $50-100, though $500+ is recommended for optimal grid spacing.

**Q: Which exchanges are supported?**
A: Currently Kraken, Binance, and Coinbase Pro via the CCXT library.

**Q: Can I lose money?**
A: All trading carries risk. Use stop-loss features and never trade more than you can afford to lose.

---

## 📬 Contact

For website-related questions, the developer can be reached through:

- GitHub Issues
- Project repository

---

*This brief is designed to give a website-building AI all the context needed to create a professional, conversion-focused landing page and website for GridBot Chuck.*

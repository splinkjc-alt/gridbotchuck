# ✅ GridBot Chuck - Quick Start Checklist

Get up and running in 15 minutes or less!

---

## 📋 Pre-Flight Checklist

### System Requirements
- [ ] Python 3.8 or higher installed
- [ ] pip (Python package manager) available
- [ ] Git installed (for cloning the repository)
- [ ] Internet connection

### Exchange Accounts (at least one)
- [ ] **Kraken account** - For crypto grid trading
- [ ] **Coinbase account** - For Triple-Threat crypto trading  
- [ ] **Alpaca account** - For stock trading (free paper trading!)

---

## 🚀 Installation Steps

### Step 1: Clone the Repository
```bash
git clone https://github.com/splinkjc-alt/gridbotchuck.git
cd gridbotchuck
```
- [ ] Repository cloned successfully

### Step 2: Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```
- [ ] Virtual environment created and activated

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```
- [ ] All dependencies installed successfully

### Step 4: Configure API Keys
```bash
# Copy the template
cp .env.example .env

# Edit with your favorite editor
# Windows: notepad .env
# Mac/Linux: nano .env
```
- [ ] `.env` file created from template
- [ ] API keys added to `.env`

---

## 🔑 API Key Setup

### Kraken (Crypto)
1. Log in to [Kraken](https://www.kraken.com)
2. Go to Security → API
3. Create new API key with permissions:
   - [ ] Query Funds
   - [ ] Create & Modify Orders
   - [ ] Query Open/Closed Orders
4. Copy API Key and Secret to `.env`

### Coinbase (Crypto)
1. Log in to [Coinbase Advanced](https://www.coinbase.com/settings/api)
2. Create new API key
3. Permissions needed:
   - [ ] View
   - [ ] Trade
4. Copy API Key and Private Key to `.env`

### Alpaca (Stocks)
1. Sign up at [Alpaca](https://app.alpaca.markets/signup) (free!)
2. Go to Paper Trading dashboard
3. Generate API keys
4. Copy API Key and Secret to `.env`

---

## 📝 .env Configuration

Your `.env` file should look like this:

```env
# Kraken
EXCHANGE_API_KEY=your_kraken_api_key
EXCHANGE_SECRET_KEY=your_kraken_secret

# Coinbase
COINBASE_API_KEY=organizations/your-org/apiKeys/your-key
COINBASE_SECRET_KEY=-----BEGIN EC PRIVATE KEY-----\nyour_key\n-----END EC PRIVATE KEY-----\n

# Alpaca
ALPACA_API_KEY=your_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
```

- [ ] All required API keys configured

---

## 🧪 First Run (Paper Trading)

### Option 1: Triple-Threat Trader (Kraken)
```bash
python triple_threat_trader.py --paper
```
- [ ] Bot starts without errors
- [ ] Sees "Paper Trading Mode" in logs

### Option 2: Triple-Threat Trader (Coinbase)
```bash
python triple_threat_trader_coinbase.py --paper
```
- [ ] Bot starts without errors

### Option 3: Grid Trading Bot
```bash
python main.py --config config/config.json
```
- [ ] Bot starts without errors

### Option 4: Stock Trading Bot
```bash
python stock_trading_assistant.py
```
- [ ] Bot starts without errors

---

## ✅ Verification Checklist

- [ ] Bot connects to exchange successfully
- [ ] Account balance is displayed
- [ ] Price feeds are updating
- [ ] No API authentication errors
- [ ] Paper trading mode confirmed

---

## ⚠️ Common Issues & Fixes

### "Invalid API Key"
- Double-check API key and secret in `.env`
- Ensure no extra spaces or quotes
- Verify API permissions on exchange

### "Module not found" Error
- Make sure you ran `pip install -r requirements.txt`
- Activate your virtual environment

### "Connection Error"
- Check your internet connection
- Verify exchange is not under maintenance
- Check if your IP is whitelisted (if required)

### "Rate Limit Exceeded"
- Wait 30-60 minutes
- Reduce scan frequency in config
- Check rate_limiter settings

---

## 🎯 Next Steps

After successful paper trading:

1. **Monitor for 24-48 hours** - Watch how the bot performs
2. **Review trade logs** - Understand the decisions being made
3. **Adjust thresholds** - Tune parameters if needed
4. **Consider live trading** - When confident, switch to real money

### Going Live
```bash
# In triple_threat_trader.py, change:
self.trading_mode = TradingMode.LIVE_TRADING

# Or use command line:
python triple_threat_trader.py --live
```

---

## 📞 Need Help?

- **Documentation:** [README.md](README.md)
- **Issues:** [GitHub Issues](https://github.com/splinkjc-alt/gridbotchuck/issues)
- **Discussions:** [GitHub Discussions](https://github.com/splinkjc-alt/gridbotchuck/discussions)

---

## 🎉 Success Criteria

You're ready to go when:

- [x] Repository cloned
- [x] Dependencies installed
- [x] API keys configured
- [x] Bot runs without errors
- [x] Paper trading mode verified
- [x] Familiar with logs and output

**Welcome to GridBot Chuck! Happy trading! 🚀**

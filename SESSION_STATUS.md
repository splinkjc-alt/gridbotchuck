# Grid Trading Bot - Session Status

**Last Updated:** December 20, 2025, 2:58 PM EST

## 🎯 Current State

### Exchange & Account

- **Exchange:** Kraken (LIVE mode)
- **Actual Balance:** ~$157 USD + ~0.43 UNI
- **Trading Pair:** UNI/USD @ ~$6.25
- **Grid Range:** $5.96 - $6.58

### Active Orders

- **Buy Limit Order:** 5.12 UNI @ $5.96 (~$30.50 reserved)
- **Available USD:** ~$127 (after reservation)

## ✅ Features Implemented This Session (Dec 20)

### 1. Position Sizing (NEW)

**Config:** `config.json` → `risk_management.position_sizing`

```json
{
  "buy_percent_of_total": 20.0,    // Use 20% of portfolio per buy
  "min_reserve_percent": 10.0,     // Stop buying when USD < 10%
  "sync_balances_on_startup": true
}
```

**Files Modified:**

- `core/order_handling/order_manager.py` - Added `config_manager` param, `_is_below_min_reserve()` method
- `core/grid_management/grid_manager.py` - Modified `get_order_size_for_grid_level()` to use buy_percent
- `core/bot_management/grid_trading_bot.py` - Pass config_manager to OrderManager
- `core/bot_management/multi_pair_manager.py` - Pass config_manager to OrderManager
- `tests/order_handling/test_order_manager.py` - Updated test fixture

### 2. Auto Pair Selection (Previously Working)

- Scans top gainers on startup
- Analyzes with MarketAnalyzer (RSI, trend, score)
- Picks highest scoring bullish pair
- Updates balance_tracker.base_currency on switch

### 3. Balance Tracker Fix (Previously Fixed)

- Fixed: balance_tracker.base_currency now updates when pair switches
- Location: `grid_trading_bot.py` lines ~274-280

## 📊 How Position Sizing Works

1. **Order Size Calculation:**
   - Total portfolio value = USD + (crypto × price)
   - Buy order size = 20% of total / current_price

2. **Minimum Reserve Check:**
   - Before each buy: check if (USD / total) < 10%
   - If below, skip buy and log warning

3. **Example with $157 portfolio:**
   - 20% = ~$31.40 per buy order
   - Can make ~4 buys before hitting 10% reserve
   - At 10% reserve = ~$16 USD minimum held

## 🔧 Config Summary (`config/config.json`)

```json
{
  "exchange": { "name": "kraken", "trading_mode": "live" },
  "pair": { "base_currency": "UNI", "quote_currency": "USD" },
  "trading_settings": {
    "initial_balance": 157,
    "initial_crypto_balance": 0.5
  },
  "grid_strategy": {
    "type": "hedged_grid",
    "num_grids": 3,
    "range": { "bottom": 5.96, "top": 6.58 }
  },
  "risk_management": {
    "position_sizing": {
      "buy_percent_of_total": 20.0,
      "min_reserve_percent": 10.0
    }
  },
  "market_scanner": { "enabled": true }
}
```

## ⚠️ Known Issues

1. **Sell Order Errors:** Bot shows errors when trying to place sell orders because crypto balance (~0.43 UNI) is less than the calculated order size (~5 UNI). This is expected behavior when mostly holding USD.

2. **Balance Sync:** On startup, bot syncs with actual exchange balance (not config values). Config values are just initial defaults.

## 🚀 To Continue

1. **Monitor the bot:** Watch if the $5.96 buy order fills
2. **Check Kraken:** Verify the limit order appears in your orders
3. **Grid will work:** When price drops to $5.96, order fills, then sell order placed at higher grid level

## 📁 Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point |
| `config/config.json` | Configuration |
| `core/order_handling/order_manager.py` | Order placement + position sizing |
| `core/grid_management/grid_manager.py` | Grid levels + order sizing |
| `core/bot_management/grid_trading_bot.py` | Main bot orchestration |

## 🏃 Run Commands

```powershell
# Start bot
cd "c:\Users\splin\OneDrive\Documents\grid_trading_bot-master"
python main.py --config config/config.json

# Kill port 8080 if needed
Get-NetTCPConnection -LocalPort 8080 | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

---

## Previous Session (Dec 19) - Settings Page

### What Was Completed ✅

| `web/dashboard/styles.css` | Added menu-item link styling |
| `web/dashboard/settings.html` | **NEW** - Complete settings page |
| `web/dashboard/settings.css` | **NEW** - Settings page styling |
| `web/dashboard/settings.js` | **NEW** - Settings page JavaScript |
| `core/bot_management/bot_api_server.py` | Added settings routes and handlers |

### To Resume

1. **Check if bot is running**: Look for process on port 8080
2. **If not running**: `python main.py --config config/config.json`
3. **Test settings page**: Navigate to <http://localhost:8080/settings.html>
4. **If still 404**: Check bot_api_server.py for route registration issues

### Quick Commands

```powershell
# Kill any process on port 8080
Get-NetTCPConnection -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }

# Start the bot
python main.py --config config/config.json

# Access dashboard
# http://localhost:8080/index.html

# Access settings (what we're testing)
# http://localhost:8080/settings.html
```

### Settings Page Features

- **Profile Section**: Personal info storage
- **8 Exchange APIs**: Each with API key, secret, optional passphrase, and test button
- **Notifications**: Email alerts, Telegram bot, Discord webhooks with test buttons
- **Trading Defaults**: Default exchange, mode, capital, risk level
- **Security**: 2FA toggle, session timeout, API access toggle
- **Advanced**: Debug mode, clear data, export/import settings

### Notes

- All settings stored in browser localStorage (client-side)
- Exchange testing uses CCXT library on server-side
- Password fields have visibility toggle buttons

# GridBot Chuck - Improvements Implementation Guide

## 🎉 What's New

Your GridBot has been enhanced with professional-grade features:

✅ **Multi-Pair Auto-Switching** - Automatically detects stuck markets and switches to better performing pairs
✅ **Rate Limiting** - Protects against API bans
✅ **Circuit Breaker** - Stops trading during cascading failures
✅ **Database Persistence** - Order history survives restarts
✅ **Enhanced Error Recovery** - Automatic retry logic for failed orders
✅ **Position Size Validation** - Prevents oversized trades
✅ **Performance Monitoring** - Tracks market volatility and trading opportunities

---

## 📋 Quick Start (For Your $55 / 2-Pair Setup)

### 1. Install Dependencies

First, add the new dependency for database support:

```bash
cd "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master"
pip install aiosqlite
```

### 2. Use the Optimized Config

The new config file is already created for your $55 capital setup:

```bash
# Use the small capital multi-pair config
python main.py --config config/config_small_capital_multi_pair.json
```

**This config is optimized for:**
- $55 total capital
- 2 trading pairs maximum
- ~$27.50 per pair
- $20 max order size (within your preference)
- Auto-switching enabled
- Checks every 30 minutes for stuck markets
- Switches to better markets automatically

### 3. Set Your API Keys

Create or update your `.env` file:

```bash
# .env
EXCHANGE_API_KEY=your_kraken_api_key_here
EXCHANGE_SECRET_KEY=your_kraken_secret_here
APPRISE_NOTIFICATION_URLS=discord://webhook_url,mailto://your@email.com
```

### 4. Run the Bot

```bash
python main.py --config config/config_small_capital_multi_pair.json
```

---

## 🔍 How Auto-Switching Works

### Detection Criteria

The bot considers a pair "stuck" if:
- **15-minute volatility < 0.3%** (very low price movement)
- **1-hour volatility < 0.8%** (minimal price action)
- **No trades for 2+ hours** (no order fills)

### Auto-Switch Process

1. **Every 30 minutes** (configurable), bot checks all active pairs
2. If a pair is stuck for **2 consecutive checks** (confirmation)
3. Bot scans candidate pairs for better opportunities
4. **Switches** to pair with 30%+ better performance score
5. **60-minute cooldown** before next switch (prevents rapid switching)

### Candidate Pairs

Default candidates (edit in config if needed):
- XLM/USD, XRP/USD, DOGE/USD
- MATIC/USD, ADA/USD, ALGO/USD

These are low-price coins suitable for your $20 order size.

---

## 🛡️ Safety Features

### Circuit Breaker

Automatically stops trading if:
- **5 consecutive order failures** occur
- **10% portfolio loss** reached
- Waits **5 minutes** before attempting recovery
- Sends notification when triggered

### Rate Limiting

- Limits API calls to **1 per second** for Kraken
- Prevents temporary exchange bans
- Automatically queues requests during high activity

### Position Size Limits

- No single order exceeds **40% of portfolio**
- Minimum order value: **$5**
- Validates before every order placement

---

## 📊 Database Persistence

All orders are now saved to SQLite database:

### Location
```
data/gridbotchuck.db
```

### View Your Trading History

```python
# Quick script to view history
import asyncio
from core.persistence.order_repository import OrderRepository

async def view_stats():
    repo = OrderRepository()
    await repo.initialize()

    stats = await repo.get_statistics()
    print(f"Total Orders: {stats['total_orders']}")
    print(f"Filled Orders: {stats['filled_orders']}")
    print(f"Total Profit: ${stats['total_profit']:.2f}")
    print(f"Total Fees: ${stats['total_fees']:.2f}")

    # Recent trades
    trades = await repo.get_trade_history(limit=10)
    for trade in trades:
        print(f"{trade['timestamp']}: {trade['side']} {trade['quantity']} @ ${trade['price']}")

asyncio.run(view_stats())
```

---

## 📁 New File Structure

```
grid_trading_bot-master/
├── config/
│   └── config_small_capital_multi_pair.json  # Your optimized config
├── core/
│   ├── bot_management/
│   │   └── enhanced_multi_pair_manager.py    # Auto-switching logic
│   ├── order_handling/
│   │   └── enhanced_order_manager.py         # Retry logic
│   ├── persistence/
│   │   └── order_repository.py               # Database layer
│   ├── risk_management/
│   │   ├── circuit_breaker.py                # Safety shutdown
│   │   └── rate_limiter.py                   # API throttling
│   └── validation/
│       └── enhanced_order_validator.py       # Position limits
├── strategies/
│   └── pair_performance_monitor.py           # Market analyzer
└── data/
    └── gridbotchuck.db                       # Order history (auto-created)
```

---

## ⚙️ Configuration Options

### Multi-Pair Settings

```json
"multi_pair": {
  "enabled": true,
  "max_pairs": 2,                      # Maximum concurrent pairs
  "min_balance_per_pair": 20.0,        # Minimum $ per pair
  "balance_split": "equal",            # How to split capital
  "auto_select": true,                 # Auto-select pairs using scanner
  "auto_switch": {
    "enabled": true,                   # Enable auto-switching
    "check_interval_minutes": 30,      # How often to check
    "min_stuck_checks_before_switch": 2,  # Confirmations needed
    "switch_cooldown_minutes": 60,     # Wait between switches
    "candidate_pairs": [               # Pairs to consider
      "XLM/USD", "XRP/USD", "DOGE/USD",
      "MATIC/USD", "ADA/USD", "ALGO/USD"
    ]
  }
}
```

### Circuit Breaker

```json
"risk_management": {
  "circuit_breaker": {
    "enabled": true,
    "max_consecutive_failures": 5,     # Failures before shutdown
    "max_loss_percent": 10,            # % loss before shutdown
    "recovery_timeout_minutes": 5      # Wait before retry
  }
}
```

### Grid Strategy for $27.50 Per Pair

```json
"grid_strategy": {
  "type": "simple_grid",
  "spacing": "geometric",              # Better for volatile coins
  "num_grids": 4,                      # 4 levels = ~$20 orders
  "range": {
    "top": 0.15,                       # Adjust based on current price
    "bottom": 0.11
  },
  "order_size_percent": 35             # ~35% of $27.50 = ~$9.50 per order
}
```

---

## 📈 Monitoring & Alerts

### Dashboard

View bot status at: `http://localhost:8080`

Shows:
- Active pairs and performance
- Auto-switch history
- Circuit breaker status
- Order history
- P&L by pair

### Notifications

Configure in `.env`:

```bash
# Discord webhook
APPRISE_NOTIFICATION_URLS=discord://webhook_id/webhook_token

# Email
APPRISE_NOTIFICATION_URLS=mailto://smtp_user:smtp_pass@smtp.gmail.com?to=you@email.com

# Multiple (comma-separated)
APPRISE_NOTIFICATION_URLS=discord://...,mailto://...
```

You'll get notified for:
- Pair switches
- Circuit breaker events
- Order failures
- Significant profits/losses

---

## 🔧 Advanced Usage

### Manually Switch Pairs

```python
# If you want to override auto-switching
from core.bot_management.enhanced_multi_pair_manager import EnhancedMultiPairManager

# In your running bot
await multi_pair_manager.manually_switch_pair("XLM/USD", "XRP/USD")
```

### View Performance Report

```python
# Get detailed performance metrics
report = multi_pair_manager.get_performance_report()
print(json.dumps(report, indent=2))
```

### Adjust Detection Thresholds

Edit `strategies/pair_performance_monitor.py`:

```python
class PairPerformanceMonitor:
    # Make more/less sensitive to stuck markets
    MIN_VOLATILITY_15M = 0.3  # Increase = less sensitive
    MIN_VOLATILITY_1H = 0.8   # Decrease = more sensitive
```

---

## 🐛 Troubleshooting

### Bot keeps switching pairs

**Solution**: Increase `switch_cooldown_minutes` or `min_stuck_checks_before_switch`

```json
"auto_switch": {
  "switch_cooldown_minutes": 120,     # Wait 2 hours instead of 1
  "min_stuck_checks_before_switch": 3  # Need 3 confirmations instead of 2
}
```

### Circuit breaker keeps triggering

**Solution**: Check for API issues, increase threshold

```json
"circuit_breaker": {
  "max_consecutive_failures": 10,     # Allow more failures
  "recovery_timeout_minutes": 10      # Wait longer before retry
}
```

### Orders too small for exchange

**Solution**: Reduce number of grids or increase balance

```json
"grid_strategy": {
  "num_grids": 3,                     # Fewer grids = larger orders
  "order_size_percent": 40            # Larger % of balance
}
```

### Database errors

**Solution**: Ensure data directory exists

```bash
mkdir -p data
chmod 755 data
```

---

## 📊 Performance Optimization Tips

### For $55 Capital

1. **Use 2 pairs maximum** - Enough diversification without spreading too thin
2. **Stick to low-price coins** - More units per order for grid trading
3. **Use 3-4 grid levels** - Keeps order sizes above exchange minimums
4. **Enable auto-switching** - Maximizes trading opportunities

### Best Pairs for Small Capital

**Ideal: $0.10 - $2.00 price range**

- XLM/USD (~$0.10-0.15)
- DOGE/USD (~$0.05-0.10)
- XRP/USD (~$0.30-0.60)
- ADA/USD (~$0.20-0.50)

**Avoid: > $10 prices** (BTC, ETH) - Order sizes too small

---

## 🎯 Expected Results

### With Auto-Switching Enabled

- **More active trading** - Switches away from dead markets
- **Better fills** - Targets volatile pairs
- **Reduced downtime** - Always in moving markets

### Performance Metrics to Track

```python
# View in dashboard or database
- Total trades per day (aim for 10-20)
- Fill rate (aim for > 70%)
- Average profit per trade
- Time in stuck markets (should decrease)
```

---

## 📝 Maintenance

### Daily
- Check dashboard for pair performance
- Review circuit breaker status

### Weekly
- Review auto-switch history
- Adjust candidate pairs if needed
- Check database size

### Monthly
- Review overall P&L
- Optimize grid ranges based on actual price movements
- Clean up old database records:

```python
from core.persistence.order_repository import OrderRepository
repo = OrderRepository()
await repo.initialize()
await repo.cleanup_old_orders(days=30)  # Keep last 30 days
```

---

## 🚀 Next Steps

1. **Test in Paper Trading First**
   ```json
   "exchange": {
     "trading_mode": "paper"
   }
   ```

2. **Start with 1 Pair**
   ```json
   "multi_pair": {
     "max_pairs": 1
   }
   ```

3. **Monitor for 24 Hours**
   - Check auto-switching behavior
   - Verify order sizes are correct
   - Ensure no circuit breaker triggers

4. **Gradually Add Second Pair**
   ```json
   "multi_pair": {
     "max_pairs": 2
   }
   ```

5. **Fine-tune Based on Results**
   - Adjust volatility thresholds
   - Modify grid ranges
   - Update candidate pairs list

---

## 💡 Tips for Success

1. **Let it run for a full week** before judging performance
2. **Don't override auto-switching too often** - Trust the algorithm
3. **Keep candidate pairs list updated** - Remove dead coins, add new ones
4. **Monitor exchange fees** - High-frequency trading increases costs
5. **Set realistic profit targets** - 1-3% per day is excellent for grid trading

---

## 📞 Support

- Check logs: `logs/gridbotchuck.log`
- Database query: See examples above
- GitHub Issues: https://github.com/splinkjc-alt/gridbotchuck/issues

---

## 🎉 You're All Set!

Your GridBot Chuck is now equipped with enterprise-grade features. Happy trading! 🚀

**Remember**: Start small, test thoroughly, and scale gradually.

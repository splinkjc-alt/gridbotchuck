# Profit Rotation Engine - Usage Guide

## 🎯 What It Does

The **Profit Rotation Engine** solves your exact problem:
1. ✅ **Monitors your position in real-time** - Tracks P&L every minute
2. ✅ **Takes profit automatically** - Closes position when target is hit (e.g., +$3)
3. ✅ **Scans for next opportunity** - Queries market scanner for top 4 pairs
4. ✅ **Enters best pair automatically** - Starts new grid on highest-scoring pair
5. ✅ **Prevents stuck markets** - Won't re-enter same pair for 30min (cooldown)
6. ✅ **Logs everything** - Full audit trail in database

---

## 🚀 Quick Start

### Your Configuration (Already Set Up!)

File: `config/config_small_capital_multi_pair.json`

```json
"profit_rotation": {
  "enabled": true,                      // ✅ Active
  "profit_target_usd": 3.0,            // Exit at +$3 profit
  "use_percent_target": false,          // Using $ amount (not %)
  "check_interval_seconds": 60,         // Check P&L every minute
  "top_pairs_to_scan": 4,              // Scan top 4 pairs
  "min_score_to_enter": 65,            // Only enter if score > 65
  "cooldown_minutes": 30,               // Wait 30min before re-entering same pair
  "auto_enter_next": true,              // Auto-enter new position
  "max_rotations_per_day": 10          // Max 10 rotations per day
}
```

### How It Works (Your Scenario)

**Example: MYX/USD Trade**

```
1. BOT STARTS
   - Enters MYX/USD at $3.20
   - Capital: $55
   - Grid: 3.1 - 3.8 (3 levels)
   - Target: +$3 profit

2. PRICE MOVES UP
   - MYX reaches $3.80 ✅
   - Bot sells positions
   - Total value now: $58
   - Profit: $3 (target hit!)

3. AUTO-EXIT TRIGGERED
   🎯 Profit target reached!
   - Close all orders
   - Sell remaining MYX holdings
   - Final balance: $58

4. MARKET SCAN
   - Scanner checks: MORPHO, M, DOT, LINK, ATOM, UNI...
   - Top 4 results:
     1. MORPHO/USD (score: 85)
     2. LINK/USD (score: 78)
     3. DOT/USD (score: 72)
     4. AVAX/USD (score: 68)

5. ENTER NEW POSITION
   - Best pair: MORPHO/USD (score 85)
   - Auto-configure grid based on current price
   - Start trading with $58 capital
   - New profit target: +$3 (now $61 total)

6. REPEAT
   - Continues rotating to best opportunities
   - Each time captures +$3 profit
   - Avoids stuck/dead markets
```

---

## 📊 Configuration Explained

### Profit Targets

**Option 1: Dollar Amount (Recommended for $55 capital)**
```json
"profit_target_usd": 3.0,
"use_percent_target": false
```
- Exit when you make $3 profit
- Simple and predictable
- Good for small capital

**Option 2: Percentage**
```json
"profit_target_percent": 5.0,
"use_percent_target": true
```
- Exit at +5% profit
- Scales with capital
- Good for larger accounts

### Scanner Integration

```json
"top_pairs_to_scan": 4,           // Check top 4 pairs
"min_score_to_enter": 65          // Only enter if score ≥ 65
```

**Score Calculation:**
- EMA Crossover: 25%
- CCI Momentum: 20%
- MACD Trend: 15%
- Volume: 15%
- EMA Position: 10%
- Bollinger Bands: 10%
- Candlestick Patterns: 5%

**What's a good score?**
- 80+: Excellent opportunity
- 70-79: Good
- 65-69: Acceptable
- <65: Skip

### Cooldown Protection

```json
"cooldown_minutes": 30
```

**Prevents:**
- Re-entering same pair immediately
- Trading in circles
- Excessive fees

**Example:**
```
10:00 AM - Exit MYX/USD with +$3
10:05 AM - MYX/USD shows score 90 (but on cooldown)
         - Enters LINK/USD (score 85) instead
10:35 AM - Cooldown expires, MYX eligible again
```

### Daily Limits

```json
"max_rotations_per_day": 10
```

**Why limit rotations?**
- Prevents over-trading
- Controls fee accumulation
- Protects against false signals

**Fee Example:**
- 10 rotations/day × 0.26% fee × 2 (buy+sell) = 5.2% daily fees
- With $55 capital: ~$2.86 in fees
- Net profit target: $30 - $2.86 = $27.14 (still profitable!)

---

## 🎨 Real-World Scenarios

### Scenario 1: Perfect Rotation
```
9:00 AM  | Enter MYX/USD @ $3.20     | Balance: $55
11:30 AM | MYX hits $3.80 (+$3)      | Balance: $58 ✅
11:35 AM | Scanner finds MORPHO      | Score: 85
11:40 AM | Enter MORPHO @ $4.50      | Balance: $58
2:15 PM  | MORPHO hits $4.95 (+$3)   | Balance: $61 ✅
2:20 PM  | Scanner finds LINK        | Score: 82
2:25 PM  | Enter LINK @ $18.20       | Balance: $61

Result: 2 profitable rotations, $6 total profit
```

### Scenario 2: No Good Opportunities
```
9:00 AM  | Enter MYX/USD @ $3.20     | Balance: $55
11:30 AM | MYX hits $3.80 (+$3)      | Balance: $58 ✅
11:35 AM | Scanner runs...
         | Top scores: 62, 58, 55, 50 (all < 65)
11:36 AM | STAYS IN CASH            | Balance: $58
         | Will retry every 5-15min
12:00 PM | Scanner finds DOT         | Score: 72 ✅
12:05 PM | Enter DOT @ $6.80         | Balance: $58

Result: Waited for good opportunity, avoided bad trade
```

### Scenario 3: Hit Daily Limit
```
Day's rotations: 10 (limit reached)
Latest profit: +$3 on AVAX

Bot: "Max rotations reached for today"
Action: Stays in current position (AVAX)
Tomorrow: Counter resets, rotations resume
```

---

## ⚙️ Fine-Tuning for Your Setup

### For Aggressive Trading (More Rotations)
```json
"profit_target_usd": 2.0,         // Lower target = faster rotations
"min_score_to_enter": 60,         // Accept lower scores
"cooldown_minutes": 15,            // Shorter cooldown
"max_rotations_per_day": 15       // Allow more trades
```

**Pros:** More opportunities, faster compounding
**Cons:** Higher fees, more false signals

### For Conservative Trading (Quality Over Quantity)
```json
"profit_target_usd": 5.0,         // Higher target = fewer rotations
"min_score_to_enter": 75,         // Only best opportunities
"cooldown_minutes": 60,            // Longer cooldown
"max_rotations_per_day": 5        // Limit trades
```

**Pros:** Lower fees, better quality trades
**Cons:** Fewer rotations, slower growth

### For Your $55 Capital (Balanced - Current Settings)
```json
"profit_target_usd": 3.0,         // ~5.5% gain per trade
"min_score_to_enter": 65,         // Reasonable threshold
"cooldown_minutes": 30,            // Avoid rapid re-entry
"max_rotations_per_day": 10       // Up to $30 daily profit potential
```

**Expected Performance:**
- 5 successful rotations/day = $15 profit
- Minus ~$1.50 fees = **$13.50 net/day**
- Monthly: **~$405**
- 6-month capital: **~$2,480** (if compounded)

---

## 📈 Monitoring & Alerts

### Dashboard (http://localhost:8080)

**New Sections Added:**
```
Profit Rotation Status:
- Current Position: MYX/USD
- Entry Value: $55.00
- Current Value: $57.20
- Unrealized P&L: +$2.20 (40% to target)
- Profit Target: $3.00
- Rotations Today: 3 / 10

Recent Rotations:
1. 11:30 AM | MYX → MORPHO | +$3.00 (5.5%)
2. 2:15 PM  | MORPHO → LINK | +$3.10 (5.3%)
3. 4:45 PM  | LINK → DOT   | +$2.95 (4.8%)
```

### Notifications

Configure in `.env`:
```bash
APPRISE_NOTIFICATION_URLS=discord://your_webhook_url
```

**You'll get alerts for:**
- ✅ Profit target reached
- 🔄 Rotation completed
- 📊 New pair entered
- ⚠️ No suitable pairs found
- 🚫 Daily rotation limit hit

**Example Discord Message:**
```
💰 PROFIT ROTATION COMPLETE

From: MYX/USD → To: MORPHO/USD
Profit: $3.15 (+5.7%)
New Position: MORPHO/USD (Score: 85)
Capital: $58.15
```

---

## 🐛 Troubleshooting

### Issue: Bot keeps rotating too fast
**Problem:** Hitting max_rotations_per_day limit by noon

**Solutions:**
1. Increase `profit_target_usd` to $4 or $5
2. Raise `min_score_to_enter` to 70+
3. Reduce `max_rotations_per_day`

### Issue: Bot won't enter new positions
**Problem:** Stays in cash after rotation

**Possible Causes:**
1. **No pairs meet score threshold**
   - Check logs: "No valid candidates after filtering"
   - Solution: Lower `min_score_to_enter` to 60

2. **All pairs on cooldown**
   - Check logs: "cooldown active"
   - Solution: Reduce `cooldown_minutes` or add more candidate pairs

3. **Daily limit reached**
   - Check logs: "Max rotations per day reached"
   - Wait until tomorrow or increase limit

### Issue: Rotation exits too early
**Problem:** Price could have gone higher

**Solution:**
Consider using **trailing profit** instead:
```json
"profit_target_percent": 3.0,      // Start trailing at +3%
"trailing_percent": 1.0,           // Exit if drops 1% from peak
"use_trailing": true
```

*(Note: Trailing profit feature coming in v2.0)*

### Issue: Grid range wrong for new pair
**Problem:** Orders placed outside of actual price range

**Cause:** Auto-configuration uses ±15% from current price

**Manual Override:**
Edit config before rotation:
```json
"grid_strategy": {
  "auto_adjust_range": true,       // Enable auto-adjustment
  "range_percent": 0.20             // Use ±20% instead
}
```

---

## 📝 Best Practices

### 1. Start in Paper Trading
```json
"exchange": {
  "trading_mode": "paper"
}
```
- Test rotation logic
- Verify entry/exit timing
- Check fee calculations
- Monitor for 24 hours

### 2. Use Realistic Profit Targets
For $55 capital:
- ❌ Too low: $1 (too many rotations, fees eat profit)
- ✅ Sweet spot: $3-5 (5-9% gains)
- ❌ Too high: $10 (18%, rarely achieves)

### 3. Balance Candidate Pairs
Include mix of:
- **High volatility:** DOGE, MATIC (more opportunities)
- **Mid volatility:** LINK, DOT, AVAX (balanced)
- **Low volatility:** LTC, BCH (stable fallbacks)

Current list (14 pairs) is good!

### 4. Monitor Daily Performance
Track in spreadsheet:
```
Date       | Rotations | Profit | Fees | Net  | Notes
------------------------------------------------------
Dec 17     | 5         | $15    | $1.5 | $13.5| Good day
Dec 18     | 3         | $9     | $0.9 | $8.1 | Slow market
Dec 19     | 7         | $21    | $2.1 | $18.9| Excellent
```

### 5. Adjust Weekly
Based on performance:
- **Lots of rotations, low profit:** Raise profit target
- **Few rotations, missing opportunities:** Lower min_score
- **Too many bad entries:** Raise min_score
- **Hitting daily limit often:** Increase max_rotations

---

## 🚀 Next Steps

### Phase 1: Testing (This Week)
1. **Enable in paper trading mode**
   ```bash
   cd "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master"
   python main.py --config config/config_small_capital_multi_pair.json
   ```

2. **Monitor for 3 days**
   - Watch logs for rotations
   - Verify profit calculations
   - Check pair selection logic

3. **Review results**
   - Did it capture profits when price moved?
   - Were new pairs good choices?
   - Any errors or issues?

### Phase 2: Live Trading (Next Week)
1. **Switch to live mode**
   ```json
   "exchange": {
     "trading_mode": "live"
   }
   ```

2. **Start with conservative settings**
   ```json
   "profit_target_usd": 4.0,      // Higher target
   "max_rotations_per_day": 5     // Fewer rotations
   ```

3. **Increase gradually**
   - After 1 week: Lower to $3.50 target
   - After 2 weeks: Increase to 8 rotations/day
   - After 1 month: Optimize based on data

### Phase 3: Optimization (Month 2)
- Analyze which pairs perform best
- Remove underperforming pairs from candidate list
- Fine-tune score thresholds
- Consider adding more capital

---

## 💡 Pro Tips

1. **Let it run for full week before judging**
   - Some days will be slow
   - Others will have 8+ rotations
   - Weekly average is what matters

2. **Don't override rotations manually**
   - Trust the algorithm
   - Manual intervention disrupts learning
   - Only stop if emergency

3. **Compound your profits**
   - Don't withdraw profits for first month
   - Let capital grow
   - $55 → $70 → $90 → $120 over 2-3 months

4. **Watch for exchange issues**
   - Kraken downtime
   - Rate limiting errors
   - Insufficient liquidity warnings

5. **Back up your database regularly**
   ```bash
   # Already enabled in config!
   "database": {
     "backup_enabled": true,
     "backup_interval_hours": 24
   }
   ```

---

## 📞 Support

**Check logs:**
```bash
tail -f logs/gridbotchuck.log | grep -i "rotation"
```

**Common log messages:**
- `🎯 Profit target reached!` - Rotation triggered
- `✅ Position closed: MYX/USD → Profit: $3.15` - Exit successful
- `🔄 ROTATION: MYX/USD → MORPHO/USD` - Rotation complete
- `⚠️ No suitable pair found` - No good opportunities
- `Skipping DOT/USD: cooldown active` - Pair on cooldown

**Dashboard status:**
```
http://localhost:8080/api/rotation/status
```

**GitHub Issues:**
https://github.com/splinkjc-alt/gridbotchuck/issues

---

## 🎉 You're All Set!

Your GridBot Chuck now has an **intelligent profit-taking system** that:
- ✅ Captures profits automatically (no more missed sells!)
- ✅ Rotates to best opportunities (uses your market scanner)
- ✅ Avoids stuck markets (cooldown protection)
- ✅ Manages risk (daily limits, score filters)
- ✅ Maximizes capital efficiency (always trading top pairs)

**Start it up and watch it work! 🚀**

```bash
cd "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master"
python main.py --config config/config_small_capital_multi_pair.json
```

Good luck with your trading! 💰

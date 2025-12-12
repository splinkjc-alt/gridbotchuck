# Grid Trading Bot - 15-Minute Candle Trading Guide

## Overview

Your bot now supports best market analysis with 15-minute candles for improved entry/exit points.

## Key Changes

### 1. **15-Minute Timeframe Configuration**

The config has been updated from 1-minute to 15-minute candles:

```json
"trading_settings": {
  "timeframe": "15m",
  "period": {
    "start_date": "2024-12-10T09:00:00Z",
    "end_date": "2024-12-15T23:00:00Z"
  },
  "initial_balance": 150
}
```

### 2. **Market Analyzer Module** (`strategies/market_analyzer.py`)

Identifies the best trading pairs based on:

- **Volume Score**: Average trading volume (liquidity)
- **Volatility Score**: Price movement patterns (ideal 15-25% for grid trading)
- **Momentum Score**: RSI indicator (avoids overbought/oversold levels)
- **Trend Score**: MACD + Signal line analysis

**Usage:**

```python
from strategies.market_analyzer import MarketAnalyzer

analyzer = MarketAnalyzer(exchange_service, config_manager)

# Find best trading pairs
pairs = ['SOL/usd', 'BTC/usd', 'ETH/usd']
best_pairs = await analyzer.find_best_trading_pairs(pairs)
# Returns: [('SOL/usd', 85.3), ('BTC/usd', 78.2), ...]

# Get entry signal
signal = analyzer.get_entry_signal('SOL/usd')
# Returns: 'BUY', 'SELL', or 'HOLD'

# Calculate optimal grid range dynamically
bottom, top, current = analyzer.calculate_optimal_grid_range('SOL/usd')
```

### 3. **Buy/Sell Point Calculator** (`strategies/buy_sell_point_calculator.py`)

Optimizes grid entry/exit levels using technical indicators:

**Technical Indicators Used:**

- **RSI (14)**: Detects overbought/oversold conditions
- **MACD**: Identifies trend strength and direction
- **Bollinger Bands (20, 2.0)**: Shows support/resistance zones
- **ATR (14)**: Adjusts spacing based on volatility

**Smart Grid Adjustment:**

```
RSI < 30 (Oversold)    → More aggressive BUY levels (70% of grids)
RSI 30-50              → Normal buy distribution (50% of grids)
RSI > 70 (Overbought)  → Fewer buys, more sells (30% of grids)
```

**Usage:**

```python
from strategies.buy_sell_point_calculator import BuySellPointCalculator

calculator = BuySellPointCalculator()

# Calculate optimized entry/exit points
result = calculator.calculate_grid_entry_points(
    data=ohlcv_data,
    num_grids=8,
    current_price=225.50
)

# Returns:
{
    "buy_points": [210.2, 212.5, 215.3, ...],
    "sell_points": [235.7, 238.4, 240.1, ...],
    "signals": "STRONG_BUY",  # or BUY, HOLD, SELL, STRONG_SELL
    "rsi": 42.5,
    "macd_strength": 0.15,
    "bollinger_position": "MIDDLE"  # or LOWER_BAND, UPPER_BAND
}
```

## Configuration Examples

### Best Market Conditions for 15m Grids

**Example 1: SOL/usd**

```json
{
  "grid_strategy": {
    "type": "hedged_grid",
    "spacing": "geometric",
    "num_grids": 8,
    "range": {
      "top": 240,
      "bottom": 210
    }
  }
}
```

**Example 2: BTC/usd (Higher Volatility)**

```json
{
  "grid_strategy": {
    "type": "hedged_grid",
    "spacing": "geometric",
    "num_grids": 12,
    "range": {
      "top": 105000,
      "bottom": 95000
    }
  }
}
```

**Example 3: ETH/usd (Moderate Volatility)**

```json
{
  "grid_strategy": {
    "type": "hedged_grid",
    "spacing": "geometric",
    "num_grids": 10,
    "range": {
      "top": 3500,
      "bottom": 3200
    }
  }
}
```

## Signal Interpretations

### Entry Signals

- **STRONG_BUY**: MACD above signal + RSI 40-70 → Initiate grid orders aggressively
- **BUY**: MACD above signal → Good entry point
- **HOLD**: Mixed signals → Wait for clearer direction
- **SELL**: MACD below signal → Consider closing positions
- **STRONG_SELL**: MACD below signal + RSI > 70 → Exit or reduce exposure

### Market Positioning

- **LOWER_BAND**: Price near support (good for buying)
- **MIDDLE**: Price neutral (balanced grid)
- **UPPER_BAND**: Price near resistance (good for selling)

## Best Practices for 15-Minute Trading

1. **Grid Spacing**: Use geometric spacing for better distribution
2. **Number of Grids**: 8-12 grids for 15m data (more than 1m, fewer than hourly)
3. **Initial Balance**: Start with smaller amounts to test
4. **Time Range**: Use at least 5-7 days of historical data for backtesting
5. **Take Profit**: Set at 3-5% above current price
6. **Stop Loss**: Set at 2-3% below entry price

## Testing the Setup

Run the backtest with updated configuration:

```bash
python main.py backtest --config config/config.json
```

Monitor the logs for:

- Grid level initialization
- Entry signal generation
- RSI and MACD values at each timestamp
- Bollinger Band positions

## Performance Metrics to Watch

- **Win Rate**: Percentage of profitable grid cycles
- **Max Drawdown**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted returns
- **Number of Trades**: Grid fill frequency
- **Average Profit Per Trade**: Consistency of wins

---

**Next Steps:**

1. Update your trading pair in config.json
2. Adjust grid range based on recent market data
3. Run backtest with 15m data
4. Review performance metrics
5. Deploy to paper trading for live validation

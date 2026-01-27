"""
Comprehensive Backtester - Test all timeframe/indicator combinations
=====================================================================

Tests VET and PEPE with:
- Timeframes: 3m, 5m, 15m, 30m
- Indicators: RSI only, RSI+BB, RSI+EMA, RSI+MACD, Full
- Strategies: Grid, Mean Reversion, Momentum
"""

import asyncio
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
TIMEFRAMES = ["3m", "5m", "15m", "30m"]
ASSETS = ["VET/USD", "PEPE/USD"]
LOOKBACK_DAYS = 30  # 30 days of history

# Indicator parameters
INDICATOR_CONFIGS = {
    "rsi_only": {
        "name": "RSI Only",
        "use_rsi": True,
        "use_bb": False,
        "use_ema": False,
        "use_macd": False,
    },
    "rsi_bb": {
        "name": "RSI + BB",
        "use_rsi": True,
        "use_bb": True,
        "use_ema": False,
        "use_macd": False,
    },
    "rsi_ema": {
        "name": "RSI + EMA",
        "use_rsi": True,
        "use_bb": False,
        "use_ema": True,
        "use_macd": False,
    },
    "rsi_macd": {
        "name": "RSI + MACD",
        "use_rsi": True,
        "use_bb": False,
        "use_ema": False,
        "use_macd": True,
    },
    "full": {
        "name": "Full Suite",
        "use_rsi": True,
        "use_bb": True,
        "use_ema": True,
        "use_macd": True,
    },
}

# Strategy types
STRATEGIES = ["grid", "mean_reversion", "momentum"]


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all technical indicators."""
    # RSI
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    # Bollinger Bands
    df["bb_mid"] = df["close"].rolling(window=20).mean()
    df["bb_std"] = df["close"].rolling(window=20).std()
    df["bb_upper"] = df["bb_mid"] + (df["bb_std"] * 2)
    df["bb_lower"] = df["bb_mid"] - (df["bb_std"] * 2)

    # EMAs
    df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
    df["ema_20"] = df["close"].ewm(span=20, adjust=False).mean()
    df["ema_50"] = df["close"].ewm(span=50, adjust=False).mean()

    # MACD
    ema_12 = df["close"].ewm(span=12, adjust=False).mean()
    ema_26 = df["close"].ewm(span=26, adjust=False).mean()
    df["macd"] = ema_12 - ema_26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"] = df["macd"] - df["macd_signal"]

    # Volume ratio
    df["vol_avg"] = df["volume"].rolling(window=20).mean()
    df["vol_ratio"] = df["volume"] / df["vol_avg"]

    return df


def check_buy_signal(row, config: dict, strategy: str) -> bool:
    """Check if buy conditions are met based on config and strategy."""
    signals = []

    if config["use_rsi"]:
        if strategy == "grid":
            signals.append(row["rsi"] < 35)  # Oversold
        elif strategy == "mean_reversion":
            signals.append(row["rsi"] < 30)  # More oversold
        elif strategy == "momentum":
            signals.append(30 < row["rsi"] < 50)  # Rising from oversold

    if config["use_bb"]:
        signals.append(row["close"] <= row["bb_lower"])  # Price at lower band

    if config["use_ema"]:
        if strategy == "momentum":
            signals.append(row["ema_9"] > row["ema_20"])  # Bullish crossover
        else:
            signals.append(row["close"] < row["ema_20"])  # Below EMA (mean reversion)

    if config["use_macd"]:
        if strategy == "momentum":
            signals.append(row["macd"] > row["macd_signal"])  # MACD bullish
        else:
            signals.append(row["macd_hist"] < 0)  # Negative histogram (oversold)

    # Need at least one signal to trigger
    if not signals:
        return False

    # For grid/mean_reversion: ALL signals must be true (more conservative)
    # For momentum: ANY signal can trigger (more aggressive)
    if strategy == "momentum":
        return any(signals)
    else:
        return all(signals)


def check_sell_signal(
    row, entry_price: float, config: dict, strategy: str
) -> tuple[bool, str]:
    """Check if sell conditions are met. Returns (should_sell, reason)."""
    pct_change = ((row["close"] - entry_price) / entry_price) * 100

    # Take profit levels by strategy
    if strategy == "grid":
        take_profit = 3.0
        stop_loss = -2.5
    elif strategy == "mean_reversion":
        take_profit = 4.0
        stop_loss = -3.0
    elif strategy == "momentum":
        take_profit = 5.0
        stop_loss = -3.5
    else:
        take_profit = 3.0
        stop_loss = -2.5

    # Take profit
    if pct_change >= take_profit:
        return True, "take_profit"

    # Stop loss
    if pct_change <= stop_loss:
        return True, "stop_loss"

    # Indicator-based exits
    if config["use_rsi"] and row["rsi"] > 70:
        return True, "rsi_overbought"

    if config["use_bb"] and row["close"] >= row["bb_upper"]:
        return True, "bb_upper"

    if config["use_ema"] and strategy == "momentum":
        if row["ema_9"] < row["ema_20"]:  # Bearish crossover
            return True, "ema_bearish"

    if config["use_macd"] and strategy == "momentum":
        if row["macd"] < row["macd_signal"]:  # MACD bearish
            return True, "macd_bearish"

    return False, ""


def backtest(df: pd.DataFrame, config: dict, strategy: str) -> dict:
    """Run backtest on data with given config and strategy."""
    initial_balance = 1000.0
    balance = initial_balance
    position = 0.0
    entry_price = 0.0
    trades = []

    # Skip first 50 rows to let indicators stabilize
    for i in range(50, len(df)):
        row = df.iloc[i]

        # Skip if indicators not ready
        if pd.isna(row["rsi"]) or pd.isna(row["bb_lower"]):
            continue

        # Not in position - check for buy
        if position == 0:
            if check_buy_signal(row, config, strategy):
                # Buy with full balance
                position = balance / row["close"]
                entry_price = row["close"]
                balance = 0
                trades.append(
                    {
                        "type": "BUY",
                        "time": row["timestamp"],
                        "price": row["close"],
                        "amount": position,
                    }
                )

        # In position - check for sell
        else:
            should_sell, reason = check_sell_signal(row, entry_price, config, strategy)
            if should_sell:
                # Sell all
                balance = position * row["close"]
                pct_change = ((row["close"] - entry_price) / entry_price) * 100
                trades.append(
                    {
                        "type": "SELL",
                        "time": row["timestamp"],
                        "price": row["close"],
                        "amount": position,
                        "pct_change": pct_change,
                        "reason": reason,
                    }
                )
                position = 0
                entry_price = 0

    # Close any open position at end
    if position > 0:
        final_price = df.iloc[-1]["close"]
        balance = position * final_price
        pct_change = ((final_price - entry_price) / entry_price) * 100
        trades.append(
            {
                "type": "SELL",
                "time": df.iloc[-1]["timestamp"],
                "price": final_price,
                "amount": position,
                "pct_change": pct_change,
                "reason": "end_of_test",
            }
        )

    # Calculate results
    final_balance = balance if balance > 0 else position * df.iloc[-1]["close"]
    total_return = ((final_balance - initial_balance) / initial_balance) * 100

    sell_trades = [t for t in trades if t["type"] == "SELL"]
    wins = len([t for t in sell_trades if t.get("pct_change", 0) > 0])
    losses = len([t for t in sell_trades if t.get("pct_change", 0) <= 0])
    win_rate = (wins / len(sell_trades) * 100) if sell_trades else 0

    return {
        "total_return": total_return,
        "final_balance": final_balance,
        "num_trades": len(sell_trades),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "trades": trades,
    }


async def fetch_ohlcv(exchange, symbol: str, timeframe: str, days: int) -> pd.DataFrame:
    """Fetch OHLCV data from exchange."""
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())

    all_data = []
    while True:
        try:
            data = await exchange.fetch_ohlcv(
                symbol, timeframe, since=since, limit=1000
            )
            if not data:
                break
            all_data.extend(data)
            since = data[-1][0] + 1  # Next millisecond after last candle
            if len(data) < 1000:
                break
            await asyncio.sleep(0.5)  # Rate limit
        except Exception as e:
            print(f"Error fetching {symbol} {timeframe}: {e}")
            break

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(
        all_data, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = (
        df.drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )

    return df


async def run_all_backtests():
    """Run backtests for all combinations."""
    exchange = ccxt.kraken(
        {
            "apiKey": os.getenv("EXCHANGE_API_KEY"),
            "secret": os.getenv("EXCHANGE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    results = []

    try:
        for asset in ASSETS:
            print(f"\n{'='*60}")
            print(f"BACKTESTING: {asset}")
            print(f"{'='*60}")

            for timeframe in TIMEFRAMES:
                print(f"\n--- Timeframe: {timeframe} ---")

                # Fetch data
                df = await fetch_ohlcv(exchange, asset, timeframe, LOOKBACK_DAYS)
                if df.empty:
                    print(f"  No data for {asset} {timeframe}")
                    continue

                print(f"  Loaded {len(df)} candles")

                # Calculate indicators
                df = calculate_indicators(df)

                # Test each indicator combo
                for ind_key, ind_config in INDICATOR_CONFIGS.items():
                    for strategy in STRATEGIES:
                        result = backtest(df, ind_config, strategy)

                        results.append(
                            {
                                "asset": asset,
                                "timeframe": timeframe,
                                "indicators": ind_config["name"],
                                "strategy": strategy,
                                "return_pct": result["total_return"],
                                "num_trades": result["num_trades"],
                                "win_rate": result["win_rate"],
                                "wins": result["wins"],
                                "losses": result["losses"],
                            }
                        )

                        # Print result
                        ret = result["total_return"]
                        emoji = "+" if ret > 0 else ""
                        print(
                            f"  {ind_config['name']:12} + {strategy:15} = {emoji}{ret:6.2f}% ({result['num_trades']} trades, {result['win_rate']:.0f}% win)"
                        )

    finally:
        await exchange.close()

    # Sort by return and show best combos
    results_df = pd.DataFrame(results)

    print("\n" + "=" * 60)
    print("TOP 10 BEST COMBINATIONS")
    print("=" * 60)

    best = results_df.sort_values("return_pct", ascending=False).head(10)
    for _, row in best.iterrows():
        print(
            f"{row['asset']:10} | {row['timeframe']:4} | {row['indicators']:12} | {row['strategy']:15} | {row['return_pct']:+7.2f}% | {row['num_trades']:3} trades | {row['win_rate']:.0f}% win"
        )

    print("\n" + "=" * 60)
    print("TOP 5 FOR VET/USD")
    print("=" * 60)
    vet_best = (
        results_df[results_df["asset"] == "VET/USD"]
        .sort_values("return_pct", ascending=False)
        .head(5)
    )
    for _, row in vet_best.iterrows():
        print(
            f"{row['timeframe']:4} | {row['indicators']:12} | {row['strategy']:15} | {row['return_pct']:+7.2f}% | {row['num_trades']:3} trades | {row['win_rate']:.0f}% win"
        )

    print("\n" + "=" * 60)
    print("TOP 5 FOR PEPE/USD")
    print("=" * 60)
    pepe_best = (
        results_df[results_df["asset"] == "PEPE/USD"]
        .sort_values("return_pct", ascending=False)
        .head(5)
    )
    for _, row in pepe_best.iterrows():
        print(
            f"{row['timeframe']:4} | {row['indicators']:12} | {row['strategy']:15} | {row['return_pct']:+7.2f}% | {row['num_trades']:3} trades | {row['win_rate']:.0f}% win"
        )

    # Save results to file
    results_df.to_csv(
        "D:/gridbotchuck/data/backtest_optimization_results.csv", index=False
    )
    print("\nResults saved to data/backtest_optimization_results.csv")

    return results_df


if __name__ == "__main__":
    print("Starting comprehensive backtest...")
    print(f"Testing: {ASSETS}")
    print(f"Timeframes: {TIMEFRAMES}")
    print(f"Indicator combos: {list(INDICATOR_CONFIGS.keys())}")
    print(f"Strategies: {STRATEGIES}")
    print(f"Lookback: {LOOKBACK_DAYS} days")

    asyncio.run(run_all_backtests())

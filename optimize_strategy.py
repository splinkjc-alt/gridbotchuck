"""
Strategy Optimizer - Test different indicator combos to find best profit.

Tests 20+ strategies on historical data and ranks by performance.
"""
from datetime import UTC, datetime, timedelta

import ccxt
import pandas as pd


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_bollinger_bands(data: pd.Series, period: int = 20, std_dev: int = 2) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Calculate Bollinger Bands."""
    sma = data.rolling(window=period).mean()
    std = data.rolling(window=period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower


def calculate_volume_ratio(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate volume ratio vs average."""
    avg_volume = data.rolling(window=period).mean()
    ratio = data / avg_volume
    return ratio


class Strategy:
    """Defines a trading strategy."""

    def __init__(self, name: str, entry_fn, target_pct: float = 4.0, stop_pct: float = 3.0):
        self.name = name
        self.entry_fn = entry_fn  # Function that returns True/False for entry signal
        self.target_pct = target_pct
        self.stop_pct = stop_pct
        self.trades = []
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0


def backtest_strategy(df: pd.DataFrame, strategy: Strategy) -> Strategy:
    """
    Backtest a strategy on historical data.
    Simulates trades and calculates profit/loss.
    """
    in_trade = False
    entry_price = 0.0
    entry_idx = 0

    for idx in range(len(df)):
        row = df.iloc[idx]

        # Skip if not enough data for indicators
        if pd.isna(row["rsi_14"]) or pd.isna(row["bb_lower"]):
            continue

        # Check for entry signal (not in trade)
        if not in_trade:
            if strategy.entry_fn(row):
                # Enter trade
                in_trade = True
                entry_price = row["close"]
                entry_idx = idx

        # Check for exit signal (in trade)
        else:
            current_price = row["close"]
            pct_change = ((current_price - entry_price) / entry_price) * 100

            # Check if target hit
            if pct_change >= strategy.target_pct:
                # WIN!
                profit = strategy.target_pct
                strategy.wins += 1
                strategy.total_profit += profit
                strategy.trades.append({
                    "entry_time": df.iloc[entry_idx]["timestamp"],
                    "exit_time": row["timestamp"],
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "profit_pct": profit,
                    "result": "WIN"
                })
                in_trade = False

            # Check if stop hit
            elif pct_change <= -strategy.stop_pct:
                # LOSS
                loss = -strategy.stop_pct
                strategy.losses += 1
                strategy.total_profit += loss
                strategy.trades.append({
                    "entry_time": df.iloc[entry_idx]["timestamp"],
                    "exit_time": row["timestamp"],
                    "entry_price": entry_price,
                    "exit_price": current_price,
                    "profit_pct": loss,
                    "result": "LOSS"
                })
                in_trade = False

    return strategy


def optimize_xrp_strategy(hours_lookback: int = 24, exchange_name: str = "kraken"):
    """
    Test multiple strategies on XRP to find the best one.
    """

    # Initialize exchange
    exchange = ccxt.kraken({"enableRateLimit": True})

    # Fetch data
    since = exchange.parse8601((datetime.now(UTC) - timedelta(hours=hours_lookback)).isoformat())
    ohlcv = exchange.fetch_ohlcv("XRP/USD", "5m", since=since, limit=1000)

    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")


    # Calculate indicators
    df["rsi_7"] = calculate_rsi(df["close"], 7)
    df["rsi_14"] = calculate_rsi(df["close"], 14)
    df["rsi_21"] = calculate_rsi(df["close"], 21)
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = calculate_bollinger_bands(df["close"], 20, 2)
    df["volume_ratio"] = calculate_volume_ratio(df["volume"], 20)
    df["price_change_pct"] = df["close"].pct_change() * 100

    # Define strategies to test
    strategies = [
        # Strategy 1: Aggressive RSI(7)
        Strategy(
            "RSI(7) < 25",
            lambda row: row["rsi_7"] < 25,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 2: Conservative RSI(7)
        Strategy(
            "RSI(7) < 30",
            lambda row: row["rsi_7"] < 30,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 3: Moderate RSI(7)
        Strategy(
            "RSI(7) < 35",
            lambda row: row["rsi_7"] < 35,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 4: Aggressive RSI(14)
        Strategy(
            "RSI(14) < 25",
            lambda row: row["rsi_14"] < 25,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 5: Conservative RSI(14)
        Strategy(
            "RSI(14) < 30",
            lambda row: row["rsi_14"] < 30,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 6: Moderate RSI(14)
        Strategy(
            "RSI(14) < 35",
            lambda row: row["rsi_14"] < 35,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 7: Current bot (RSI < 45)
        Strategy(
            "RSI(14) < 45 [Current Bot]",
            lambda row: row["rsi_14"] < 45,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 8: Bollinger Band touch
        Strategy(
            "Price touches BB lower",
            lambda row: row["close"] <= row["bb_lower"],
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 9: Combo - RSI + BB
        Strategy(
            "RSI(7)<30 + BB touch",
            lambda row: row["rsi_7"] < 30 and row["close"] <= row["bb_lower"],
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 10: Combo - RSI + Volume
        Strategy(
            "RSI(7)<30 + Volume>1.5x",
            lambda row: row["rsi_7"] < 30 and row["volume_ratio"] > 1.5,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 11: Volume spike only
        Strategy(
            "Volume spike > 2x",
            lambda row: row["volume_ratio"] > 2.0,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 12: Large red candle
        Strategy(
            "Red candle > -2%",
            lambda row: row["price_change_pct"] < -2.0,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 13: RSI + Red candle
        Strategy(
            "RSI(7)<35 + Red>-1.5%",
            lambda row: row["rsi_7"] < 35 and row["price_change_pct"] < -1.5,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 14: Triple combo
        Strategy(
            "RSI(7)<30 + BB + Vol>1.5x",
            lambda row: row["rsi_7"] < 30 and row["close"] <= row["bb_lower"] and row["volume_ratio"] > 1.5,
            target_pct=4.0,
            stop_pct=3.0
        ),

        # Strategy 15: Extreme oversold
        Strategy(
            "RSI(7) < 20",
            lambda row: row["rsi_7"] < 20,
            target_pct=4.0,
            stop_pct=3.0
        ),
    ]

    # Run backtests
    results = []

    for strategy in strategies:
        backtest_strategy(df, strategy)

        total_trades = strategy.wins + strategy.losses
        win_rate = (strategy.wins / total_trades * 100) if total_trades > 0 else 0

        results.append({
            "name": strategy.name,
            "trades": total_trades,
            "wins": strategy.wins,
            "losses": strategy.losses,
            "win_rate": win_rate,
            "total_profit": strategy.total_profit,
            "strategy": strategy
        })

    # Sort by total profit (descending)
    results.sort(key=lambda x: x["total_profit"], reverse=True)

    # Print results

    for _i, _result in enumerate(results, 1):
        pass

    # Show details of top 3 strategies

    for _i, result in enumerate(results[:3], 1):

        if result["strategy"].trades:
            for _trade in result["strategy"].trades[:3]:  # Show first 3 trades
                pass


    if results:
        best = results[0]

        if best["total_profit"] > 0:
            pass
        else:
            pass



if __name__ == "__main__":
    try:
        # Test on last 24 hours of XRP data
        optimize_xrp_strategy(hours_lookback=24, exchange_name="kraken")
    except Exception:
        import traceback
        traceback.print_exc()

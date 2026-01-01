"""
Multi-Coin Strategy Tester
Tests different strategy options across multiple coins to find best approach.
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


def calculate_volume_ratio(data: pd.Series, period: int = 20) -> pd.Series:
    """Calculate volume ratio vs average."""
    avg_volume = data.rolling(window=period).mean()
    ratio = data / avg_volume
    return ratio


class Strategy:
    """Defines a trading strategy."""
    def __init__(self, name: str, entry_fn, target_pct: float = 4.0, stop_pct: float = 3.0):
        self.name = name
        self.entry_fn = entry_fn
        self.target_pct = target_pct
        self.stop_pct = stop_pct
        self.trades = []
        self.wins = 0
        self.losses = 0
        self.total_profit = 0.0


def backtest_strategy(df: pd.DataFrame, strategy: Strategy) -> Strategy:
    """Backtest a strategy on historical data."""
    in_trade = False
    entry_price = 0.0
    entry_idx = 0

    for idx in range(len(df)):
        row = df.iloc[idx]

        if pd.isna(row["rsi_14"]) or pd.isna(row["rsi_7"]):
            continue

        if not in_trade:
            if strategy.entry_fn(row):
                in_trade = True
                entry_price = row["close"]
                entry_idx = idx
        else:
            current_price = row["close"]
            pct_change = ((current_price - entry_price) / entry_price) * 100

            if pct_change >= strategy.target_pct:
                profit = strategy.target_pct
                strategy.wins += 1
                strategy.total_profit += profit
                strategy.trades.append({
                    "entry_time": df.iloc[entry_idx]["timestamp"],
                    "exit_time": row["timestamp"],
                    "profit_pct": profit,
                    "result": "WIN"
                })
                in_trade = False

            elif pct_change <= -strategy.stop_pct:
                loss = -strategy.stop_pct
                strategy.losses += 1
                strategy.total_profit += loss
                strategy.trades.append({
                    "entry_time": df.iloc[entry_idx]["timestamp"],
                    "exit_time": row["timestamp"],
                    "profit_pct": loss,
                    "result": "LOSS"
                })
                in_trade = False

    return strategy


def test_coin(exchange, pair: str, hours_lookback: int = 24) -> dict:
    """Test all strategies on a single coin."""
    try:
        since = exchange.parse8601((datetime.now(UTC) - timedelta(hours=hours_lookback)).isoformat())
        ohlcv = exchange.fetch_ohlcv(pair, "5m", since=since, limit=1000)

        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

        # Calculate indicators
        df["rsi_7"] = calculate_rsi(df["close"], 7)
        df["rsi_14"] = calculate_rsi(df["close"], 14)
        df["volume_ratio"] = calculate_volume_ratio(df["volume"], 20)
        df["price_change_pct"] = df["close"].pct_change() * 100

        # Calculate stats over the period
        price_min = df["low"].min()
        price_max = df["high"].max()
        volatility = ((price_max - price_min) / price_min) * 100
        rsi_min = df["rsi_14"].min()
        rsi_max = df["rsi_14"].max()

        # Define strategies to test
        strategies = {
            "Current Bot (RSI<45)": Strategy(
                "Current Bot (RSI<45)",
                lambda row: row["rsi_14"] < 45,
                target_pct=4.0,
                stop_pct=3.0
            ),
            "Moderate (RSI 45-55)": Strategy(
                "Moderate (RSI 45-55)",
                lambda row: 45 <= row["rsi_14"] <= 55,
                target_pct=2.0,  # Smaller target
                stop_pct=1.5     # Tighter stop
            ),
            "Looser (RSI<50)": Strategy(
                "Looser (RSI<50)",
                lambda row: row["rsi_14"] < 50,
                target_pct=4.0,
                stop_pct=3.0
            ),
            "Aggressive (RSI<35)": Strategy(
                "Aggressive (RSI<35)",
                lambda row: row["rsi_14"] < 35,
                target_pct=5.0,  # Bigger target
                stop_pct=3.0
            ),
            "RSI(7) Fast": Strategy(
                "RSI(7) Fast",
                lambda row: row["rsi_7"] < 30,
                target_pct=4.0,
                stop_pct=3.0
            ),
        }

        # Backtest all strategies
        results = {}
        for name, strategy in strategies.items():
            backtest_strategy(df, strategy)
            total_trades = strategy.wins + strategy.losses
            win_rate = (strategy.wins / total_trades * 100) if total_trades > 0 else 0

            results[name] = {
                "trades": total_trades,
                "wins": strategy.wins,
                "losses": strategy.losses,
                "win_rate": win_rate,
                "profit": strategy.total_profit
            }

        return {
            "pair": pair,
            "volatility": volatility,
            "rsi_range": f"{rsi_min:.0f}-{rsi_max:.0f}",
            "strategies": results
        }

    except Exception:
        return None


def test_all_coins():
    """Test all strategies across multiple coins."""

    exchange = ccxt.kraken({"enableRateLimit": True})

    # Test these coins
    pairs = [
        "XRP/USD",
        "ADA/USD",
        "DOGE/USD",
        "LINK/USD",
        "ATOM/USD",
        "UNI/USD",
        "DOT/USD",
        "AVAX/USD",
        "NEAR/USD",
        "ARB/USD",
    ]


    coin_results = []
    for pair in pairs:
        result = test_coin(exchange, pair, hours_lookback=168)  # 7 days
        if result:
            coin_results.append(result)

    # Print results

    for result in coin_results:

        for strategy_name, stats in result["strategies"].items():
            if stats["trades"] > 0:
                " <-- BEST" if stats["profit"] > 0 else ""
            else:
                pass

    # Summary by strategy

    strategy_totals = {}
    for result in coin_results:
        for strategy_name, stats in result["strategies"].items():
            if strategy_name not in strategy_totals:
                strategy_totals[strategy_name] = {
                    "total_trades": 0,
                    "total_wins": 0,
                    "total_losses": 0,
                    "total_profit": 0.0,
                    "coins_traded": 0
                }

            if stats["trades"] > 0:
                strategy_totals[strategy_name]["total_trades"] += stats["trades"]
                strategy_totals[strategy_name]["total_wins"] += stats["wins"]
                strategy_totals[strategy_name]["total_losses"] += stats["losses"]
                strategy_totals[strategy_name]["total_profit"] += stats["profit"]
                strategy_totals[strategy_name]["coins_traded"] += 1

    # Sort by profit
    sorted_strategies = sorted(strategy_totals.items(), key=lambda x: x[1]["total_profit"], reverse=True)


    for strategy_name, totals in sorted_strategies:
        total_trades = totals["total_trades"]
        (totals["total_wins"] / total_trades * 100) if total_trades > 0 else 0
        totals["coins_traded"]

        if total_trades > 0:
            " [WINNER]" if totals == sorted_strategies[0][1] else ""
        else:
            pass

    # Recommendation

    if sorted_strategies and sorted_strategies[0][1]["total_trades"] > 0:
        best_strategy = sorted_strategies[0]
        best_strategy[0]
        stats = best_strategy[1]


        if stats["total_profit"] > 0:
            pass
        else:
            pass
    else:
        pass



if __name__ == "__main__":
    try:
        test_all_coins()
    except Exception:
        import traceback
        traceback.print_exc()

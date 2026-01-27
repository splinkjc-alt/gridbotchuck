"""
Backtest CrossKiller coins on 5m timeframe
==========================================

Tests Coinbase assets with different indicator combinations.
"""

import asyncio
from datetime import datetime, timedelta
import ccxt.async_support as ccxt
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

# Coinbase assets to test
ASSETS = [
    "SOL/USD",
    "ATOM/USD",
    "UNI/USD",
    "XRP/USD",
    "DOT/USD",
    "AVAX/USD",
    "ADA/USD",
    "LINK/USD",
]
TIMEFRAME = "5m"
LOOKBACK_DAYS = 14  # 2 weeks of 5m data

# Indicator configs
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
    "ema_only": {
        "name": "EMA 9/20",
        "use_rsi": False,
        "use_bb": False,
        "use_ema": True,
        "use_macd": False,
    },
    "full": {
        "name": "Full Suite",
        "use_rsi": True,
        "use_bb": True,
        "use_ema": True,
        "use_macd": True,
    },
}

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

    return df


def check_buy_signal(row, config: dict, strategy: str) -> bool:
    """Check if buy conditions are met."""
    signals = []

    if config["use_rsi"]:
        if strategy == "grid":
            signals.append(row["rsi"] < 35)
        elif strategy == "mean_reversion":
            signals.append(row["rsi"] < 30)
        elif strategy == "momentum":
            signals.append(30 < row["rsi"] < 50)

    if config["use_bb"]:
        signals.append(row["close"] <= row["bb_lower"])

    if config["use_ema"]:
        if strategy == "momentum":
            signals.append(row["ema_9"] > row["ema_20"])
        else:
            signals.append(row["close"] < row["ema_20"])

    if config["use_macd"]:
        if strategy == "momentum":
            signals.append(row["macd"] > row["macd_signal"])
        else:
            signals.append(row["macd_hist"] < 0)

    if not signals:
        return False

    if strategy == "momentum":
        return any(signals)
    else:
        return all(signals)


def check_sell_signal(
    row, entry_price: float, config: dict, strategy: str
) -> tuple[bool, str]:
    """Check if sell conditions are met."""
    pct_change = ((row["close"] - entry_price) / entry_price) * 100

    # Day trading targets - quick in/out
    if strategy == "grid":
        take_profit, stop_loss = 1.5, -1.0
    elif strategy == "mean_reversion":
        take_profit, stop_loss = 2.0, -1.5
    elif strategy == "momentum":
        take_profit, stop_loss = 2.5, -1.5
    else:
        take_profit, stop_loss = 1.5, -1.0

    if pct_change >= take_profit:
        return True, "take_profit"
    if pct_change <= stop_loss:
        return True, "stop_loss"

    if config["use_rsi"] and row["rsi"] > 70:
        return True, "rsi_overbought"
    if config["use_bb"] and row["close"] >= row["bb_upper"]:
        return True, "bb_upper"
    if config["use_ema"] and strategy == "momentum" and row["ema_9"] < row["ema_20"]:
        return True, "ema_bearish"
    if (
        config["use_macd"]
        and strategy == "momentum"
        and row["macd"] < row["macd_signal"]
    ):
        return True, "macd_bearish"

    return False, ""


def backtest(df: pd.DataFrame, config: dict, strategy: str) -> dict:
    """Run backtest."""
    initial_balance = 1000.0
    balance = initial_balance
    position = 0.0
    entry_price = 0.0
    trades = []

    for i in range(50, len(df)):
        row = df.iloc[i]
        if pd.isna(row["rsi"]) or pd.isna(row["bb_lower"]):
            continue

        if position == 0:
            if check_buy_signal(row, config, strategy):
                position = balance / row["close"]
                entry_price = row["close"]
                balance = 0
                trades.append({"type": "BUY", "price": row["close"]})
        else:
            should_sell, reason = check_sell_signal(row, entry_price, config, strategy)
            if should_sell:
                balance = position * row["close"]
                pct = ((row["close"] - entry_price) / entry_price) * 100
                trades.append(
                    {
                        "type": "SELL",
                        "price": row["close"],
                        "pct": pct,
                        "reason": reason,
                    }
                )
                position = 0
                entry_price = 0

    # Close open position
    if position > 0:
        balance = position * df.iloc[-1]["close"]

    total_return = ((balance - initial_balance) / initial_balance) * 100
    sell_trades = [t for t in trades if t["type"] == "SELL"]
    wins = len([t for t in sell_trades if t.get("pct", 0) > 0])
    losses = len(sell_trades) - wins
    win_rate = (wins / len(sell_trades) * 100) if sell_trades else 0

    return {
        "total_return": total_return,
        "num_trades": len(sell_trades),
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
    }


async def fetch_ohlcv(exchange, symbol: str, timeframe: str, days: int) -> pd.DataFrame:
    """Fetch OHLCV data."""
    since = exchange.parse8601((datetime.utcnow() - timedelta(days=days)).isoformat())
    all_data = []

    while True:
        try:
            data = await exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=300)
            if not data:
                break
            all_data.extend(data)
            since = data[-1][0] + 1
            if len(data) < 300:
                break
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            break

    if not all_data:
        return pd.DataFrame()

    df = pd.DataFrame(
        all_data, columns=["timestamp", "open", "high", "low", "close", "volume"]
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    return (
        df.drop_duplicates(subset=["timestamp"])
        .sort_values("timestamp")
        .reset_index(drop=True)
    )


async def run_backtests():
    """Run all backtests."""
    exchange = ccxt.coinbase(
        {
            "apiKey": os.getenv("COINBASE_API_KEY"),
            "secret": os.getenv("COINBASE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    results = []

    try:
        for asset in ASSETS:
            print(f"\n{'='*50}")
            print(f"BACKTESTING: {asset} @ 5m")
            print(f"{'='*50}")

            df = await fetch_ohlcv(exchange, asset, TIMEFRAME, LOOKBACK_DAYS)
            if df.empty:
                print(f"  No data for {asset}")
                continue

            print(f"  Loaded {len(df)} candles")
            df = calculate_indicators(df)

            for ind_key, ind_config in INDICATOR_CONFIGS.items():
                for strategy in STRATEGIES:
                    result = backtest(df, ind_config, strategy)
                    results.append(
                        {
                            "asset": asset,
                            "indicators": ind_config["name"],
                            "strategy": strategy,
                            "return_pct": result["total_return"],
                            "num_trades": result["num_trades"],
                            "win_rate": result["win_rate"],
                            "wins": result["wins"],
                            "losses": result["losses"],
                        }
                    )

                    ret = result["total_return"]
                    sign = "+" if ret > 0 else ""
                    print(
                        f"  {ind_config['name']:12} + {strategy:15} = {sign}{ret:6.2f}% ({result['num_trades']} trades, {result['win_rate']:.0f}% win)"
                    )

    finally:
        await exchange.close()

    # Results summary
    results_df = pd.DataFrame(results)

    print("\n" + "=" * 60)
    print("TOP 10 BEST COMBINATIONS (5m Coinbase)")
    print("=" * 60)

    best = results_df.sort_values("return_pct", ascending=False).head(10)
    for _, row in best.iterrows():
        print(
            f"{row['asset']:10} | {row['indicators']:12} | {row['strategy']:15} | {row['return_pct']:+7.2f}% | {row['num_trades']:3} trades | {row['win_rate']:.0f}% win"
        )

    # Best per asset
    print("\n" + "=" * 60)
    print("BEST COMBO PER ASSET")
    print("=" * 60)

    for asset in ASSETS:
        asset_best = (
            results_df[results_df["asset"] == asset]
            .sort_values("return_pct", ascending=False)
            .head(1)
        )
        if not asset_best.empty:
            row = asset_best.iloc[0]
            print(
                f"{row['asset']:10} | {row['indicators']:12} | {row['strategy']:15} | {row['return_pct']:+7.2f}%"
            )

    results_df.to_csv("D:/gridbotchuck/data/backtest_coinbase_5m.csv", index=False)
    print("\nResults saved to data/backtest_coinbase_5m.csv")

    return results_df


if __name__ == "__main__":
    print("Backtesting CrossKiller coins on 5m timeframe...")
    print(f"Assets: {ASSETS}")
    print(f"Lookback: {LOOKBACK_DAYS} days")
    asyncio.run(run_backtests())

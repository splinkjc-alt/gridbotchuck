"""
Analyze the BTC drop opportunity from the chart.
Pull data and calculate what indicators would have caught it.
"""

import ccxt
import pandas as pd


def calculate_rsi(data, period=14):
    """Calculate RSI."""
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_volume_ratio(data, period=20):
    """Calculate current volume vs average volume."""
    avg_volume = data.rolling(window=period).mean()
    ratio = data / avg_volume
    return ratio

def analyze_btc_drop():
    """Analyze the BTC drop around Dec 29, 2025 6:00 AM."""

    # Initialize Kraken exchange
    exchange = ccxt.kraken({"enableRateLimit": True})

    # Target time: Dec 29, 2025 around 6:00 AM UTC
    # Fetch 15-minute candles from Dec 28 to Dec 29
    since = exchange.parse8601("2025-12-28T00:00:00Z")

    ohlcv = exchange.fetch_ohlcv("BTC/USD", "5m", since=since, limit=200)

    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms")

    # Calculate indicators
    df["rsi_14"] = calculate_rsi(df["close"], 14)
    df["rsi_7"] = calculate_rsi(df["close"], 7)
    df["volume_ratio"] = calculate_volume_ratio(df["volume"], 20)
    df["price_change_pct"] = df["close"].pct_change() * 100

    # Show what data we got

    # Find the biggest drop in the entire dataset
    df["drop_from_prev"] = df["low"].diff()
    df["drop_pct"] = (df["low"] - df["low"].shift(1)) / df["low"].shift(1) * 100

    # Find the lowest point overall
    lowest_idx = df["low"].idxmin()
    opportunity_candle = df.loc[lowest_idx]



    # Check a few candles before
    if lowest_idx > 0:
        df.loc[lowest_idx - 1]

    # Check a few candles after (recovery)
    if lowest_idx < len(df) - 3:
        recovery_candles = df.loc[lowest_idx:lowest_idx+3]
        for i, (idx, candle) in enumerate(recovery_candles.iterrows()):
            if i > 0:  # Skip the bottom candle itself
                ((candle["close"] - opportunity_candle["close"]) / opportunity_candle["close"] * 100)

    # What would have caught this?
    triggers = []

    if opportunity_candle["rsi_7"] < 30:
        triggers.append(f"[YES] RSI(7) < 30: {opportunity_candle['rsi_7']:.1f}")
    elif opportunity_candle["rsi_7"] < 40:
        triggers.append(f"[YES] RSI(7) < 40: {opportunity_candle['rsi_7']:.1f}")

    if opportunity_candle["rsi_14"] < 30:
        triggers.append(f"[YES] RSI(14) < 30: {opportunity_candle['rsi_14']:.1f}")
    elif opportunity_candle["rsi_14"] < 40:
        triggers.append(f"[YES] RSI(14) < 40: {opportunity_candle['rsi_14']:.1f}")

    if opportunity_candle["volume_ratio"] > 2.0:
        triggers.append(f"[YES] Volume Spike > 2x: {opportunity_candle['volume_ratio']:.2f}x")

    if opportunity_candle["price_change_pct"] < -2.0:
        triggers.append(f"[YES] Large Red Candle < -2%: {opportunity_candle['price_change_pct']:.2f}%")

    if triggers:
        pass
    else:
        pass

    # Print full dataframe around the opportunity

    context_start = max(0, lowest_idx - 3)
    context_end = min(len(df), lowest_idx + 4)

    for idx in range(context_start, context_end):
        df.loc[idx]


if __name__ == "__main__":
    try:
        analyze_btc_drop()
    except Exception:
        import traceback
        traceback.print_exc()

"""
Analyze the BTC drop opportunity from the chart.
Pull data and calculate what indicators would have caught it.
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

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
    exchange = ccxt.kraken({'enableRateLimit': True})

    # Target time: Dec 29, 2025 around 6:00 AM UTC
    # Fetch 15-minute candles from Dec 28 to Dec 29
    since = exchange.parse8601('2025-12-28T00:00:00Z')

    print("Fetching BTC/USD data from Kraken...")
    ohlcv = exchange.fetch_ohlcv('BTC/USD', '5m', since=since, limit=200)

    # Convert to DataFrame
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Calculate indicators
    print("\nCalculating indicators...")
    df['rsi_14'] = calculate_rsi(df['close'], 14)
    df['rsi_7'] = calculate_rsi(df['close'], 7)
    df['volume_ratio'] = calculate_volume_ratio(df['volume'], 20)
    df['price_change_pct'] = df['close'].pct_change() * 100

    # Show what data we got
    print(f"\nData range: {df['datetime'].min()} to {df['datetime'].max()}")
    print(f"Total candles: {len(df)}")

    # Find the biggest drop in the entire dataset
    df['drop_from_prev'] = df['low'].diff()
    df['drop_pct'] = (df['low'] - df['low'].shift(1)) / df['low'].shift(1) * 100

    # Find the lowest point overall
    lowest_idx = df['low'].idxmin()
    opportunity_candle = df.loc[lowest_idx]

    print("\n" + "="*60)
    print("OPPORTUNITY ANALYSIS - BTC DROP")
    print("="*60)
    print(f"\nTime: {opportunity_candle['datetime']}")
    print(f"Price: ${opportunity_candle['close']:,.2f}")
    print(f"Low: ${opportunity_candle['low']:,.2f}")
    print(f"High: ${opportunity_candle['high']:,.2f}")

    print(f"\nINDICATORS AT THE BOTTOM:")
    print(f"  RSI(14): {opportunity_candle['rsi_14']:.1f}")
    print(f"  RSI(7): {opportunity_candle['rsi_7']:.1f}")
    print(f"  Volume Ratio: {opportunity_candle['volume_ratio']:.2f}x normal")
    print(f"  Candle % Change: {opportunity_candle['price_change_pct']:.2f}%")

    # Check a few candles before
    if lowest_idx > 0:
        prev_candle = df.loc[lowest_idx - 1]
        print(f"\nPREVIOUS CANDLE:")
        print(f"  Price: ${prev_candle['close']:,.2f}")
        print(f"  % Drop: {((opportunity_candle['close'] - prev_candle['close']) / prev_candle['close'] * 100):.2f}%")

    # Check a few candles after (recovery)
    if lowest_idx < len(df) - 3:
        recovery_candles = df.loc[lowest_idx:lowest_idx+3]
        print(f"\nRECOVERY (Next 3 candles):")
        for i, (idx, candle) in enumerate(recovery_candles.iterrows()):
            if i > 0:  # Skip the bottom candle itself
                pct_from_bottom = ((candle['close'] - opportunity_candle['close']) / opportunity_candle['close'] * 100)
                print(f"  +{i*5}min: ${candle['close']:,.2f} (+{pct_from_bottom:.2f}%)")

    # What would have caught this?
    print(f"\nWHAT WOULD HAVE CAUGHT THIS:")
    triggers = []

    if opportunity_candle['rsi_7'] < 30:
        triggers.append(f"[YES] RSI(7) < 30: {opportunity_candle['rsi_7']:.1f}")
    elif opportunity_candle['rsi_7'] < 40:
        triggers.append(f"[YES] RSI(7) < 40: {opportunity_candle['rsi_7']:.1f}")

    if opportunity_candle['rsi_14'] < 30:
        triggers.append(f"[YES] RSI(14) < 30: {opportunity_candle['rsi_14']:.1f}")
    elif opportunity_candle['rsi_14'] < 40:
        triggers.append(f"[YES] RSI(14) < 40: {opportunity_candle['rsi_14']:.1f}")

    if opportunity_candle['volume_ratio'] > 2.0:
        triggers.append(f"[YES] Volume Spike > 2x: {opportunity_candle['volume_ratio']:.2f}x")

    if opportunity_candle['price_change_pct'] < -2.0:
        triggers.append(f"[YES] Large Red Candle < -2%: {opportunity_candle['price_change_pct']:.2f}%")

    if triggers:
        print("\n" + "\n".join(triggers))
    else:
        print("\n[WARNING] Standard indicators didn't fire! Need custom detection.")

    # Print full dataframe around the opportunity
    print(f"\nFULL DATA AROUND THE OPPORTUNITY:")
    print("\nTime                 | Close    | RSI(7) | RSI(14) | Vol Ratio | % Chg")
    print("-" * 80)

    context_start = max(0, lowest_idx - 3)
    context_end = min(len(df), lowest_idx + 4)

    for idx in range(context_start, context_end):
        row = df.loc[idx]
        marker = " <-- BOTTOM" if idx == lowest_idx else ""
        print(f"{row['datetime'].strftime('%m-%d %H:%M')} | ${row['close']:>8,.0f} | {row['rsi_7']:>6.1f} | {row['rsi_14']:>7.1f} | {row['volume_ratio']:>9.2f} | {row['price_change_pct']:>6.2f}%{marker}")

    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        analyze_btc_drop()
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

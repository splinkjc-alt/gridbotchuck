"""
EMA Signal Scanner - Portable Version

Scans market for EMA crossover signals (dry run - no trading)
"""

import asyncio
import os
from pathlib import Path
import sys

# Setup paths for portable version
script_dir = Path(__file__).parent
portable_root = script_dir.parent
sys.path.insert(0, str(script_dir))

import ccxt.async_support as ccxt
from dotenv import load_dotenv
import pandas as pd

# Load env from config folder
env_path = portable_root / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv(script_dir / ".env")


PAIRS = [
    "UNI/USD",
    "SOL/USD",
    "XRP/USD",
    "ADA/USD",
    "DOGE/USD",
    "AVAX/USD",
    "DOT/USD",
    "LINK/USD",
    "ATOM/USD",
    "FIL/USD",
    "NEAR/USD",
    "APT/USD",
    "ARB/USD",
    "OP/USD",
    "SUI/USD",
    "TIA/USD",
    "INJ/USD",
    "FET/USD",
]


async def analyze_pair(exchange, pair: str) -> dict:
    """Analyze a single pair."""
    try:
        ohlcv = await exchange.fetch_ohlcv(pair, "15m", limit=50)
        df = pd.DataFrame(ohlcv, columns=["ts", "open", "high", "low", "close", "volume"])

        if len(df) < 25:
            return None

        # Calculate EMAs
        ema_9 = df["close"].ewm(span=9, adjust=False).mean()
        ema_20 = df["close"].ewm(span=20, adjust=False).mean()

        current_9 = ema_9.iloc[-1]
        current_20 = ema_20.iloc[-1]
        prev_9 = ema_9.iloc[-2]
        prev_20 = ema_20.iloc[-2]
        prev2_9 = ema_9.iloc[-3]
        prev2_20 = ema_20.iloc[-3]
        price = df["close"].iloc[-1]

        # Calculate spreads (gap between EMAs)
        spread = ((current_9 - current_20) / current_20) * 100
        prev_spread = ((prev_9 - prev_20) / prev_20) * 100
        prev2_spread = ((prev2_9 - prev2_20) / prev2_20) * 100
        spread_change = spread - prev_spread
        spread_trend = spread - prev2_spread

        # Determine action
        if prev_9 <= prev_20 and current_9 > current_20:
            action = "BUY"  # Fresh crossover
        elif prev_9 >= prev_20 and current_9 < current_20:
            action = "SELL"  # Bearish crossover
        elif current_9 > current_20:
            if spread_change > 0 and spread_trend > 0:
                action = "SAFE_BUY"  # Gap widening - momentum building
            elif spread < 0.1 or spread_change < -0.05:
                action = "WARN"  # Gap closing
            else:
                action = "HOLD"
        else:
            action = "AVOID"

        return {
            "pair": pair,
            "price": price,
            "ema_9": current_9,
            "ema_20": current_20,
            "spread": spread,
            "spread_change": spread_change,
            "spread_trend": spread_trend,
            "action": action,
        }

    except Exception:
        return None


async def main():

    # Verify API keys
    api_key = os.getenv("EXCHANGE_API_KEY")
    api_secret = os.getenv("EXCHANGE_SECRET_KEY")

    if not api_key or not api_secret or api_key == "your_api_key_here":
        return

    exchange = ccxt.kraken(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        }
    )

    try:
        results = []

        for pair in PAIRS:
            result = await analyze_pair(exchange, pair)
            if result:
                results.append(result)

        # Sort by action priority
        action_order = {"BUY": 0, "SAFE_BUY": 1, "HOLD": 2, "WARN": 3, "SELL": 4, "AVOID": 5}
        results.sort(key=lambda x: (action_order.get(x["action"], 99), -x["spread_change"]))


        for r in results:
            action = r["action"]

            # Color coding via markers
            if action in ("BUY", "SAFE_BUY") or action == "SELL" or action == "WARN":
                pass
            else:
                pass



        # Summary
        buys = [r for r in results if r["action"] in ("BUY", "SAFE_BUY")]
        [r for r in results if r["action"] == "SELL"]


        if buys:
            for r in buys[:3]:
                pass

    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())

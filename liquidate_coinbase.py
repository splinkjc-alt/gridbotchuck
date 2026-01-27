"""Liquidate all Coinbase positions."""

import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

load_dotenv()


async def liquidate():
    ex = ccxt.coinbase(
        {
            "apiKey": os.getenv("COINBASE_API_KEY"),
            "secret": os.getenv("COINBASE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    try:
        bal = await ex.fetch_balance()
        print("=== COINBASE POSITIONS ===")

        coins = [
            "XRP",
            "ATOM",
            "UNI",
            "SOL",
            "DOT",
            "AVAX",
            "ADA",
            "LINK",
            "BTC",
            "ETH",
        ]
        for c in coins:
            v = bal.get(c, {}).get("free", 0)
            if v > 0.0001:
                try:
                    t = await ex.fetch_ticker(f"{c}/USD")
                    val = v * t["last"]
                    print(f"{c}: {v:.6f} = ${val:.2f}")
                    if val > 1:
                        await ex.create_market_sell_order(f"{c}/USD", v)
                        print(f"  SOLD {c}")
                except Exception as e:
                    print(f"  Skip {c}: {e}")

        await asyncio.sleep(2)
        bal = await ex.fetch_balance()
        usd = bal.get("USD", {}).get("free", 0)
        print(f"\n=== FINAL USD: ${usd:.2f} ===")

    finally:
        await ex.close()


asyncio.run(liquidate())

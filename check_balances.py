"""Quick balance check."""

import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

load_dotenv()


async def check():
    # Coinbase
    ex = ccxt.coinbase(
        {
            "apiKey": os.getenv("COINBASE_API_KEY"),
            "secret": os.getenv("COINBASE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )
    bal = await ex.fetch_balance()
    usd = bal.get("USD", {}).get("free", 0)
    print("=== COINBASE (CrossKiller) ===")
    print(f"USD: ${usd:.2f}")
    total = usd
    for c in [
        "LTC",
        "AAVE",
        "DOGE",
        "BCH",
        "XRP",
        "ATOM",
        "UNI",
        "SOL",
        "DOT",
        "AVAX",
        "ADA",
        "LINK",
    ]:
        v = bal.get(c, {}).get("total", 0)
        if v > 0.001:
            try:
                t = await ex.fetch_ticker(f"{c}/USD")
                val = v * t["last"]
                total += val
                print(f"{c}: {v:.4f} x ${t['last']:.2f} = ${val:.2f}")
            except Exception:
                pass
    print(f"TOTAL: ${total:.2f}")
    await ex.close()

    # Kraken
    ex2 = ccxt.kraken(
        {
            "apiKey": os.getenv("EXCHANGE_API_KEY"),
            "secret": os.getenv("EXCHANGE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )
    bal2 = await ex2.fetch_balance()
    usd2 = bal2.get("USD", {}).get("free", 0)
    print("\n=== KRAKEN (Chuck/Growler) ===")
    print(f"USD: ${usd2:.2f}")
    total2 = usd2
    for c in ["VET", "PEPE", "ATOM", "AVAX", "BTC", "ETH", "ADA"]:
        v = bal2.get(c, {}).get("total", 0)
        if v > 0.001:
            try:
                t = await ex2.fetch_ticker(f"{c}/USD")
                val = v * t["last"]
                total2 += val
                print(f"{c}: {v:.2f} x ${t['last']:.6f} = ${val:.2f}")
            except Exception:
                pass
    print(f"TOTAL: ${total2:.2f}")
    await ex2.close()


asyncio.run(check())

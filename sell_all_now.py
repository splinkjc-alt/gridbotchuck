"""Quick script to sell all positions."""

import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

load_dotenv()


async def sell_all():
    # Kraken
    kraken = ccxt.kraken(
        {
            "apiKey": os.getenv("EXCHANGE_API_KEY"),
            "secret": os.getenv("EXCHANGE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    # VET - remaining
    print("Selling VET...")
    try:
        order = await kraken.create_market_sell_order("VET/USD", 15164)
        print(f'VET sold: {order.get("id")}')
    except Exception as e:
        print(f"VET error: {e}")

    # PEPE - remaining
    print("Selling PEPE...")
    try:
        order = await kraken.create_market_sell_order("PEPE/USD", 200244)
        print(f'PEPE sold: {order.get("id")}')
    except Exception as e:
        print(f"PEPE error: {e}")

    # ATOM
    print("Selling ATOM...")
    try:
        order = await kraken.create_market_sell_order("ATOM/USD", 75.41)
        print(f'ATOM sold: {order.get("id")}')
    except Exception as e:
        print(f"ATOM error: {e}")

    await kraken.close()

    # Coinbase DOT
    coinbase = ccxt.coinbase(
        {
            "apiKey": os.getenv("COINBASE_API_KEY"),
            "secret": os.getenv("COINBASE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    print("Selling DOT...")
    try:
        order = await coinbase.create_market_sell_order("DOT/USD", 307.46)
        print(f'DOT sold: {order.get("id")}')
    except Exception as e:
        print(f"DOT error: {e}")

    await coinbase.close()
    print("Done!")


if __name__ == "__main__":
    asyncio.run(sell_all())

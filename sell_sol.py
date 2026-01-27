"""Quick script to sell all SOL on Coinbase."""

import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

load_dotenv()


async def sell_all_sol():
    exchange = ccxt.coinbase(
        {
            "apiKey": os.getenv("COINBASE_API_KEY"),
            "secret": os.getenv("COINBASE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    try:
        # Get SOL balance
        balance = await exchange.fetch_balance()
        sol_balance = balance.get("SOL", {}).get("free", 0)
        print(f"SOL balance: {sol_balance}")

        if sol_balance > 0.001:
            # Get current price
            ticker = await exchange.fetch_ticker("SOL/USD")
            price = ticker["last"]
            print(f"Current SOL price: ${price:.2f}")
            print(f"Estimated value: ${sol_balance * price:.2f}")

            # Market sell all SOL
            order = await exchange.create_market_sell_order("SOL/USD", sol_balance)
            print(f"SOLD: {sol_balance} SOL")
            print(f'Order ID: {order["id"]}')
        else:
            print("No SOL to sell")

        # Show final USD balance
        await asyncio.sleep(1)
        balance = await exchange.fetch_balance()
        usd = balance.get("USD", {}).get("free", 0)
        print(f"\nFinal USD balance: ${usd:.2f}")

    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(sell_all_sol())

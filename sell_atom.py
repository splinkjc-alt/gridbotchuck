"""Quick script to sell all ATOM."""

import asyncio
import os
from dotenv import load_dotenv
import ccxt.async_support as ccxt

load_dotenv()


async def sell_atom():
    ex = ccxt.coinbase(
        {
            "apiKey": os.getenv("COINBASE_API_KEY"),
            "secret": os.getenv("COINBASE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    # Get balance
    balance = await ex.fetch_balance()
    atom_amount = balance.get("ATOM", {}).get("free", 0)

    if atom_amount < 0.01:
        print("No ATOM to sell")
        await ex.close()
        return

    ticker = await ex.fetch_ticker("ATOM/USD")
    price = ticker["last"]
    value = atom_amount * price

    print(f"ATOM: {atom_amount:.4f} @ ${price:.2f} = ${value:.2f}")

    # Sell all ATOM
    order = await ex.create_market_sell_order("ATOM/USD", atom_amount)
    print(f"SOLD {atom_amount:.4f} ATOM @ ~${price:.2f}")
    print(f"Order ID: {order.get('id')}")

    await ex.close()


if __name__ == "__main__":
    asyncio.run(sell_atom())

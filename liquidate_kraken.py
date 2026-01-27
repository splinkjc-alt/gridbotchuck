"""Liquidate VET and PEPE positions on Kraken."""

import asyncio
import ccxt.async_support as ccxt
import os
from dotenv import load_dotenv

load_dotenv()


async def liquidate():
    ex = ccxt.kraken(
        {
            "apiKey": os.getenv("EXCHANGE_API_KEY"),
            "secret": os.getenv("EXCHANGE_SECRET_KEY"),
            "enableRateLimit": True,
        }
    )

    try:
        print("=== LIQUIDATING KRAKEN POSITIONS ===\n")

        # Get balances
        bal = await ex.fetch_balance()

        # Sell VET
        vet = bal.get("VET", {}).get("free", 0)
        if vet > 1:
            ticker = await ex.fetch_ticker("VET/USD")
            print(
                f"VET: {vet:.2f} @ ${ticker['last']:.6f} = ${vet * ticker['last']:.2f}"
            )
            order = await ex.create_market_sell_order("VET/USD", vet)
            print(f"SOLD VET - Order ID: {order['id']}\n")
        else:
            print("No VET to sell\n")

        # Sell PEPE
        pepe = bal.get("PEPE", {}).get("free", 0)
        if pepe > 1000:
            ticker = await ex.fetch_ticker("PEPE/USD")
            print(
                f"PEPE: {pepe:.0f} @ ${ticker['last']:.8f} = ${pepe * ticker['last']:.2f}"
            )
            order = await ex.create_market_sell_order("PEPE/USD", pepe)
            print(f"SOLD PEPE - Order ID: {order['id']}\n")
        else:
            print("No PEPE to sell\n")

        # Final balance
        await asyncio.sleep(2)
        bal = await ex.fetch_balance()
        usd = bal.get("USD", {}).get("free", 0)
        print(f"=== FINAL USD BALANCE: ${usd:.2f} ===")

    finally:
        await ex.close()


asyncio.run(liquidate())

"""
Kraken Account Health Check - Portable Version

Shows current balances and open orders.
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

# Load env from config folder
env_path = portable_root / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv(script_dir / ".env")


async def main():
    print("=" * 50)
    print("  KRAKEN ACCOUNT STATUS")
    print("=" * 50)
    print()

    # Verify API keys
    api_key = os.getenv("EXCHANGE_API_KEY")
    api_secret = os.getenv("EXCHANGE_SECRET_KEY")

    if not api_key or not api_secret or api_key == "your_api_key_here":
        print("ERROR: API keys not configured!")
        print("Please edit config\\.env with your Kraken API keys")
        return

    exchange = ccxt.kraken(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        }
    )

    try:
        # Get balances
        balance = await exchange.fetch_balance()

        print("BALANCES:")
        print("-" * 30)

        total_value = 0
        usd_balance = balance["total"].get("USD", 0)

        for currency, amount in sorted(balance["total"].items()):
            if amount > 0.0001:
                if currency == "USD":
                    print(f"  USD: ${amount:.2f}")
                    total_value += amount
                else:
                    # Try to get USD value
                    pair = f"{currency}/USD"
                    try:
                        ticker = await exchange.fetch_ticker(pair)
                        price = ticker["last"]
                        value = amount * price
                        if value > 0.01:
                            total_value += value
                            print(f"  {currency}: {amount:.4f} (~${value:.2f})")
                    except:
                        if amount > 0.01:
                            print(f"  {currency}: {amount:.4f}")

        print("-" * 30)
        print(f"  TOTAL: ~${total_value:.2f}")
        print()

        # Get open orders
        orders = await exchange.fetch_open_orders()

        print("OPEN ORDERS:")
        print("-" * 30)

        if orders:
            for order in orders:
                print(f"  {order['side'].upper()} {order['amount']} {order['symbol']} @ ${order['price']}")
        else:
            print("  No open orders")

        print()
        print("Connection OK!")

    except Exception as e:
        print(f"ERROR: {e}")

    finally:
        await exchange.close()


if __name__ == "__main__":
    asyncio.run(main())

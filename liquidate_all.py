"""
Liquidate All Positions
=======================
Cancels all open orders and sells all crypto back to USD on both exchanges.
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import ccxt.async_support as ccxt
from dotenv import load_dotenv

# Load .env from project directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)
print(f"Loading env from: {env_path}")


async def liquidate_exchange(exchange_name: str, exchange: ccxt.Exchange):
    """Liquidate all positions on a single exchange."""
    print(f"\n{'='*60}")
    print(f"  LIQUIDATING: {exchange_name.upper()}")
    print(f"{'='*60}")

    try:
        # Load markets
        await exchange.load_markets()

        # 1. Cancel all open orders
        print(f"\n[{exchange_name}] Cancelling open orders...")
        try:
            open_orders = await exchange.fetch_open_orders()
            if open_orders:
                for order in open_orders:
                    try:
                        await exchange.cancel_order(order["id"], order["symbol"])
                        print(
                            f"  Cancelled: {order['side']} {order['amount']} {order['symbol']} @ {order['price']}"
                        )
                    except Exception as e:
                        print(f"  Failed to cancel {order['id']}: {e}")
                print(f"  Cancelled {len(open_orders)} orders")
            else:
                print("  No open orders found")
        except Exception as e:
            print(f"  Could not fetch open orders: {e}")

        # 2. Get all balances
        print(f"\n[{exchange_name}] Fetching balances...")
        balance = await exchange.fetch_balance()

        # 3. Sell all non-USD assets
        print(f"\n[{exchange_name}] Selling all crypto to USD...")
        sold_any = False

        for currency, amount in balance["free"].items():
            # Skip USD and stablecoins
            if currency in ["USD", "USDT", "USDC", "DAI", "BUSD"]:
                if amount > 0:
                    print(f"  {currency}: ${amount:.2f} (keeping)")
                continue

            # Skip dust (less than $1 worth approximately)
            if amount <= 0:
                continue

            # Try to sell to USD
            symbol = f"{currency}/USD"

            if symbol not in exchange.markets:
                # Try USDT pair as fallback
                symbol = f"{currency}/USDT"
                if symbol not in exchange.markets:
                    if amount > 0.0001:  # Only warn for non-dust
                        print(f"  {currency}: {amount} (no USD pair available)")
                    continue

            try:
                # Get current price to check if worth selling
                ticker = await exchange.fetch_ticker(symbol)
                value_usd = amount * (ticker["last"] or ticker["bid"] or 0)

                # Skip if worth less than $0.50
                if value_usd < 0.50:
                    print(
                        f"  {currency}: {amount:.6f} (~${value_usd:.2f}) - dust, skipping"
                    )
                    continue

                # Get minimum order size
                market = exchange.markets[symbol]
                min_amount = (
                    market.get("limits", {}).get("amount", {}).get("min", 0) or 0
                )

                if amount < min_amount:
                    print(
                        f"  {currency}: {amount:.6f} below min order size {min_amount}, skipping"
                    )
                    continue

                # Place market sell order
                print(f"  Selling {amount:.6f} {currency} (~${value_usd:.2f})...")

                order = await exchange.create_market_sell_order(symbol, amount)
                print(
                    f"    SOLD: {order['filled']} {currency} @ ~${ticker['last']:.6f}"
                )
                sold_any = True

                # Small delay to avoid rate limits
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  Failed to sell {currency}: {e}")

        if not sold_any:
            print("  No crypto positions to sell")

        # 4. Show final USD balance
        print(f"\n[{exchange_name}] Fetching final balance...")
        await asyncio.sleep(2)  # Wait for orders to settle
        final_balance = await exchange.fetch_balance()

        usd_total = final_balance["free"].get("USD", 0) + final_balance["free"].get(
            "USDT", 0
        )
        print(f"\n  FINAL USD BALANCE: ${usd_total:.2f}")

        return usd_total

    except Exception as e:
        print(f"ERROR on {exchange_name}: {e}")
        return 0


async def main():
    print("\n" + "=" * 60)
    print("  LIQUIDATE ALL POSITIONS TO USD")
    print("=" * 60)
    print("\nThis will:")
    print("  1. Cancel all open orders on Kraken & Coinbase")
    print("  2. Sell ALL crypto holdings to USD")
    print("\n*** THIS IS IRREVERSIBLE ***\n")

    # Confirmation
    confirm = input("Type 'LIQUIDATE' to confirm: ")
    if confirm != "LIQUIDATE":
        print("Aborted.")
        return

    print("\nStarting liquidation...\n")

    total_usd = 0

    # Kraken
    kraken_key = os.getenv("EXCHANGE_API_KEY")
    kraken_secret = os.getenv("EXCHANGE_SECRET_KEY") or os.getenv("EXCHANGE_API_SECRET")

    if kraken_key and kraken_secret:
        kraken = ccxt.kraken(
            {
                "apiKey": kraken_key,
                "secret": kraken_secret,
                "enableRateLimit": True,
            }
        )
        try:
            total_usd += await liquidate_exchange("Kraken", kraken)
        finally:
            await kraken.close()
    else:
        print("Kraken: No API keys found, skipping")

    # Coinbase
    coinbase_key = os.getenv("COINBASE_API_KEY")
    coinbase_secret = os.getenv("COINBASE_SECRET_KEY")

    if coinbase_key and coinbase_secret:
        coinbase = ccxt.coinbase(
            {
                "apiKey": coinbase_key,
                "secret": coinbase_secret,
                "enableRateLimit": True,
            }
        )
        try:
            total_usd += await liquidate_exchange("Coinbase", coinbase)
        finally:
            await coinbase.close()
    else:
        print("Coinbase: No API keys found, skipping")

    # Summary
    print("\n" + "=" * 60)
    print("  LIQUIDATION COMPLETE")
    print(f"  Total USD across all exchanges: ${total_usd:.2f}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm", action="store_true", help="Skip confirmation prompt"
    )
    args = parser.parse_args()

    if args.confirm:
        # Bypass confirmation
        async def main_no_confirm():
            print("\n" + "=" * 60)
            print("  LIQUIDATE ALL POSITIONS TO USD")
            print("=" * 60)
            print("\n--confirm flag used, proceeding...\n")

            total_usd = 0

            kraken_key = os.getenv("EXCHANGE_API_KEY")
            kraken_secret = os.getenv("EXCHANGE_SECRET_KEY") or os.getenv(
                "EXCHANGE_API_SECRET"
            )

            if kraken_key and kraken_secret:
                kraken = ccxt.kraken(
                    {
                        "apiKey": kraken_key,
                        "secret": kraken_secret,
                        "enableRateLimit": True,
                    }
                )
                try:
                    total_usd += await liquidate_exchange("Kraken", kraken)
                finally:
                    await kraken.close()
            else:
                print("Kraken: No API keys found, skipping")

            coinbase_key = os.getenv("COINBASE_API_KEY")
            coinbase_secret = os.getenv("COINBASE_SECRET_KEY")

            if coinbase_key and coinbase_secret:
                coinbase = ccxt.coinbase(
                    {
                        "apiKey": coinbase_key,
                        "secret": coinbase_secret,
                        "enableRateLimit": True,
                    }
                )
                try:
                    total_usd += await liquidate_exchange("Coinbase", coinbase)
                finally:
                    await coinbase.close()
            else:
                print("Coinbase: No API keys found, skipping")

            print("\n" + "=" * 60)
            print("  LIQUIDATION COMPLETE")
            print(f"  Total USD across all exchanges: ${total_usd:.2f}")
            print("=" * 60 + "\n")

        asyncio.run(main_no_confirm())
    else:
        asyncio.run(main())

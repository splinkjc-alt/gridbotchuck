"""
Reset Coinbase Portfolio to USD
===============================
Sells all crypto holdings on Coinbase to convert back to USD.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import ccxt


def reset_coinbase_to_usd():
    """Sell all crypto holdings to USD on Coinbase."""
    print("=" * 60)
    print("RESETTING COINBASE PORTFOLIO TO USD")
    print("=" * 60)

    # Initialize Coinbase
    exchange = ccxt.coinbase({
        'apiKey': os.getenv('COINBASE_API_KEY'),
        'secret': os.getenv('COINBASE_PRIVATE_KEY'),
        'enableRateLimit': True,
    })

    # Get balances
    print("\nFetching balances...")
    try:
        balance = exchange.fetch_balance()
    except Exception as e:
        print(f"Error fetching balance: {e}")
        return

    # Find crypto holdings to sell
    to_sell = []
    print("\nCurrent holdings:")
    for currency, amount in balance['total'].items():
        if amount > 0:
            if currency in ['USD', 'USDT', 'USDC']:
                print(f"  {currency}: ${amount:.2f}")
            else:
                # Check if there's a USD pair
                pair = f"{currency}/USD"
                try:
                    ticker = exchange.fetch_ticker(pair)
                    value_usd = amount * ticker['last']
                    print(f"  {currency}: {amount:.6f} @ ${ticker['last']:.6f} = ${value_usd:.2f}")
                    if value_usd > 1:  # Only sell if worth more than $1
                        to_sell.append({
                            'currency': currency,
                            'amount': amount,
                            'pair': pair,
                            'price': ticker['last'],
                            'value_usd': value_usd
                        })
                except Exception as e:
                    if amount > 0.0001:
                        print(f"  {currency}: {amount:.6f} (no USD pair)")

    if not to_sell:
        print("\nNo crypto holdings to sell!")
        return

    print(f"\nFound {len(to_sell)} positions to liquidate")
    print("-" * 40)

    # Cancel all open orders first
    print("\nCancelling all open orders...")
    try:
        open_orders = exchange.fetch_open_orders()
        for order in open_orders:
            try:
                exchange.cancel_order(order['id'], order['symbol'])
                print(f"  Cancelled: {order['side']} {order['amount']} {order['symbol']}")
            except Exception as e:
                print(f"  Failed to cancel order {order['id']}: {e}")
        if not open_orders:
            print("  No open orders")
    except Exception as e:
        print(f"  Error fetching open orders: {e}")

    # Sell each position
    print("\nSelling positions...")
    total_sold = 0

    for pos in to_sell:
        try:
            sell_amount = pos['amount']
            print(f"  Selling {sell_amount:.6f} {pos['currency']}...")

            # Place market sell order
            order = exchange.create_market_sell_order(pos['pair'], sell_amount)

            status = order.get('status', 'unknown')
            if status in ['closed', 'filled']:
                filled_price = order.get('average', pos['price'])
                filled_amount = order.get('filled', sell_amount)
                usd_received = filled_amount * filled_price
                total_sold += usd_received
                print(f"    SOLD: {filled_amount:.6f} @ ${filled_price:.6f} = ${usd_received:.2f}")
            else:
                print(f"    Order status: {status}")
                # Check if it filled anyway
                if order.get('filled', 0) > 0:
                    filled = order['filled']
                    price = order.get('average', pos['price'])
                    print(f"    Filled: {filled:.6f} @ ${price:.4f}")
                    total_sold += filled * price

        except Exception as e:
            print(f"  Error selling {pos['currency']}: {e}")

    # Final balance check
    print("\n" + "=" * 60)
    print("FINAL COINBASE BALANCES")
    print("=" * 60)

    try:
        balance = exchange.fetch_balance()
        total_value = 0

        for currency, amount in balance['total'].items():
            if amount > 0:
                if currency in ['USD']:
                    print(f"  USD: ${amount:.2f}")
                    total_value += amount
                elif currency in ['USDT', 'USDC']:
                    print(f"  {currency}: ${amount:.2f}")
                    total_value += amount
                else:
                    try:
                        ticker = exchange.fetch_ticker(f"{currency}/USD")
                        value = amount * ticker['last']
                        if value > 0.01:
                            print(f"  {currency}: {amount:.6f} (${value:.2f})")
                            total_value += value
                    except Exception:
                        if amount > 0.0001:
                            print(f"  {currency}: {amount:.6f}")

        print(f"\nTotal Coinbase Value: ${total_value:.2f}")
    except Exception as e:
        print(f"Error fetching final balance: {e}")

    print("=" * 60)


if __name__ == "__main__":
    reset_coinbase_to_usd()

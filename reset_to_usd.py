"""
Reset Portfolio to USD
======================
Sells all crypto holdings on Kraken to convert back to USD.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

import ccxt


def reset_to_usd():
    """Sell all crypto holdings to USD."""
    print("=" * 60)
    print("RESETTING PORTFOLIO TO USD")
    print("=" * 60)

    # Initialize Kraken
    exchange = ccxt.kraken({
        'apiKey': os.getenv('EXCHANGE_API_KEY'),
        'secret': os.getenv('EXCHANGE_SECRET_KEY'),
        'enableRateLimit': True,
    })

    # Get balances
    print("\nFetching balances...")
    balance = exchange.fetch_balance()

    # Find crypto holdings to sell
    to_sell = []
    for currency, amount in balance['total'].items():
        if amount > 0 and currency not in ['USD', 'ZUSD', 'USDT', 'USDC']:
            # Check if there's a USD pair
            pair = f"{currency}/USD"
            try:
                ticker = exchange.fetch_ticker(pair)
                value_usd = amount * ticker['last']
                if value_usd > 1:  # Only sell if worth more than $1
                    to_sell.append({
                        'currency': currency,
                        'amount': amount,
                        'pair': pair,
                        'price': ticker['last'],
                        'value_usd': value_usd
                    })
                    print(f"  {currency}: {amount:.6f} @ ${ticker['last']:.6f} = ${value_usd:.2f}")
            except Exception as e:
                print(f"  {currency}: {amount:.6f} (no USD pair or error: {e})")

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
                print(f"  Cancelled: {order['side']} {order['amount']} {order['symbol']} @ {order['price']}")
            except Exception as e:
                print(f"  Failed to cancel order {order['id']}: {e}")
    except Exception as e:
        print(f"  Error fetching open orders: {e}")

    # Sell each position
    print("\nSelling positions...")
    total_sold = 0

    for pos in to_sell:
        try:
            # Get market info for minimum order size
            market = exchange.market(pos['pair'])
            min_amount = market.get('limits', {}).get('amount', {}).get('min', 0)

            sell_amount = pos['amount']
            if sell_amount < min_amount:
                print(f"  {pos['currency']}: Amount {sell_amount} below minimum {min_amount}, skipping")
                continue

            # Place market sell order
            print(f"  Selling {sell_amount:.6f} {pos['currency']}...")
            order = exchange.create_market_sell_order(pos['pair'], sell_amount)

            if order['status'] == 'closed':
                filled_price = order.get('average', pos['price'])
                filled_amount = order.get('filled', sell_amount)
                usd_received = filled_amount * filled_price
                total_sold += usd_received
                print(f"    SOLD: {filled_amount:.6f} @ ${filled_price:.6f} = ${usd_received:.2f}")
            else:
                print(f"    Order placed: {order['status']}")

        except Exception as e:
            print(f"  Error selling {pos['currency']}: {e}")

    # Final balance check
    print("\n" + "=" * 60)
    print("FINAL BALANCES")
    print("=" * 60)

    balance = exchange.fetch_balance()
    total_value = 0

    for currency, amount in balance['total'].items():
        if amount > 0:
            if currency in ['USD', 'ZUSD']:
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

    print(f"\nTotal Portfolio Value: ${total_value:.2f}")
    print("=" * 60)


if __name__ == "__main__":
    reset_to_usd()

import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

e = ccxt.kraken(
    {
        "apiKey": os.getenv("EXCHANGE_API_KEY"),
        "secret": os.getenv("EXCHANGE_SECRET_KEY"),
    }
)

# Check all open orders
orders = e.fetch_open_orders()
print(f"Total open orders: {len(orders)}")
for o in orders:
    print(f"  {o['symbol']}: {o['side']} {o['amount']:.2f} @ ${o['price']}")

# Check balance
b = e.fetch_balance()
print("\nBalances:")
print(f"  USD: ${b['USD']['free']:.2f} (total: ${b['USD']['total']:.2f})")
print(f"  PEPE: {b['PEPE']['free']:,.0f} (total: {b['PEPE']['total']:,.0f})")
print(f"  ADA: {b['ADA']['free']:.2f} (total: {b['ADA']['total']:.2f})")

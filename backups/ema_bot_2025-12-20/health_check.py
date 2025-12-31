"""Quick health check - no trades placed"""
import ccxt
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from script directory
script_dir = Path(__file__).parent
env_path = script_dir / '.env'
print(f"Loading .env from: {env_path}")
print(f"File exists: {env_path.exists()}")
load_dotenv(env_path)

api_key = os.getenv('EXCHANGE_API_KEY')
api_secret = os.getenv('EXCHANGE_SECRET_KEY')

if not api_key or not api_secret:
    print("ERROR: API keys not found in .env file")
    print(f"EXCHANGE_API_KEY present: {bool(api_key)}")
    print(f"EXCHANGE_SECRET_KEY present: {bool(api_secret)}")
    sys.exit(1)

exchange = ccxt.kraken({
    'apiKey': api_key,
    'secret': api_secret,
})

print('=== KRAKEN HEALTH CHECK ===')
print()

# Check balance
balance = exchange.fetch_balance()
print('💰 BALANCES:')
for currency, amount in balance['total'].items():
    if amount > 0:
        print(f'   {currency}: {amount:.4f}')

print()

# Check open orders
orders = exchange.fetch_open_orders()
print(f'📋 OPEN ORDERS: {len(orders)}')
for order in orders:
    print(f'   {order["side"].upper()} {order["amount"]} {order["symbol"]} @ ${order["price"]}')

print()

# Check UNI price
ticker = exchange.fetch_ticker('UNI/USD')
print(f'📊 UNI/USD: ${ticker["last"]:.4f}')
if ticker.get("percentage"):
    print(f'   24h Change: {ticker["percentage"]:+.2f}%')

print()
print('✅ Connection OK - No trades placed')

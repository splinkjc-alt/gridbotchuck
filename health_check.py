"""Quick health check - no trades placed"""

import os
from pathlib import Path
import sys

import ccxt
from dotenv import load_dotenv

# Load .env from script directory
script_dir = Path(__file__).parent
env_path = script_dir / ".env"
load_dotenv(env_path)

api_key = os.getenv("EXCHANGE_API_KEY")
api_secret = os.getenv("EXCHANGE_SECRET_KEY")

if not api_key or not api_secret:
    sys.exit(1)

exchange = ccxt.kraken(
    {
        "apiKey": api_key,
        "secret": api_secret,
    }
)


# Check balance
balance = exchange.fetch_balance()
for _currency, amount in balance["total"].items():
    if amount > 0:
        pass


# Check open orders
orders = exchange.fetch_open_orders()
for _order in orders:
    pass


# Check UNI price
ticker = exchange.fetch_ticker("UNI/USD")
if ticker.get("percentage"):
    pass

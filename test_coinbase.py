"""Quick test to see what's available on Coinbase."""
import os

import ccxt
from dotenv import load_dotenv

load_dotenv()

def test_coinbase():
    # Convert literal \n to actual newlines for EC private key
    secret = os.getenv("COINBASE_SECRET_KEY").replace("\\n", "\n")

    exchange = ccxt.coinbase({
        "apiKey": os.getenv("COINBASE_API_KEY"),
        "secret": secret,
        "enableRateLimit": True,
    })

    try:
        # Load markets
        markets = exchange.load_markets()

        # Find USD pairs
        usd_pairs = [symbol for symbol in markets if "/USD" in symbol and markets[symbol]["active"]]


        # Test fetching OHLCV for XRP/USD
        if "XRP/USD" in usd_pairs:
            exchange.fetch_ohlcv("XRP/USD", "5m", limit=10)
        else:
            [s for s in usd_pairs if "XRP" in s]

    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coinbase()

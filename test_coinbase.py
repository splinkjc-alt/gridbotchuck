"""Quick test to see what's available on Coinbase."""
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

def test_coinbase():
    # Convert literal \n to actual newlines for EC private key
    secret = os.getenv('COINBASE_SECRET_KEY').replace('\\n', '\n')

    exchange = ccxt.coinbase({
        'apiKey': os.getenv('COINBASE_API_KEY'),
        'secret': secret,
        'enableRateLimit': True,
    })

    try:
        # Load markets
        print("Loading Coinbase markets...")
        markets = exchange.load_markets()

        # Find USD pairs
        usd_pairs = [symbol for symbol in markets.keys() if '/USD' in symbol and markets[symbol]['active']]

        print(f"\nFound {len(usd_pairs)} active USD pairs:")
        print(usd_pairs[:20])  # Show first 20

        # Test fetching OHLCV for XRP/USD
        if 'XRP/USD' in usd_pairs:
            print("\nTesting XRP/USD OHLCV fetch...")
            ohlcv = exchange.fetch_ohlcv('XRP/USD', '5m', limit=10)
            print(f"Got {len(ohlcv)} candles")
            print(f"Latest: {ohlcv[-1]}")
        else:
            print("\nXRP/USD not found! Available XRP pairs:")
            xrp_pairs = [s for s in usd_pairs if 'XRP' in s]
            print(xrp_pairs)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_coinbase()

import yfinance as yf
import ccxt
import pandas as pd
import config
from strategies import long_term, strategic, risk, trading


class MarketScanner:
    def __init__(self):
        self.currency = config.CURRENCY
        self.scan_limit = config.SCAN_LIMIT

    def get_ai_stocks(self):
        """Returns the configured list of AI stocks."""
        stocks = config.AI_STOCKS
        if self.scan_limit:
            return stocks[: self.scan_limit]
        return stocks

    def get_ai_crypto_pairs(self):
        """Returns a list of AI-related crypto pairs."""
        pairs = [f"{token}/{self.currency}" for token in config.AI_CRYPTO_TOKENS]
        if self.scan_limit:
            return pairs[: self.scan_limit]
        return pairs

    def get_stock_data(self, symbol):
        """Fetches historical data for a stock symbol."""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="2y")
            return hist
        except Exception:
            return None

    def get_crypto_data(self, symbol):
        """Fetches historical data for a crypto pair."""
        try:
            exchange = ccxt.coinbase()
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe="1d", limit=300)
            if ohlcv:
                df = pd.DataFrame(
                    ohlcv,
                    columns=["Timestamp", "Open", "High", "Low", "Close", "Volume"],
                )
                df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="ms")
                df.set_index("Timestamp", inplace=True)
                return df
        except Exception:
            return None
        return None

    def analyze_asset(self, ticker, data):
        """Runs all strategies on the provided data."""
        if data is None or data.empty:
            return None

        return {
            "Long-Term": (ticker, long_term.analyze(ticker, data)),
            "Strategic": (ticker, strategic.analyze(ticker, data)),
            "Risk": (ticker, risk.analyze(ticker, data)),
            "Trading": (ticker, trading.analyze(ticker, data)),
        }


def run_cli_scan():
    scanner = MarketScanner()

    # 1. Get Asset Lists
    stocks = scanner.get_ai_stocks()
    crypto = scanner.get_ai_crypto_pairs()

    results = {"Long-Term": [], "Strategic": [], "Risk": [], "Trading": []}

    print(f"Scanning {len(stocks)} Stocks...")
    for i, ticker in enumerate(stocks):
        print(f"  [{i+1}/{len(stocks)}] Fetching {ticker}...", end="\r")
        data = scanner.get_stock_data(ticker)
        analysis = scanner.analyze_asset(ticker, data)
        if analysis:
            for category, result in analysis.items():
                results[category].append(result)

    print(f"\nScanning {len(crypto)} Crypto Pairs...")
    for i, ticker in enumerate(crypto):
        print(f"  [{i+1}/{len(crypto)}] Fetching {ticker}...", end="\r")
        data = scanner.get_crypto_data(ticker)
        analysis = scanner.analyze_asset(ticker, data)
        if analysis:
            for category, result in analysis.items():
                results[category].append(result)

    print("\n" + "=" * 60)
    print("MARKET SCANNER RESULTS - TOP 5 PICKS")
    print("=" * 60)

    # Process and Print Top 5 for each category
    categories = {
        "Long-Term": "Strongest Trend (Price vs 200 SMA)",
        "Strategic": "Best Momentum (1-Month Return)",
        "Risk": "Safest Assets (Lowest Volatility)",
        "Trading": "Best Dip Buy Opportunities (Lowest RSI)",
    }

    for cat, desc in categories.items():
        print(f"\n[{cat} Investor] - {desc}")
        print(f"{'Rank':<5} {'Asset':<10} {'Score':<10}")
        print("-" * 30)

        # Sort descending
        sorted_picks = sorted(results[cat], key=lambda x: x[1], reverse=True)

        for i, (asset, score) in enumerate(sorted_picks[:5], 1):
            score_display = f"{score:.2f}" if score != -999 else "N/A"
            print(f"{i:<5} {asset:<10} {score_display}")


if __name__ == "__main__":
    run_cli_scan()

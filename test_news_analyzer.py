"""
Test script for the News Analyzer module.
"""

import logging
from news_analyzer import NewsAnalyzer, SentimentAnalyzer, NewsBacktester

logging.basicConfig(level=logging.INFO)


def test_sentiment():
    """Test sentiment analysis on sample headlines."""
    print("\n" + "=" * 60)
    print("TESTING SENTIMENT ANALYZER")
    print("=" * 60)

    analyzer = SentimentAnalyzer()

    headlines = [
        "Apple stock surges after record iPhone sales beat expectations",
        "Tesla shares plunge on disappointing delivery numbers",
        "NVIDIA announces breakthrough AI chip technology",
        "Amazon faces antitrust investigation from regulators",
        "Microsoft reports strong quarterly earnings growth",
        "Crypto exchange Coinbase hit by security concerns",
        "Meta stock rallies on advertising revenue boost",
    ]

    for headline in headlines:
        result = analyzer.analyze(headline)
        emoji = "+" if result.score > 0.15 else ("-" if result.score < -0.15 else "~")
        print(f"\n{emoji} {result.label.upper()} ({result.score:+.2f})")
        print(f"  \"{headline[:60]}...\"")
        print(f"  Keywords: {', '.join([k[0] for k in result.keywords[:5]])}")


def test_news_fetch():
    """Test news fetching (requires API keys)."""
    print("\n" + "=" * 60)
    print("TESTING NEWS FETCHER")
    print("=" * 60)

    analyzer = NewsAnalyzer()

    # Test with a single symbol
    signal = analyzer.analyze_symbol("NVDA", track=False)

    print(f"\nSymbol: {signal.symbol}")
    print(f"Sentiment: {signal.sentiment} ({signal.score:+.2f})")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Headlines: {signal.headline_count}")
    print(f"Recommendation: {signal.recommendation}")
    print(f"Reason: {signal.reason}")

    if signal.top_headlines:
        print("\nTop Headlines:")
        for h in signal.top_headlines[:3]:
            print(f"  - {h[:70]}...")


def test_backtester():
    """Test the backtester."""
    print("\n" + "=" * 60)
    print("TESTING BACKTESTER")
    print("=" * 60)

    backtester = NewsBacktester()

    # Generate report from stored predictions
    report = backtester.generate_backtest_report()
    print(report)


if __name__ == "__main__":
    # Test sentiment (no API keys needed)
    test_sentiment()

    # Test news fetch (needs API keys)
    print("\n\nNote: News fetching requires API keys in .env")
    print("Get free keys from:")
    print("  - Finnhub: https://finnhub.io/")
    print("  - Alpha Vantage: https://www.alphavantage.co/")
    print("  - NewsAPI: https://newsapi.org/")

    try:
        test_news_fetch()
    except Exception as e:
        print(f"\nNews fetch test skipped: {e}")

    try:
        test_backtester()
    except Exception as e:
        print(f"\nBacktest test skipped: {e}")

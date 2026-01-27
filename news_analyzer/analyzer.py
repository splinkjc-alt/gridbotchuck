"""
News Analyzer - Main Module
===========================
Combines news fetching, sentiment analysis, and tracking.
"""

import logging
from typing import Optional
from dataclasses import dataclass

import yfinance as yf

from .fetcher import NewsFetcher
from .sentiment import SentimentAnalyzer, SentimentResult
from .tracker import NewsTracker

logger = logging.getLogger(__name__)


@dataclass
class NewsSignal:
    """A trading signal from news analysis."""

    symbol: str
    sentiment: str  # "bullish", "bearish", "neutral"
    score: float  # -1 to +1
    confidence: float  # 0 to 1
    headline_count: int
    top_headlines: list[str]
    sources: list[str]
    recommendation: str  # "buy", "sell", "hold", "avoid"
    reason: str


class NewsAnalyzer:
    """
    Main news analyzer class.

    Fetches news, analyzes sentiment, tracks predictions,
    and generates trading signals.
    """

    def __init__(self, db_path: str = None):
        self.fetcher = NewsFetcher()
        self.sentiment = SentimentAnalyzer()
        self.tracker = NewsTracker(db_path)

        # Company name mappings for better news search
        self.company_names = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google Alphabet",
            "AMZN": "Amazon",
            "META": "Meta Facebook",
            "TSLA": "Tesla",
            "NVDA": "NVIDIA",
            "AMD": "AMD Advanced Micro",
            "PLTR": "Palantir",
            "HOOD": "Robinhood",
            "COIN": "Coinbase",
            "SHOP": "Shopify",
            "SOFI": "SoFi",
            "MARA": "Marathon Digital",
            "RIOT": "Riot Platforms",
        }

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period="1d")
            if not data.empty:
                return data["Close"].iloc[-1]
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
        return None

    def analyze_symbol(self, symbol: str, track: bool = True) -> NewsSignal:
        """
        Analyze news for a symbol and generate a signal.

        Args:
            symbol: Stock symbol (e.g., "AAPL")
            track: Whether to track predictions in database

        Returns:
            NewsSignal with recommendation
        """
        company_name = self.company_names.get(symbol)

        # Fetch news from all sources
        articles = self.fetcher.fetch_all(symbol, company_name)

        if not articles:
            return NewsSignal(
                symbol=symbol,
                sentiment="neutral",
                score=0,
                confidence=0,
                headline_count=0,
                top_headlines=[],
                sources=[],
                recommendation="hold",
                reason="No recent news found",
            )

        # Analyze sentiment of all headlines
        headlines = [a.headline for a in articles[:20]]  # Top 20 recent
        aggregate = self.sentiment.analyze_multiple(headlines)

        # Get unique sources
        sources = list(set(a.source for a in articles[:20]))

        # Get current price for tracking
        current_price = self.get_current_price(symbol)

        # Track predictions
        if track and current_price:
            for article in articles[:10]:  # Track top 10
                result = self.sentiment.analyze(article.headline)
                self.tracker.add_prediction(
                    symbol=symbol,
                    headline=article.headline,
                    summary=article.summary[:500] if article.summary else "",
                    source=article.source,
                    api_source=article.api_source,
                    url=article.url,
                    sentiment_score=result.score,
                    sentiment_label=result.label,
                    confidence=result.confidence,
                    price_at_news=current_price,
                    news_published_at=article.published,
                )

        # Generate recommendation
        recommendation, reason = self._generate_recommendation(
            aggregate, len(articles), sources
        )

        return NewsSignal(
            symbol=symbol,
            sentiment=aggregate.label,
            score=aggregate.score,
            confidence=aggregate.confidence,
            headline_count=len(articles),
            top_headlines=headlines[:5],
            sources=sources[:10],
            recommendation=recommendation,
            reason=reason,
        )

    def _generate_recommendation(
        self, sentiment: SentimentResult, article_count: int, sources: list
    ) -> tuple[str, str]:
        """Generate trading recommendation from sentiment analysis."""

        # Need minimum data
        if article_count < 3:
            return "hold", "Insufficient news data"

        # High confidence bullish
        if sentiment.score > 0.3 and sentiment.confidence > 0.5:
            return (
                "buy",
                f"Strong bullish sentiment ({sentiment.score:.2f}) with high confidence",
            )

        # Moderate bullish
        elif sentiment.score > 0.15 and sentiment.confidence > 0.3:
            return "buy", f"Positive news sentiment ({sentiment.score:.2f})"

        # High confidence bearish
        elif sentiment.score < -0.3 and sentiment.confidence > 0.5:
            return (
                "avoid",
                f"Strong bearish sentiment ({sentiment.score:.2f}) - wait for reversal",
            )

        # Moderate bearish
        elif sentiment.score < -0.15 and sentiment.confidence > 0.3:
            return "sell", f"Negative news sentiment ({sentiment.score:.2f})"

        # Neutral or low confidence
        else:
            return (
                "hold",
                f"Neutral sentiment ({sentiment.score:.2f}) or low confidence",
            )

    def scan_watchlist(
        self, symbols: list[str], track: bool = True
    ) -> list[NewsSignal]:
        """
        Scan multiple symbols and return sorted signals.

        Returns signals sorted by absolute sentiment score (strongest first).
        """
        signals = []

        for symbol in symbols:
            try:
                signal = self.analyze_symbol(symbol, track=track)
                signals.append(signal)
                logger.info(
                    f"{symbol}: {signal.sentiment} ({signal.score:.2f}) - {signal.recommendation}"
                )
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")

        # Sort by absolute score (strongest signals first)
        signals.sort(key=lambda x: abs(x.score), reverse=True)

        return signals

    def update_outcomes(self):
        """
        Update outcomes for pending predictions.

        Call this periodically to track prediction accuracy.
        """
        for hours in [1, 4, 24]:
            pending = self.tracker.get_pending_outcomes(hours)

            for pred_id, symbol, created_at in pending:
                try:
                    price = self.get_current_price(symbol)
                    if price:
                        self.tracker.update_outcome(pred_id, price, hours)
                        logger.debug(f"Updated {hours}h outcome for {symbol}")
                except Exception as e:
                    logger.error(f"Error updating outcome for {symbol}: {e}")

    def get_source_rankings(self) -> str:
        """Get news source accuracy rankings."""
        return self.tracker.generate_report()

    def filter_by_trusted_sources(
        self, signal: NewsSignal, min_accuracy: float = 55
    ) -> bool:
        """
        Check if signal comes from trusted (accurate) sources.

        Args:
            signal: The news signal to check
            min_accuracy: Minimum 24h accuracy percentage

        Returns:
            True if signal should be trusted
        """
        stats = self.tracker.get_source_stats(min_predictions=10)
        trusted_sources = {s.source for s in stats if s.accuracy_24h >= min_accuracy}

        # Check if any of signal's sources are trusted
        signal_sources = set(signal.sources)
        trusted_in_signal = signal_sources & trusted_sources

        return len(trusted_in_signal) > 0


def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    analyzer = NewsAnalyzer()

    # Analyze a single stock
    print("\nAnalyzing NVDA...")
    signal = analyzer.analyze_symbol("NVDA")

    print(f"\nSymbol: {signal.symbol}")
    print(f"Sentiment: {signal.sentiment} ({signal.score:.2f})")
    print(f"Confidence: {signal.confidence:.2f}")
    print(f"Headlines analyzed: {signal.headline_count}")
    print(f"Recommendation: {signal.recommendation}")
    print(f"Reason: {signal.reason}")
    print("\nTop Headlines:")
    for h in signal.top_headlines:
        print(f"  - {h[:80]}...")

    # Get source rankings
    print("\n" + analyzer.get_source_rankings())


if __name__ == "__main__":
    main()

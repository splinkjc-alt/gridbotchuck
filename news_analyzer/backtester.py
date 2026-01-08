"""
News Source Backtester
======================
Backtests news sources to determine which are most accurate
for predicting stock price movements.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass

import yfinance as yf
import pandas as pd

from .sentiment import SentimentAnalyzer
from .tracker import NewsTracker

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from backtesting a news source."""
    source: str
    total_predictions: int
    correct_1h: int
    correct_4h: int
    correct_24h: int
    accuracy_1h: float
    accuracy_4h: float
    accuracy_24h: float
    avg_return_bullish: float
    avg_return_bearish: float
    best_symbols: list[str]
    worst_symbols: list[str]


class NewsBacktester:
    """
    Backtests news predictions against historical price data.

    Can run backtests on:
    1. Live predictions stored in the database
    2. Historical news data (if available)
    """

    def __init__(self, tracker: NewsTracker = None):
        self.tracker = tracker or NewsTracker()
        self.sentiment = SentimentAnalyzer()
        self._price_cache = {}

    def get_historical_prices(self, symbol: str,
                              start_date: datetime,
                              end_date: datetime = None) -> Optional[pd.DataFrame]:
        """
        Get historical price data for a symbol.

        Uses yfinance for free historical data.
        """
        if end_date is None:
            end_date = datetime.now()

        cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
        if cache_key in self._price_cache:
            return self._price_cache[cache_key]

        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=start_date, end=end_date, interval="1h")

            if not df.empty:
                self._price_cache[cache_key] = df
                return df
        except Exception as e:
            logger.error(f"Error fetching prices for {symbol}: {e}")

        return None

    def get_price_at_time(self, symbol: str, target_time: datetime) -> Optional[float]:
        """Get price closest to a specific time."""
        start = target_time - timedelta(days=1)
        end = target_time + timedelta(days=2)

        prices = self.get_historical_prices(symbol, start, end)
        if prices is None or prices.empty:
            return None

        # Find closest time
        prices.index = prices.index.tz_localize(None)
        time_diffs = abs(prices.index - target_time)
        closest_idx = time_diffs.argmin()

        return prices['Close'].iloc[closest_idx]

    def backtest_prediction(self, symbol: str,
                           prediction_time: datetime,
                           sentiment_score: float) -> dict:
        """
        Backtest a single prediction.

        Returns actual price changes at 1h, 4h, 24h.
        """
        price_at_prediction = self.get_price_at_time(symbol, prediction_time)
        if not price_at_prediction:
            return None

        results = {
            'price_at_prediction': price_at_prediction,
            'sentiment_score': sentiment_score,
            'predicted_direction': 'up' if sentiment_score > 0.15 else ('down' if sentiment_score < -0.15 else 'neutral')
        }

        # Check prices at different intervals
        for hours in [1, 4, 24]:
            future_time = prediction_time + timedelta(hours=hours)
            future_price = self.get_price_at_time(symbol, future_time)

            if future_price:
                pct_change = ((future_price - price_at_prediction) / price_at_prediction) * 100

                if pct_change > 0.5:
                    actual_direction = 'up'
                elif pct_change < -0.5:
                    actual_direction = 'down'
                else:
                    actual_direction = 'neutral'

                correct = (results['predicted_direction'] == actual_direction) or \
                         (results['predicted_direction'] == 'neutral' and abs(pct_change) < 1)

                results[f'price_{hours}h'] = future_price
                results[f'pct_change_{hours}h'] = pct_change
                results[f'actual_direction_{hours}h'] = actual_direction
                results[f'correct_{hours}h'] = correct

        return results

    def run_backtest_on_stored(self, min_predictions: int = 10) -> list[BacktestResult]:
        """
        Run backtest on predictions stored in the database.

        Returns accuracy stats for each news source.
        """
        stats = self.tracker.get_source_stats(min_predictions=min_predictions)

        results = []
        for s in stats:
            results.append(BacktestResult(
                source=s.source,
                total_predictions=s.total_predictions,
                correct_1h=s.correct_1h,
                correct_4h=s.correct_4h,
                correct_24h=s.correct_24h,
                accuracy_1h=s.accuracy_1h,
                accuracy_4h=s.accuracy_4h,
                accuracy_24h=s.accuracy_24h,
                avg_return_bullish=0,  # Would need more data
                avg_return_bearish=0,
                best_symbols=[],
                worst_symbols=[]
            ))

        return results

    def update_all_outcomes(self):
        """
        Update outcomes for all pending predictions.

        Call this periodically to fill in actual price movements.
        """
        updated_count = 0

        for hours in [1, 4, 24]:
            pending = self.tracker.get_pending_outcomes(hours)

            for pred_id, symbol, created_at in pending:
                try:
                    # Parse created_at if string
                    if isinstance(created_at, str):
                        created_at = datetime.fromisoformat(created_at)

                    # Get price at the appropriate future time
                    target_time = created_at + timedelta(hours=hours)
                    if target_time > datetime.now():
                        continue  # Not enough time elapsed

                    price = self.get_price_at_time(symbol, target_time)
                    if price:
                        self.tracker.update_outcome(pred_id, price, hours)
                        updated_count += 1
                        logger.debug(f"Updated {hours}h outcome for prediction {pred_id}")

                except Exception as e:
                    logger.error(f"Error updating outcome for prediction {pred_id}: {e}")

        return updated_count

    def generate_backtest_report(self) -> str:
        """Generate a detailed backtest report."""
        results = self.run_backtest_on_stored(min_predictions=5)

        if not results:
            return "No backtest data available yet. Need more predictions with outcomes."

        report = []
        report.append("=" * 70)
        report.append("NEWS SOURCE BACKTEST REPORT")
        report.append("=" * 70)
        report.append("")

        # Summary table
        report.append(f"{'Source':<25} {'Total':>6} {'1h Acc':>8} {'4h Acc':>8} {'24h Acc':>8}")
        report.append("-" * 70)

        for r in sorted(results, key=lambda x: x.accuracy_24h, reverse=True):
            report.append(
                f"{r.source[:24]:<25} {r.total_predictions:>6} "
                f"{r.accuracy_1h:>7.1f}% {r.accuracy_4h:>7.1f}% {r.accuracy_24h:>7.1f}%"
            )

        report.append("")

        # Best and worst performers
        if len(results) >= 2:
            best = max(results, key=lambda x: x.accuracy_24h)
            worst = min(results, key=lambda x: x.accuracy_24h)

            report.append("RECOMMENDATIONS:")
            report.append(f"  Best source (24h):  {best.source} ({best.accuracy_24h:.1f}%)")
            report.append(f"  Worst source (24h): {worst.source} ({worst.accuracy_24h:.1f}%)")

            # Calculate trust threshold
            avg_accuracy = sum(r.accuracy_24h for r in results) / len(results)
            report.append(f"  Average accuracy:   {avg_accuracy:.1f}%")
            report.append(f"  Trust threshold:    {max(50, avg_accuracy):.1f}%")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)


def main():
    """Example backtest run."""
    logging.basicConfig(level=logging.INFO)

    backtester = NewsBacktester()

    # Update outcomes for stored predictions
    print("Updating outcomes...")
    updated = backtester.update_all_outcomes()
    print(f"Updated {updated} outcomes")

    # Generate report
    print("\n" + backtester.generate_backtest_report())


if __name__ == "__main__":
    main()

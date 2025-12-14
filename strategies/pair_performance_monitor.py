"""
Pair Performance Monitor - Detects stuck/underperforming pairs and suggests replacements.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Dict, List

from core.services.exchange_interface import ExchangeInterface


@dataclass
class PairPerformance:
    """Performance metrics for a trading pair."""

    pair: str
    volatility_15m: float  # 15-minute price volatility %
    volatility_1h: float  # 1-hour price volatility %
    volume_24h: float  # 24-hour trading volume
    price_change_1h: float  # Price change in last hour %
    price_change_24h: float  # Price change in 24 hours %
    last_trade_time: datetime = None
    trades_last_hour: int = 0
    is_stuck: bool = False
    performance_score: float = 0.0


class PairPerformanceMonitor:
    """
    Monitors trading pairs to detect:
    1. Stuck markets (no price movement / low volatility)
    2. Better performing alternative pairs
    3. Optimal times to switch pairs
    """

    # Thresholds for detecting stuck pairs
    MIN_VOLATILITY_15M = 0.3  # Minimum 0.3% price movement in 15min
    MIN_VOLATILITY_1H = 0.8  # Minimum 0.8% price movement in 1hr
    MIN_TRADES_PER_HOUR = 3  # Minimum trades per hour to stay active

    def __init__(self, exchange_service: ExchangeInterface, check_interval: int = 300):
        """
        Initialize performance monitor.

        Args:
            exchange_service: Exchange service for fetching market data
            check_interval: How often to check performance (seconds)
        """
        self.exchange_service = exchange_service
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)

        self.pair_metrics: Dict[str, PairPerformance] = {}
        self.monitoring = False

    async def analyze_pair(self, pair: str) -> PairPerformance:
        """
        Analyze current performance of a trading pair.

        Args:
            pair: Trading pair symbol (e.g., 'XLM/USD')

        Returns:
            PairPerformance metrics
        """
        try:
            # Fetch recent OHLCV data
            ohlcv_15m = await self.exchange_service.fetch_ohlcv(pair, "15m", limit=10)
            ohlcv_1h = await self.exchange_service.fetch_ohlcv(pair, "1h", limit=24)

            if not ohlcv_15m or not ohlcv_1h:
                self.logger.warning(f"No data available for {pair}")
                return None

            # Calculate 15m volatility
            vol_15m = self._calculate_volatility(ohlcv_15m[-10:])

            # Calculate 1h volatility
            vol_1h = self._calculate_volatility(ohlcv_1h[-6:])

            # Calculate price changes
            price_change_1h = self._calculate_price_change(ohlcv_1h, hours=1)
            price_change_24h = self._calculate_price_change(ohlcv_1h, hours=24)

            # Get 24h volume
            volume_24h = sum(candle[5] for candle in ohlcv_1h[-24:])

            # Determine if pair is stuck
            is_stuck = vol_15m < self.MIN_VOLATILITY_15M or vol_1h < self.MIN_VOLATILITY_1H

            # Calculate performance score (higher is better)
            performance_score = self._calculate_performance_score(vol_15m, vol_1h, volume_24h, abs(price_change_1h))

            metrics = PairPerformance(
                pair=pair,
                volatility_15m=vol_15m,
                volatility_1h=vol_1h,
                volume_24h=volume_24h,
                price_change_1h=price_change_1h,
                price_change_24h=price_change_24h,
                is_stuck=is_stuck,
                performance_score=performance_score,
            )

            self.pair_metrics[pair] = metrics

            status = "🔴 STUCK" if is_stuck else "✅ ACTIVE"
            self.logger.info(
                f"{status} {pair}: vol_15m={vol_15m:.2f}%, vol_1h={vol_1h:.2f}%, "
                f"score={performance_score:.1f}"
            )

            return metrics

        except Exception as e:
            self.logger.error(f"Error analyzing {pair}: {e}")
            return None

    def _calculate_volatility(self, candles: List) -> float:
        """
        Calculate price volatility from OHLCV candles.

        Args:
            candles: List of OHLCV candles [timestamp, open, high, low, close, volume]

        Returns:
            Volatility as percentage
        """
        if not candles or len(candles) < 2:
            return 0.0

        prices = [candle[4] for candle in candles]  # Close prices
        max_price = max(prices)
        min_price = min(prices)
        avg_price = sum(prices) / len(prices)

        if avg_price == 0:
            return 0.0

        volatility = ((max_price - min_price) / avg_price) * 100
        return volatility

    def _calculate_price_change(self, candles: List, hours: int) -> float:
        """
        Calculate price change over specified hours.

        Args:
            candles: List of 1h OHLCV candles
            hours: Number of hours to look back

        Returns:
            Price change as percentage
        """
        if not candles or len(candles) < hours:
            return 0.0

        start_price = candles[-hours][4]  # Close price N hours ago
        end_price = candles[-1][4]  # Latest close price

        if start_price == 0:
            return 0.0

        change = ((end_price - start_price) / start_price) * 100
        return change

    def _calculate_performance_score(
        self, vol_15m: float, vol_1h: float, volume: float, price_momentum: float
    ) -> float:
        """
        Calculate overall performance score for a pair.
        Higher score = better for grid trading.

        Args:
            vol_15m: 15-minute volatility %
            vol_1h: 1-hour volatility %
            volume: 24h trading volume
            price_momentum: Absolute price change %

        Returns:
            Performance score (0-100)
        """
        # Weights for each factor
        vol_15m_weight = 30
        vol_1h_weight = 30
        volume_weight = 20
        momentum_weight = 20

        # Normalize each component (0-100 scale)
        vol_15m_score = min(100, (vol_15m / 2.0) * 100)  # 2% vol = 100 points
        vol_1h_score = min(100, (vol_1h / 5.0) * 100)  # 5% vol = 100 points
        volume_score = min(100, (volume / 100000) * 100)  # Simplified volume scoring
        momentum_score = min(100, (price_momentum / 5.0) * 100)  # 5% move = 100 points

        # Calculate weighted score
        total_score = (
            vol_15m_score * vol_15m_weight / 100
            + vol_1h_score * vol_1h_weight / 100
            + volume_score * volume_weight / 100
            + momentum_score * momentum_weight / 100
        )

        return total_score

    async def find_better_pair(self, current_pair: str, candidate_pairs: List[str]) -> str | None:
        """
        Find a better performing pair than the current one.

        Args:
            current_pair: Current trading pair
            candidate_pairs: List of alternative pairs to consider

        Returns:
            Better pair symbol, or None if no better option found
        """
        current_metrics = await self.analyze_pair(current_pair)

        if not current_metrics:
            return None

        best_pair = None
        best_score = current_metrics.performance_score

        self.logger.info(f"Searching for better alternative to {current_pair} (score: {best_score:.1f})")

        for pair in candidate_pairs:
            if pair == current_pair:
                continue

            metrics = await self.analyze_pair(pair)

            if metrics and metrics.performance_score > best_score * 1.3:  # Must be 30% better
                best_pair = pair
                best_score = metrics.performance_score

            # Rate limiting - small delay between checks
            await asyncio.sleep(0.5)

        if best_pair:
            improvement = ((best_score / current_metrics.performance_score) - 1) * 100
            self.logger.info(f"✨ Found better pair: {best_pair} (score: {best_score:.1f}, +{improvement:.0f}% better)")
        else:
            self.logger.info(f"No significantly better alternative found for {current_pair}")

        return best_pair

    async def should_replace_pair(self, pair: str, last_trade_time: datetime = None, trades_count: int = 0) -> bool:
        """
        Determine if a pair should be replaced due to poor performance.

        Args:
            pair: Trading pair to evaluate
            last_trade_time: Time of last successful trade
            trades_count: Number of trades in last hour

        Returns:
            True if pair should be replaced
        """
        metrics = await self.analyze_pair(pair)

        if not metrics:
            return False

        # Check if stuck
        if metrics.is_stuck:
            self.logger.warning(f"⚠️ {pair} is STUCK (low volatility)")
            return True

        # Check if no recent trades
        if last_trade_time:
            time_since_trade = datetime.now() - last_trade_time
            if time_since_trade > timedelta(hours=2):
                self.logger.warning(f"⚠️ {pair} has no trades for {time_since_trade.total_seconds()/3600:.1f} hours")
                return True

        # Check trade frequency
        if trades_count < self.MIN_TRADES_PER_HOUR:
            self.logger.warning(f"⚠️ {pair} has only {trades_count} trades/hour (minimum: {self.MIN_TRADES_PER_HOUR})")
            return True

        return False

    def get_top_performers(self, n: int = 5) -> List[PairPerformance]:
        """
        Get top N performing pairs from monitored pairs.

        Args:
            n: Number of top pairs to return

        Returns:
            List of top performing pairs
        """
        sorted_pairs = sorted(self.pair_metrics.values(), key=lambda x: x.performance_score, reverse=True)

        return sorted_pairs[:n]

    def get_pair_status(self, pair: str) -> Dict:
        """Get current status of a trading pair."""
        metrics = self.pair_metrics.get(pair)

        if not metrics:
            return {"pair": pair, "status": "not_monitored"}

        return {
            "pair": metrics.pair,
            "is_stuck": metrics.is_stuck,
            "performance_score": metrics.performance_score,
            "volatility_15m": metrics.volatility_15m,
            "volatility_1h": metrics.volatility_1h,
            "price_change_1h": metrics.price_change_1h,
            "volume_24h": metrics.volume_24h,
        }

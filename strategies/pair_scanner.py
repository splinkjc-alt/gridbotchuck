"""
Pair Scanner Module for GridBot Chuck
======================================

Smart pair scanner that identifies the best trading pairs for grid trading.

Analyzes pairs based on:
- Range-Bound Score (50%): Prefers sideways markets
- Volatility Score (30%): Optimal 2-5% daily volatility
- Volume Score (20%): Ensures sufficient liquidity

Scoring outputs:
- Ranked list of pairs with suitability scores (0-100)
- Auto-generated grid configurations for top pairs
"""

from dataclasses import dataclass
from datetime import datetime
import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd

from core.services.exchange_interface import ExchangeInterface


@dataclass
class PairScanResult:
    """Scan result for a single trading pair."""

    pair: str

    # Overall score (0-100)
    total_score: float
    rank: int

    # Component scores (0-100)
    range_bound_score: float
    volatility_score: float
    volume_score: float

    # Market data
    current_price: float
    price_24h_high: float
    price_24h_low: float
    price_24h_change_pct: float

    # Volatility metrics
    daily_volatility_pct: float
    atr_pct: float  # Average True Range as percentage

    # Volume metrics
    volume_24h: float
    volume_avg: float

    # Grid recommendations
    suggested_grid_top: float
    suggested_grid_bottom: float
    suggested_num_grids: int

    # Quality flags
    is_range_bound: bool
    has_good_volume: bool
    volatility_optimal: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/display."""
        return {
            "pair": self.pair,
            "rank": self.rank,
            "total_score": round(self.total_score, 1),
            "scores": {
                "range_bound": round(self.range_bound_score, 1),
                "volatility": round(self.volatility_score, 1),
                "volume": round(self.volume_score, 1),
            },
            "market_data": {
                "current_price": round(self.current_price, 6),
                "high_24h": round(self.price_24h_high, 6),
                "low_24h": round(self.price_24h_low, 6),
                "change_24h_pct": round(self.price_24h_change_pct, 2),
            },
            "volatility": {
                "daily_pct": round(self.daily_volatility_pct, 2),
                "atr_pct": round(self.atr_pct, 2),
            },
            "volume": {
                "volume_24h": round(self.volume_24h, 2),
                "volume_avg": round(self.volume_avg, 2),
            },
            "grid_config": {
                "top": round(self.suggested_grid_top, 6),
                "bottom": round(self.suggested_grid_bottom, 6),
                "num_grids": self.suggested_num_grids,
            },
            "quality": {
                "is_range_bound": self.is_range_bound,
                "has_good_volume": self.has_good_volume,
                "volatility_optimal": self.volatility_optimal,
            },
        }

    def to_config(
        self, exchange_name: str = "kraken", initial_balance: float = 100.0
    ) -> dict:
        """Generate a config.json compatible configuration."""
        return {
            "exchange": {
                "name": exchange_name,
                "trading_fee": 0.0026,
                "trading_mode": "paper_trading",
            },
            "pair": {
                "base_currency": self.pair.split("/")[0],
                "quote_currency": self.pair.split("/")[1],
            },
            "trading_settings": {
                "timeframe": "15m",
                "period": {
                    "start_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "end_date": None,  # Live trading
                },
                "initial_balance": initial_balance,
            },
            "grid_strategy": {
                "type": "hedged_grid",
                "spacing": "geometric",
                "num_grids": self.suggested_num_grids,
                "range": {
                    "top": self.suggested_grid_top,
                    "bottom": self.suggested_grid_bottom,
                },
            },
            "risk_management": {
                "take_profit": {"enabled": False, "threshold": None},
                "stop_loss": {"enabled": False, "threshold": None},
            },
            "logging": {
                "level": "INFO",
                "log_to_file": True,
            },
            "_scan_metadata": {
                "scanned_at": datetime.utcnow().isoformat(),
                "suitability_score": self.total_score,
                "rank": self.rank,
            },
        }


class PairScanner:
    """
    Smart pair scanner for grid trading opportunities.

    Scans available trading pairs and ranks them by grid trading suitability
    based on volatility, volume, and range-bound behavior.
    """

    # Scoring weights
    WEIGHT_RANGE_BOUND = 0.50  # Most important: is it trading sideways?
    WEIGHT_VOLATILITY = 0.30  # Optimal volatility for profits
    WEIGHT_VOLUME = 0.20  # Enough liquidity

    # Volatility thresholds (daily %)
    VOLATILITY_OPTIMAL_LOW = 2.0
    VOLATILITY_OPTIMAL_HIGH = 5.0
    VOLATILITY_MAX = 15.0

    # Volume thresholds (24h USD)
    VOLUME_MIN_THRESHOLD = 100_000  # $100k minimum
    VOLUME_GOOD_THRESHOLD = 1_000_000  # $1M is good
    VOLUME_EXCELLENT_THRESHOLD = 10_000_000  # $10M is excellent

    def __init__(self, exchange_service: ExchangeInterface):
        self.exchange_service = exchange_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def scan_pairs(
        self,
        pairs: list[str] | None = None,
        quote_currency: str = "USD",
        min_price: float = 0.0001,
        max_price: float = 1000.0,
        min_volume_24h: float = 100_000,
        timeframe: str = "1h",
        lookback_candles: int = 168,  # 7 days of hourly candles
        max_results: int = 20,
    ) -> list[PairScanResult]:
        """
        Scan pairs for grid trading suitability.

        Args:
            pairs: Specific pairs to scan (None = scan all available)
            quote_currency: Quote currency filter (e.g., 'USD', 'USDT')
            min_price: Minimum price filter
            max_price: Maximum price filter
            min_volume_24h: Minimum 24h volume in quote currency
            timeframe: Candle timeframe for analysis
            lookback_candles: Number of candles to analyze
            max_results: Maximum number of results to return

        Returns:
            List of PairScanResult objects, sorted by score (highest first)
        """
        self.logger.info(f"Starting pair scan for {quote_currency} pairs...")

        # Get pairs to scan
        if pairs is None:
            pairs = await self._get_available_pairs(quote_currency)

        self.logger.info(f"Scanning {len(pairs)} pairs...")

        # Analyze each pair
        results: list[PairScanResult] = []

        for pair in pairs:
            try:
                result = await self._analyze_pair(
                    pair=pair,
                    min_price=min_price,
                    max_price=max_price,
                    min_volume_24h=min_volume_24h,
                    timeframe=timeframe,
                    lookback_candles=lookback_candles,
                )
                if result:
                    results.append(result)
                    self.logger.debug(
                        f"Analyzed {pair}: Score={result.total_score:.1f}"
                    )
            except Exception as e:
                self.logger.warning(f"Failed to analyze {pair}: {e}")

        # Sort by score and assign ranks
        results.sort(key=lambda x: x.total_score, reverse=True)
        for i, result in enumerate(results):
            result.rank = i + 1

        # Limit results
        results = results[:max_results]

        self.logger.info(f"Scan complete. Found {len(results)} suitable pairs.")

        return results

    async def _get_available_pairs(self, quote_currency: str) -> list[str]:
        """Get all available trading pairs for a quote currency."""
        try:
            pairs = await self.exchange_service.get_available_pairs(quote_currency)
            self.logger.info(f"Found {len(pairs)} {quote_currency} pairs on exchange")
            return pairs
        except Exception as e:
            self.logger.error(f"Failed to get available pairs: {e}")
            return []

    async def _analyze_pair(
        self,
        pair: str,
        min_price: float,
        max_price: float,
        min_volume_24h: float,
        timeframe: str,
        lookback_candles: int,
    ) -> PairScanResult | None:
        """Analyze a single pair for grid trading suitability."""
        try:
            # Fetch OHLCV data
            ohlcv = await self.exchange_service.fetch_ohlcv_simple(
                pair, timeframe, lookback_candles
            )

            if ohlcv is None or len(ohlcv) < 24:  # Need at least 24 candles
                return None

            # Get current price
            current_price = float(ohlcv["close"].iloc[-1])

            # Price filter
            if current_price < min_price or current_price > max_price:
                return None

            # Calculate metrics
            price_high = float(ohlcv["high"].max())
            price_low = float(ohlcv["low"].min())
            price_24h_high = float(ohlcv["high"].iloc[-24:].max())
            price_24h_low = float(ohlcv["low"].iloc[-24:].min())
            price_24h_change_pct = (
                ((current_price / float(ohlcv["close"].iloc[-24]) - 1) * 100)
                if len(ohlcv) >= 24
                else 0
            )

            # Volume metrics
            volume_24h = (
                float(ohlcv["volume"].iloc[-24:].sum()) * current_price
            )  # Convert to quote currency
            volume_avg = float(ohlcv["volume"].mean()) * current_price

            # Volume filter
            if volume_24h < min_volume_24h:
                return None

            # Calculate volatility metrics
            daily_volatility = self._calculate_daily_volatility(ohlcv)
            atr_pct = self._calculate_atr_percentage(ohlcv)

            # Calculate component scores
            range_bound_score = self._score_range_bound(ohlcv, price_high, price_low)
            volatility_score = self._score_volatility(daily_volatility)
            volume_score = self._score_volume(volume_24h)

            # Calculate total score
            total_score = (
                range_bound_score * self.WEIGHT_RANGE_BOUND
                + volatility_score * self.WEIGHT_VOLATILITY
                + volume_score * self.WEIGHT_VOLUME
            )

            # Generate grid recommendations
            grid_top, grid_bottom = self._calculate_grid_range(ohlcv, current_price)
            num_grids = self._calculate_optimal_grids(
                grid_top, grid_bottom, current_price
            )

            # Quality flags
            is_range_bound = range_bound_score >= 60
            has_good_volume = volume_24h >= self.VOLUME_GOOD_THRESHOLD
            volatility_optimal = (
                self.VOLATILITY_OPTIMAL_LOW
                <= daily_volatility
                <= self.VOLATILITY_OPTIMAL_HIGH
            )

            return PairScanResult(
                pair=pair,
                total_score=total_score,
                rank=0,  # Will be set after sorting
                range_bound_score=range_bound_score,
                volatility_score=volatility_score,
                volume_score=volume_score,
                current_price=current_price,
                price_24h_high=price_24h_high,
                price_24h_low=price_24h_low,
                price_24h_change_pct=price_24h_change_pct,
                daily_volatility_pct=daily_volatility,
                atr_pct=atr_pct,
                volume_24h=volume_24h,
                volume_avg=volume_avg,
                suggested_grid_top=grid_top,
                suggested_grid_bottom=grid_bottom,
                suggested_num_grids=num_grids,
                is_range_bound=is_range_bound,
                has_good_volume=has_good_volume,
                volatility_optimal=volatility_optimal,
            )

        except Exception as e:
            self.logger.debug(f"Error analyzing {pair}: {e}")
            return None

    def _calculate_daily_volatility(self, ohlcv: pd.DataFrame) -> float:
        """Calculate average daily volatility as percentage."""
        # Calculate daily high-low range as percentage of close
        daily_range_pct = ((ohlcv["high"] - ohlcv["low"]) / ohlcv["close"]) * 100
        return float(daily_range_pct.mean())

    def _calculate_atr_percentage(self, ohlcv: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range as percentage of price."""
        high = ohlcv["high"]
        low = ohlcv["low"]
        close = ohlcv["close"].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period).mean().iloc[-1]

        current_price = ohlcv["close"].iloc[-1]
        return (atr / current_price) * 100 if current_price > 0 else 0

    def _score_range_bound(
        self,
        ohlcv: pd.DataFrame,
        price_high: float,
        price_low: float,
    ) -> float:
        """
        Score how range-bound the price action is (0-100).

        Range-bound = price oscillates within a range without strong trend.

        Metrics:
        - Price range consistency (are highs/lows repeated?)
        - Trend strength (lower is better for grid trading)
        - Mean reversion tendency
        """
        close = ohlcv["close"]

        # Calculate trend strength using linear regression slope
        range(len(close))
        slope = pd.Series(close).diff().mean() / close.mean() * 100

        # Higher absolute slope = stronger trend = lower score
        trend_score = max(0, 100 - abs(slope) * 500)

        # Check price oscillation around mean
        mean_price = close.mean()
        crossings = ((close > mean_price).astype(int).diff().abs()).sum()
        oscillation_score = min(100, crossings * 3)  # More crossings = more range-bound

        # Check if price stays within consistent range
        range_pct = (price_high - price_low) / mean_price * 100

        # Ideal range is 5-15%
        if 5 <= range_pct <= 15:
            range_consistency_score = 100
        elif range_pct < 5:
            range_consistency_score = range_pct * 20  # Too narrow
        elif range_pct <= 25:
            range_consistency_score = 100 - (range_pct - 15) * 5  # Slightly wide
        else:
            range_consistency_score = max(0, 50 - (range_pct - 25) * 2)  # Too wide

        # Combine scores
        return (
            trend_score * 0.4 + oscillation_score * 0.3 + range_consistency_score * 0.3
        )

    def _score_volatility(self, daily_volatility: float) -> float:
        """
        Score volatility for grid trading (0-100).

        Optimal volatility: 2-5% daily range
        Too low (<1%): Not enough price movement for profits
        Too high (>10%): Risk of grid being breached
        """
        if (
            self.VOLATILITY_OPTIMAL_LOW
            <= daily_volatility
            <= self.VOLATILITY_OPTIMAL_HIGH
        ):
            # Perfect range
            return 100
        elif daily_volatility < self.VOLATILITY_OPTIMAL_LOW:
            # Too low - scale from 0 at 0% to 100 at optimal low
            return (daily_volatility / self.VOLATILITY_OPTIMAL_LOW) * 100
        elif daily_volatility <= 8:
            # Slightly high but acceptable
            return 100 - (daily_volatility - self.VOLATILITY_OPTIMAL_HIGH) * 10
        elif daily_volatility <= self.VOLATILITY_MAX:
            # High but tradeable
            return max(20, 70 - (daily_volatility - 8) * 7)
        else:
            # Too volatile
            return max(0, 20 - (daily_volatility - self.VOLATILITY_MAX) * 2)

    def _score_volume(self, volume_24h: float) -> float:
        """
        Score volume for grid trading (0-100).

        Higher volume = better liquidity = better fills
        """
        if volume_24h >= self.VOLUME_EXCELLENT_THRESHOLD:
            return 100
        elif volume_24h >= self.VOLUME_GOOD_THRESHOLD:
            # Scale from 80 to 100
            ratio = (volume_24h - self.VOLUME_GOOD_THRESHOLD) / (
                self.VOLUME_EXCELLENT_THRESHOLD - self.VOLUME_GOOD_THRESHOLD
            )
            return 80 + ratio * 20
        elif volume_24h >= self.VOLUME_MIN_THRESHOLD:
            # Scale from 40 to 80
            ratio = (volume_24h - self.VOLUME_MIN_THRESHOLD) / (
                self.VOLUME_GOOD_THRESHOLD - self.VOLUME_MIN_THRESHOLD
            )
            return 40 + ratio * 40
        else:
            # Below minimum
            return max(0, (volume_24h / self.VOLUME_MIN_THRESHOLD) * 40)

    def _calculate_grid_range(
        self,
        ohlcv: pd.DataFrame,
        current_price: float,
        buffer_pct: float = 0.05,
    ) -> tuple[float, float]:
        """
        Calculate optimal grid range based on recent price action.

        Uses recent high/low with a buffer for safety.
        """
        # Use recent data for range (last 7 days of data)
        recent_data = ohlcv.tail(168) if len(ohlcv) >= 168 else ohlcv

        recent_high = float(recent_data["high"].max())
        recent_low = float(recent_data["low"].min())

        # Add buffer
        range_size = recent_high - recent_low
        buffer = range_size * buffer_pct

        grid_top = recent_high + buffer
        grid_bottom = recent_low - buffer

        # Ensure current price is within range
        if current_price > grid_top:
            grid_top = current_price * 1.05
        if current_price < grid_bottom:
            grid_bottom = current_price * 0.95

        return (round(grid_top, 6), round(grid_bottom, 6))

    def _calculate_optimal_grids(
        self,
        grid_top: float,
        grid_bottom: float,
        current_price: float,
    ) -> int:
        """
        Calculate optimal number of grid levels.

        Based on price range and typical trading fee impact.
        """
        range_pct = ((grid_top - grid_bottom) / current_price) * 100

        # More grids for larger ranges, fewer for smaller
        if range_pct >= 20:
            return 15
        elif range_pct >= 15:
            return 12
        elif range_pct >= 10:
            return 10
        elif range_pct >= 7:
            return 8
        elif range_pct >= 5:
            return 6
        else:
            return 5

    def print_scan_results(
        self, results: list[PairScanResult], top_n: int = 10
    ) -> None:
        """Print formatted scan results to console."""

        for result in results[:top_n]:
            # Format volume
            if result.volume_24h >= 1_000_000:
                f"${result.volume_24h / 1_000_000:.1f}M"
            elif result.volume_24h >= 1_000:
                f"${result.volume_24h / 1_000:.1f}K"
            else:
                pass

            # Range quality descriptor
            if (
                result.range_bound_score >= 80
                or result.range_bound_score >= 60
                or result.range_bound_score >= 40
            ):
                pass
            else:
                pass

    async def save_configs(
        self,
        results: list[PairScanResult],
        output_dir: str = "config/scanned_pairs",
        exchange_name: str = "kraken",
        balance_per_pair: float = 100.0,
        max_pairs: int = 10,
    ) -> list[str]:
        """
        Save grid configurations for scanned pairs.

        Args:
            results: Scan results to save
            output_dir: Directory to save configs
            exchange_name: Exchange name for configs
            balance_per_pair: Initial balance per pair
            max_pairs: Maximum number of configs to save

        Returns:
            List of saved config file paths
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        saved_files = []

        for result in results[:max_pairs]:
            config = result.to_config(exchange_name, balance_per_pair)

            # Generate filename
            pair_safe = result.pair.replace("/", "_")
            filename = (
                f"config_{pair_safe}_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            )
            filepath = output_path / filename

            with open(filepath, "w") as f:
                json.dump(config, f, indent=2, default=str)

            saved_files.append(str(filepath))
            self.logger.info(f"Saved config for {result.pair} to {filepath}")

        return saved_files


async def run_smart_scan(
    exchange_service: ExchangeInterface,
    quote_currency: str = "USD",
    num_pairs: int = 10,
    min_price: float = 0.01,
    max_price: float = 100.0,
    min_volume: float = 100_000,
    save_configs: bool = True,
    exchange_name: str = "kraken",
    balance_per_pair: float = 100.0,
) -> list[PairScanResult]:
    """
    Convenience function to run a smart pair scan.

    Args:
        exchange_service: Exchange service instance
        quote_currency: Quote currency to scan
        num_pairs: Number of top pairs to return
        min_price: Minimum price filter
        max_price: Maximum price filter
        min_volume: Minimum 24h volume
        save_configs: Whether to save configs for top pairs
        exchange_name: Exchange name for saved configs
        balance_per_pair: Balance per pair in saved configs

    Returns:
        List of top scan results
    """
    scanner = PairScanner(exchange_service)

    results = await scanner.scan_pairs(
        quote_currency=quote_currency,
        min_price=min_price,
        max_price=max_price,
        min_volume_24h=min_volume,
        max_results=num_pairs,
    )

    # Print results
    scanner.print_scan_results(results)

    # Save configs if requested
    if save_configs and results:
        await scanner.save_configs(
            results,
            exchange_name=exchange_name,
            balance_per_pair=balance_per_pair,
        )

    return results

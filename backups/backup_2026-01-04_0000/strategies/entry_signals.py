"""
Entry Signals Module for GridBot Chuck
=======================================

Analyzes market conditions to determine optimal entry timing using:
- RSI (Relative Strength Index) - Oversold/overbought detection
- Price Position - Where price sits within the grid range
- Volume Trend - Consolidation vs expansion patterns

Entry Signal Scoring (0-100):
- Price Position (40% weight): Prefers price near grid bottom (0-20%)
- RSI Indicator (30% weight): Prefers oversold conditions (RSI < 30)
- Volume Trend (10% weight): Prefers consolidation/stable volume
- Grid Suitability (20% weight): Uses pair scanner score
"""

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any

import pandas as pd


class SignalStrength(Enum):
    """Entry signal strength levels."""

    EXCELLENT = "excellent"  # 80+ : Enter immediately
    GOOD = "good"  # 65-79: Strong entry signal
    MODERATE = "moderate"  # 50-64: Wait for better conditions
    WEAK = "weak"  # 35-49: Poor entry timing
    POOR = "poor"  # <35: Avoid entry


@dataclass
class EntrySignal:
    """Complete entry signal analysis for a trading pair."""

    pair: str
    timestamp: pd.Timestamp

    # Overall score (0-100)
    score: float
    strength: SignalStrength

    # Component scores (0-100)
    price_position_score: float
    rsi_score: float
    volume_trend_score: float
    grid_suitability_score: float

    # Raw indicator values
    current_price: float
    price_position_pct: float  # 0% = bottom, 100% = top
    rsi: float
    volume_trend: str  # "increasing", "decreasing", "stable"
    volume_ratio: float  # Current vs average volume

    # Grid context
    grid_top: float
    grid_bottom: float

    # Recommendation
    should_enter: bool
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API/display."""
        return {
            "pair": self.pair,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "score": round(self.score, 1),
            "strength": self.strength.value,
            "should_enter": self.should_enter,
            "reason": self.reason,
            "components": {
                "price_position": round(self.price_position_score, 1),
                "rsi": round(self.rsi_score, 1),
                "volume_trend": round(self.volume_trend_score, 1),
                "grid_suitability": round(self.grid_suitability_score, 1),
            },
            "indicators": {
                "current_price": round(self.current_price, 6),
                "price_position_pct": round(self.price_position_pct, 1),
                "rsi": round(self.rsi, 1),
                "volume_trend": self.volume_trend,
                "volume_ratio": round(self.volume_ratio, 2),
            },
            "grid": {
                "top": self.grid_top,
                "bottom": self.grid_bottom,
            },
        }


class EntrySignalAnalyzer:
    """
    Analyzes market conditions for optimal entry timing.

    Combines multiple indicators to generate a composite entry score,
    helping determine the best time to enter a grid trading position.
    """

    # Scoring weights (must sum to 1.0)
    WEIGHT_PRICE_POSITION = 0.40  # Most important: where is price in range?
    WEIGHT_RSI = 0.30  # Is it oversold?
    WEIGHT_VOLUME = 0.10  # Is volume stable/consolidating?
    WEIGHT_GRID_SUITABILITY = 0.20  # How good is this pair for grid trading?

    # Signal thresholds
    EXCELLENT_THRESHOLD = 80
    GOOD_THRESHOLD = 65
    MODERATE_THRESHOLD = 50
    WEAK_THRESHOLD = 35

    # RSI levels
    RSI_OVERSOLD = 30
    RSI_OVERBOUGHT = 70
    RSI_NEUTRAL_LOW = 40
    RSI_NEUTRAL_HIGH = 60

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """
        Calculate the Relative Strength Index.

        Args:
            prices: Series of closing prices
            period: RSI period (default 14)

        Returns:
            Current RSI value (0-100)
        """
        if len(prices) < period + 1:
            return 50.0  # Neutral if insufficient data

        # Calculate price changes
        delta = prices.diff()

        # Separate gains and losses
        gains = delta.where(delta > 0, 0.0)
        losses = (-delta).where(delta < 0, 0.0)

        # Calculate average gains and losses (Wilder's smoothing)
        avg_gain = gains.ewm(alpha=1 / period, min_periods=period).mean()
        avg_loss = losses.ewm(alpha=1 / period, min_periods=period).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss.replace(0, float("inf"))
        rsi = 100 - (100 / (1 + rs))

        current_rsi = rsi.iloc[-1]

        # Handle edge cases
        if pd.isna(current_rsi) or current_rsi < 0:
            return 50.0
        elif current_rsi > 100:
            return 100.0

        return float(current_rsi)

    def calculate_price_position(
        self,
        current_price: float,
        grid_top: float,
        grid_bottom: float,
    ) -> float:
        """
        Calculate where price sits within the grid range.

        Args:
            current_price: Current market price
            grid_top: Top of grid range
            grid_bottom: Bottom of grid range

        Returns:
            Position percentage (0% = bottom, 100% = top)
        """
        if grid_top <= grid_bottom:
            return 50.0  # Invalid range

        grid_range = grid_top - grid_bottom
        position = (current_price - grid_bottom) / grid_range * 100

        # Clamp to 0-100 range
        return max(0.0, min(100.0, position))

    def analyze_volume_trend(
        self,
        volume: pd.Series,
        lookback_short: int = 5,
        lookback_long: int = 20,
    ) -> tuple[str, float]:
        """
        Analyze volume trend to detect consolidation vs expansion.

        Args:
            volume: Series of volume data
            lookback_short: Short-term lookback period
            lookback_long: Long-term lookback period

        Returns:
            Tuple of (trend_type, volume_ratio)
            - trend_type: "increasing", "decreasing", or "stable"
            - volume_ratio: Short-term avg / Long-term avg
        """
        if len(volume) < lookback_long:
            return ("stable", 1.0)

        short_avg = volume.iloc[-lookback_short:].mean()
        long_avg = volume.iloc[-lookback_long:].mean()

        if long_avg == 0:
            return ("stable", 1.0)

        volume_ratio = short_avg / long_avg

        if volume_ratio > 1.3:
            return ("increasing", volume_ratio)
        elif volume_ratio < 0.7:
            return ("decreasing", volume_ratio)
        else:
            return ("stable", volume_ratio)

    def score_rsi(self, rsi: float) -> float:
        """
        Score RSI for entry signal (0-100).

        Lower RSI (oversold) = higher score for buying.

        Scoring:
        - RSI < 20: 100 (extremely oversold - best entry)
        - RSI 20-30: 85-100 (oversold - great entry)
        - RSI 30-40: 65-85 (slightly oversold - good entry)
        - RSI 40-60: 40-65 (neutral - moderate)
        - RSI 60-70: 20-40 (slightly overbought - poor entry)
        - RSI > 70: 0-20 (overbought - avoid entry)
        """
        if rsi < 20:
            return 100.0
        elif rsi < 30:
            # Linear scale from 85 to 100 as RSI goes from 30 to 20
            return 85 + (30 - rsi) / 10 * 15
        elif rsi < 40:
            # Linear scale from 65 to 85 as RSI goes from 40 to 30
            return 65 + (40 - rsi) / 10 * 20
        elif rsi < 60:
            # Neutral zone: 40 to 65 as RSI goes from 60 to 40
            return 40 + (60 - rsi) / 20 * 25
        elif rsi < 70:
            # Linear scale from 20 to 40 as RSI goes from 70 to 60
            return 20 + (70 - rsi) / 10 * 20
        else:
            # Overbought: scale from 0 to 20 as RSI goes from 100 to 70
            return max(0, 20 - (rsi - 70) / 30 * 20)

    def score_price_position(self, position_pct: float) -> float:
        """
        Score price position for entry signal (0-100).

        Lower position (near bottom) = higher score for buying.

        Scoring:
        - 0-10%: 100 (at/near bottom - best entry)
        - 10-20%: 85-100 (near bottom - excellent)
        - 20-35%: 65-85 (lower third - good)
        - 35-50%: 50-65 (lower middle - moderate)
        - 50-65%: 35-50 (upper middle - weak)
        - 65-80%: 20-35 (upper third - poor)
        - 80-100%: 0-20 (near/at top - avoid)
        """
        if position_pct <= 10:
            return 100.0
        elif position_pct <= 20:
            return 85 + (20 - position_pct) / 10 * 15
        elif position_pct <= 35:
            return 65 + (35 - position_pct) / 15 * 20
        elif position_pct <= 50:
            return 50 + (50 - position_pct) / 15 * 15
        elif position_pct <= 65:
            return 35 + (65 - position_pct) / 15 * 15
        elif position_pct <= 80:
            return 20 + (80 - position_pct) / 15 * 15
        else:
            return max(0, 20 - (position_pct - 80) / 20 * 20)

    def score_volume_trend(self, trend: str, volume_ratio: float) -> float:
        """
        Score volume trend for entry signal (0-100).

        Stable/consolidating volume is preferred for grid trading.

        Scoring:
        - Stable (ratio 0.8-1.2): 80-100 (ideal for grid)
        - Decreasing (ratio < 0.8): 60-80 (consolidation - good)
        - Increasing (ratio > 1.2): 30-60 (volatility - caution)
        - Highly increasing (ratio > 2.0): 0-30 (high volatility - avoid)
        """
        if trend == "stable":
            # Closer to 1.0 = higher score
            deviation = abs(volume_ratio - 1.0)
            return max(80, 100 - deviation * 100)
        elif trend == "decreasing":
            # Lower ratio = more consolidation = higher score
            if volume_ratio < 0.5:
                return 80.0
            else:
                return 60 + (0.8 - volume_ratio) / 0.3 * 20
        else:  # increasing
            if volume_ratio > 2.0:
                return max(0, 30 - (volume_ratio - 2.0) * 15)
            elif volume_ratio > 1.5:
                return 30 + (2.0 - volume_ratio) / 0.5 * 30
            else:
                return 60 - (volume_ratio - 1.2) / 0.3 * 30

    def determine_signal_strength(self, score: float) -> SignalStrength:
        """Determine signal strength from composite score."""
        if score >= self.EXCELLENT_THRESHOLD:
            return SignalStrength.EXCELLENT
        elif score >= self.GOOD_THRESHOLD:
            return SignalStrength.GOOD
        elif score >= self.MODERATE_THRESHOLD:
            return SignalStrength.MODERATE
        elif score >= self.WEAK_THRESHOLD:
            return SignalStrength.WEAK
        else:
            return SignalStrength.POOR

    def generate_entry_reason(
        self,
        strength: SignalStrength,
        rsi: float,
        price_position_pct: float,
        volume_trend: str,
    ) -> str:
        """Generate human-readable reason for entry decision."""
        reasons = []

        # RSI assessment
        if rsi < self.RSI_OVERSOLD:
            reasons.append(f"RSI oversold ({rsi:.0f})")
        elif rsi > self.RSI_OVERBOUGHT:
            reasons.append(f"RSI overbought ({rsi:.0f})")
        else:
            reasons.append(f"RSI neutral ({rsi:.0f})")

        # Price position assessment
        if price_position_pct < 20:
            reasons.append("price near grid bottom")
        elif price_position_pct < 40:
            reasons.append("price in lower range")
        elif price_position_pct > 80:
            reasons.append("price near grid top")
        elif price_position_pct > 60:
            reasons.append("price in upper range")
        else:
            reasons.append("price mid-range")

        # Volume assessment
        if volume_trend == "stable":
            reasons.append("stable volume")
        elif volume_trend == "decreasing":
            reasons.append("consolidating volume")
        else:
            reasons.append("increasing volume")

        # Final recommendation
        if strength in (SignalStrength.EXCELLENT, SignalStrength.GOOD):
            prefix = "ENTER: "
        elif strength == SignalStrength.MODERATE:
            prefix = "WAIT: "
        else:
            prefix = "AVOID: "

        return prefix + ", ".join(reasons)

    def analyze_entry(
        self,
        pair: str,
        ohlcv_data: pd.DataFrame,
        grid_top: float,
        grid_bottom: float,
        grid_suitability_score: float = 50.0,
        min_entry_score: float = 65.0,
    ) -> EntrySignal:
        """
        Perform complete entry signal analysis for a trading pair.

        Args:
            pair: Trading pair symbol (e.g., 'BTC/USD')
            ohlcv_data: DataFrame with columns: timestamp, open, high, low, close, volume
            grid_top: Top of grid range
            grid_bottom: Bottom of grid range
            grid_suitability_score: Score from pair scanner (0-100)
            min_entry_score: Minimum score to recommend entry

        Returns:
            EntrySignal object with complete analysis
        """
        # Extract data
        close_prices = ohlcv_data["close"]
        volume = ohlcv_data["volume"]
        current_price = float(close_prices.iloc[-1])
        timestamp = ohlcv_data["timestamp"].iloc[-1] if "timestamp" in ohlcv_data.columns else pd.Timestamp.now()

        # Calculate indicators
        rsi = self.calculate_rsi(close_prices)
        price_position_pct = self.calculate_price_position(current_price, grid_top, grid_bottom)
        volume_trend, volume_ratio = self.analyze_volume_trend(volume)

        # Calculate component scores
        rsi_score = self.score_rsi(rsi)
        price_position_score = self.score_price_position(price_position_pct)
        volume_trend_score = self.score_volume_trend(volume_trend, volume_ratio)

        # Calculate composite score
        composite_score = (
            price_position_score * self.WEIGHT_PRICE_POSITION
            + rsi_score * self.WEIGHT_RSI
            + volume_trend_score * self.WEIGHT_VOLUME
            + grid_suitability_score * self.WEIGHT_GRID_SUITABILITY
        )

        # Determine signal strength
        strength = self.determine_signal_strength(composite_score)

        # Should we enter?
        should_enter = composite_score >= min_entry_score

        # Generate reason
        reason = self.generate_entry_reason(strength, rsi, price_position_pct, volume_trend)

        self.logger.info(
            f"Entry signal for {pair}: Score={composite_score:.1f} ({strength.value}), "
            f"RSI={rsi:.1f}, Position={price_position_pct:.1f}%, "
            f"Volume={volume_trend} (ratio={volume_ratio:.2f})"
        )

        return EntrySignal(
            pair=pair,
            timestamp=timestamp,
            score=composite_score,
            strength=strength,
            price_position_score=price_position_score,
            rsi_score=rsi_score,
            volume_trend_score=volume_trend_score,
            grid_suitability_score=grid_suitability_score,
            current_price=current_price,
            price_position_pct=price_position_pct,
            rsi=rsi,
            volume_trend=volume_trend,
            volume_ratio=volume_ratio,
            grid_top=grid_top,
            grid_bottom=grid_bottom,
            should_enter=should_enter,
            reason=reason,
        )

    def analyze_multiple_entries(
        self,
        pairs_data: list[dict],
        min_entry_score: float = 65.0,
    ) -> list[EntrySignal]:
        """
        Analyze entry signals for multiple pairs.

        Args:
            pairs_data: List of dicts containing:
                - pair: Trading pair symbol
                - ohlcv_data: DataFrame with OHLCV data
                - grid_top: Top of grid range
                - grid_bottom: Bottom of grid range
                - grid_suitability_score: Score from pair scanner (optional)
            min_entry_score: Minimum score to recommend entry

        Returns:
            List of EntrySignal objects, sorted by score (highest first)
        """
        signals = []

        for data in pairs_data:
            try:
                signal = self.analyze_entry(
                    pair=data["pair"],
                    ohlcv_data=data["ohlcv_data"],
                    grid_top=data["grid_top"],
                    grid_bottom=data["grid_bottom"],
                    grid_suitability_score=data.get("grid_suitability_score", 50.0),
                    min_entry_score=min_entry_score,
                )
                signals.append(signal)
            except Exception as e:
                self.logger.error(f"Error analyzing entry for {data.get('pair', 'unknown')}: {e}")

        # Sort by score (highest first)
        signals.sort(key=lambda x: x.score, reverse=True)

        return signals

    def get_best_entries(
        self,
        signals: list[EntrySignal],
        max_positions: int = 5,
        prioritize_excellent: bool = True,
    ) -> list[EntrySignal]:
        """
        Get the best entry signals for opening positions.

        Prioritization logic:
        1. EXCELLENT signals (any rank) - Best opportunities anywhere
        2. Top ranked pairs with GOOD+ signals
        3. Others ranked by score

        Args:
            signals: List of analyzed EntrySignal objects
            max_positions: Maximum number of positions to recommend
            prioritize_excellent: Whether to prioritize excellent signals over rank

        Returns:
            List of best signals to act on
        """
        if not signals:
            return []

        # Separate by strength
        excellent = [s for s in signals if s.strength == SignalStrength.EXCELLENT and s.should_enter]
        good = [s for s in signals if s.strength == SignalStrength.GOOD and s.should_enter]
        moderate = [s for s in signals if s.strength == SignalStrength.MODERATE and s.should_enter]

        best_entries = []

        if prioritize_excellent:
            # Add all excellent signals first
            best_entries.extend(excellent)

            # Fill remaining spots with good signals
            remaining = max_positions - len(best_entries)
            if remaining > 0:
                best_entries.extend(good[:remaining])

            # Fill any remaining spots with moderate signals
            remaining = max_positions - len(best_entries)
            if remaining > 0:
                best_entries.extend(moderate[:remaining])
        else:
            # Simply take top scores
            all_enterable = [s for s in signals if s.should_enter]
            best_entries = all_enterable[:max_positions]

        return best_entries[:max_positions]

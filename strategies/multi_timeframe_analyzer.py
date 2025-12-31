"""
Multi-Timeframe Analysis Module for Grid Trading.

This module provides intelligent market analysis across multiple timeframes
to determine optimal conditions for grid trading, including:
- Trend detection (avoid grids in strong trends)
- Range validity confirmation
- Volatility-based grid spacing adjustments
- Entry timing optimization
"""

from dataclasses import dataclass
from enum import Enum
import logging

import pandas as pd

from core.services.exchange_interface import ExchangeInterface


class MarketCondition(Enum):
    """Market condition classifications."""
    STRONG_TREND_UP = "strong_trend_up"
    TREND_UP = "trend_up"
    RANGING = "ranging"
    TREND_DOWN = "trend_down"
    STRONG_TREND_DOWN = "strong_trend_down"
    VOLATILE = "volatile"
    CONSOLIDATING = "consolidating"


class GridTradingSignal(Enum):
    """Grid trading signal recommendations."""
    IDEAL = "ideal"  # Perfect conditions for grid trading
    FAVORABLE = "favorable"  # Good conditions
    NEUTRAL = "neutral"  # Can proceed with caution
    UNFAVORABLE = "unfavorable"  # Consider pausing
    AVOID = "avoid"  # Do not run grids


@dataclass
class TimeframeAnalysis:
    """Analysis result for a single timeframe."""
    timeframe: str
    trend: str  # "bullish", "bearish", "neutral"
    trend_strength: float  # 0-100
    volatility: float  # ATR-based
    volatility_percentile: float  # 0-100 relative to recent history
    is_ranging: bool
    support_level: float
    resistance_level: float
    current_price: float
    ma_50: float
    ma_200: float
    rsi: float
    atr: float
    atr_percent: float  # ATR as percentage of price


@dataclass
class MultiTimeframeResult:
    """Combined multi-timeframe analysis result."""
    primary_trend: str  # Overall trend from higher timeframes
    trend_alignment: bool  # Are all timeframes aligned?
    market_condition: MarketCondition
    grid_signal: GridTradingSignal
    recommended_spacing_multiplier: float  # 1.0 = normal, >1 = wider, <1 = tighter
    recommended_bias: str  # "neutral", "buy", "sell" for hedged grids
    range_valid: bool  # Is the configured range still valid?
    suggested_range: tuple[float, float]  # Suggested grid range based on analysis
    confidence: float  # 0-100
    analysis_details: dict[str, TimeframeAnalysis]
    warnings: list[str]
    recommendations: list[str]


class MultiTimeframeAnalyzer:
    """
    Analyzes market conditions across multiple timeframes to optimize grid trading.

    Uses higher timeframes (Daily/4H) for trend detection and lower timeframes
    (1H/15M) for execution timing.

    Primary Timeframes:
    - Daily: Overall trend direction, major support/resistance
    - 4H: Grid configuration, trend confirmation
    - 1H: Entry timing, volatility monitoring
    """

    # Default timeframes for analysis
    TREND_TIMEFRAME = "1d"  # Daily for trend
    CONFIG_TIMEFRAME = "4h"  # 4-hour for grid config
    EXECUTION_TIMEFRAME = "1h"  # 1-hour for execution

    # Trend thresholds
    STRONG_TREND_THRESHOLD = 75  # ADX or similar
    TREND_THRESHOLD = 40

    # Volatility thresholds
    HIGH_VOLATILITY_PERCENTILE = 80
    LOW_VOLATILITY_PERCENTILE = 20

    def __init__(
        self,
        exchange_service: ExchangeInterface,
        config_timeframes: dict[str, str] | None = None,
    ):
        """
        Initialize the multi-timeframe analyzer.

        Args:
            exchange_service: Exchange interface for fetching market data
            config_timeframes: Override default timeframes
                {"trend": "1d", "config": "4h", "execution": "1h"}
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange_service = exchange_service

        # Allow custom timeframe configuration
        if config_timeframes:
            self.TREND_TIMEFRAME = config_timeframes.get("trend", "1d")
            self.CONFIG_TIMEFRAME = config_timeframes.get("config", "4h")
            self.EXECUTION_TIMEFRAME = config_timeframes.get("execution", "1h")

        self._cache: dict = {}
        self._cache_ttl = 300  # 5 minutes cache

    async def analyze(
        self,
        pair: str,
        grid_bottom: float,
        grid_top: float,
    ) -> MultiTimeframeResult:
        """
        Perform comprehensive multi-timeframe analysis.

        Args:
            pair: Trading pair (e.g., "FARM/USD")
            grid_bottom: Configured grid bottom price
            grid_top: Configured grid top price

        Returns:
            MultiTimeframeResult with analysis and recommendations
        """
        self.logger.info(f"Starting multi-timeframe analysis for {pair}")

        # Analyze each timeframe
        analyses = {}
        warnings = []
        recommendations = []

        for tf_name, timeframe in [
            ("trend", self.TREND_TIMEFRAME),
            ("config", self.CONFIG_TIMEFRAME),
            ("execution", self.EXECUTION_TIMEFRAME),
        ]:
            try:
                analysis = await self._analyze_timeframe(pair, timeframe)
                if analysis:
                    analyses[tf_name] = analysis
                else:
                    warnings.append(f"Failed to analyze {timeframe} timeframe")
            except Exception as e:
                self.logger.error(f"Error analyzing {timeframe}: {e}")
                warnings.append(f"Error analyzing {timeframe}: {e!s}")

        if not analyses:
            return self._create_neutral_result(warnings)

        # Determine primary trend from daily
        primary_trend = "neutral"
        trend_strength = 50
        if "trend" in analyses:
            primary_trend = analyses["trend"].trend
            trend_strength = analyses["trend"].trend_strength

        # Check trend alignment across timeframes
        trends = [a.trend for a in analyses.values()]
        trend_alignment = len(set(trends)) == 1

        # Determine market condition
        market_condition = self._determine_market_condition(analyses, trend_strength)

        # Calculate grid trading signal
        grid_signal = self._calculate_grid_signal(market_condition, trend_strength, analyses)

        # Calculate spacing multiplier based on volatility
        spacing_multiplier = self._calculate_spacing_multiplier(analyses)

        # Determine recommended bias for hedged grids
        recommended_bias = self._determine_recommended_bias(analyses)

        # Validate configured range
        range_valid, suggested_range = self._validate_range(
            analyses, grid_bottom, grid_top
        )

        if not range_valid:
            warnings.append(
                f"Configured range [{grid_bottom:.2f}-{grid_top:.2f}] may be outdated. "
                f"Suggested: [{suggested_range[0]:.2f}-{suggested_range[1]:.2f}]"
            )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            market_condition, grid_signal, spacing_multiplier, recommended_bias, analyses
        )

        # Calculate confidence
        confidence = self._calculate_confidence(analyses, trend_alignment)

        result = MultiTimeframeResult(
            primary_trend=primary_trend,
            trend_alignment=trend_alignment,
            market_condition=market_condition,
            grid_signal=grid_signal,
            recommended_spacing_multiplier=spacing_multiplier,
            recommended_bias=recommended_bias,
            range_valid=range_valid,
            suggested_range=suggested_range,
            confidence=confidence,
            analysis_details=analyses,
            warnings=warnings,
            recommendations=recommendations,
        )

        self._log_analysis_summary(result)
        return result

    async def _analyze_timeframe(
        self,
        pair: str,
        timeframe: str,
    ) -> TimeframeAnalysis | None:
        """Analyze a single timeframe."""
        try:
            # Fetch OHLCV data
            data = await self._fetch_ohlcv(pair, timeframe, limit=200)

            if data is None or len(data) < 50:
                self.logger.warning(f"Insufficient data for {pair} on {timeframe}")
                return None

            current_price = data["close"].iloc[-1]

            # Calculate moving averages
            ma_50 = self._calculate_sma(data["close"], 50)
            ma_200 = self._calculate_sma(data["close"], 200) if len(data) >= 200 else ma_50

            # Calculate RSI
            rsi = self._calculate_rsi(data["close"], 14)

            # Calculate ATR (Average True Range)
            atr = self._calculate_atr(data, 14)
            atr_percent = (atr / current_price) * 100 if current_price > 0 else 0

            # Calculate ATR percentile (relative to recent history)
            atr_series = self._calculate_atr_series(data, 14)
            volatility_percentile = self._calculate_percentile(atr_series, atr)

            # Determine trend
            trend, trend_strength = self._determine_trend(data, ma_50, ma_200, current_price)

            # Calculate support and resistance
            support, resistance = self._calculate_support_resistance(data)

            # Determine if ranging
            is_ranging = self._is_ranging(data, atr)

            return TimeframeAnalysis(
                timeframe=timeframe,
                trend=trend,
                trend_strength=trend_strength,
                volatility=atr,
                volatility_percentile=volatility_percentile,
                is_ranging=is_ranging,
                support_level=support,
                resistance_level=resistance,
                current_price=current_price,
                ma_50=ma_50,
                ma_200=ma_200,
                rsi=rsi,
                atr=atr,
                atr_percent=atr_percent,
            )

        except Exception as e:
            self.logger.error(f"Error in _analyze_timeframe for {timeframe}: {e}")
            return None

    async def _fetch_ohlcv(
        self,
        pair: str,
        timeframe: str,
        limit: int = 200,
    ) -> pd.DataFrame | None:
        """Fetch OHLCV data from exchange."""
        try:
            if hasattr(self.exchange_service, "fetch_ohlcv_simple"):
                return await self.exchange_service.fetch_ohlcv_simple(pair, timeframe, limit)
            elif hasattr(self.exchange_service, "fetch_ohlcv"):
                return self.exchange_service.fetch_ohlcv(pair, timeframe, limit=limit)
            return None
        except Exception as e:
            self.logger.error(f"Failed to fetch OHLCV for {pair} {timeframe}: {e}")
            return None

    def _calculate_sma(self, series: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(series) < period:
            return series.mean()
        return series.rolling(window=period).mean().iloc[-1]

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0  # Neutral default

        deltas = prices.diff()
        gain = deltas.where(deltas > 0, 0).rolling(window=period).mean()
        loss = (-deltas.where(deltas < 0, 0)).rolling(window=period).mean()

        rs = gain / loss.replace(0, 1e-10)
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50.0

    def _calculate_atr(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(data) < period:
            return 0.0

        high = data["high"]
        low = data["low"]
        close = data["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean().iloc[-1]

        return atr if not pd.isna(atr) else 0.0

    def _calculate_atr_series(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR series for percentile ranking."""
        high = data["high"]
        low = data["low"]
        close = data["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    def _calculate_percentile(self, series: pd.Series, value: float) -> float:
        """Calculate percentile of value within series."""
        valid_series = series.dropna()
        if len(valid_series) == 0:
            return 50.0
        return (valid_series < value).sum() / len(valid_series) * 100

    def _determine_trend(
        self,
        data: pd.DataFrame,
        ma_50: float,
        ma_200: float,
        current_price: float,
    ) -> tuple[str, float]:
        """
        Determine trend direction and strength.

        Returns:
            Tuple of (trend: str, strength: float 0-100)
        """
        # Calculate ADX for trend strength
        adx = self._calculate_adx(data, 14)

        # Price position relative to MAs
        above_ma50 = current_price > ma_50
        above_ma200 = current_price > ma_200
        ma50_above_ma200 = ma_50 > ma_200

        # Calculate price momentum (rate of change)
        roc = ((current_price - data["close"].iloc[-20]) / data["close"].iloc[-20]) * 100 if len(data) >= 20 else 0

        # Determine trend
        if above_ma50 and above_ma200 and ma50_above_ma200:
            trend = "bullish"
            strength = min(100, adx + abs(roc) * 2)
        elif not above_ma50 and not above_ma200 and not ma50_above_ma200:
            trend = "bearish"
            strength = min(100, adx + abs(roc) * 2)
        else:
            trend = "neutral"
            strength = max(0, 50 - adx)

        return trend, strength

    def _calculate_adx(self, data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average Directional Index for trend strength."""
        if len(data) < period * 2:
            return 25.0  # Neutral default

        try:
            high = data["high"]
            low = data["low"]
            close = data["close"]

            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()

            plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
            minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

            # Calculate ATR
            tr1 = high - low
            tr2 = abs(high - close.shift())
            tr3 = abs(low - close.shift())
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=period).mean()

            # Calculate +DI and -DI
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

            # Calculate DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
            adx = dx.rolling(window=period).mean().iloc[-1]

            return adx if not pd.isna(adx) else 25.0
        except Exception:
            return 25.0

    def _calculate_support_resistance(
        self,
        data: pd.DataFrame,
        lookback: int = 50,
    ) -> tuple[float, float]:
        """Calculate support and resistance levels from recent price action."""
        recent = data.tail(lookback)

        support = recent["low"].min()
        resistance = recent["high"].max()

        return support, resistance

    def _is_ranging(self, data: pd.DataFrame, atr: float, lookback: int = 20) -> bool:
        """Determine if market is in a ranging condition."""
        recent = data.tail(lookback)

        price_range = recent["high"].max() - recent["low"].min()
        recent["close"].mean()

        # Market is ranging if price range is less than 4x ATR
        range_ratio = price_range / (atr * 4) if atr > 0 else 1

        return range_ratio < 1.0

    def _determine_market_condition(
        self,
        analyses: dict[str, TimeframeAnalysis],
        trend_strength: float,
    ) -> MarketCondition:
        """Determine overall market condition from analyses."""
        if not analyses:
            return MarketCondition.RANGING

        # Check for strong trends
        if trend_strength >= self.STRONG_TREND_THRESHOLD:
            trend = analyses.get("trend", analyses.get("config"))
            if trend:
                if trend.trend == "bullish":
                    return MarketCondition.STRONG_TREND_UP
                elif trend.trend == "bearish":
                    return MarketCondition.STRONG_TREND_DOWN

        # Check for moderate trends
        if trend_strength >= self.TREND_THRESHOLD:
            trend = analyses.get("trend", analyses.get("config"))
            if trend:
                if trend.trend == "bullish":
                    return MarketCondition.TREND_UP
                elif trend.trend == "bearish":
                    return MarketCondition.TREND_DOWN

        # Check for high volatility
        config_analysis = analyses.get("config", analyses.get("execution"))
        if config_analysis and config_analysis.volatility_percentile >= self.HIGH_VOLATILITY_PERCENTILE:
            return MarketCondition.VOLATILE

        # Check for consolidation
        if config_analysis and config_analysis.volatility_percentile <= self.LOW_VOLATILITY_PERCENTILE:
            return MarketCondition.CONSOLIDATING

        # Check if ranging
        ranging_count = sum(1 for a in analyses.values() if a.is_ranging)
        if ranging_count >= len(analyses) // 2:
            return MarketCondition.RANGING

        return MarketCondition.RANGING

    def _calculate_grid_signal(
        self,
        market_condition: MarketCondition,
        trend_strength: float,
        analyses: dict[str, TimeframeAnalysis],
    ) -> GridTradingSignal:
        """Calculate grid trading recommendation."""

        # Strong trends are bad for grids
        if market_condition in [MarketCondition.STRONG_TREND_UP, MarketCondition.STRONG_TREND_DOWN]:
            return GridTradingSignal.AVOID

        # Moderate trends are unfavorable
        if market_condition in [MarketCondition.TREND_UP, MarketCondition.TREND_DOWN]:
            if trend_strength >= 60:
                return GridTradingSignal.UNFAVORABLE
            return GridTradingSignal.NEUTRAL

        # Ranging markets are ideal
        if market_condition == MarketCondition.RANGING:
            # Check RSI for extremes
            config_analysis = analyses.get("config", analyses.get("execution"))
            if config_analysis:
                if 30 <= config_analysis.rsi <= 70:
                    return GridTradingSignal.IDEAL
                return GridTradingSignal.FAVORABLE
            return GridTradingSignal.FAVORABLE

        # Volatile markets can work with wider spacing
        if market_condition == MarketCondition.VOLATILE:
            return GridTradingSignal.NEUTRAL

        # Consolidating markets are good
        if market_condition == MarketCondition.CONSOLIDATING:
            return GridTradingSignal.FAVORABLE

        return GridTradingSignal.NEUTRAL

    def _calculate_spacing_multiplier(
        self,
        analyses: dict[str, TimeframeAnalysis],
    ) -> float:
        """
        Calculate recommended grid spacing multiplier based on volatility.

        Returns:
            Multiplier: 1.0 = normal, >1.0 = wider spacing, <1.0 = tighter
        """
        config_analysis = analyses.get("config", analyses.get("execution"))

        if not config_analysis:
            return 1.0

        volatility_pct = config_analysis.volatility_percentile

        # High volatility = wider spacing
        if volatility_pct >= 80:
            return 1.5
        elif volatility_pct >= 60:
            return 1.25
        # Low volatility = tighter spacing
        elif volatility_pct <= 20:
            return 0.75
        elif volatility_pct <= 40:
            return 0.9

        return 1.0

    def _determine_recommended_bias(
        self,
        analyses: dict[str, TimeframeAnalysis],
    ) -> str:
        """Determine recommended bias for hedged grids."""
        trend_analysis = analyses.get("trend", analyses.get("config"))

        if not trend_analysis:
            return "neutral"

        # Strong trends = bias towards the trend
        if trend_analysis.trend_strength >= 50:
            if trend_analysis.trend == "bullish":
                return "buy"  # Favor buying dips
            elif trend_analysis.trend == "bearish":
                return "sell"  # Favor selling rallies

        return "neutral"

    def _validate_range(
        self,
        analyses: dict[str, TimeframeAnalysis],
        grid_bottom: float,
        grid_top: float,
    ) -> tuple[bool, tuple[float, float]]:
        """
        Validate if the configured grid range is still appropriate.

        Returns:
            Tuple of (is_valid, suggested_range)
        """
        config_analysis = analyses.get("config", analyses.get("execution"))

        if not config_analysis:
            return True, (grid_bottom, grid_top)

        current_price = config_analysis.current_price
        support = config_analysis.support_level
        resistance = config_analysis.resistance_level
        atr = config_analysis.atr

        # Check if current price is within range
        price_in_range = grid_bottom <= current_price <= grid_top

        # Check if range makes sense with support/resistance
        range_covers_sr = grid_bottom <= support and grid_top >= resistance

        # Suggest range based on current analysis
        buffer = atr * 2
        suggested_bottom = max(support - buffer, current_price * 0.9)
        suggested_top = min(resistance + buffer, current_price * 1.1)

        # Range is valid if price is in range and it somewhat covers S/R
        is_valid = price_in_range and (
            range_covers_sr or
            (abs(grid_bottom - support) / support < 0.1 and abs(grid_top - resistance) / resistance < 0.1)
        )

        return is_valid, (suggested_bottom, suggested_top)

    def _generate_recommendations(
        self,
        market_condition: MarketCondition,
        grid_signal: GridTradingSignal,
        spacing_multiplier: float,
        recommended_bias: str,
        analyses: dict[str, TimeframeAnalysis],
    ) -> list[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Signal-based recommendations
        if grid_signal == GridTradingSignal.AVOID:
            recommendations.append(
                "[!] AVOID grid trading now - market is in a strong trend. "
                "Wait for ranging conditions or trend reversal."
            )
        elif grid_signal == GridTradingSignal.UNFAVORABLE:
            recommendations.append(
                "[!] Consider pausing grids - moderate trend detected. "
                "If proceeding, use wider spacing and monitor closely."
            )
        elif grid_signal == GridTradingSignal.IDEAL:
            recommendations.append(
                "[OK] Ideal conditions for grid trading - market is ranging. "
                "Proceed with normal grid configuration."
            )
        elif grid_signal == GridTradingSignal.FAVORABLE:
            recommendations.append(
                "[OK] Favorable conditions for grid trading. "
                "Market shows good range-bound behavior."
            )

        # Spacing recommendations
        if spacing_multiplier > 1.0:
            recommendations.append(
                f"[VOL] High volatility detected - consider {spacing_multiplier:.0%} wider grid spacing."
            )
        elif spacing_multiplier < 1.0:
            recommendations.append(
                f"[VOL] Low volatility detected - consider {spacing_multiplier:.0%} tighter grid spacing "
                "for more frequent trades."
            )

        # Bias recommendations for hedged grids
        if recommended_bias != "neutral":
            recommendations.append(
                f"[BIAS] Trend bias: {recommended_bias.upper()} - "
                f"Consider {'buying dips' if recommended_bias == 'buy' else 'selling rallies'} "
                "more aggressively in your hedged grid."
            )

        # RSI-based recommendations
        config_analysis = analyses.get("config", analyses.get("execution"))
        if config_analysis:
            if config_analysis.rsi > 70:
                recommendations.append(
                    "[RSI] Overbought (>70) - expect potential pullback. "
                    "Good time to have sell orders ready."
                )
            elif config_analysis.rsi < 30:
                recommendations.append(
                    "[RSI] Oversold (<30) - expect potential bounce. "
                    "Good time to have buy orders ready."
                )

        return recommendations

    def _calculate_confidence(
        self,
        analyses: dict[str, TimeframeAnalysis],
        trend_alignment: bool,
    ) -> float:
        """Calculate confidence level of the analysis."""
        base_confidence = 60.0

        # More timeframes analyzed = higher confidence
        base_confidence += len(analyses) * 10

        # Trend alignment increases confidence
        if trend_alignment:
            base_confidence += 15

        # Data quality
        for analysis in analyses.values():
            if analysis.volatility_percentile > 0:
                base_confidence += 5

        return min(100.0, base_confidence)

    def _log_analysis_summary(self, result: MultiTimeframeResult) -> None:
        """Log a summary of the analysis."""
        self.logger.info(
            f"Multi-Timeframe Analysis Complete:\n"
            f"  Primary Trend: {result.primary_trend}\n"
            f"  Market Condition: {result.market_condition.value}\n"
            f"  Grid Signal: {result.grid_signal.value}\n"
            f"  Spacing Multiplier: {result.recommended_spacing_multiplier:.2f}x\n"
            f"  Recommended Bias: {result.recommended_bias}\n"
            f"  Range Valid: {result.range_valid}\n"
            f"  Confidence: {result.confidence:.1f}%"
        )

        for warning in result.warnings:
            self.logger.warning(f"  [!] {warning}")

        for rec in result.recommendations[:3]:  # Log first 3 recommendations
            self.logger.info(f"  {rec}")

    def _create_neutral_result(self, warnings: list[str]) -> MultiTimeframeResult:
        """Create a neutral result when analysis fails."""
        warnings.append("Unable to complete analysis - using neutral defaults")
        return MultiTimeframeResult(
            primary_trend="neutral",
            trend_alignment=True,
            market_condition=MarketCondition.RANGING,
            grid_signal=GridTradingSignal.NEUTRAL,
            recommended_spacing_multiplier=1.0,
            recommended_bias="neutral",
            range_valid=True,
            suggested_range=(0, 0),
            confidence=30.0,
            analysis_details={},
            warnings=warnings,
            recommendations=["Unable to analyze - proceed with caution"],
        )

    async def should_start_grid(
        self,
        pair: str,
        grid_bottom: float,
        grid_top: float,
    ) -> tuple[bool, str]:
        """
        Quick check if grid trading should be started.

        Returns:
            Tuple of (should_start: bool, reason: str)
        """
        result = await self.analyze(pair, grid_bottom, grid_top)

        if result.grid_signal == GridTradingSignal.AVOID:
            return False, f"Market in {result.market_condition.value} - not suitable for grid trading"

        if result.grid_signal == GridTradingSignal.UNFAVORABLE:
            return False, f"Unfavorable conditions: {result.market_condition.value}"

        if not result.range_valid:
            return False, f"Grid range may be outdated. Suggested: {result.suggested_range}"

        return True, f"Conditions: {result.grid_signal.value} ({result.confidence:.0f}% confidence)"

    async def get_optimal_spacing(
        self,
        pair: str,
        base_spacing_percent: float,
    ) -> float:
        """
        Get volatility-adjusted spacing percentage.

        Args:
            pair: Trading pair
            base_spacing_percent: Base spacing as percentage (e.g., 2.0 for 2%)

        Returns:
            Adjusted spacing percentage
        """
        try:
            result = await self.analyze(pair, 0, 0)  # Range not needed for this
            adjusted = base_spacing_percent * result.recommended_spacing_multiplier

            self.logger.info(
                f"Spacing adjustment: {base_spacing_percent:.2f}% -> {adjusted:.2f}% "
                f"(multiplier: {result.recommended_spacing_multiplier:.2f}x)"
            )

            return adjusted
        except Exception as e:
            self.logger.error(f"Failed to calculate optimal spacing: {e}")
            return base_spacing_percent

from dataclasses import dataclass
from enum import Enum
import logging

import pandas as pd

from config.config_manager import ConfigManager
from core.services.exchange_interface import ExchangeInterface


class TrendSignal(Enum):
    """Trend signal types."""

    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class CoinAnalysis:
    """Analysis result for a single coin."""

    pair: str
    price: float
    score: float
    signal: TrendSignal

    # Individual indicator scores (0-100)
    ema_crossover_score: float
    ema_position_score: float
    cci_score: float
    macd_score: float
    volume_score: float
    bollinger_score: float
    candlestick_score: float

    # Indicator values
    ema_9: float
    ema_21: float
    cci: float
    macd_value: float
    macd_signal: float
    rsi: float

    # Flags
    ema_bullish_cross: bool
    price_above_emas: bool
    cci_bullish: bool
    macd_bullish: bool

    # 24h change percentage (from ticker) - has default so must be last
    change_24h_pct: float = 0.0

    def _safe_float(self, value, default=0.0) -> float:
        """Convert value to float, handling NaN and None."""
        import math

        if value is None:
            return default
        try:
            f = float(value)
            if math.isnan(f) or math.isinf(f):
                return default
            return f
        except (ValueError, TypeError):
            return default

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        return {
            "pair": self.pair,
            "price": round(self._safe_float(self.price), 4),
            "score": round(self._safe_float(self.score), 2),
            "signal": self.signal.value,
            "change_24h_pct": round(self._safe_float(self.change_24h_pct), 2),
            "indicators": {
                "ema_9": round(self._safe_float(self.ema_9), 4),
                "ema_21": round(self._safe_float(self.ema_21), 4),
                "cci": round(self._safe_float(self.cci), 2),
                "macd": round(self._safe_float(self.macd_value), 4),
                "macd_signal": round(self._safe_float(self.macd_signal), 4),
                "rsi": round(self._safe_float(self.rsi, 50.0), 2),
            },
            "scores": {
                "ema_crossover": round(self._safe_float(self.ema_crossover_score), 2),
                "ema_position": round(self._safe_float(self.ema_position_score), 2),
                "cci": round(self._safe_float(self.cci_score), 2),
                "macd": round(self._safe_float(self.macd_score), 2),
                "volume": round(self._safe_float(self.volume_score), 2),
                "bollinger": round(self._safe_float(self.bollinger_score), 2),
                "candlestick": round(self._safe_float(self.candlestick_score), 2),
            },
            "flags": {
                "ema_bullish_cross": bool(self.ema_bullish_cross),
                "price_above_emas": bool(self.price_above_emas),
                "cci_bullish": bool(self.cci_bullish),
                "macd_bullish": bool(self.macd_bullish),
            },
        }


class MarketAnalyzer:
    """
    Analyzes market conditions to identify the best trading pairs and entry/exit points
    using technical indicators: EMA crossover (9/21), CCI, MACD, Bollinger Bands, RSI.

    Scoring weights for coin selection:
    - EMA Crossover (9/21): 25% - Primary trend signal
    - CCI Momentum: 20% - Momentum confirmation
    - MACD Trend: 15% - Trend direction validation
    - Volume Ranking: 15% - Liquidity and activity
    - EMA Position: 10% - Price relative to EMAs
    - Bollinger Position: 10% - Volatility and mean reversion
    - Candlestick Patterns: 5% - Reversal confirmation
    """

    # Scoring weights
    WEIGHT_EMA_CROSSOVER = 0.25
    WEIGHT_CCI = 0.20
    WEIGHT_MACD = 0.15
    WEIGHT_VOLUME = 0.15
    WEIGHT_EMA_POSITION = 0.10
    WEIGHT_BOLLINGER = 0.10
    WEIGHT_CANDLESTICK = 0.05

    def __init__(
        self, exchange_service: ExchangeInterface, config_manager: ConfigManager
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange_service = exchange_service
        self.config_manager = config_manager

    async def find_best_trading_pairs(
        self,
        candidate_pairs: list[str],
        timeframe: str = "15m",
        min_volume_threshold: float = 1000000,
        min_price: float = 1.0,
        max_price: float = 20.0,
        ema_fast_period: int = 9,
        ema_slow_period: int = 21,
        pair_info: list[dict] | None = None,
    ) -> list[CoinAnalysis]:
        """
        Identifies the best trading pairs based on:
        - EMA crossover (bullish cross preferred)
        - CCI momentum (crossing above -100 or >0)
        - MACD trend confirmation
        - Trading volume ranking
        - Bollinger band position
        - Candlestick reversal patterns

        Args:
            candidate_pairs: List of trading pairs to analyze (e.g., ['SOL/USD', 'BTC/USD'])
            timeframe: Candle timeframe (default: 15m)
            min_volume_threshold: Minimum 24h volume required
            min_price: Minimum price filter (default: $1.00)
            max_price: Maximum price filter (default: $20.00)
            ema_fast_period: Fast EMA period (default: 9)
            ema_slow_period: Slow EMA period (default: 21)
            pair_info: Optional list of dicts with pre-fetched pair data (from get_top_gainers)
                       Each dict should have: pair, price, change_pct, volume

        Returns:
            List of CoinAnalysis objects sorted by score (highest first)
        """
        # Store EMA periods for use in analysis
        self._ema_fast_period = ema_fast_period
        self._ema_slow_period = ema_slow_period

        # Build lookup for pair info (24h change, volume, etc.)
        pair_info_lookup = {}
        if pair_info:
            for info in pair_info:
                pair_info_lookup[info["pair"]] = info

        analyses: list[CoinAnalysis] = []
        volume_data: list[tuple[str, float]] = []  # For relative volume ranking

        # First pass: collect volume data for ranking
        for pair in candidate_pairs:
            try:
                data = await self._fetch_ohlcv_async(pair, timeframe, limit=100)
                if data is not None and len(data) >= ema_slow_period:
                    avg_volume = data["volume"].mean()
                    volume_data.append((pair, avg_volume))
            except Exception as e:
                self.logger.warning(f"Failed to fetch volume for {pair}: {e}")

        # Calculate volume percentiles for ranking
        volumes = [v for _, v in volume_data]
        max_volume = max(volumes) if volumes else 1

        # Second pass: full analysis
        for pair in candidate_pairs:
            try:
                # Get 24h change % if available
                change_24h = pair_info_lookup.get(pair, {}).get("change_pct", 0.0)

                analysis = await self._analyze_pair(
                    pair, timeframe, min_price, max_price, max_volume, change_24h
                )
                if analysis is not None:
                    analyses.append(analysis)
                    self.logger.info(
                        f"Pair {pair}: Score={analysis.score:.2f}, "
                        f"Signal={analysis.signal.value}, Price=${analysis.price:.2f}, "
                        f"24h={analysis.change_24h_pct:+.2f}%"
                    )
            except Exception as e:
                self.logger.warning(f"Failed to analyze pair {pair}: {e}")

        # Sort by score in descending order
        analyses.sort(key=lambda x: x.score, reverse=True)
        return analyses

    async def _fetch_ohlcv_async(
        self, pair: str, timeframe: str, limit: int = 100
    ) -> pd.DataFrame | None:
        """Fetch OHLCV data using the exchange service."""
        try:
            # Try the simple limit-based fetch first
            if hasattr(self.exchange_service, "fetch_ohlcv_simple"):
                return await self.exchange_service.fetch_ohlcv_simple(
                    pair, timeframe, limit
                )

            # Fallback to sync method if available
            if hasattr(self.exchange_service, "fetch_ohlcv"):
                # For backtest service compatibility
                return self.exchange_service.fetch_ohlcv(pair, timeframe, limit=limit)

            return None
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {pair}: {e}")
            return None

    async def _analyze_pair(
        self,
        pair: str,
        timeframe: str,
        min_price: float,
        max_price: float,
        max_volume: float,
        change_24h: float = 0.0,
    ) -> CoinAnalysis | None:
        """
        Performs comprehensive analysis on a single trading pair.
        """
        try:
            # Fetch OHLCV data
            data = await self._fetch_ohlcv_async(pair, timeframe, limit=100)

            if data is None or len(data) < 26:
                self.logger.warning(f"Insufficient data for {pair}")
                return None

            # Get current price
            current_price = data["close"].iloc[-1]

            # Filter by price range
            if current_price < min_price or current_price > max_price:
                self.logger.debug(
                    f"Skipping {pair}: price ${current_price:.2f} outside range"
                )
                return None

            # Get EMA periods (use stored values or defaults)
            ema_fast = getattr(self, "_ema_fast_period", 9)
            ema_slow = getattr(self, "_ema_slow_period", 21)

            # Calculate all indicators
            ema_fast_series = self._calculate_ema(data["close"], period=ema_fast)
            ema_slow_series = self._calculate_ema(data["close"], period=ema_slow)
            cci = self._calculate_cci(data, period=20)
            macd_line, signal_line = self._calculate_macd(data["close"])
            rsi = self._calculate_rsi(
                data["close"], period=7
            )  # Changed to RSI(7) - more responsive
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                data["close"]
            )

            # Import candlestick patterns
            from strategies.candlestick_patterns import detect_patterns

            candle_patterns = detect_patterns(data)

            # Calculate individual scores
            ema_crossover_score = self._score_ema_crossover(
                ema_fast_series, ema_slow_series
            )
            ema_position_score = self._score_ema_position(
                current_price, ema_fast_series, ema_slow_series
            )
            cci_score = self._score_cci(cci)
            macd_score = self._score_macd(macd_line, signal_line)
            volume_score = self._calculate_volume_score(data, max_volume)
            bollinger_score = self._score_bollinger(
                current_price, bb_upper, bb_middle, bb_lower
            )
            candlestick_score = self._score_candlestick_patterns(candle_patterns)

            # Calculate composite score
            composite_score = (
                ema_crossover_score * self.WEIGHT_EMA_CROSSOVER
                + cci_score * self.WEIGHT_CCI
                + macd_score * self.WEIGHT_MACD
                + volume_score * self.WEIGHT_VOLUME
                + ema_position_score * self.WEIGHT_EMA_POSITION
                + bollinger_score * self.WEIGHT_BOLLINGER
                + candlestick_score * self.WEIGHT_CANDLESTICK
            )

            # Determine overall signal
            signal = self._determine_signal(
                ema_crossover_score, cci_score, macd_score, ema_position_score
            )

            # Determine flags
            ema_bullish_cross = (
                ema_fast_series.iloc[-1] > ema_slow_series.iloc[-1]
                and ema_fast_series.iloc[-2] <= ema_slow_series.iloc[-2]
            )
            price_above_emas = (
                current_price > ema_fast_series.iloc[-1]
                and current_price > ema_slow_series.iloc[-1]
            )
            cci_bullish = cci.iloc[-1] > 0 or (
                cci.iloc[-1] > -100 and cci.iloc[-2] <= -100
            )
            macd_bullish = macd_line.iloc[-1] > signal_line.iloc[-1]

            return CoinAnalysis(
                pair=pair,
                price=current_price,
                score=composite_score,
                signal=signal,
                ema_crossover_score=ema_crossover_score,
                ema_position_score=ema_position_score,
                cci_score=cci_score,
                macd_score=macd_score,
                volume_score=volume_score,
                bollinger_score=bollinger_score,
                candlestick_score=candlestick_score,
                ema_9=ema_fast_series.iloc[-1],
                ema_21=ema_slow_series.iloc[-1],
                cci=cci.iloc[-1],
                macd_value=macd_line.iloc[-1],
                macd_signal=signal_line.iloc[-1],
                rsi=rsi if rsi else 50,
                ema_bullish_cross=ema_bullish_cross,
                price_above_emas=price_above_emas,
                cci_bullish=cci_bullish,
                macd_bullish=macd_bullish,
                change_24h_pct=change_24h,
            )

        except Exception as e:
            self.logger.error(f"Error analyzing {pair}: {e}")
            return None

    def _determine_signal(
        self,
        ema_score: float,
        cci_score: float,
        macd_score: float,
        position_score: float,
    ) -> TrendSignal:
        """Determine overall trend signal based on indicator scores."""
        avg_score = (ema_score + cci_score + macd_score + position_score) / 4

        if avg_score >= 80:
            return TrendSignal.STRONG_BULLISH
        elif avg_score >= 60:
            return TrendSignal.BULLISH
        elif avg_score >= 40:
            return TrendSignal.NEUTRAL
        elif avg_score >= 20:
            return TrendSignal.BEARISH
        else:
            return TrendSignal.STRONG_BEARISH

    @staticmethod
    def _calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """Calculate Exponential Moving Average."""
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _calculate_cci(data: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        Calculate Commodity Channel Index (CCI).
        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)
        Typical Price = (High + Low + Close) / 3
        """
        typical_price = (data["high"] + data["low"] + data["close"]) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mean_deviation = typical_price.rolling(window=period).apply(
            lambda x: abs(x - x.mean()).mean(), raw=True
        )
        cci = (typical_price - sma_tp) / (0.015 * mean_deviation)
        return cci

    @staticmethod
    def _calculate_bollinger_bands(
        prices: pd.Series, period: int = 20, num_std: float = 2.0
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate Bollinger Bands (upper, middle, lower)."""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * num_std)
        lower = middle - (std * num_std)
        return upper, middle, lower

    def _score_ema_crossover(self, ema_fast: pd.Series, ema_slow: pd.Series) -> float:
        """
        Score EMA crossover signal (0-100).
        - Recent bullish cross (fast crosses above slow): 100
        - Fast above slow (uptrend): 75
        - Fast below slow (downtrend): 25
        - Recent bearish cross: 0
        """
        if len(ema_fast) < 3 or len(ema_slow) < 3:
            return 50

        current_fast = ema_fast.iloc[-1]
        current_slow = ema_slow.iloc[-1]
        prev_fast = ema_fast.iloc[-2]
        prev_slow = ema_slow.iloc[-2]
        prev2_fast = ema_fast.iloc[-3]
        prev2_slow = ema_slow.iloc[-3]

        # Check for recent crossover (within last 2 candles)
        bullish_cross_now = current_fast > current_slow and prev_fast <= prev_slow
        bullish_cross_prev = prev_fast > prev_slow and prev2_fast <= prev2_slow
        bearish_cross_now = current_fast < current_slow and prev_fast >= prev_slow
        bearish_cross_prev = prev_fast < prev_slow and prev2_fast >= prev2_slow

        if bullish_cross_now:
            return 100
        elif bullish_cross_prev:
            return 90
        elif current_fast > current_slow:
            # Calculate strength of uptrend
            spread_pct = ((current_fast - current_slow) / current_slow) * 100
            return min(85, 60 + spread_pct * 10)
        elif bearish_cross_now:
            return 0
        elif bearish_cross_prev:
            return 10
        else:
            # Downtrend - calculate weakness
            spread_pct = ((current_slow - current_fast) / current_slow) * 100
            return max(15, 40 - spread_pct * 10)

    def _score_ema_position(
        self, price: float, ema_fast: pd.Series, ema_slow: pd.Series
    ) -> float:
        """
        Score price position relative to EMAs (0-100).
        - Price above both EMAs: 100
        - Price between EMAs: 50
        - Price below both EMAs: 0
        """
        fast = ema_fast.iloc[-1]
        slow = ema_slow.iloc[-1]

        if price > fast and price > slow:
            # Above both - calculate distance
            min_ema = min(fast, slow)
            distance_pct = ((price - min_ema) / min_ema) * 100
            return min(100, 75 + distance_pct * 5)
        elif price < fast and price < slow:
            # Below both
            max_ema = max(fast, slow)
            distance_pct = ((max_ema - price) / max_ema) * 100
            return max(0, 25 - distance_pct * 5)
        else:
            # Between EMAs
            return 50

    def _score_cci(self, cci: pd.Series) -> float:
        """
        Score CCI momentum (0-100).
        - CCI > 100: Overbought, but strong momentum (60-70)
        - CCI 0 to 100: Bullish momentum (70-90)
        - CCI -100 to 0: Neutral/recovering (50-70)
        - CCI crossing above -100: Bullish reversal signal (85)
        - CCI < -100: Oversold (30-50, potential reversal)
        """
        if len(cci) < 2:
            return 50

        current = cci.iloc[-1]
        prev = cci.iloc[-2]

        # Bullish reversal: crossing above -100
        if current > -100 and prev <= -100:
            return 90

        # Bullish reversal: crossing above 0
        if current > 0 and prev <= 0:
            return 85

        if current > 100:
            # Overbought but strong
            return 65
        elif current > 0:
            # Bullish momentum
            return 70 + min(20, current / 5)
        elif current > -100:
            # Recovering from oversold
            return 50 + (100 + current) / 4  # 50-75 range
        else:
            # Oversold - potential reversal zone
            return max(30, 50 + (current + 100) / 5)

    def _score_macd(
        self, macd_line: pd.Series | None, signal_line: pd.Series | None
    ) -> float:
        """
        Score MACD trend (0-100).
        - MACD crossing above signal: 100
        - MACD above signal: 70-90
        - MACD below signal: 10-30
        - MACD crossing below signal: 0
        """
        if macd_line is None or signal_line is None:
            return 50

        if len(macd_line) < 2:
            return 50

        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]

        # Bullish crossover
        if current_macd > current_signal and prev_macd <= prev_signal:
            return 100

        # Bearish crossover
        if current_macd < current_signal and prev_macd >= prev_signal:
            return 0

        if current_macd > current_signal:
            # Above signal line
            spread = current_macd - current_signal
            return min(90, 70 + abs(spread) * 100)
        else:
            # Below signal line
            spread = current_signal - current_macd
            return max(10, 30 - abs(spread) * 100)

    def _score_bollinger(
        self,
        price: float,
        upper: pd.Series,
        middle: pd.Series,
        lower: pd.Series,
    ) -> float:
        """
        Score Bollinger Band position (0-100).
        - Price near lower band: Potential buy zone (70-90)
        - Price at middle: Neutral (50)
        - Price near upper band: Potential sell zone (10-30)
        """
        if len(upper) < 1:
            return 50

        u = upper.iloc[-1]
        middle.iloc[-1]
        lo = lower.iloc[-1]

        band_width = u - lo
        if band_width == 0:
            return 50

        # Position as percentage (0 = lower, 1 = upper)
        position = (price - lo) / band_width

        if position <= 0.2:
            # Near lower band - bullish
            return 90 - position * 50
        elif position <= 0.4:
            return 70 - (position - 0.2) * 100
        elif position <= 0.6:
            # Middle zone
            return 50
        elif position <= 0.8:
            return 50 - (position - 0.6) * 100
        else:
            # Near upper band - bearish
            return max(10, 30 - (position - 0.8) * 100)

    def _score_candlestick_patterns(self, patterns: dict) -> float:
        """
        Score candlestick patterns (0-100).
        Bullish patterns increase score, bearish decrease.
        """
        score = 50  # Neutral baseline

        bullish_patterns = [
            "hammer",
            "bullish_engulfing",
            "morning_star",
            "dragonfly_doji",
            "three_white_soldiers",
        ]
        bearish_patterns = [
            "shooting_star",
            "bearish_engulfing",
            "evening_star",
            "hanging_man",
        ]

        for pattern in bullish_patterns:
            if patterns.get(pattern, False):
                score += 15

        for pattern in bearish_patterns:
            if patterns.get(pattern, False):
                score -= 15

        return max(0, min(100, score))

    def _calculate_volume_score(self, data: pd.DataFrame, max_volume: float) -> float:
        """
        Calculates volume score (0-100) based on relative volume ranking.
        Higher average volume relative to other pairs = higher score.
        """
        if max_volume == 0:
            return 50

        avg_volume = data["volume"].mean()

        # Score based on percentile of max volume across all pairs
        volume_ratio = avg_volume / max_volume

        # Apply logarithmic scaling for better distribution
        import math

        score = (
            min(100, 50 + (math.log10(volume_ratio + 0.1) + 1) * 25)
            if volume_ratio > 0
            else 0
        )

        return max(0, score)

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> float | None:
        """Calculates Relative Strength Index."""
        if len(prices) < period + 1:
            return None

        deltas = prices.diff()
        seed = deltas[: period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rs = up / down if down != 0 else 0
        rsi = 100.0 - 100.0 / (1.0 + rs)
        return rsi

    @staticmethod
    def _calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[pd.Series | None, pd.Series | None]:
        """Calculates MACD and Signal line."""
        if len(prices) < slow_period:
            return None, None

        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period).mean()

        return macd_line, signal_line

    def calculate_optimal_grid_range(
        self,
        pair: str,
        timeframe: str = "15m",
        lookback_periods: int = 50,
    ) -> tuple[float, float, float]:
        """
        Calculates optimal grid range based on recent price action.

        Returns:
            Tuple of (bottom_price, top_price, central_price)
        """
        try:
            data = self.exchange_service.fetch_ohlcv(
                pair, timeframe, limit=lookback_periods
            )

            if data is None or len(data) == 0:
                self.logger.error(f"No data available for {pair}")
                return None, None, None

            current_price = data["close"].iloc[-1]
            min_price = data["low"].min()
            max_price = data["high"].max()
            atr = self._calculate_atr(data, period=14)

            # Set range based on ATR (Average True Range)
            if atr is None:
                atr = (max_price - min_price) / 4

            # Grid range: current price ± 2 ATR
            bottom_price = current_price - (2 * atr)
            top_price = current_price + (2 * atr)
            central_price = current_price

            # Ensure bottom and top are within recent range
            bottom_price = max(bottom_price, min_price * 0.98)
            top_price = min(top_price, max_price * 1.02)

            self.logger.info(
                f"Optimal grid range for {pair}: {bottom_price:.4f} - {top_price:.4f} "
                f"(Current: {current_price:.4f}, ATR: {atr:.4f})"
            )

            return bottom_price, top_price, central_price

        except Exception as e:
            self.logger.error(f"Error calculating grid range for {pair}: {e}")
            return None, None, None

    @staticmethod
    def _calculate_atr(data: pd.DataFrame, period: int = 14) -> float | None:
        """Calculates Average True Range."""
        if len(data) < period:
            return None

        high = data["high"]
        low = data["low"]
        close = data["close"]

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())

        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr.iloc[-1]

    def get_entry_signal(self, pair: str, timeframe: str = "15m") -> str:
        """
        Determines if it's a good time to enter a trade.

        Returns:
            'BUY' if uptrend, 'SELL' if downtrend, 'HOLD' if neutral
        """
        try:
            data = self.exchange_service.fetch_ohlcv(pair, timeframe, limit=50)

            if data is None or len(data) < 26:
                return "HOLD"

            rsi = self._calculate_rsi(data["close"], period=7)  # Changed to RSI(7)
            macd_line, signal_line = self._calculate_macd(data["close"])

            if macd_line is None or signal_line is None or rsi is None:
                return "HOLD"

            # Signal conditions
            bullish = (macd_line.iloc[-1] > signal_line.iloc[-1]) and (rsi < 70)
            bearish = (macd_line.iloc[-1] < signal_line.iloc[-1]) and (rsi > 30)

            if bullish:
                return "BUY"
            elif bearish:
                return "SELL"
            else:
                return "HOLD"

        except Exception as e:
            self.logger.error(f"Error getting entry signal for {pair}: {e}")
            return "HOLD"

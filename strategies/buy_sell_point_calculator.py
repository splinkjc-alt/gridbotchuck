"""
Enhanced buy/sell point calculator using technical indicators.
This module provides intelligent entry/exit signal generation for grid trading.
"""

import logging

import numpy as np
import pandas as pd


class BuySellPointCalculator:
    """
    Calculates optimal buy and sell points using technical indicators
    on 15-minute candles.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_grid_entry_points(
        self,
        data: pd.DataFrame,
        num_grids: int = 8,
        current_price: float | None = None,
    ) -> dict[str, list[float]]:
        """
        Calculates optimized entry (buy) points using price levels and technical indicators.

        Args:
            data: OHLCV DataFrame with 15-minute candles
            num_grids: Number of grid levels
            current_price: Current market price (optional)

        Returns:
            Dictionary with 'buy_points', 'sell_points', and 'signals'
        """
        if len(data) < 26:
            self.logger.warning("Insufficient data for indicator calculation")
            return {"buy_points": [], "sell_points": [], "signals": "HOLD"}

        # Calculate technical indicators
        rsi = self._calculate_rsi(data["close"], period=14)
        macd_line, signal_line = self._calculate_macd(data["close"])
        bb_upper, _bb_middle, bb_lower = self._calculate_bollinger_bands(
            data["close"], period=20
        )

        current_price = current_price or data["close"].iloc[-1]
        price_high = data["high"].max()
        price_low = data["low"].min()
        price_high - price_low

        # Determine trend
        trend = self._determine_trend(
            rsi.iloc[-1], macd_line.iloc[-1], signal_line.iloc[-1]
        )

        # Calculate grid levels with adjustments based on technical indicators
        buy_points = self._calculate_buy_levels(
            price_low,
            current_price,
            num_grids,
            rsi.iloc[-1],
            bb_lower,
            bb_upper,
        )

        sell_points = self._calculate_sell_levels(
            current_price,
            price_high,
            num_grids,
            rsi.iloc[-1],
            bb_lower,
            bb_upper,
        )

        return {
            "buy_points": buy_points,
            "sell_points": sell_points,
            "signals": trend,
            "rsi": rsi.iloc[-1],
            "macd_strength": abs(macd_line.iloc[-1] - signal_line.iloc[-1]),
            "bollinger_position": self._get_bollinger_position(
                current_price, bb_lower, bb_upper
            ),
        }

    def _calculate_buy_levels(
        self,
        price_low: float,
        current_price: float,
        num_grids: int,
        rsi: float,
        bb_lower: pd.Series,
        bb_upper: pd.Series,
    ) -> list[float]:
        """
        Calculates optimal buy price levels based on technical indicators.

        - Clusters more buys near Bollinger Band lower when RSI is low
        - Spreads buys more when RSI is moderate
        """
        buy_points = []
        bb_lower_price = bb_lower.iloc[-1]

        # Adjust the number of buy levels based on RSI
        if rsi < 30:
            # Oversold condition - more aggressive buying
            num_buy_levels = max(int(num_grids * 0.7), 3)
        elif rsi < 50:
            # Moderate - normal distribution
            num_buy_levels = int(num_grids * 0.5)
        else:
            # Overbought condition - fewer buys
            num_buy_levels = max(int(num_grids * 0.3), 2)

        # Generate buy levels between low and current price
        base_levels = np.linspace(price_low, current_price, num_buy_levels)

        # Weight levels toward Bollinger Band lower
        weighted_levels = []
        for level in base_levels:
            # Pull levels toward BB lower if RSI < 50
            if rsi < 50:
                weight = (50 - rsi) / 50  # 0 to 1
                adjusted_level = level + (bb_lower_price - level) * weight * 0.5
                weighted_levels.append(adjusted_level)
            else:
                weighted_levels.append(level)

        buy_points = sorted(weighted_levels)
        return buy_points

    def _calculate_sell_levels(
        self,
        current_price: float,
        price_high: float,
        num_grids: int,
        rsi: float,
        bb_lower: pd.Series,
        bb_upper: pd.Series,
    ) -> list[float]:
        """
        Calculates optimal sell price levels based on technical indicators.

        - Clusters more sells near Bollinger Band upper when RSI is high
        - Spreads sells more when RSI is moderate
        """
        sell_points = []
        bb_upper_price = bb_upper.iloc[-1]

        # Adjust the number of sell levels based on RSI
        if rsi > 70:
            # Overbought condition - more aggressive selling
            num_sell_levels = max(int(num_grids * 0.7), 3)
        elif rsi > 50:
            # Moderate high - normal distribution
            num_sell_levels = int(num_grids * 0.5)
        else:
            # Oversold condition - fewer sells
            num_sell_levels = max(int(num_grids * 0.3), 2)

        # Generate sell levels between current and high
        base_levels = np.linspace(current_price, price_high, num_sell_levels)

        # Weight levels toward Bollinger Band upper
        weighted_levels = []
        for level in base_levels:
            # Pull levels toward BB upper if RSI > 50
            if rsi > 50:
                weight = (rsi - 50) / 50  # 0 to 1
                adjusted_level = level + (bb_upper_price - level) * weight * 0.5
                weighted_levels.append(adjusted_level)
            else:
                weighted_levels.append(level)

        sell_points = sorted(weighted_levels, reverse=True)
        return sell_points

    def _determine_trend(self, rsi: float, macd: float, signal: float) -> str:
        """
        Determines overall trend from technical indicators.
        """
        macd_bullish = macd > signal
        rsi_bullish = 40 <= rsi <= 70

        if macd_bullish and rsi_bullish:
            return "STRONG_BUY"
        elif macd_bullish:
            return "BUY"
        elif not macd_bullish and rsi > 70:
            return "SELL"
        elif not macd_bullish:
            return "STRONG_SELL"
        else:
            return "HOLD"

    def _get_bollinger_position(
        self, price: float, bb_lower: float, bb_upper: float
    ) -> str:
        """
        Determines where price is within Bollinger Bands.
        """
        range_size = bb_upper - bb_lower

        if price < bb_lower + (range_size * 0.2):
            return "LOWER_BAND"
        elif price > bb_upper - (range_size * 0.2):
            return "UPPER_BAND"
        else:
            return "MIDDLE"

    @staticmethod
    def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculates Relative Strength Index."""
        deltas = prices.diff()
        seed = deltas[: period + 1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period

        rs = up / down if down != 0 else 0
        rsi = 100.0 - 100.0 / (1.0 + rs)

        # Return full series with RSI calculated
        rsi_series = pd.Series(np.nan, index=prices.index)
        rsi_series.iloc[period:] = rsi

        # Calculate for entire series
        ups = prices.diff().clip(lower=0)
        downs = -prices.diff().clip(upper=0)
        avg_up = ups.rolling(window=period).mean()
        avg_down = downs.rolling(window=period).mean()

        rs = avg_up / avg_down
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def _calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[pd.Series, pd.Series]:
        """Calculates MACD and Signal line."""
        ema_fast = prices.ewm(span=fast_period, adjust=False).mean()
        ema_slow = prices.ewm(span=slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        return macd_line, signal_line

    @staticmethod
    def _calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        num_std: float = 2.0,
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Calculates Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()

        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)

        return upper_band, sma, lower_band

    def adjust_grid_levels_for_volatility(
        self,
        base_levels: list[float],
        data: pd.DataFrame,
        period: int = 14,
    ) -> list[float]:
        """
        Adjusts grid spacing based on Average True Range (ATR).
        Higher volatility = wider spacing, Lower volatility = tighter spacing.
        """
        atr = self._calculate_atr(data, period)

        if atr is None:
            return base_levels

        current_price = data["close"].iloc[-1]
        atr_percent = (atr / current_price) * 100

        # Adjust spacing based on volatility
        if atr_percent < 1:
            # Very low volatility - keep tight spacing
            return base_levels
        elif atr_percent > 3:
            # High volatility - increase spacing
            return [level * (1 + (atr_percent - 2) * 0.01) for level in base_levels]
        else:
            # Normal volatility
            return base_levels

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

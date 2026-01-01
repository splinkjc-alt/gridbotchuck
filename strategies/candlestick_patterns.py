"""
Candlestick pattern detection module.
Detects bullish and bearish reversal patterns for trend change confirmation.
"""

import pandas as pd


def detect_patterns(data: pd.DataFrame) -> dict[str, bool]:
    """
    Detect candlestick patterns in OHLCV data.

    Args:
        data: DataFrame with columns: open, high, low, close, volume

    Returns:
        Dictionary with pattern names as keys and boolean detection as values
    """
    if len(data) < 3:
        return {}

    patterns = {
        # Bullish patterns
        "hammer": detect_hammer(data),
        "bullish_engulfing": detect_bullish_engulfing(data),
        "morning_star": detect_morning_star(data),
        "dragonfly_doji": detect_dragonfly_doji(data),
        "three_white_soldiers": detect_three_white_soldiers(data),
        "piercing_line": detect_piercing_line(data),
        "bullish_harami": detect_bullish_harami(data),
        # Bearish patterns
        "shooting_star": detect_shooting_star(data),
        "bearish_engulfing": detect_bearish_engulfing(data),
        "evening_star": detect_evening_star(data),
        "hanging_man": detect_hanging_man(data),
        "three_black_crows": detect_three_black_crows(data),
        "dark_cloud_cover": detect_dark_cloud_cover(data),
        "bearish_harami": detect_bearish_harami(data),
        # Indecision patterns
        "doji": detect_doji(data),
        "spinning_top": detect_spinning_top(data),
    }

    return patterns


def _get_body_size(open_price: float, close_price: float) -> float:
    """Calculate absolute body size."""
    return abs(close_price - open_price)


def _get_upper_shadow(open_price: float, high: float, close_price: float) -> float:
    """Calculate upper shadow length."""
    return high - max(open_price, close_price)


def _get_lower_shadow(open_price: float, low: float, close_price: float) -> float:
    """Calculate lower shadow length."""
    return min(open_price, close_price) - low


def _is_bullish(open_price: float, close_price: float) -> bool:
    """Check if candle is bullish (green)."""
    return close_price > open_price


def _is_bearish(open_price: float, close_price: float) -> bool:
    """Check if candle is bearish (red)."""
    return close_price < open_price


def detect_hammer(data: pd.DataFrame) -> bool:
    """
    Detect Hammer pattern (bullish reversal).
    Characteristics:
    - Small body at the top
    - Long lower shadow (2x+ body)
    - Little or no upper shadow
    - Appears after a downtrend
    """
    if len(data) < 5:
        return False

    candle = data.iloc[-1]
    o, h, low, c = candle["open"], candle["high"], candle["low"], candle["close"]

    body = _get_body_size(o, c)
    upper_shadow = _get_upper_shadow(o, h, c)
    lower_shadow = _get_lower_shadow(o, low, c)

    # Avoid division by zero
    if body == 0:
        body = 0.0001

    # Hammer criteria
    has_small_upper_shadow = upper_shadow <= body * 0.5
    has_long_lower_shadow = lower_shadow >= body * 2

    # Check for prior downtrend (last 4 candles declining)
    prior_closes = data["close"].iloc[-5:-1]
    in_downtrend = prior_closes.iloc[0] > prior_closes.iloc[-1]

    return has_small_upper_shadow and has_long_lower_shadow and in_downtrend


def detect_shooting_star(data: pd.DataFrame) -> bool:
    """
    Detect Shooting Star pattern (bearish reversal).
    Characteristics:
    - Small body at the bottom
    - Long upper shadow (2x+ body)
    - Little or no lower shadow
    - Appears after an uptrend
    """
    if len(data) < 5:
        return False

    candle = data.iloc[-1]
    o, h, low, c = candle["open"], candle["high"], candle["low"], candle["close"]

    body = _get_body_size(o, c)
    upper_shadow = _get_upper_shadow(o, h, c)
    lower_shadow = _get_lower_shadow(o, low, c)

    if body == 0:
        body = 0.0001

    # Shooting star criteria
    has_long_upper_shadow = upper_shadow >= body * 2
    has_small_lower_shadow = lower_shadow <= body * 0.5

    # Check for prior uptrend
    prior_closes = data["close"].iloc[-5:-1]
    in_uptrend = prior_closes.iloc[0] < prior_closes.iloc[-1]

    return has_long_upper_shadow and has_small_lower_shadow and in_uptrend


def detect_bullish_engulfing(data: pd.DataFrame) -> bool:
    """
    Detect Bullish Engulfing pattern.
    Characteristics:
    - First candle: bearish (red)
    - Second candle: bullish (green) that completely engulfs first candle's body
    """
    if len(data) < 2:
        return False

    prev = data.iloc[-2]
    curr = data.iloc[-1]

    prev_o, prev_c = prev["open"], prev["close"]
    curr_o, curr_c = curr["open"], curr["close"]

    # First candle bearish, second bullish
    first_bearish = _is_bearish(prev_o, prev_c)
    second_bullish = _is_bullish(curr_o, curr_c)

    # Current body engulfs previous body
    engulfs = curr_o <= prev_c and curr_c >= prev_o

    return first_bearish and second_bullish and engulfs


def detect_bearish_engulfing(data: pd.DataFrame) -> bool:
    """
    Detect Bearish Engulfing pattern.
    Characteristics:
    - First candle: bullish (green)
    - Second candle: bearish (red) that completely engulfs first candle's body
    """
    if len(data) < 2:
        return False

    prev = data.iloc[-2]
    curr = data.iloc[-1]

    prev_o, prev_c = prev["open"], prev["close"]
    curr_o, curr_c = curr["open"], curr["close"]

    # First candle bullish, second bearish
    first_bullish = _is_bullish(prev_o, prev_c)
    second_bearish = _is_bearish(curr_o, curr_c)

    # Current body engulfs previous body
    engulfs = curr_o >= prev_c and curr_c <= prev_o

    return first_bullish and second_bearish and engulfs


def detect_morning_star(data: pd.DataFrame) -> bool:
    """
    Detect Morning Star pattern (bullish reversal).
    Three-candle pattern:
    1. Long bearish candle
    2. Small body (star) that gaps down
    3. Long bullish candle that closes above midpoint of first candle
    """
    if len(data) < 3:
        return False

    first = data.iloc[-3]
    second = data.iloc[-2]
    third = data.iloc[-1]

    # First candle: long bearish
    first_body = _get_body_size(first["open"], first["close"])
    first_bearish = _is_bearish(first["open"], first["close"])

    # Second candle: small body (star)
    second_body = _get_body_size(second["open"], second["close"])
    is_small_star = second_body < first_body * 0.3

    # Third candle: long bullish, closes above first midpoint
    _get_body_size(third["open"], third["close"])
    third_bullish = _is_bullish(third["open"], third["close"])
    first_midpoint = (first["open"] + first["close"]) / 2
    closes_above_midpoint = third["close"] > first_midpoint

    return first_bearish and is_small_star and third_bullish and closes_above_midpoint


def detect_evening_star(data: pd.DataFrame) -> bool:
    """
    Detect Evening Star pattern (bearish reversal).
    Three-candle pattern:
    1. Long bullish candle
    2. Small body (star) that gaps up
    3. Long bearish candle that closes below midpoint of first candle
    """
    if len(data) < 3:
        return False

    first = data.iloc[-3]
    second = data.iloc[-2]
    third = data.iloc[-1]

    # First candle: long bullish
    first_body = _get_body_size(first["open"], first["close"])
    first_bullish = _is_bullish(first["open"], first["close"])

    # Second candle: small body (star)
    second_body = _get_body_size(second["open"], second["close"])
    is_small_star = second_body < first_body * 0.3

    # Third candle: long bearish, closes below first midpoint
    third_bearish = _is_bearish(third["open"], third["close"])
    first_midpoint = (first["open"] + first["close"]) / 2
    closes_below_midpoint = third["close"] < first_midpoint

    return first_bullish and is_small_star and third_bearish and closes_below_midpoint


def detect_doji(data: pd.DataFrame) -> bool:
    """
    Detect Doji pattern (indecision).
    Characteristics:
    - Open and close are virtually equal
    - Body is very small relative to the full range
    """
    if len(data) < 1:
        return False

    candle = data.iloc[-1]
    o, h, low, c = candle["open"], candle["high"], candle["low"], candle["close"]

    body = _get_body_size(o, c)
    full_range = h - low

    if full_range == 0:
        return False

    # Doji: body is less than 10% of full range
    return body / full_range < 0.1


def detect_dragonfly_doji(data: pd.DataFrame) -> bool:
    """
    Detect Dragonfly Doji (bullish).
    Characteristics:
    - Open and close at or near the high
    - Long lower shadow
    - Little or no upper shadow
    """
    if len(data) < 1:
        return False

    candle = data.iloc[-1]
    o, h, low, c = candle["open"], candle["high"], candle["low"], candle["close"]

    body = _get_body_size(o, c)
    full_range = h - low
    upper_shadow = _get_upper_shadow(o, h, c)
    lower_shadow = _get_lower_shadow(o, low, c)

    if full_range == 0:
        return False

    is_doji = body / full_range < 0.1
    has_long_lower = lower_shadow > full_range * 0.6
    has_small_upper = upper_shadow < full_range * 0.1

    return is_doji and has_long_lower and has_small_upper


def detect_hanging_man(data: pd.DataFrame) -> bool:
    """
    Detect Hanging Man pattern (bearish reversal).
    Same shape as hammer but appears after uptrend.
    """
    if len(data) < 5:
        return False

    candle = data.iloc[-1]
    o, h, low, c = candle["open"], candle["high"], candle["low"], candle["close"]

    body = _get_body_size(o, c)
    upper_shadow = _get_upper_shadow(o, h, c)
    lower_shadow = _get_lower_shadow(o, low, c)

    if body == 0:
        body = 0.0001

    # Hanging man criteria (same as hammer)
    has_small_upper_shadow = upper_shadow <= body * 0.5
    has_long_lower_shadow = lower_shadow >= body * 2

    # Check for prior uptrend (opposite of hammer)
    prior_closes = data["close"].iloc[-5:-1]
    in_uptrend = prior_closes.iloc[0] < prior_closes.iloc[-1]

    return has_small_upper_shadow and has_long_lower_shadow and in_uptrend


def detect_three_white_soldiers(data: pd.DataFrame) -> bool:
    """
    Detect Three White Soldiers pattern (strong bullish).
    Three consecutive long bullish candles with higher closes.
    """
    if len(data) < 3:
        return False

    candles = data.iloc[-3:]

    all_bullish = True
    progressively_higher = True

    for i, (_, candle) in enumerate(candles.iterrows()):
        # Check if bullish
        if not _is_bullish(candle["open"], candle["close"]):
            all_bullish = False
            break

        # Check progressively higher closes
        if i > 0:
            prev_candle = candles.iloc[i - 1]
            if candle["close"] <= prev_candle["close"]:
                progressively_higher = False
                break

    return all_bullish and progressively_higher


def detect_three_black_crows(data: pd.DataFrame) -> bool:
    """
    Detect Three Black Crows pattern (strong bearish).
    Three consecutive long bearish candles with lower closes.
    """
    if len(data) < 3:
        return False

    candles = data.iloc[-3:]

    all_bearish = True
    progressively_lower = True

    for i, (_, candle) in enumerate(candles.iterrows()):
        # Check if bearish
        if not _is_bearish(candle["open"], candle["close"]):
            all_bearish = False
            break

        # Check progressively lower closes
        if i > 0:
            prev_candle = candles.iloc[i - 1]
            if candle["close"] >= prev_candle["close"]:
                progressively_lower = False
                break

    return all_bearish and progressively_lower


def detect_piercing_line(data: pd.DataFrame) -> bool:
    """
    Detect Piercing Line pattern (bullish reversal).
    Two-candle pattern:
    1. Long bearish candle
    2. Bullish candle that opens below prior low but closes above midpoint
    """
    if len(data) < 2:
        return False

    prev = data.iloc[-2]
    curr = data.iloc[-1]

    # First candle bearish
    first_bearish = _is_bearish(prev["open"], prev["close"])

    # Second candle bullish
    second_bullish = _is_bullish(curr["open"], curr["close"])

    # Opens below prior low
    opens_below = curr["open"] < prev["low"]

    # Closes above midpoint of first candle
    first_midpoint = (prev["open"] + prev["close"]) / 2
    closes_above_midpoint = curr["close"] > first_midpoint

    # But not above open of first candle (would be engulfing)
    not_engulfing = curr["close"] < prev["open"]

    return first_bearish and second_bullish and opens_below and closes_above_midpoint and not_engulfing


def detect_dark_cloud_cover(data: pd.DataFrame) -> bool:
    """
    Detect Dark Cloud Cover pattern (bearish reversal).
    Two-candle pattern:
    1. Long bullish candle
    2. Bearish candle that opens above prior high but closes below midpoint
    """
    if len(data) < 2:
        return False

    prev = data.iloc[-2]
    curr = data.iloc[-1]

    # First candle bullish
    first_bullish = _is_bullish(prev["open"], prev["close"])

    # Second candle bearish
    second_bearish = _is_bearish(curr["open"], curr["close"])

    # Opens above prior high
    opens_above = curr["open"] > prev["high"]

    # Closes below midpoint of first candle
    first_midpoint = (prev["open"] + prev["close"]) / 2
    closes_below_midpoint = curr["close"] < first_midpoint

    # But not below open of first candle (would be engulfing)
    not_engulfing = curr["close"] > prev["open"]

    return first_bullish and second_bearish and opens_above and closes_below_midpoint and not_engulfing


def detect_bullish_harami(data: pd.DataFrame) -> bool:
    """
    Detect Bullish Harami pattern.
    Small bullish candle contained within prior large bearish candle.
    """
    if len(data) < 2:
        return False

    prev = data.iloc[-2]
    curr = data.iloc[-1]

    # First candle: large bearish
    first_bearish = _is_bearish(prev["open"], prev["close"])
    first_body = _get_body_size(prev["open"], prev["close"])

    # Second candle: small bullish
    second_bullish = _is_bullish(curr["open"], curr["close"])
    second_body = _get_body_size(curr["open"], curr["close"])

    # Second body smaller than first
    smaller_body = second_body < first_body * 0.5

    # Second body contained within first
    contained = curr["open"] > prev["close"] and curr["close"] < prev["open"]

    return first_bearish and second_bullish and smaller_body and contained


def detect_bearish_harami(data: pd.DataFrame) -> bool:
    """
    Detect Bearish Harami pattern.
    Small bearish candle contained within prior large bullish candle.
    """
    if len(data) < 2:
        return False

    prev = data.iloc[-2]
    curr = data.iloc[-1]

    # First candle: large bullish
    first_bullish = _is_bullish(prev["open"], prev["close"])
    first_body = _get_body_size(prev["open"], prev["close"])

    # Second candle: small bearish
    second_bearish = _is_bearish(curr["open"], curr["close"])
    second_body = _get_body_size(curr["open"], curr["close"])

    # Second body smaller than first
    smaller_body = second_body < first_body * 0.5

    # Second body contained within first
    contained = curr["open"] < prev["close"] and curr["close"] > prev["open"]

    return first_bullish and second_bearish and smaller_body and contained


def detect_spinning_top(data: pd.DataFrame) -> bool:
    """
    Detect Spinning Top pattern (indecision).
    Small body with upper and lower shadows.
    """
    if len(data) < 1:
        return False

    candle = data.iloc[-1]
    o, h, low, c = candle["open"], candle["high"], candle["low"], candle["close"]

    body = _get_body_size(o, c)
    upper_shadow = _get_upper_shadow(o, h, c)
    lower_shadow = _get_lower_shadow(o, low, c)
    full_range = h - low

    if full_range == 0:
        return False

    # Small body (10-30% of range)
    small_body = 0.1 < body / full_range < 0.3

    # Both shadows present
    has_both_shadows = upper_shadow > body * 0.5 and lower_shadow > body * 0.5

    return small_body and has_both_shadows


def get_pattern_summary(patterns: dict[str, bool]) -> dict:
    """
    Get a summary of detected patterns.

    Returns:
        Dictionary with bullish_count, bearish_count, and list of detected patterns
    """
    bullish_patterns = [
        "hammer",
        "bullish_engulfing",
        "morning_star",
        "dragonfly_doji",
        "three_white_soldiers",
        "piercing_line",
        "bullish_harami",
    ]
    bearish_patterns = [
        "shooting_star",
        "bearish_engulfing",
        "evening_star",
        "hanging_man",
        "three_black_crows",
        "dark_cloud_cover",
        "bearish_harami",
    ]

    detected_bullish = [p for p in bullish_patterns if patterns.get(p, False)]
    detected_bearish = [p for p in bearish_patterns if patterns.get(p, False)]
    detected_neutral = [p for p in ["doji", "spinning_top"] if patterns.get(p, False)]

    return {
        "bullish_count": len(detected_bullish),
        "bearish_count": len(detected_bearish),
        "neutral_count": len(detected_neutral),
        "bullish_patterns": detected_bullish,
        "bearish_patterns": detected_bearish,
        "neutral_patterns": detected_neutral,
        "bias": "bullish"
        if len(detected_bullish) > len(detected_bearish)
        else "bearish"
        if len(detected_bearish) > len(detected_bullish)
        else "neutral",
    }

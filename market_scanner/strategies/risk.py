import numpy as np
import pandas as pd

def analyze(ticker, data):
    """
    Returns a score based on Risk Management (Safety).
    Higher Score = Lower Volatility (Safer).
    """
    if data is not None and not data.empty and len(data) > 14:
        # Calculate ATR
        high_low = data['High'] - data['Low']
        high_close = np.abs(data['High'] - data['Close'].shift())
        low_close = np.abs(data['Low'] - data['Close'].shift())

        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        atr = true_range.rolling(14).mean().iloc[-1]
        current_price = data['Close'].iloc[-1]

        # ATR Percentage
        atr_pct = (atr / current_price) * 100

        # Score: Inverse of volatility (Higher is safer)
        # Avoid division by zero
        if atr_pct == 0:
            return 0
        score = 100 / atr_pct
        return score
    return -999

def analyze(ticker, data):
    """
    Returns a score based on Strategic Positioning (Relative Strength / Momentum).
    Using 1-month (20 trading days) return.
    """
    if data is not None and not data.empty and len(data) > 20:
        current_price = data['Close'].iloc[-1]
        past_price = data['Close'].iloc[-20]
        
        # Score is 1-month return percentage
        score = ((current_price - past_price) / past_price) * 100
        return score
    return -999

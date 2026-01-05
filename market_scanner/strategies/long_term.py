def analyze(ticker, data):
    """
    Returns a score based on Long-Term trend (Price vs 200 SMA).
    Higher Score = Stronger Trend (Price higher above SMA).
    """
    if data is not None and not data.empty and len(data) > 200:
        sma200 = data['Close'].rolling(window=200).mean().iloc[-1]
        current_price = data['Close'].iloc[-1]
        
        # Score is percentage above/below SMA
        score = ((current_price - sma200) / sma200) * 100
        return score
    return -999 # Not enough data

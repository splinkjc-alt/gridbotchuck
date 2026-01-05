def analyze(ticker, data):
    """
    Returns a score based on Trading opportunity (Oversold RSI).
    Higher Score = Lower RSI (Better Buy Dip).
    """
    if data is not None and not data.empty and len(data) > 26:
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]
        
        # Score: We want low RSI (Oversold) to be "Top Pick" for buying
        # So we invert RSI: 100 - RSI. 
        # RSI 30 -> Score 70. RSI 70 -> Score 30.
        score = 100 - rsi
        return score
    return -999

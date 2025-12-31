================================================================================
                     GRIDBOT EMA TRADING BOT - QUICK START
================================================================================

WHAT IS THIS?
-------------
This is an automated cryptocurrency trading bot that uses EMA (Exponential 
Moving Average) crossover signals to buy and sell on Kraken exchange.

Strategy: Buy when Fast EMA crosses above Slow EMA with widening gap (momentum)
          Sell when gap narrows (momentum fading)

DEFAULT: EMA 9/20 (can be changed in config/ema_settings.json)


FIRST TIME SETUP (5 minutes)
----------------------------

1. GET KRAKEN API KEYS
   - Go to: https://www.kraken.com/u/security/api
   - Create new API key with permissions:
     * Query Funds
     * Query Open Orders & Trades  
     * Query Closed Orders & Trades
     * Create & Modify Orders
     * Cancel/Close Orders
   - Copy the API Key and Secret Key

2. CONFIGURE THE BOT
   - Open the "config" folder
   - Rename ".env.example" to ".env"
   - Edit ".env" with Notepad
   - Paste your API keys:
     EXCHANGE_API_KEY=your_key_here
     EXCHANGE_SECRET_KEY=your_secret_here
   - Save and close


HOW TO USE
----------

CHECK_ACCOUNT.bat   - See your balances and open orders
SCAN_MARKET.bat     - See current buy/sell signals (dry run, no trading)
START_BOT.bat       - Start the trading bot (LIVE TRADING!)
STOP_BOT.bat        - Stop the bot


BOT SETTINGS (Default)
----------------------
- EMA Fast Period: 9  (adjustable in config/ema_settings.json)
- EMA Slow Period: 20 (adjustable in config/ema_settings.json)
- Position Size: 20% of account per trade
- Reserve: 10% always kept in USD
- Max Positions: 2 coins at once
- Scan Interval: Every 60 seconds

To change EMA periods, edit config/ema_settings.json:
  {
    "ema_fast": 9,      <- Change to your preferred fast EMA (e.g., 12)
    "ema_slow": 20,     <- Change to your preferred slow EMA (e.g., 26)
    ...
  }


COINS MONITORED
---------------
UNI, SOL, XRP, ADA, DOGE, AVAX, DOT, LINK, ATOM, FIL, 
NEAR, APT, ARB, OP, SUI, TIA, INJ, FET


UNDERSTANDING THE SIGNALS
-------------------------
BUY       = Fresh EMA crossover just happened
SAFE_BUY  = EMA 9 > EMA 20 AND gap is widening (good momentum)
HOLD      = EMA 9 > EMA 20 but gap narrowing (momentum fading)
SELL      = EMA 9 crossed below EMA 20 (bearish)


WARNINGS
--------
* This bot trades with REAL MONEY
* Cryptocurrency trading is risky
* Never invest more than you can afford to lose
* Test with small amounts first
* Past performance does not guarantee future results


TROUBLESHOOTING
---------------
"No API keys found" - Make sure you created config\.env file
"Connection error"  - Check your internet connection
"Insufficient funds" - Need at least $50 USD in Kraken account
"Invalid API key"    - Double-check your API keys in .env file


================================================================================
                              HAPPY TRADING!
================================================================================

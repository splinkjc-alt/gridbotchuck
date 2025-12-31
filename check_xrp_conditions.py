"""Quick XRP market condition check."""
import ccxt
import pandas as pd
from datetime import datetime, timedelta

exchange = ccxt.kraken({'enableRateLimit': True})
since = exchange.parse8601((datetime.now() - timedelta(hours=24)).isoformat())
ohlcv = exchange.fetch_ohlcv('XRP/USD', '5m', since=since, limit=300)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Calculate price range
price_min = df['low'].min()
price_max = df['high'].max()
price_range = ((price_max - price_min) / price_min) * 100

# Calculate RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))

print('XRP/USD Last 24 Hours Summary')
print('=' * 50)
print(f'Price Range: ${price_min:.4f} - ${price_max:.4f}')
print(f'Total Movement: {price_range:.2f}%')
print(f'Current Price: ${df["close"].iloc[-1]:.4f}')
print(f'RSI(14) Low: {rsi.min():.1f}')
print(f'RSI(14) High: {rsi.max():.1f}')
print(f'RSI(14) Current: {rsi.iloc[-1]:.1f}')
print()

if rsi.min() < 35:
    print('ANALYSIS: XRP had oversold conditions - bot should have found entries')
elif rsi.max() > 65:
    print('ANALYSIS: XRP was overbought - momentum strategy might work')
else:
    print('ANALYSIS: XRP stayed neutral - no clear entry signals')
    print('This is why the optimizer found 0 trades - market was flat')

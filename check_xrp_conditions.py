"""Quick XRP market condition check."""

from datetime import datetime, timedelta

import ccxt
import pandas as pd

exchange = ccxt.kraken({"enableRateLimit": True})
since = exchange.parse8601((datetime.now() - timedelta(hours=24)).isoformat())
ohlcv = exchange.fetch_ohlcv("XRP/USD", "5m", since=since, limit=300)
df = pd.DataFrame(
    ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
)
df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

# Calculate price range
price_min = df["low"].min()
price_max = df["high"].max()
price_range = ((price_max - price_min) / price_min) * 100

# Calculate RSI
delta = df["close"].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
rsi = 100 - (100 / (1 + rs))


if rsi.min() < 35 or rsi.max() > 65:
    pass
else:
    pass

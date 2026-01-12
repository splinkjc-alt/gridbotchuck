"""
Sleeping Marketbot - Stock Day Trader
=====================================

RSI cross strategy for stock day trading via Alpaca.
- Buy when RSI crosses below 30 (oversold)
- Sell when RSI crosses above 70 (overbought)
- Take profit: +2%, Stop loss: -1.5%

Only trades during market hours (9:30 AM - 4:00 PM ET).
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, time, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import pytz

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

# Try importing alpaca
try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.requests import MarketOrderRequest
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

# Stock watchlist
STOCK_WATCHLIST = ["TSLA", "NVDA", "AMD", "AAPL", "MSFT", "META", "GOOGL"]

# Trading settings
POSITION_SIZE_USD = 500.0
MAX_POSITIONS = 3
TAKE_PROFIT_PCT = 2.0
STOP_LOSS_PCT = 1.5
MAX_HOLD_HOURS = 6

# Anti-churn settings
MIN_HOLD_MINUTES = 30
MIN_PROFIT_TO_SELL = 0.5
COOLDOWN_MINUTES = 20


class MarketBot:
    def __init__(self):
        self.trading_client = None
        self.data_client = None
        self.positions = {}  # symbol -> {shares, entry_price, entry_time}
        self.cooldowns = {}  # symbol -> datetime when cooldown expires
        self.et_tz = pytz.timezone("US/Eastern")
        self.logger = logging.getLogger("Marketbot")
        self.error_count = 0
        self.max_errors = 5

    async def start(self, paper_mode: bool = True):
        """Initialize Alpaca connection."""
        if not ALPACA_AVAILABLE:
            self.logger.error("Alpaca not installed. Run: pip install alpaca-py")
            return False

        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")

        if not api_key or not secret_key:
            self.logger.error("ALPACA_API_KEY and ALPACA_SECRET_KEY required in .env")
            return False

        try:
            self.trading_client = TradingClient(api_key, secret_key, paper=paper_mode)
            self.data_client = StockHistoricalDataClient(api_key, secret_key)
            account = self.trading_client.get_account()
            mode_str = "Paper" if paper_mode else "Live"
            self.logger.info(f"Connected to Alpaca ({mode_str})")
            self.logger.info(f"Account: ${float(account.cash):.2f} cash")
            return True
        except Exception as e:
            self.logger.error(f"Alpaca connection failed: {e}")
            return False

    def is_market_open(self) -> bool:
        """Check if US market is open."""
        now = datetime.now(self.et_tz)
        if now.weekday() > 4:  # Weekend
            return False
        market_open = time(9, 30)
        market_close = time(16, 0)
        return market_open <= now.time() <= market_close

    def get_next_market_open(self) -> str:
        """Get time until next market open."""
        now = datetime.now(self.et_tz)
        if now.weekday() >= 5:  # Weekend
            days_until_monday = 7 - now.weekday()
            return f"{days_until_monday} days"
        if now.time() < time(9, 30):
            market_open = now.replace(hour=9, minute=30, second=0)
            delta = market_open - now
            return f"{delta.seconds // 3600}h {(delta.seconds % 3600) // 60}m"
        if now.time() >= time(16, 0):
            return "Tomorrow 9:30 AM ET"
        return "Now"

    async def fetch_bars(self, symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch stock bar data."""
        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Minute,
                limit=limit * 15,  # Get more data for 15m aggregation
            )
            bars = self.data_client.get_stock_bars(request)

            if symbol not in bars or not bars[symbol]:
                return None

            df = pd.DataFrame(
                [
                    {
                        "timestamp": bar.timestamp,
                        "open": bar.open,
                        "high": bar.high,
                        "low": bar.low,
                        "close": bar.close,
                        "volume": bar.volume,
                    }
                    for bar in bars[symbol]
                ]
            )

            # Resample to 15m
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
            df = (
                df.resample("15min")
                .agg(
                    {
                        "open": "first",
                        "high": "max",
                        "low": "min",
                        "close": "last",
                        "volume": "sum",
                    }
                )
                .dropna()
            )

            return df.reset_index()
        except Exception as e:
            self.logger.error(f"Error fetching {symbol}: {e}")
            return None

    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """Calculate RSI."""
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        return df

    def check_buy_signal(self, symbol: str, df: pd.DataFrame) -> tuple[bool, str]:
        """Check buy signal - RSI crosses below 30."""
        # Check cooldown
        if symbol in self.cooldowns:
            if datetime.now() < self.cooldowns[symbol]:
                return False, ""
            else:
                del self.cooldowns[symbol]

        if len(df) < 3:
            return False, ""

        row = df.iloc[-1]
        prev = df.iloc[-2]

        # RSI cross: Previous >= 30, Current < 30
        if prev["rsi"] >= 30 and row["rsi"] < 30:
            return True, f"RSI_cross_DOWN={row['rsi']:.1f}"

        return False, ""

    def check_sell_signal(
        self, symbol: str, current_price: float, df: pd.DataFrame
    ) -> tuple[bool, str]:
        """Check sell conditions."""
        if symbol not in self.positions:
            return False, ""

        pos = self.positions[symbol]
        entry_price = pos["entry_price"]
        entry_time = pos["entry_time"]
        pct_change = ((current_price - entry_price) / entry_price) * 100
        minutes_held = (datetime.now() - entry_time).total_seconds() / 60

        # Take profit
        if pct_change >= TAKE_PROFIT_PCT:
            return True, f"TAKE_PROFIT +{pct_change:.2f}%"

        # Stop loss
        if pct_change <= -STOP_LOSS_PCT:
            return True, f"STOP_LOSS {pct_change:.2f}%"

        # Time stop
        hours_held = minutes_held / 60
        if hours_held >= MAX_HOLD_HOURS:
            return True, f"TIME_STOP ({hours_held:.1f}h) {pct_change:+.2f}%"

        # Min hold check
        if minutes_held < MIN_HOLD_MINUTES:
            return False, ""

        # Min profit check
        if pct_change < MIN_PROFIT_TO_SELL:
            return False, ""

        # RSI cross above 70
        if len(df) >= 2:
            row = df.iloc[-1]
            prev = df.iloc[-2]
            if prev["rsi"] <= 70 and row["rsi"] > 70:
                return True, f"RSI_cross_UP={row['rsi']:.1f} {pct_change:+.2f}%"

        return False, ""

    async def execute_buy(
        self, symbol: str, price: float, reason: str, paper_mode: bool = True
    ):
        """Execute buy order."""
        try:
            shares = int(POSITION_SIZE_USD / price)
            if shares < 1:
                self.logger.warning(f"Price too high for {symbol}: ${price:.2f}")
                return False

            if paper_mode:
                self.logger.info(f"[PAPER BUY] {symbol} @ ${price:.2f} | {reason}")
                self.positions[symbol] = {
                    "shares": shares,
                    "entry_price": price,
                    "entry_time": datetime.now(),
                }
                self.logger.info(f"[PAPER BOUGHT] {shares} {symbol} @ ${price:.2f}")
            else:
                self.logger.info(f"[BUY] {symbol} @ ${price:.2f} | {reason}")
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=shares,
                    side=OrderSide.BUY,
                    time_in_force=TimeInForce.DAY,
                )
                self.trading_client.submit_order(order)
                self.positions[symbol] = {
                    "shares": shares,
                    "entry_price": price,
                    "entry_time": datetime.now(),
                }
                self.logger.info(f"[BOUGHT] {shares} {symbol} @ ${price:.2f}")
            return True
        except Exception as e:
            self.logger.error(f"Buy error {symbol}: {e}")
            return False

    async def execute_sell(
        self, symbol: str, price: float, reason: str, paper_mode: bool = True
    ):
        """Execute sell order."""
        if symbol not in self.positions:
            return False

        try:
            pos = self.positions[symbol]
            shares = pos["shares"]
            entry_price = pos["entry_price"]
            pct_change = ((price - entry_price) / entry_price) * 100
            profit_usd = (price - entry_price) * shares

            if paper_mode:
                self.logger.info(f"[PAPER SELL] {symbol} @ ${price:.2f} | {reason}")
                self.logger.info(
                    f"[PAPER SOLD] {symbol} | P/L: ${profit_usd:.2f} ({pct_change:+.2f}%)"
                )
            else:
                self.logger.info(f"[SELL] {symbol} @ ${price:.2f} | {reason}")
                order = MarketOrderRequest(
                    symbol=symbol,
                    qty=shares,
                    side=OrderSide.SELL,
                    time_in_force=TimeInForce.DAY,
                )
                self.trading_client.submit_order(order)
                self.logger.info(
                    f"[SOLD] {symbol} | P/L: ${profit_usd:.2f} ({pct_change:+.2f}%)"
                )

            self.cooldowns[symbol] = datetime.now() + timedelta(
                minutes=COOLDOWN_MINUTES
            )
            del self.positions[symbol]
            return True
        except Exception as e:
            self.logger.error(f"Sell error {symbol}: {e}")
            return False

    async def run(self, paper_mode: bool = True):
        """Main trading loop."""
        mode_str = "PAPER MODE" if paper_mode else "LIVE"
        self.logger.info("=" * 60)
        self.logger.info(f"SLEEPING MARKETBOT - {mode_str}")
        self.logger.info("=" * 60)
        self.logger.info(f"Stocks: {STOCK_WATCHLIST}")
        self.logger.info(f"Position Size: ${POSITION_SIZE_USD}")
        self.logger.info(f"Take Profit: +{TAKE_PROFIT_PCT}%")
        self.logger.info(f"Stop Loss: -{STOP_LOSS_PCT}%")
        self.logger.info(f"Max Hold: {MAX_HOLD_HOURS}h")
        self.logger.info(
            f"Min Hold: {MIN_HOLD_MINUTES}m | Min Profit: {MIN_PROFIT_TO_SELL}% | Cooldown: {COOLDOWN_MINUTES}m"
        )
        self.logger.info("=" * 60)

        if not await self.start(paper_mode):
            return

        cycle_count = 0

        while True:
            try:
                # Check market hours
                if not self.is_market_open():
                    next_open = self.get_next_market_open()
                    self.logger.info(
                        f"[SLEEPING] Market closed. Next open: {next_open}"
                    )
                    await asyncio.sleep(300)  # Check every 5 min
                    continue

                cycle_count += 1
                stocks_checked = 0

                for symbol in STOCK_WATCHLIST:
                    df = await self.fetch_bars(symbol)
                    if df is None or df.empty:
                        self.error_count += 1
                        continue

                    stocks_checked += 1
                    df = self.calculate_rsi(df)
                    price = df.iloc[-1]["close"]

                    # Check sell first
                    if symbol in self.positions:
                        should_sell, reason = self.check_sell_signal(symbol, price, df)
                        if should_sell:
                            await self.execute_sell(symbol, price, reason, paper_mode)

                    # Check buy
                    elif len(self.positions) < MAX_POSITIONS:
                        should_buy, reason = self.check_buy_signal(symbol, df)
                        if should_buy:
                            await self.execute_buy(symbol, price, reason, paper_mode)

                    await asyncio.sleep(0.5)

                # Reset error count on success
                if stocks_checked > 0:
                    self.error_count = 0

                # Auto-reset after too many errors
                if self.error_count >= self.max_errors:
                    self.logger.warning(
                        f"[REFRESH] {self.error_count} errors - reconnecting..."
                    )
                    await asyncio.sleep(5)
                    await self.start(paper_mode)
                    self.error_count = 0
                    self.logger.info("[REFRESH] Reconnected")

                # Status update
                if cycle_count % 5 == 0:
                    if self.positions:
                        pos_str = ", ".join(self.positions.keys())
                        self.logger.info(
                            f"[HOLDING] {len(self.positions)}/{MAX_POSITIONS}: {pos_str}"
                        )
                    else:
                        self.logger.info(
                            f"[SCANNING] Cycle {cycle_count} - watching for entries"
                        )

                await asyncio.sleep(60)

            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(30)


async def main(paper_mode: bool = True):
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = "marketbot_paper.log" if paper_mode else "marketbot_live.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / log_file),
        ],
    )

    bot = MarketBot()
    try:
        await bot.run(paper_mode=paper_mode)
    except KeyboardInterrupt:
        logging.info("Shutting down...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Sleeping Marketbot")
    parser.add_argument(
        "--paper", action="store_true", default=True, help="Run in paper trading mode"
    )
    parser.add_argument("--live", action="store_true", help="Run in live trading mode")
    args = parser.parse_args()

    paper = not args.live
    asyncio.run(main(paper_mode=paper))

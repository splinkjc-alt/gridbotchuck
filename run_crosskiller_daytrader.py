"""
CrossKiller Day Trader - 5m Optimized
=====================================

Based on backtest results:
- SOL: EMA 9/20 + mean_reversion = +13.91%
- XRP: Full Suite + momentum = +13.52%
- ADA: Full Suite + momentum = +11.41%
- LINK: RSI+EMA + mean_reversion = +11.37%

Day trading targets: +2% take profit, -1.5% stop loss
"""

import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
import ccxt.async_support as ccxt
import os

load_dotenv()

# Optimized coin configs from backtest
COIN_CONFIGS = {
    "SOL/USD": {
        "name": "SOL",
        "use_rsi": False,
        "use_bb": False,
        "use_ema": True,
        "strategy": "mean_reversion",
        "backtest_return": 13.91,
    },
    "ADA/USD": {
        "name": "ADA",
        "use_rsi": True,
        "use_bb": True,
        "use_ema": True,
        "use_macd": True,
        "strategy": "momentum",
        "backtest_return": 11.41,
    },
    "LINK/USD": {
        "name": "LINK",
        "use_rsi": True,
        "use_bb": False,
        "use_ema": True,
        "use_macd": False,
        "strategy": "mean_reversion",
        "backtest_return": 11.37,
    },
}

# Day trading settings
TIMEFRAME = "15m"
POSITION_SIZE_USD = 350.0  # $400 per position
MAX_POSITIONS = 3
TAKE_PROFIT_PCT = 2.0
STOP_LOSS_PCT = 1.5
MAX_HOLD_HOURS = 4  # Quick trades

# Anti-churn settings
MIN_HOLD_MINUTES = 20  # Don't sell within first 20 min (unless stop loss)
MIN_PROFIT_TO_SELL = 0.5  # Need at least 0.5% profit to sell on signals
COOLDOWN_MINUTES = 15  # After selling, wait 15 min before re-buying same coin


class DayTraderBot:
    def __init__(self):
        self.exchange = None
        self.positions = {}  # symbol -> {amount, entry_price, entry_time}
        self.cooldowns = {}  # symbol -> datetime when cooldown expires
        self.logger = logging.getLogger("CrossKiller-DayTrader")

    async def start(self):
        """Initialize exchange connection."""
        self.exchange = ccxt.coinbase(
            {
                "apiKey": os.getenv("COINBASE_API_KEY"),
                "secret": os.getenv("COINBASE_SECRET_KEY"),
                "enableRateLimit": True,
            }
        )
        self.logger.info("Connected to Coinbase")

    async def close(self):
        """Close exchange connection."""
        if self.exchange:
            await self.exchange.close()

    async def fetch_ohlcv(
        self, symbol: str, limit: int = 100
    ) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data."""
        try:
            data = await self.exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=limit)
            if not data:
                return None
            df = pd.DataFrame(
                data, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            return df
        except Exception as e:
            self.logger.error(f"Error fetching {symbol}: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        """Calculate indicators based on config."""
        if config.get("use_rsi", False):
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

        if config.get("use_bb", False):
            df["bb_mid"] = df["close"].rolling(window=20).mean()
            df["bb_std"] = df["close"].rolling(window=20).std()
            df["bb_upper"] = df["bb_mid"] + (df["bb_std"] * 2)
            df["bb_lower"] = df["bb_mid"] - (df["bb_std"] * 2)

        if config.get("use_ema", False):
            df["ema_9"] = df["close"].ewm(span=9, adjust=False).mean()
            df["ema_16"] = df["close"].ewm(span=16, adjust=False).mean()

        if config.get("use_macd", False):
            ema_12 = df["close"].ewm(span=12, adjust=False).mean()
            ema_26 = df["close"].ewm(span=26, adjust=False).mean()
            df["macd"] = ema_12 - ema_26
            df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()

        return df

    def check_buy_signal(
        self, symbol: str, row: pd.Series, config: dict
    ) -> tuple[bool, str]:
        """Check buy signal based on coin's optimal config."""
        # === ANTI-CHURN: Check cooldown ===
        if symbol in self.cooldowns:
            if datetime.now() < self.cooldowns[symbol]:
                return False, ""  # Still in cooldown
            else:
                del self.cooldowns[symbol]  # Cooldown expired

        signals = []
        reasons = []
        strategy = config.get("strategy", "momentum")

        if config.get("use_rsi", False) and "rsi" in row:
            if strategy == "mean_reversion" and row["rsi"] < 30:
                signals.append(True)
                reasons.append(f"RSI={row['rsi']:.1f}")
            elif strategy == "momentum" and 30 < row["rsi"] < 50:
                signals.append(True)
                reasons.append(f"RSI={row['rsi']:.1f}")

        if config.get("use_bb", False) and "bb_lower" in row:
            if row["close"] <= row["bb_lower"]:
                signals.append(True)
                reasons.append("BB_lower")

        if config.get("use_ema", False) and "ema_9" in row:
            # Buy on bearish cross (dip) - EMA 9 below EMA 20
            if row["ema_9"] < row["ema_16"]:
                signals.append(True)
                reasons.append("EMA_dip")

        if config.get("use_macd", False) and "macd" in row:
            if strategy == "momentum" and row["macd"] > row["macd_signal"]:
                signals.append(True)
                reasons.append("MACD_bull")

        if not signals:
            return False, ""

        # Momentum: any signal, Mean reversion: all signals
        if strategy == "momentum":
            return any(signals), " + ".join(reasons)
        else:
            return all(signals), " + ".join(reasons)

    def check_sell_signal(
        self, symbol: str, current_price: float, config: dict, row: pd.Series
    ) -> tuple[bool, str]:
        """Check sell conditions."""
        if symbol not in self.positions:
            return False, ""

        pos = self.positions[symbol]
        entry_price = pos["entry_price"]
        entry_time = pos["entry_time"]
        pct_change = ((current_price - entry_price) / entry_price) * 100
        minutes_held = (datetime.now() - entry_time).total_seconds() / 60

        # Take profit - always allowed
        if pct_change >= TAKE_PROFIT_PCT:
            return True, f"TAKE_PROFIT +{pct_change:.2f}%"

        # Stop loss - always allowed (protect capital)
        if pct_change <= -STOP_LOSS_PCT:
            return True, f"STOP_LOSS {pct_change:.2f}%"

        # Time stop - always allowed
        hours_held = minutes_held / 60
        if hours_held >= MAX_HOLD_HOURS:
            return True, f"TIME_STOP ({hours_held:.1f}h) {pct_change:+.2f}%"

        # === ANTI-CHURN: Check minimum hold time for indicator sells ===
        if minutes_held < MIN_HOLD_MINUTES:
            return False, ""  # Too early to sell on indicators

        # === ANTI-CHURN: Check minimum profit for indicator sells ===
        if pct_change < MIN_PROFIT_TO_SELL:
            return False, ""  # Not enough profit to justify selling

        # Indicator-based exits (only if past min hold AND min profit)
        strategy = config.get("strategy", "momentum")

        if config.get("use_rsi", False) and "rsi" in row and row["rsi"] > 70:
            return True, f"RSI_OVERBOUGHT {pct_change:+.2f}%"

        if config.get("use_ema", False) and "ema_9" in row:
            # Sell on bullish cross (recovery) - EMA 9 above EMA 20
            if row["ema_9"] > row["ema_16"]:
                return True, f"EMA_RECOVERY {pct_change:+.2f}%"

        if config.get("use_macd", False) and "macd" in row:
            if strategy == "momentum" and row["macd"] < row["macd_signal"]:
                return True, f"MACD_BEARISH {pct_change:+.2f}%"

        return False, ""

    async def execute_buy(
        self, symbol: str, price: float, reason: str, paper_mode: bool = False
    ):
        """Execute buy order."""
        try:
            amount = POSITION_SIZE_USD / price

            if paper_mode:
                self.logger.info(f"[PAPER BUY] {symbol} @ ${price:.4f} | {reason}")
                self.positions[symbol] = {
                    "amount": amount,
                    "entry_price": price,
                    "entry_time": datetime.now(),
                    "order_id": "PAPER",
                }
                self.logger.info(
                    f"[PAPER BOUGHT] {amount:.4f} {symbol.split('/')[0]} @ ${price:.4f}"
                )
            else:
                self.logger.info(f"[BUY] {symbol} @ ${price:.4f} | {reason}")
                # Coinbase market buy: pass amount and price
                order = await self.exchange.create_order(
                    symbol, "market", "buy", amount, price
                )
                self.positions[symbol] = {
                    "amount": amount,
                    "entry_price": price,
                    "entry_time": datetime.now(),
                    "order_id": order.get("id"),
                }
                self.logger.info(
                    f"[BOUGHT] {amount:.4f} {symbol.split('/')[0]} @ ${price:.4f}"
                )
            return True
        except Exception as e:
            self.logger.error(f"Buy error {symbol}: {e}")
            return False

    async def execute_sell(
        self, symbol: str, price: float, reason: str, paper_mode: bool = False
    ):
        """Execute sell order."""
        if symbol not in self.positions:
            return False

        try:
            pos = self.positions[symbol]
            entry_price = pos["entry_price"]
            amount = pos["amount"]

            pct_change = ((price - entry_price) / entry_price) * 100
            profit_usd = (price - entry_price) * amount

            if paper_mode:
                self.logger.info(f"[PAPER SELL] {symbol} @ ${price:.4f} | {reason}")
                self.logger.info(
                    f"[PAPER SOLD] {symbol} | P/L: ${profit_usd:.2f} ({pct_change:+.2f}%)"
                )
            else:
                # Get ACTUAL balance (fees may have reduced tracked amount)
                coin = symbol.split("/")[0]
                balance = await self.exchange.fetch_balance()
                amount = balance.get(coin, {}).get("free", 0)

                if amount < 0.0001:
                    self.logger.warning(f"No {coin} balance to sell, clearing position")
                    del self.positions[symbol]
                    return False

                pct_change = ((price - entry_price) / entry_price) * 100
                profit_usd = (price - entry_price) * amount

                self.logger.info(f"[SELL] {symbol} @ ${price:.4f} | {reason}")
                await self.exchange.create_market_sell_order(symbol, amount)
                self.logger.info(
                    f"[SOLD] {symbol} | P/L: ${profit_usd:.2f} ({pct_change:+.2f}%)"
                )

            # Set cooldown before re-buying this coin
            self.cooldowns[symbol] = datetime.now() + timedelta(
                minutes=COOLDOWN_MINUTES
            )
            del self.positions[symbol]
            return True
        except Exception as e:
            self.logger.error(f"Sell error {symbol}: {e}")
            return False

    async def check_existing_positions(self):
        """Check for existing positions on startup."""
        try:
            balance = await self.exchange.fetch_balance()
            for symbol, config in COIN_CONFIGS.items():
                coin = symbol.split("/")[0]
                held = balance.get(coin, {}).get("free", 0)
                if held > 0:
                    ticker = await self.exchange.fetch_ticker(symbol)
                    value = held * ticker["last"]
                    if value > 5:  # More than $5
                        self.logger.info(
                            f"Found existing: {held:.4f} {coin} (${value:.2f})"
                        )
                        self.positions[symbol] = {
                            "amount": held,
                            "entry_price": ticker["last"],
                            "entry_time": datetime.now() - timedelta(hours=1),
                        }
        except Exception as e:
            self.logger.warning(f"Error checking positions: {e}")

    async def run(self, paper_mode: bool = False):
        """Main trading loop."""
        mode_str = "PAPER MODE" if paper_mode else "LIVE"
        self.logger.info("=" * 60)
        self.logger.info(f"CROSSKILLER DAY TRADER - {mode_str}")
        self.logger.info("=" * 60)
        self.logger.info(f"Coins: {list(COIN_CONFIGS.keys())}")
        self.logger.info(f"Timeframe: {TIMEFRAME}")
        self.logger.info(f"Position Size: ${POSITION_SIZE_USD}")
        self.logger.info(f"Take Profit: +{TAKE_PROFIT_PCT}%")
        self.logger.info(f"Stop Loss: -{STOP_LOSS_PCT}%")
        self.logger.info(f"Max Hold: {MAX_HOLD_HOURS}h")
        self.logger.info(
            f"Min Hold: {MIN_HOLD_MINUTES}m | Min Profit: {MIN_PROFIT_TO_SELL}% | Cooldown: {COOLDOWN_MINUTES}m"
        )
        self.logger.info("=" * 60)

        await self.start()
        if not paper_mode:
            await self.check_existing_positions()

        error_count = 0
        max_errors = 5
        cycle_count = 0

        while True:
            try:
                cycle_count += 1
                coins_checked = 0

                # Check each coin
                for symbol, config in COIN_CONFIGS.items():
                    df = await self.fetch_ohlcv(symbol)
                    if df is None or df.empty:
                        error_count += 1
                        continue

                    coins_checked += 1
                    df = self.calculate_indicators(df, config)
                    current = df.iloc[-1]
                    price = current["close"]

                    # Check sell first (if in position)
                    if symbol in self.positions:
                        should_sell, reason = self.check_sell_signal(
                            symbol, price, config, current
                        )
                        if should_sell:
                            await self.execute_sell(symbol, price, reason, paper_mode)

                    # Check buy (if not in position and under max)
                    elif len(self.positions) < MAX_POSITIONS:
                        should_buy, reason = self.check_buy_signal(
                            symbol, current, config
                        )
                        if should_buy:
                            await self.execute_buy(symbol, price, reason, paper_mode)

                    await asyncio.sleep(0.5)  # Rate limit between coins

                # Reset error count if we got data
                if coins_checked > 0:
                    error_count = 0

                # Auto-refresh exchange connection if too many errors
                if error_count >= max_errors:
                    self.logger.warning(
                        f"[REFRESH] {error_count} errors - reconnecting exchange..."
                    )
                    try:
                        await self.exchange.close()
                        await asyncio.sleep(5)
                        await self.start()
                        error_count = 0
                        self.logger.info("[REFRESH] Exchange reconnected")
                    except Exception as e:
                        self.logger.error(f"[REFRESH] Failed: {e}")

                # Status update every 5 cycles
                if cycle_count % 5 == 0:
                    if self.positions:
                        pos_str = ", ".join(
                            [f"{s.split('/')[0]}" for s in self.positions]
                        )
                        self.logger.info(
                            f"[HOLDING] {len(self.positions)}/{MAX_POSITIONS}: {pos_str}"
                        )
                    else:
                        self.logger.info(
                            f"[SCANNING] Cycle {cycle_count} - watching for entries"
                        )

                # Wait for next 5m candle (check every minute)
                await asyncio.sleep(60)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                error_count += 1
                await asyncio.sleep(30)


async def main(paper_mode: bool = False):
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = "crosskiller_paper.log" if paper_mode else "crosskiller_daytrader.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / log_file),
        ],
    )

    bot = DayTraderBot()
    try:
        await bot.run(paper_mode=paper_mode)
    except KeyboardInterrupt:
        logging.info("Shutting down...")
    finally:
        await bot.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CrossKiller Day Trader")
    parser.add_argument(
        "--paper", action="store_true", help="Run in paper trading mode"
    )
    args = parser.parse_args()
    asyncio.run(main(paper_mode=args.paper))

"""
Momentum Strategy - Optimized for VET and PEPE
==============================================

Configurable momentum strategy with RSI, Bollinger Bands, EMA indicators.
Based on backtest optimization results.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd


class MomentumStrategy:
    """
    Momentum trading strategy with configurable indicators.

    Supports:
    - RSI + Bollinger Bands (best for VET)
    - RSI + EMA crossover (best for PEPE)
    """

    def __init__(
        self,
        config_manager,
        exchange_service,
        symbol: str,
        timeframe: str = "15m",
        # Indicator config
        use_rsi: bool = True,
        use_bb: bool = False,
        use_ema: bool = False,
        # RSI params
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        # BB params
        bb_period: int = 20,
        bb_std: float = 2.0,
        # EMA params
        ema_fast: int = 9,
        ema_slow: int = 20,
        # Position sizing
        position_size_usd: float = 100.0,
        # Risk management
        take_profit_pct: float = 5.0,
        stop_loss_pct: float = 3.5,
        max_hold_hours: float = 24.0,
    ):
        self.config_manager = config_manager
        self.exchange_service = exchange_service
        self.symbol = symbol
        self.timeframe = timeframe

        # Indicators
        self.use_rsi = use_rsi
        self.use_bb = use_bb
        self.use_ema = use_ema

        # RSI
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought

        # Bollinger Bands
        self.bb_period = bb_period
        self.bb_std = bb_std

        # EMA
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow

        # Position
        self.position_size_usd = position_size_usd
        self.take_profit_pct = take_profit_pct
        self.stop_loss_pct = stop_loss_pct
        self.max_hold_hours = max_hold_hours

        # State
        self._running = False
        self._position = (
            None  # {'amount': float, 'entry_price': float, 'entry_time': datetime}
        )
        self._check_interval = self._timeframe_to_seconds(timeframe)

        self.logger = logging.getLogger(f"Momentum-{symbol.replace('/', '')}")

    def _timeframe_to_seconds(self, tf: str) -> int:
        """Convert timeframe string to seconds."""
        multipliers = {"m": 60, "h": 3600, "d": 86400}
        unit = tf[-1]
        value = int(tf[:-1])
        return value * multipliers.get(unit, 60)

    async def fetch_ohlcv(self, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from exchange."""
        try:
            df = await self.exchange_service.fetch_ohlcv_simple(
                self.symbol, self.timeframe, limit=limit
            )
            if df is None or df.empty:
                return None
            return df
        except Exception as e:
            self.logger.error(f"Error fetching OHLCV: {e}")
            return None

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all configured indicators."""
        if self.use_rsi:
            delta = df["close"].diff()
            gain = delta.where(delta > 0, 0).rolling(window=self.rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
            rs = gain / loss
            df["rsi"] = 100 - (100 / (1 + rs))

        if self.use_bb:
            df["bb_mid"] = df["close"].rolling(window=self.bb_period).mean()
            df["bb_std"] = df["close"].rolling(window=self.bb_period).std()
            df["bb_upper"] = df["bb_mid"] + (df["bb_std"] * self.bb_std)
            df["bb_lower"] = df["bb_mid"] - (df["bb_std"] * self.bb_std)

        if self.use_ema:
            df["ema_fast"] = df["close"].ewm(span=self.ema_fast, adjust=False).mean()
            df["ema_slow"] = df["close"].ewm(span=self.ema_slow, adjust=False).mean()

        return df

    def check_buy_signal(self, row: pd.Series) -> tuple[bool, str]:
        """Check if buy conditions are met. Returns (should_buy, reason)."""
        signals = []
        reasons = []

        if self.use_rsi and "rsi" in row:
            # Momentum: RSI rising from oversold
            if 30 < row["rsi"] < 50:
                signals.append(True)
                reasons.append(f"RSI={row['rsi']:.1f}")

        if self.use_bb and "bb_lower" in row:
            # Price bouncing off lower band
            if row["close"] <= row["bb_lower"] * 1.02:  # Within 2% of lower band
                signals.append(True)
                reasons.append("BB_lower")

        if self.use_ema and "ema_fast" in row:
            # Bullish crossover
            if row["ema_fast"] > row["ema_slow"]:
                signals.append(True)
                reasons.append(f"EMA({self.ema_fast}>{self.ema_slow})")

        # Need at least one signal
        if signals and any(signals):
            return True, " + ".join(reasons)

        return False, ""

    def check_sell_signal(self, row: pd.Series) -> tuple[bool, str]:
        """Check if sell conditions are met for open position."""
        if not self._position:
            return False, ""

        entry_price = self._position["entry_price"]
        entry_time = self._position["entry_time"]
        current_price = row["close"]

        pct_change = ((current_price - entry_price) / entry_price) * 100

        # Take profit
        if pct_change >= self.take_profit_pct:
            return True, f"TAKE_PROFIT +{pct_change:.2f}%"

        # Stop loss
        if pct_change <= -self.stop_loss_pct:
            return True, f"STOP_LOSS {pct_change:.2f}%"

        # Max hold time
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600
        if hours_held >= self.max_hold_hours:
            return True, f"TIME_STOP ({hours_held:.1f}h)"

        # RSI overbought
        if self.use_rsi and "rsi" in row and row["rsi"] > self.rsi_overbought:
            return True, f"RSI_OVERBOUGHT ({row['rsi']:.1f})"

        # Price at upper BB
        if self.use_bb and "bb_upper" in row and current_price >= row["bb_upper"]:
            return True, "BB_UPPER"

        # EMA bearish crossover
        if self.use_ema and "ema_fast" in row:
            if row["ema_fast"] < row["ema_slow"]:
                return True, "EMA_BEARISH"

        return False, ""

    async def execute_buy(self, price: float, reason: str):
        """Execute a buy order."""
        try:
            # Calculate amount
            amount = self.position_size_usd / price

            # Execute order
            self.logger.info(f"[BUY] {self.symbol} @ ${price:.6f} | {reason}")
            order = await self.exchange_service.place_order(
                self.symbol, "market", "buy", amount, None
            )

            if order:
                self._position = {
                    "amount": amount,
                    "entry_price": price,
                    "entry_time": datetime.now(),
                    "order_id": order.get("id"),
                }
                self.logger.info(
                    f"[BOUGHT] {amount:.4f} {self.symbol.split('/')[0]} @ ${price:.6f}"
                )
                return True

        except Exception as e:
            self.logger.error(f"Buy error: {e}")

        return False

    async def execute_sell(self, price: float, reason: str):
        """Execute a sell order."""
        if not self._position:
            return False

        try:
            amount = self._position["amount"]
            entry_price = self._position["entry_price"]
            pct_change = ((price - entry_price) / entry_price) * 100

            self.logger.info(f"[SELL] {self.symbol} @ ${price:.6f} | {reason}")
            order = await self.exchange_service.place_order(
                self.symbol, "market", "sell", amount, None
            )

            if order:
                profit_usd = (price - entry_price) * amount
                self.logger.info(
                    f"[SOLD] {amount:.4f} @ ${price:.6f} | "
                    f"P/L: ${profit_usd:.2f} ({pct_change:+.2f}%)"
                )
                self._position = None
                return True

        except Exception as e:
            self.logger.error(f"Sell error: {e}")

        return False

    async def check_existing_position(self):
        """Check if we already have a position from previous run."""
        try:
            self.logger.info("Fetching balance...")
            balance = await self.exchange_service.get_balance()
            self.logger.info(f"Balance fetched: {list(balance.keys())[:5]}...")
            base_currency = self.symbol.split("/")[0]
            held = balance.get(base_currency, {}).get("free", 0)

            if held > 0:
                # Get current price
                ticker = await self.exchange_service.fetch_ticker(self.symbol)
                if ticker:
                    price = ticker.get("last", 0)
                    value = held * price

                    if value > 1:  # More than $1 worth
                        self.logger.info(
                            f"Found existing position: {held:.4f} {base_currency} (${value:.2f})"
                        )
                        self._position = {
                            "amount": held,
                            "entry_price": price,  # Assume current price as entry
                            "entry_time": datetime.now()
                            - timedelta(hours=1),  # Assume held 1h
                        }
                        return True
        except Exception as e:
            self.logger.warning(f"Error checking position: {e}")

        return False

    async def start(self):
        """Start the momentum strategy."""
        self._running = True

        self.logger.info("=" * 50)
        self.logger.info(f"MOMENTUM STRATEGY - {self.symbol}")
        self.logger.info("=" * 50)
        self.logger.info(f"Timeframe: {self.timeframe}")
        self.logger.info(
            f"Indicators: RSI={self.use_rsi}, BB={self.use_bb}, EMA={self.use_ema}"
        )
        self.logger.info(f"Position Size: ${self.position_size_usd}")
        self.logger.info(f"Take Profit: +{self.take_profit_pct}%")
        self.logger.info(f"Stop Loss: -{self.stop_loss_pct}%")
        self.logger.info(f"Max Hold: {self.max_hold_hours}h")
        self.logger.info("=" * 50)

        # Check for existing position
        self.logger.info("Checking for existing positions...")
        await self.check_existing_position()
        self.logger.info("Starting main loop...")

        error_count = 0
        max_errors = 5

        while self._running:
            try:
                # Fetch data
                df = await self.fetch_ohlcv(limit=100)
                if df is None or df.empty:
                    error_count += 1
                    if error_count >= max_errors:
                        self.logger.warning(
                            f"[REFRESH] {error_count} errors - reconnecting exchange..."
                        )
                        try:
                            await self.exchange_service.exchange.close()
                            await asyncio.sleep(5)
                            await self.exchange_service.exchange.load_markets()
                            error_count = 0
                            self.logger.info("[REFRESH] Exchange reconnected")
                        except Exception as e:
                            self.logger.error(f"[REFRESH] Failed: {e}")
                    self.logger.warning("No data received")
                    await asyncio.sleep(60)
                    continue

                # Reset error count on success
                error_count = 0

                # Calculate indicators
                df = self.calculate_indicators(df)
                current = df.iloc[-1]
                price = current["close"]

                # Check for sell first (if in position)
                if self._position:
                    should_sell, reason = self.check_sell_signal(current)
                    if should_sell:
                        await self.execute_sell(price, reason)
                    else:
                        # Show holding status
                        entry = self._position["entry_price"]
                        pnl_pct = ((price - entry) / entry) * 100
                        hrs = (
                            datetime.now() - self._position["entry_time"]
                        ).total_seconds() / 3600
                        self.logger.info(
                            f"[HOLD] {self.symbol} | Entry:{entry:.6f} | Now:{price:.6f} | P/L:{pnl_pct:+.2f}% | {hrs:.1f}h"
                        )

                # Check for buy (if not in position)
                else:
                    should_buy, reason = self.check_buy_signal(current)
                    if should_buy:
                        await self.execute_buy(price, reason)
                    else:
                        # Verbose scanning output
                        scan_parts = [f"[SCAN] {self.symbol} @ ${price:.6f}"]
                        if self.use_rsi and "rsi" in current:
                            rsi_val = current["rsi"]
                            rsi_status = (
                                "OVERSOLD"
                                if rsi_val < 30
                                else ("OVERBOUGHT" if rsi_val > 70 else "neutral")
                            )
                            scan_parts.append(f"RSI:{rsi_val:.1f}({rsi_status})")
                        if self.use_bb and "bb_lower" in current:
                            bb_pct = (
                                (price - current["bb_lower"])
                                / (current["bb_upper"] - current["bb_lower"])
                            ) * 100
                            scan_parts.append(f"BB:{bb_pct:.0f}%")
                        if self.use_ema and "ema_fast" in current:
                            ema_diff = (
                                (current["ema_fast"] - current["ema_slow"])
                                / current["ema_slow"]
                            ) * 100
                            ema_status = (
                                "BULL"
                                if current["ema_fast"] > current["ema_slow"]
                                else "BEAR"
                            )
                            scan_parts.append(
                                f"EMA({self.ema_fast}/{self.ema_slow}):{ema_status}({ema_diff:+.2f}%)"
                            )
                        scan_parts.append("waiting...")
                        self.logger.info(" | ".join(scan_parts))

                # Wait for next candle
                await asyncio.sleep(self._check_interval)

            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)

    def stop(self):
        """Stop the strategy."""
        self._running = False

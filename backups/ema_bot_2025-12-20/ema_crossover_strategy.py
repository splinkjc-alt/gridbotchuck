"""
EMA Crossover Strategy

This strategy:
1. Scans market for top performing coins by 24h volume/momentum
2. Monitors EMA 9 and EMA 20 crossovers
3. Buys when EMA 9 crosses ABOVE EMA 20 (bullish crossover)
4. Sells when EMA 9 crosses BELOW EMA 20 (bearish crossover)
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd

from config.config_manager import ConfigManager
from core.services.exchange_interface import ExchangeInterface


class CrossoverSignal(Enum):
    BUY = "BUY"           # EMA 9 crossed above EMA 20
    SELL = "SELL"         # EMA 9 crossed below EMA 20
    HOLD_LONG = "HOLD_LONG"   # Already in uptrend, stay long
    HOLD_SHORT = "HOLD_SHORT"  # In downtrend, stay out
    NO_SIGNAL = "NO_SIGNAL"


@dataclass
class CoinStatus:
    """Tracks the status of a coin being monitored."""
    pair: str
    last_signal: CrossoverSignal
    position_held: bool = False
    entry_price: float = 0.0
    entry_time: Optional[datetime] = None
    quantity: float = 0.0
    ema_9: float = 0.0
    ema_20: float = 0.0
    current_price: float = 0.0
    score: float = 0.0  # Ranking score


class EMACrossoverStrategy:
    """
    EMA 9/20 Crossover Trading Strategy
    
    - Scans top 10 coins by momentum/volume
    - Buys on bullish EMA crossover (9 crosses above 20)
    - Sells on bearish EMA crossover (9 crosses below 20)
    """
    
    def __init__(
        self,
        config_manager: ConfigManager,
        exchange_service: ExchangeInterface,
        ema_fast: int = 9,
        ema_slow: int = 20,
        max_positions: int = 3,
        position_size_percent: float = 20.0,
        min_reserve_percent: float = 10.0,
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = config_manager
        self.exchange_service = exchange_service
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.max_positions = max_positions
        self.position_size_percent = position_size_percent
        self.min_reserve_percent = min_reserve_percent
        
        # Track monitored coins and positions
        self.monitored_coins: dict[str, CoinStatus] = {}
        self.active_positions: dict[str, CoinStatus] = {}
        
        self._running = False
        self._scan_interval = 300  # 5 minutes
        self._check_interval = 60   # 1 minute for crossover checks
        
    async def start(self):
        """Start the strategy."""
        self._running = True
        self.logger.info(f"Starting EMA {self.ema_fast}/{self.ema_slow} Crossover Strategy")
        self.logger.info(f"Max positions: {self.max_positions}, Position size: {self.position_size_percent}%")
        
        # Initial market scan
        await self.scan_market()
        
        # Main loop
        while self._running:
            try:
                await self.check_all_signals()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(10)
                
    def stop(self):
        """Stop the strategy."""
        self._running = False
        self.logger.info("EMA Crossover Strategy stopped")
        
    async def scan_market(self) -> list[tuple[str, float]]:
        """
        Scan market for top performing coins.
        Returns list of (pair, score) sorted by score.
        """
        self.logger.info("Scanning market for top coins...")
        
        # Get candidate pairs from config
        scanner_config = self.config_manager.get_market_scanner_config()
        candidate_pairs = scanner_config.get("candidate_pairs", [])
        quote_currency = scanner_config.get("quote_currency", "USD")
        min_price = scanner_config.get("min_price", 1.0)
        max_price = scanner_config.get("max_price", 100.0)
        
        scored_pairs = []
        
        for pair in candidate_pairs:
            try:
                score = await self._score_pair(pair)
                if score is not None and score > 0:
                    scored_pairs.append((pair, score))
                    self.logger.debug(f"{pair}: Score = {score:.2f}")
            except Exception as e:
                self.logger.warning(f"Failed to score {pair}: {e}")
                
        # Sort by score, take top 10
        scored_pairs.sort(key=lambda x: x[1], reverse=True)
        top_10 = scored_pairs[:10]
        
        self.logger.info(f"Top 10 coins by momentum:")
        for i, (pair, score) in enumerate(top_10, 1):
            self.logger.info(f"  {i}. {pair}: {score:.2f}")
            
            # Add to monitored if not already
            if pair not in self.monitored_coins:
                self.monitored_coins[pair] = CoinStatus(
                    pair=pair,
                    last_signal=CrossoverSignal.NO_SIGNAL,
                    score=score,
                )
                
        return top_10
        
    async def _score_pair(self, pair: str) -> Optional[float]:
        """
        Score a pair based on momentum and volume.
        Higher score = better momentum.
        """
        try:
            # Fetch OHLCV data
            data = await self._fetch_ohlcv(pair, "15m", limit=100)
            if data is None or len(data) < self.ema_slow + 5:
                return None
                
            # Get current price
            ticker = await self._fetch_ticker(pair)
            if ticker is None:
                return None
                
            price = ticker.get("last", 0)
            change_24h = ticker.get("percentage", 0) or 0
            volume_24h = ticker.get("quoteVolume", 0) or 0
            
            # Calculate EMAs
            ema_9 = self._calculate_ema(data["close"], self.ema_fast)
            ema_20 = self._calculate_ema(data["close"], self.ema_slow)
            
            if ema_9 is None or ema_20 is None:
                return None
                
            # Score components:
            # 1. Positive momentum (EMA 9 > EMA 20) = +40
            # 2. Recent crossover bonus = +30
            # 3. 24h change positive = +20
            # 4. Volume score = +10
            
            score = 0
            
            # Momentum: EMA relationship
            ema_9_val = ema_9.iloc[-1]
            ema_20_val = ema_20.iloc[-1]
            
            if ema_9_val > ema_20_val:
                # Bullish - EMA 9 above 20
                spread = ((ema_9_val - ema_20_val) / ema_20_val) * 100
                score += min(40, 20 + spread * 10)
            else:
                # Bearish - but might be about to cross
                spread = ((ema_20_val - ema_9_val) / ema_20_val) * 100
                if spread < 0.5:  # Very close to crossover
                    score += 15
                else:
                    score += max(0, 10 - spread * 5)
                    
            # Recent crossover bonus
            if len(ema_9) >= 3:
                prev_9 = ema_9.iloc[-2]
                prev_20 = ema_20.iloc[-2]
                if prev_9 <= prev_20 and ema_9_val > ema_20_val:
                    # Just crossed bullish!
                    score += 30
                    
            # 24h change
            if change_24h > 0:
                score += min(20, change_24h * 2)
            elif change_24h > -5:
                score += 5
                
            # Volume (normalized, max 10 points)
            if volume_24h > 1000000:  # $1M+ volume
                score += 10
            elif volume_24h > 100000:
                score += 5
                
            return score
            
        except Exception as e:
            self.logger.debug(f"Error scoring {pair}: {e}")
            return None
            
    async def check_all_signals(self):
        """Check EMA crossover signals for all monitored coins."""
        for pair, status in list(self.monitored_coins.items()):
            try:
                signal = await self.check_crossover_signal(pair)
                
                if signal == CrossoverSignal.BUY and not status.position_held:
                    await self.execute_buy(pair)
                elif signal == CrossoverSignal.SELL and status.position_held:
                    await self.execute_sell(pair)
                    
            except Exception as e:
                self.logger.error(f"Error checking signal for {pair}: {e}")
                
    async def check_crossover_signal(self, pair: str) -> CrossoverSignal:
        """
        Check EMA 9/20 crossover for a pair.
        
        Smart logic:
        - BUY on crossover (EMA 9 crosses above EMA 20)
        - BUY if gap is WIDENING (momentum growing, safe entry)
        - SELL when gap narrows significantly or crossover occurs
        
        Returns:
            CrossoverSignal indicating the signal type
        """
        try:
            data = await self._fetch_ohlcv(pair, "15m", limit=50)
            if data is None or len(data) < self.ema_slow + 5:
                return CrossoverSignal.NO_SIGNAL
                
            ema_9 = self._calculate_ema(data["close"], self.ema_fast)
            ema_20 = self._calculate_ema(data["close"], self.ema_slow)
            
            if ema_9 is None or ema_20 is None:
                return CrossoverSignal.NO_SIGNAL
                
            # Current and previous values
            current_9 = ema_9.iloc[-1]
            current_20 = ema_20.iloc[-1]
            prev_9 = ema_9.iloc[-2]
            prev_20 = ema_20.iloc[-2]
            prev2_9 = ema_9.iloc[-3]
            prev2_20 = ema_20.iloc[-3]
            
            # Calculate spread (gap between EMAs)
            current_spread = ((current_9 - current_20) / current_20) * 100
            prev_spread = ((prev_9 - prev_20) / prev_20) * 100
            prev2_spread = ((prev2_9 - prev2_20) / prev2_20) * 100
            
            # Is gap widening or narrowing?
            spread_change = current_spread - prev_spread
            spread_trend = current_spread - prev2_spread
            
            # Update status
            if pair in self.monitored_coins:
                self.monitored_coins[pair].ema_9 = current_9
                self.monitored_coins[pair].ema_20 = current_20
                self.monitored_coins[pair].current_price = data["close"].iloc[-1]
                
            # Check for crossover
            if prev_9 <= prev_20 and current_9 > current_20:
                # Bullish crossover - EMA 9 crossed ABOVE EMA 20
                self.logger.info(f"🟢 {pair}: BULLISH CROSSOVER - EMA 9 ({current_9:.4f}) crossed above EMA 20 ({current_20:.4f})")
                return CrossoverSignal.BUY
                
            elif prev_9 >= prev_20 and current_9 < current_20:
                # Bearish crossover - EMA 9 crossed BELOW EMA 20
                self.logger.info(f"🔴 {pair}: BEARISH CROSSOVER - EMA 9 ({current_9:.4f}) crossed below EMA 20 ({current_20:.4f})")
                return CrossoverSignal.SELL
                
            elif current_9 > current_20:
                # Already in uptrend - check if gap is widening (safe to buy)
                if spread_change > 0 and spread_trend > 0:
                    # Gap is widening - momentum growing, safe to enter
                    self.logger.info(f"✅ {pair}: GAP WIDENING - Safe to buy (spread +{spread_change:.3f}%)")
                    return CrossoverSignal.BUY
                elif current_spread < 0.1 or spread_change < -0.05:
                    # Gap very small or narrowing fast - prepare to sell
                    self.logger.info(f"⚠️ {pair}: Gap narrowing ({spread_change:.3f}%) - momentum fading")
                    return CrossoverSignal.HOLD_LONG
                else:
                    return CrossoverSignal.HOLD_LONG
                
            else:
                # In downtrend
                return CrossoverSignal.HOLD_SHORT
                
        except Exception as e:
            self.logger.error(f"Error checking crossover for {pair}: {e}")
            return CrossoverSignal.NO_SIGNAL
            
    async def execute_buy(self, pair: str):
        """Execute a buy order when bullish crossover detected."""
        if len(self.active_positions) >= self.max_positions:
            self.logger.warning(f"Max positions ({self.max_positions}) reached, skipping buy for {pair}")
            return
            
        try:
            # Get current balance
            balance = await self._get_balance()
            usd_balance = balance.get("USD", 0)
            
            # Calculate position size
            total_value = usd_balance  # Simplified - just use USD balance
            reserve = total_value * (self.min_reserve_percent / 100)
            available = total_value - reserve
            
            if available <= 0:
                self.logger.warning(f"Insufficient funds for {pair}")
                return
                
            position_value = available * (self.position_size_percent / 100)
            
            # Get current price
            ticker = await self._fetch_ticker(pair)
            price = ticker.get("last", 0)
            if price <= 0:
                return
                
            quantity = position_value / price
            
            self.logger.info(f"💰 BUYING {quantity:.4f} {pair} @ ${price:.4f} (${position_value:.2f})")
            
            # Execute order
            order = await self.exchange_service.place_order(
                symbol=pair,
                side="buy",
                order_type="market",
                amount=quantity,
            )
            
            if order:
                # Update tracking
                status = self.monitored_coins.get(pair, CoinStatus(pair=pair, last_signal=CrossoverSignal.BUY))
                status.position_held = True
                status.entry_price = price
                status.entry_time = datetime.now()
                status.quantity = quantity
                status.last_signal = CrossoverSignal.BUY
                
                self.monitored_coins[pair] = status
                self.active_positions[pair] = status
                
                self.logger.info(f"✅ BUY ORDER FILLED: {pair}")
            else:
                self.logger.error(f"❌ BUY ORDER FAILED: {pair}")
                
        except Exception as e:
            self.logger.error(f"Error executing buy for {pair}: {e}")
            
    async def execute_sell(self, pair: str):
        """Execute a sell order when bearish crossover detected."""
        try:
            status = self.active_positions.get(pair)
            if not status or not status.position_held:
                return
                
            # Get current price
            ticker = await self._fetch_ticker(pair)
            price = ticker.get("last", 0)
            if price <= 0:
                return
                
            quantity = status.quantity
            pnl = (price - status.entry_price) * quantity
            pnl_pct = ((price / status.entry_price) - 1) * 100
            
            self.logger.info(f"💸 SELLING {quantity:.4f} {pair} @ ${price:.4f} (P&L: ${pnl:.2f} / {pnl_pct:+.2f}%)")
            
            # Execute order
            order = await self.exchange_service.place_order(
                symbol=pair,
                side="sell",
                order_type="market",
                amount=quantity,
            )
            
            if order:
                # Update tracking
                status.position_held = False
                status.last_signal = CrossoverSignal.SELL
                status.quantity = 0
                
                if pair in self.active_positions:
                    del self.active_positions[pair]
                    
                self.logger.info(f"✅ SELL ORDER FILLED: {pair} (P&L: ${pnl:.2f})")
            else:
                self.logger.error(f"❌ SELL ORDER FAILED: {pair}")
                
        except Exception as e:
            self.logger.error(f"Error executing sell for {pair}: {e}")
            
    def _calculate_ema(self, prices: pd.Series, period: int) -> Optional[pd.Series]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None
        return prices.ewm(span=period, adjust=False).mean()
        
    async def _fetch_ohlcv(self, pair: str, timeframe: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data."""
        try:
            if hasattr(self.exchange_service, "fetch_ohlcv_simple"):
                return await self.exchange_service.fetch_ohlcv_simple(pair, timeframe, limit)
            elif hasattr(self.exchange_service, "fetch_ohlcv"):
                return self.exchange_service.fetch_ohlcv(pair, timeframe, limit=limit)
            return None
        except Exception as e:
            self.logger.debug(f"Error fetching OHLCV for {pair}: {e}")
            return None
            
    async def _fetch_ticker(self, pair: str) -> dict:
        """Fetch ticker data."""
        try:
            if hasattr(self.exchange_service, "fetch_ticker"):
                return await self.exchange_service.fetch_ticker(pair)
            return {}
        except Exception:
            return {}
            
    async def _get_balance(self) -> dict:
        """Get current balance."""
        try:
            if hasattr(self.exchange_service, "fetch_balance"):
                balance = await self.exchange_service.fetch_balance()
                return balance.get("total", {})
            return {}
        except Exception:
            return {}
            
    def get_status(self) -> dict:
        """Get current strategy status."""
        return {
            "running": self._running,
            "ema_fast": self.ema_fast,
            "ema_slow": self.ema_slow,
            "max_positions": self.max_positions,
            "active_positions": len(self.active_positions),
            "monitored_coins": len(self.monitored_coins),
            "positions": [
                {
                    "pair": p.pair,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "quantity": p.quantity,
                    "ema_9": p.ema_9,
                    "ema_20": p.ema_20,
                    "pnl_pct": ((p.current_price / p.entry_price) - 1) * 100 if p.entry_price > 0 else 0,
                }
                for p in self.active_positions.values()
            ],
        }

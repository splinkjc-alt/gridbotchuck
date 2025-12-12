"""
Activity Monitor - Monitors trading pair activity and triggers switch when stale.
"""

import asyncio
from datetime import UTC, datetime
import logging
from typing import TYPE_CHECKING

from core.bot_management.event_bus import Events

if TYPE_CHECKING:
    from core.services.exchange_interface import ExchangeInterface
    from strategies.market_analyzer import MarketAnalyzer


class ActivityMonitor:
    """
    Monitors the current trading pair for activity.
    If volume/volatility drops below thresholds, triggers a rescan and switch.
    """

    def __init__(
        self,
        exchange_service: "ExchangeInterface",
        market_analyzer: "MarketAnalyzer",
        event_bus,
        config: dict,
    ):
        self.exchange_service = exchange_service
        self.market_analyzer = market_analyzer
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)

        # Configuration
        self.enabled = config.get("enabled", True)
        self.check_interval_minutes = config.get("check_interval_minutes", 15)
        self.min_volume_usd = config.get("min_volume_24h_usd", 10000)  # Minimum 24h volume
        self.min_price_change_pct = config.get("min_price_change_pct", 0.5)  # Minimum % movement
        self.stale_periods_before_switch = config.get("stale_periods_before_switch", 3)
        self.cooldown_minutes = config.get("cooldown_after_switch_minutes", 60)

        # State
        self.current_pair = None
        self.stale_count = 0
        self.last_switch_time = None
        self.running = False
        self._task = None
        self.price_history = []  # Track recent prices

    async def start(self, trading_pair: str):
        """Start monitoring the given trading pair."""
        if not self.enabled:
            self.logger.info("Activity monitor is disabled")
            return

        self.current_pair = trading_pair
        self.running = True
        self.stale_count = 0
        self.price_history = []

        self.logger.info(
            f"Activity monitor started for {trading_pair} "
            f"(check every {self.check_interval_minutes}min, "
            f"switch after {self.stale_periods_before_switch} stale periods)"
        )

        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """Stop monitoring."""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Activity monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        # Log initial status
        await self._log_status_update()

        while self.running:
            try:
                await asyncio.sleep(self.check_interval_minutes * 60)

                if not self.running:
                    break

                # Check if we're in cooldown after a switch
                if self._in_cooldown():
                    self.logger.info(f"[STATUS] Trading {self.current_pair} (in cooldown after switch)")
                    continue

                # Check activity
                is_active = await self._check_activity()

                if is_active:
                    self.stale_count = 0
                    self.logger.info(f"[STATUS] {self.current_pair} is ACTIVE - Continuing to trade")
                else:
                    self.stale_count += 1
                    self.logger.warning(
                        f"[STATUS] {self.current_pair} is STALE ({self.stale_count}/{self.stale_periods_before_switch} before switch)"
                    )

                    if self.stale_count >= self.stale_periods_before_switch:
                        await self._trigger_switch()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in activity monitor: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _check_activity(self) -> bool:
        """
        Check if the current pair has sufficient activity.
        Returns True if active, False if stale.
        """
        try:
            # Get current ticker
            ticker = await self.exchange_service.get_ticker(self.current_pair)

            if not ticker:
                self.logger.warning(f"Could not fetch ticker for {self.current_pair}")
                return True  # Assume active if we can't check

            # Check 24h volume
            volume_usd = ticker.get("quoteVolume", 0) or 0
            if volume_usd < self.min_volume_usd:
                self.logger.info(f"Low volume: ${volume_usd:,.0f} < ${self.min_volume_usd:,.0f}")
                return False

            # Check price movement
            current_price = ticker.get("last") or ticker.get("close")
            if current_price:
                self.price_history.append(current_price)
                # Keep last 6 readings (about 1.5 hours at 15min intervals)
                self.price_history = self.price_history[-6:]

                if len(self.price_history) >= 3:
                    min_price = min(self.price_history)
                    max_price = max(self.price_history)
                    if min_price > 0:
                        price_range_pct = ((max_price - min_price) / min_price) * 100
                        if price_range_pct < self.min_price_change_pct:
                            self.logger.info(f"Low volatility: {price_range_pct:.2f}% < {self.min_price_change_pct}%")
                            return False

            # Check 24h change percentage
            change_pct = abs(ticker.get("percentage", 0) or 0)
            if change_pct < self.min_price_change_pct:
                self.logger.info(f"Low 24h change: {change_pct:.2f}% < {self.min_price_change_pct}%")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking activity: {e}")
            return True  # Assume active on error

    async def _trigger_switch(self):
        """Find a better pair and trigger a switch."""
        self.logger.info("🔄 Triggering pair switch due to low activity...")
        self.logger.info("🔍 SCANNING: Looking for better trading pairs...")

        try:
            # Run a market scan to find better options
            results = await self.market_analyzer.find_best_trading_pairs(
                exchange_service=self.exchange_service,
                quote_currency="USD",
                min_price=1.0,
                max_price=20.0,
                timeframe="15m",
                top_n=5,
            )

            if not results:
                self.logger.warning("[SCAN] No alternative pairs found")
                self.stale_count = 0  # Reset to avoid spam
                return

            # Log all candidates found
            self.logger.info(f"[SCAN] Found {len(results)} candidates:")
            for i, r in enumerate(results, 1):
                current_marker = " (current)" if r.pair == self.current_pair else ""
                self.logger.info(
                    f"   {i}. {r.pair}: score={r.score:.1f}, signal={r.signal}, "
                    f"price=${r.current_price:.4f}, 24h={r.change_24h:+.1f}%{current_marker}"
                )

            # Find the best alternative (not current pair)
            for result in results:
                if result.pair != self.current_pair:
                    new_pair = result.pair
                    self.logger.info(
                        f"[SWITCH] SWITCHING TO: {new_pair} (score: {result.score:.1f}, signal: {result.signal})"
                    )

                    # Publish switch event
                    self.event_bus.publish(
                        Events.SWITCH_PAIR,
                        {
                            "old_pair": self.current_pair,
                            "new_pair": new_pair,
                            "reason": "low_activity",
                            "score": result.score,
                            "timestamp": datetime.now(UTC).isoformat(),
                        },
                    )

                    # Update state
                    self.current_pair = new_pair
                    self.stale_count = 0
                    self.last_switch_time = datetime.now(UTC)
                    self.price_history = []

                    return

            self.logger.info("Current pair is still the best option")
            self.stale_count = 0

        except Exception as e:
            self.logger.error(f"Error triggering switch: {e}")
            self.stale_count = 0

    def _in_cooldown(self) -> bool:
        """Check if we're in cooldown period after a switch."""
        if not self.last_switch_time:
            return False

        elapsed = (datetime.now(UTC) - self.last_switch_time).total_seconds()
        return elapsed < (self.cooldown_minutes * 60)

    async def _log_status_update(self):
        """Log current trading status with pair info."""
        try:
            ticker = await self.exchange_service.exchange.fetch_ticker(self.current_pair)
            if ticker:
                price = ticker.get("last") or ticker.get("close", 0)
                volume = ticker.get("quoteVolume", 0) or 0
                change = ticker.get("percentage", 0) or 0
                self.logger.info(
                    f"[STATUS] TRADING: {self.current_pair} @ ${price:.4f} | "
                    f"24h Vol: ${volume:,.0f} | 24h Change: {change:+.2f}%"
                )
            else:
                self.logger.info(f"[STATUS] TRADING: {self.current_pair} (waiting for ticker data)")
        except Exception:
            self.logger.info(f"[STATUS] TRADING: {self.current_pair}")

    def update_pair(self, new_pair: str):
        """Update the monitored pair (called when pair is changed externally)."""
        self.current_pair = new_pair
        self.stale_count = 0
        self.price_history = []
        self.logger.info(f"[STATUS] NOW MONITORING: {new_pair}")

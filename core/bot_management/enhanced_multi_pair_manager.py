"""
Enhanced Multi-Pair Manager with Auto-Switching.
Automatically detects stuck markets and switches to better performing pairs.
"""

import asyncio
import contextlib
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from core.bot_management.multi_pair_manager import MultiPairManager, PairStatus
from strategies.pair_performance_monitor import PairPerformanceMonitor

if TYPE_CHECKING:
    from config.config_manager import ConfigManager
    from core.bot_management.event_bus import EventBus
    from core.services.exchange_interface import ExchangeInterface
    from strategies.market_analyzer import MarketAnalyzer


@dataclass
class EnhancedPairStatus(PairStatus):
    """Extended pair status with performance tracking."""

    performance_score: float = 0.0
    volatility: float = 0.0
    last_performance_check: datetime = None
    replacement_candidate: str | None = None
    trades_last_hour: int = 0
    consecutive_stuck_checks: int = 0


class EnhancedMultiPairManager(MultiPairManager):
    """
    Enhanced multi-pair manager with automatic pair switching.

    Features:
    - Detects stuck/low-volatility markets
    - Automatically switches to better performing pairs
    - Monitors performance continuously
    - Protects against frequent switching (cooldown periods)
    """

    def __init__(
        self,
        config_manager: "ConfigManager",
        exchange_service: "ExchangeInterface",
        event_bus: "EventBus",
        market_analyzer: "MarketAnalyzer",
    ):
        super().__init__(config_manager, exchange_service, event_bus, market_analyzer)

        # Performance monitoring
        self.performance_monitor = PairPerformanceMonitor(
            exchange_service, check_interval=300
        )

        # Auto-switching configuration
        auto_switch_config = config_manager.config.get("multi_pair", {}).get(
            "auto_switch", {}
        )
        self.auto_switch_enabled = auto_switch_config.get("enabled", True)
        self.check_interval = (
            auto_switch_config.get("check_interval_minutes", 15) * 60
        )  # Convert to seconds
        self.min_stuck_checks = auto_switch_config.get(
            "min_stuck_checks_before_switch", 2
        )  # Confirm stuck before switching
        self.switch_cooldown = (
            auto_switch_config.get("switch_cooldown_minutes", 30) * 60
        )  # Prevent rapid switching

        # Candidate pairs for replacement
        self.candidate_pairs = auto_switch_config.get(
            "candidate_pairs",
            [
                "XLM/USD",
                "XRP/USD",
                "DOGE/USD",
                "MATIC/USD",
                "ADA/USD",
                "ALGO/USD",
                "DOT/USD",
                "LINK/USD",
                "UNI/USD",
                "ATOM/USD",
            ],
        )

        # Tracking
        self.last_switch_time: dict[str, datetime] = {}
        self.performance_check_task = None

    async def start(self):
        """Start multi-pair trading with auto-switching."""
        # Start the base multi-pair manager
        await super().start()

        # Start performance monitoring task
        if self.auto_switch_enabled:
            self.performance_check_task = asyncio.create_task(
                self._performance_monitoring_loop()
            )
            self.logger.info(
                f"🔍 Auto-switching enabled: checking every {self.check_interval/60:.0f} minutes, "
                f"cooldown {self.switch_cooldown/60:.0f} minutes"
            )

    async def stop(self):
        """Stop trading and monitoring."""
        if self.performance_check_task:
            self.performance_check_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self.performance_check_task

        await super().stop()

    async def _performance_monitoring_loop(self):
        """Continuously monitor pair performance and switch if needed."""
        self.logger.info("Starting performance monitoring loop...")

        while self.running:
            try:
                await asyncio.sleep(self.check_interval)

                if not self.running:
                    break

                self.logger.info("🔍 Running scheduled performance check...")

                # Check each active pair
                for pair in list(self.active_pairs.keys()):
                    await self._check_and_switch_if_needed(pair)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Error in performance monitoring loop: {e}", exc_info=True
                )
                await asyncio.sleep(60)  # Brief pause before retrying

    async def _check_and_switch_if_needed(self, pair: str):
        """
        Check if a pair should be replaced and switch if necessary.

        Args:
            pair: Trading pair to check
        """
        try:
            status = self.active_pairs.get(pair)

            if not status or status.status != "running":
                return

            # Check if we're in cooldown period
            last_switch = self.last_switch_time.get(pair)
            if last_switch:
                time_since_switch = datetime.now() - last_switch
                if time_since_switch.total_seconds() < self.switch_cooldown:
                    remaining = self.switch_cooldown - time_since_switch.total_seconds()
                    self.logger.debug(
                        f"Skipping {pair} - in cooldown period ({remaining/60:.0f}min remaining)"
                    )
                    return

            # Get trade statistics
            trades_last_hour = 0
            last_trade_time = None

            if pair in self.pair_strategies:
                strategy = self.pair_strategies[pair]
                if hasattr(strategy, "order_manager"):
                    # Count recent filled orders
                    # This is a simplified approach - you'd want to track this properly
                    trades_last_hour = getattr(status, "trades_last_hour", 0)
                    last_trade_time = getattr(status, "last_trade_time", None)

            # Check if pair should be replaced
            should_replace = await self.performance_monitor.should_replace_pair(
                pair, last_trade_time, trades_last_hour
            )

            if not should_replace:
                self.logger.debug(f"✅ {pair} performing well, keeping it")
                if hasattr(status, "consecutive_stuck_checks"):
                    status.consecutive_stuck_checks = 0
                return

            # Increment stuck counter
            if not hasattr(status, "consecutive_stuck_checks"):
                status.consecutive_stuck_checks = 0
            status.consecutive_stuck_checks += 1

            # Only switch after multiple confirmations
            if status.consecutive_stuck_checks < self.min_stuck_checks:
                self.logger.warning(
                    f"⚠️ {pair} appears stuck (check {status.consecutive_stuck_checks}/{self.min_stuck_checks})"
                )
                return

            # Find a better replacement
            self.logger.warning(f"🔴 {pair} is STUCK. Searching for replacement...")

            better_pair = await self.performance_monitor.find_better_pair(
                pair, self.candidate_pairs
            )

            if not better_pair:
                self.logger.info(
                    f"No better alternative found for {pair}. Keeping it for now."
                )
                return

            # Don't switch to a pair we're already trading
            if better_pair in self.active_pairs:
                self.logger.info(f"{better_pair} already in active pairs. Skipping.")
                return

            # Perform the switch
            await self._switch_pair(pair, better_pair, reason="stuck_market")

        except Exception as e:
            self.logger.error(f"Error checking pair {pair}: {e}", exc_info=True)

    async def _switch_pair(self, old_pair: str, new_pair: str, reason: str = "manual"):
        """
        Switch from old pair to new pair.

        Args:
            old_pair: Pair to stop trading
            new_pair: Pair to start trading
            reason: Reason for switch (for logging)
        """
        self.logger.info(
            f"🔄 SWITCHING PAIR: {old_pair} → {new_pair} (reason: {reason})"
        )

        try:
            # Use the base class replace_pair method
            success = await self.replace_pair(old_pair, new_pair)

            if success:
                # Record switch time
                self.last_switch_time[new_pair] = datetime.now()

                # Publish event
                await self.event_bus.publish(
                    "PAIR_SWITCHED",
                    {
                        "old_pair": old_pair,
                        "new_pair": new_pair,
                        "reason": reason,
                        "timestamp": datetime.now().isoformat(),
                    },
                )

                self.logger.info(f"✅ Successfully switched to {new_pair}")
            else:
                self.logger.error(f"❌ Failed to switch to {new_pair}")

        except Exception as e:
            self.logger.error(
                f"Error switching from {old_pair} to {new_pair}: {e}", exc_info=True
            )

    async def manually_switch_pair(self, old_pair: str, new_pair: str):
        """
        Manually trigger a pair switch (for user control).

        Args:
            old_pair: Pair to stop
            new_pair: Pair to start
        """
        await self._switch_pair(old_pair, new_pair, reason="manual_override")

    def get_status(self) -> dict:
        """Get enhanced status with performance metrics."""
        base_status = super().get_status()

        # Add performance metrics
        if self.auto_switch_enabled:
            base_status["auto_switch"] = {
                "enabled": True,
                "check_interval_minutes": self.check_interval / 60,
                "switch_cooldown_minutes": self.switch_cooldown / 60,
                "candidate_pairs": len(self.candidate_pairs),
            }

            # Add performance data for each pair
            for pair, pair_status in base_status.get("pairs", {}).items():
                perf_status = self.performance_monitor.get_pair_status(pair)
                pair_status["performance"] = perf_status

                # Add switch history
                last_switch = self.last_switch_time.get(pair)
                if last_switch:
                    time_since_switch = datetime.now() - last_switch
                    pair_status["time_since_switch_minutes"] = (
                        time_since_switch.total_seconds() / 60
                    )

        return base_status

    def get_performance_report(self) -> dict:
        """Get detailed performance report for all monitored pairs."""
        top_performers = self.performance_monitor.get_top_performers(n=10)

        return {
            "timestamp": datetime.now().isoformat(),
            "active_pairs": list(self.active_pairs.keys()),
            "top_performers": [
                {
                    "pair": p.pair,
                    "score": p.performance_score,
                    "volatility_15m": p.volatility_15m,
                    "volatility_1h": p.volatility_1h,
                    "is_stuck": p.is_stuck,
                }
                for p in top_performers
            ],
            "switches_history": [
                {"pair": pair, "last_switch": time.isoformat()}
                for pair, time in self.last_switch_time.items()
            ],
        }

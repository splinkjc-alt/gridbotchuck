"""
Profit Rotation Manager - Captures profits and rotates to top-performing pairs.

Key Features:
- Monitors position P&L in real-time
- Closes all positions when profit target is reached
- Scans market for top N opportunities
- Automatically enters best new position
- Prevents rapid re-entry of same pair
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from config.config_manager import ConfigManager
    from core.bot_management.event_bus import EventBus
    from core.services.exchange_interface import ExchangeInterface
    from strategies.market_analyzer import MarketAnalyzer


@dataclass
class PositionSnapshot:
    """Snapshot of current position state."""

    pair: str
    entry_value: float  # Total USD invested
    current_value: float  # Current position worth
    unrealized_pnl: float
    unrealized_pnl_percent: float
    crypto_balance: float
    quote_balance: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RotationEvent:
    """Record of a rotation event."""

    timestamp: datetime
    from_pair: str
    to_pair: str
    profit_realized: float
    profit_percent: float
    exit_reason: str  # "profit_target", "manual", "stop_loss"
    new_pair_score: float


class ProfitRotationManager:
    """
    Manages profit-taking and automatic rotation to better trading opportunities.

    Workflow:
    1. Monitor active position P&L every check_interval
    2. When profit target hit → close all orders and exit position
    3. Query market scanner for top N candidates
    4. Filter out recently exited pairs (cooldown)
    5. Enter best opportunity with fresh grid
    6. Log rotation event to database
    """

    def __init__(
        self,
        config_manager: "ConfigManager",
        exchange_service: "ExchangeInterface",
        event_bus: "EventBus",
        market_analyzer: "MarketAnalyzer",
    ):
        self.config_manager = config_manager
        self.exchange_service = exchange_service
        self.event_bus = event_bus
        self.market_analyzer = market_analyzer
        self.logger = logging.getLogger(self.__class__.__name__)

        # Load configuration
        rotation_config = config_manager.config.get("profit_rotation", {})
        self.enabled = rotation_config.get("enabled", True)
        self.profit_target_percent = rotation_config.get("profit_target_percent", 5.0)
        self.profit_target_usd = rotation_config.get("profit_target_usd", 3.0)
        self.use_percent_target = rotation_config.get("use_percent_target", True)
        self.check_interval_seconds = rotation_config.get("check_interval_seconds", 60)
        self.top_pairs_to_scan = rotation_config.get("top_pairs_to_scan", 4)
        self.min_score_to_enter = rotation_config.get("min_score_to_enter", 65)
        self.cooldown_minutes = rotation_config.get("cooldown_minutes", 30)
        self.auto_enter_next = rotation_config.get("auto_enter_next", True)
        self.max_rotations_per_day = rotation_config.get("max_rotations_per_day", 10)

        # Scanner config
        scanner_config = config_manager.config.get("market_scanner", {})
        self.candidate_pairs = scanner_config.get("candidate_pairs", [])
        self.min_price = scanner_config.get("min_price", 1.0)
        self.max_price = scanner_config.get("max_price", 20.0)
        self.timeframe = scanner_config.get("timeframe", "15m")

        # State
        self.current_position: PositionSnapshot | None = None
        self.rotation_history: list[RotationEvent] = []
        self.recently_exited_pairs: dict[str, datetime] = {}  # pair -> exit_time
        self.running = False
        self.monitoring_task: asyncio.Task | None = None
        self.rotation_count_today = 0
        self.last_rotation_reset = datetime.now().date()

    async def start(self, initial_pair: str, entry_value: float):
        """
        Start profit rotation monitoring for a position.

        Args:
            initial_pair: Trading pair (e.g., "MYX/USD")
            entry_value: Initial USD value invested
        """
        if not self.enabled:
            self.logger.info("Profit rotation is disabled in config")
            return

        self.logger.info(
            f"Starting profit rotation manager for {initial_pair} "
            f"(entry: ${entry_value:.2f}, target: {self.profit_target_percent}%)"
        )

        # Initialize position snapshot
        self.current_position = PositionSnapshot(
            pair=initial_pair,
            entry_value=entry_value,
            current_value=entry_value,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            crypto_balance=0.0,
            quote_balance=entry_value,
        )

        self.running = True
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop(self):
        """Stop profit rotation monitoring."""
        self.running = False
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Profit rotation manager stopped")

    async def _monitoring_loop(self):
        """Main monitoring loop - checks P&L and triggers rotations."""
        while self.running:
            try:
                # Reset daily rotation counter
                today = datetime.now().date()
                if today > self.last_rotation_reset:
                    self.rotation_count_today = 0
                    self.last_rotation_reset = today
                    self.logger.info("Daily rotation counter reset")

                # Update position snapshot
                await self._update_position_snapshot()

                # Check if profit target hit
                if self._should_take_profit():
                    self.logger.info(
                        f"🎯 Profit target reached! "
                        f"P&L: ${self.current_position.unrealized_pnl:.2f} "
                        f"({self.current_position.unrealized_pnl_percent:.2f}%)"
                    )
                    await self._execute_rotation()

                # Wait before next check
                await asyncio.sleep(self.check_interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval_seconds)

    async def _update_position_snapshot(self):
        """Update current position value and P&L."""
        if not self.current_position:
            return

        try:
            pair = self.current_position.pair

            # Get current balances
            base, quote = pair.split("/")
            balance_info = await self.exchange_service.get_balance()

            crypto_balance = balance_info.get(base, {}).get("total", 0.0)
            quote_balance = balance_info.get(quote, {}).get("total", 0.0)

            # Get current price
            ticker = await self.exchange_service.fetch_ticker(pair)
            current_price = ticker.get("last", 0.0)

            # Calculate position value
            crypto_value = crypto_balance * current_price
            total_value = crypto_value + quote_balance

            # Calculate P&L
            pnl = total_value - self.current_position.entry_value
            pnl_percent = (pnl / self.current_position.entry_value * 100) if self.current_position.entry_value > 0 else 0

            # Update snapshot
            self.current_position.current_value = total_value
            self.current_position.unrealized_pnl = pnl
            self.current_position.unrealized_pnl_percent = pnl_percent
            self.current_position.crypto_balance = crypto_balance
            self.current_position.quote_balance = quote_balance
            self.current_position.timestamp = datetime.now()

            # Log status every 10th check (reduce spam)
            if asyncio.current_task().get_name().endswith("0"):
                self.logger.info(
                    f"Position {pair}: ${total_value:.2f} "
                    f"(P&L: ${pnl:+.2f} / {pnl_percent:+.2f}%)"
                )

        except Exception as e:
            self.logger.error(f"Error updating position snapshot: {e}")

    def _should_take_profit(self) -> bool:
        """Determine if profit target has been reached."""
        if not self.current_position:
            return False

        # Check rotation limits
        if self.rotation_count_today >= self.max_rotations_per_day:
            self.logger.debug(f"Max rotations per day reached ({self.max_rotations_per_day})")
            return False

        # Check profit target
        if self.use_percent_target:
            return self.current_position.unrealized_pnl_percent >= self.profit_target_percent
        else:
            return self.current_position.unrealized_pnl >= self.profit_target_usd

    async def _execute_rotation(self):
        """Execute profit-taking and rotation to new pair."""
        if not self.current_position:
            return

        try:
            # Step 1: Close current position
            self.logger.info(f"Closing position in {self.current_position.pair}...")
            exit_value = await self._close_position()

            # Record exit
            self.recently_exited_pairs[self.current_position.pair] = datetime.now()
            profit_realized = exit_value - self.current_position.entry_value
            profit_percent = (profit_realized / self.current_position.entry_value * 100)

            self.logger.info(
                f"✅ Position closed: {self.current_position.pair} "
                f"→ Profit: ${profit_realized:.2f} ({profit_percent:.2f}%)"
            )

            # Step 2: Find next best opportunity
            if self.auto_enter_next:
                new_pair, new_score = await self._find_best_entry()

                if new_pair:
                    # Record rotation event
                    rotation = RotationEvent(
                        timestamp=datetime.now(),
                        from_pair=self.current_position.pair,
                        to_pair=new_pair,
                        profit_realized=profit_realized,
                        profit_percent=profit_percent,
                        exit_reason="profit_target",
                        new_pair_score=new_score,
                    )
                    self.rotation_history.append(rotation)
                    self.rotation_count_today += 1

                    self.logger.info(
                        f"🔄 ROTATION: {self.current_position.pair} → {new_pair} "
                        f"(score: {new_score:.1f}) | Profit: ${profit_realized:.2f}"
                    )

                    # Step 3: Enter new position
                    await self._enter_new_position(new_pair, exit_value)

                    # Publish event
                    await self.event_bus.publish(
                        "profit_rotation_completed",
                        {
                            "from_pair": rotation.from_pair,
                            "to_pair": rotation.to_pair,
                            "profit": profit_realized,
                            "profit_percent": profit_percent,
                            "new_score": new_score,
                        },
                    )
                else:
                    self.logger.warning("No suitable pair found for re-entry. Staying in cash.")
                    self.current_position = None
            else:
                self.logger.info("Auto-enter disabled. Position closed, staying in cash.")
                self.current_position = None

        except Exception as e:
            self.logger.error(f"Error executing rotation: {e}", exc_info=True)

    async def _close_position(self) -> float:
        """
        Close all orders and liquidate position.
        Returns final USD value.
        """
        if not self.current_position:
            return 0.0

        pair = self.current_position.pair
        base, quote = pair.split("/")

        # Cancel all open orders
        try:
            open_orders = await self.exchange_service.fetch_open_orders(pair)
            for order in open_orders:
                await self.exchange_service.cancel_order(order["id"], pair)
            self.logger.info(f"Cancelled {len(open_orders)} open orders")
        except Exception as e:
            self.logger.warning(f"Error cancelling orders: {e}")

        # Sell all crypto holdings
        try:
            crypto_balance = self.current_position.crypto_balance
            if crypto_balance > 0:
                ticker = await self.exchange_service.fetch_ticker(pair)
                current_price = ticker.get("last", 0.0)

                # Place market sell order
                sell_order = await self.exchange_service.create_order(
                    symbol=pair,
                    order_type="market",
                    side="sell",
                    amount=crypto_balance,
                    price=current_price,
                )
                self.logger.info(f"Market sell executed: {crypto_balance} {base} @ ${current_price:.4f}")

                # Wait for order to fill
                await asyncio.sleep(2)

        except Exception as e:
            self.logger.error(f"Error liquidating crypto: {e}")

        # Get final balance
        balance_info = await self.exchange_service.get_balance()
        final_value = balance_info.get(quote, {}).get("total", 0.0)

        return final_value

    async def _find_best_entry(self) -> tuple[str | None, float]:
        """
        Scan market for best entry opportunity.
        Returns (pair, score) or (None, 0) if no suitable pair found.
        """
        try:
            self.logger.info(f"Scanning market for top {self.top_pairs_to_scan} opportunities...")

            # Run market analysis
            results = await self.market_analyzer.find_best_trading_pairs(
                candidate_pairs=self.candidate_pairs,
                timeframe=self.timeframe,
                min_price=self.min_price,
                max_price=self.max_price,
            )

            if not results:
                self.logger.warning("Market scanner returned no results")
                return None, 0.0

            # Filter and rank
            valid_candidates = []
            cutoff_time = datetime.now() - timedelta(minutes=self.cooldown_minutes)

            for analysis in results[:self.top_pairs_to_scan]:
                # Skip if score too low
                if analysis.score < self.min_score_to_enter:
                    self.logger.debug(f"Skipping {analysis.pair}: score {analysis.score:.1f} too low")
                    continue

                # Skip if recently exited (cooldown)
                exit_time = self.recently_exited_pairs.get(analysis.pair)
                if exit_time and exit_time > cutoff_time:
                    remaining = (cutoff_time + timedelta(minutes=self.cooldown_minutes) - datetime.now()).seconds // 60
                    self.logger.debug(f"Skipping {analysis.pair}: cooldown active ({remaining}min remaining)")
                    continue

                valid_candidates.append((analysis.pair, analysis.score))

            if not valid_candidates:
                self.logger.warning("No valid candidates after filtering")
                return None, 0.0

            # Pick best candidate
            best_pair, best_score = max(valid_candidates, key=lambda x: x[1])
            self.logger.info(
                f"Best entry: {best_pair} (score: {best_score:.1f}) "
                f"[Top {len(valid_candidates)}: {', '.join(f'{p}={s:.0f}' for p, s in valid_candidates)}]"
            )

            return best_pair, best_score

        except Exception as e:
            self.logger.error(f"Error finding best entry: {e}", exc_info=True)
            return None, 0.0

    async def _enter_new_position(self, pair: str, capital: float):
        """
        Enter new position in selected pair.
        This will trigger the bot to create a new grid.
        """
        self.logger.info(f"Entering new position: {pair} with ${capital:.2f}")

        # Initialize new position snapshot
        self.current_position = PositionSnapshot(
            pair=pair,
            entry_value=capital,
            current_value=capital,
            unrealized_pnl=0.0,
            unrealized_pnl_percent=0.0,
            crypto_balance=0.0,
            quote_balance=capital,
        )

        # Publish event to trigger bot to create new grid
        await self.event_bus.publish(
            "profit_rotation_new_entry",
            {
                "pair": pair,
                "capital": capital,
                "timestamp": datetime.now().isoformat(),
            },
        )

    def get_status(self) -> dict[str, Any]:
        """Get current rotation manager status."""
        return {
            "enabled": self.enabled,
            "running": self.running,
            "current_position": (
                {
                    "pair": self.current_position.pair,
                    "entry_value": self.current_position.entry_value,
                    "current_value": self.current_position.current_value,
                    "pnl": self.current_position.unrealized_pnl,
                    "pnl_percent": self.current_position.unrealized_pnl_percent,
                    "progress_to_target": (
                        (self.current_position.unrealized_pnl_percent / self.profit_target_percent * 100)
                        if self.use_percent_target
                        else (self.current_position.unrealized_pnl / self.profit_target_usd * 100)
                    ),
                }
                if self.current_position
                else None
            ),
            "profit_target": (
                f"{self.profit_target_percent}%"
                if self.use_percent_target
                else f"${self.profit_target_usd}"
            ),
            "rotations_today": self.rotation_count_today,
            "max_rotations_per_day": self.max_rotations_per_day,
            "recent_rotations": [
                {
                    "timestamp": r.timestamp.isoformat(),
                    "from": r.from_pair,
                    "to": r.to_pair,
                    "profit": r.profit_realized,
                    "profit_percent": r.profit_percent,
                    "new_score": r.new_pair_score,
                }
                for r in self.rotation_history[-5:]
            ],
        }

"""
Multi-Pair Manager - Manages multiple trading pairs simultaneously.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from config.config_manager import ConfigManager
    from core.bot_management.event_bus import EventBus
    from core.services.exchange_interface import ExchangeInterface
    from strategies.market_analyzer import MarketAnalyzer


@dataclass
class PairStatus:
    """Status of a single trading pair."""

    pair: str
    allocated_balance: float
    current_balance: float
    crypto_balance: float
    pnl: float = 0.0
    pnl_percent: float = 0.0
    active_orders: int = 0
    filled_orders: int = 0
    last_trade_time: datetime | None = None
    status: str = "idle"  # idle, running, stopped, error
    grid_levels: list = field(default_factory=list)


class MultiPairManager:
    """
    Manages trading across multiple pairs simultaneously.
    Splits balance and runs independent grid strategies for each pair.
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

        # Configuration
        multi_config = config_manager.config.get("multi_pair", {})
        self.enabled = multi_config.get("enabled", False)
        self.max_pairs = multi_config.get("max_pairs", 2)
        self.balance_split = multi_config.get("balance_split", "equal")  # equal, weighted
        self.min_balance_per_pair = multi_config.get("min_balance_per_pair", 15.0)
        self.auto_select = multi_config.get("auto_select", True)  # Use scanner to pick pairs

        # State
        self.active_pairs: dict[str, PairStatus] = {}
        self.pair_strategies: dict[str, Any] = {}  # Strategy instances per pair
        self.running = False
        self.total_balance = 0.0

    async def initialize(self, pairs: list[str] | None = None):
        """
        Initialize multi-pair trading.

        Args:
            pairs: List of pairs to trade. If None and auto_select is True,
                   will use scanner to find best pairs.
        """
        self.logger.info("Initializing Multi-Pair Manager...")

        # Get total available balance
        balance_info = await self.exchange_service.get_balance()
        self.total_balance = balance_info.get("USD", {}).get("free", 0.0)
        self.logger.info(f"Total available balance: ${self.total_balance:.2f}")

        # Check minimum balance requirement
        min_required = self.min_balance_per_pair * self.max_pairs
        if self.total_balance < min_required:
            adjusted_pairs = int(self.total_balance / self.min_balance_per_pair)
            if adjusted_pairs < 1:
                raise ValueError(
                    f"Insufficient balance: ${self.total_balance:.2f}. "
                    f"Minimum ${self.min_balance_per_pair:.2f} required per pair."
                )
            self.logger.warning(
                f"Balance ${self.total_balance:.2f} only supports {adjusted_pairs} pairs "
                f"(minimum ${self.min_balance_per_pair:.2f} each)"
            )
            self.max_pairs = adjusted_pairs

        # Select pairs to trade
        if pairs:
            selected_pairs = pairs[: self.max_pairs]
        elif self.auto_select:
            selected_pairs = await self._auto_select_pairs()
        else:
            # Use configured symbol as single pair
            selected_pairs = [self.config_manager.get_symbol()]

        if not selected_pairs:
            raise ValueError("No pairs selected for trading")

        # Calculate balance allocation
        allocations = self._calculate_allocations(selected_pairs)

        # Initialize pair statuses
        for pair, allocation in allocations.items():
            self.active_pairs[pair] = PairStatus(
                pair=pair,
                allocated_balance=allocation,
                current_balance=allocation,
                crypto_balance=0.0,
                status="initialized",
            )
            self.logger.info(f"  📊 {pair}: ${allocation:.2f} allocated")

        self.logger.info(f"Multi-Pair Manager initialized with {len(self.active_pairs)} pairs")

    async def _auto_select_pairs(self) -> list[str]:
        """Use market scanner to select best pairs."""
        self.logger.info("Auto-selecting pairs using market scanner...")

        try:
            results = await self.market_analyzer.find_best_trading_pairs(
                exchange_service=self.exchange_service,
                quote_currency="USD",
                min_price=1.0,
                max_price=20.0,
                timeframe="15m",
                top_n=self.max_pairs * 2,  # Get extra in case some fail
            )

            if not results:
                self.logger.warning("Scanner returned no results")
                return []

            # Take top N pairs with STRONG_BUY or BUY signal
            selected = []
            for result in results:
                if len(selected) >= self.max_pairs:
                    break
                if result.signal in ("STRONG_BUY", "BUY"):
                    selected.append(result.pair)
                    self.logger.info(
                        f"  ✅ Selected {result.pair} (score: {result.score:.1f}, signal: {result.signal})"
                    )

            # If we don't have enough BUY signals, add NEUTRAL pairs
            if len(selected) < self.max_pairs:
                for result in results:
                    if len(selected) >= self.max_pairs:
                        break
                    if result.pair not in selected:
                        selected.append(result.pair)
                        self.logger.info(
                            f"  ➕ Added {result.pair} (score: {result.score:.1f}, signal: {result.signal})"
                        )

            return selected

        except Exception as e:
            self.logger.error(f"Error auto-selecting pairs: {e}")
            return []

    def _calculate_allocations(self, pairs: list[str]) -> dict[str, float]:
        """Calculate balance allocation for each pair."""
        allocations = {}

        if self.balance_split == "equal":
            # Equal split
            per_pair = self.total_balance / len(pairs)
            for pair in pairs:
                allocations[pair] = per_pair
        else:
            # Could implement weighted allocation based on score later
            per_pair = self.total_balance / len(pairs)
            for pair in pairs:
                allocations[pair] = per_pair

        return allocations

    async def start(self):
        """Start trading on all pairs."""
        if not self.active_pairs:
            raise ValueError("No pairs initialized. Call initialize() first.")

        self.logger.info(f"Starting multi-pair trading on {len(self.active_pairs)} pairs...")
        self.running = True

        # Start each pair's strategy
        tasks = []
        for pair, status in self.active_pairs.items():
            status.status = "starting"
            task = asyncio.create_task(self._run_pair_strategy(pair, status))
            tasks.append(task)

        # Run all strategies concurrently
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(f"Error in multi-pair trading: {e}")
        finally:
            self.running = False

    async def _run_pair_strategy(self, pair: str, status: PairStatus):
        """Run the grid strategy for a single pair."""
        self.logger.info(f"Starting strategy for {pair}...")

        try:
            status.status = "running"

            # Create a modified config for this pair
            pair_config = self._create_pair_config(pair, status.allocated_balance)

            # Import here to avoid circular imports
            from core.grid_management.grid_manager import GridManager
            from core.order_handling.balance_tracker import BalanceTracker
            from core.order_handling.order_manager import OrderManager
            from core.order_handling.order_status_tracker import OrderStatusTracker
            from strategies.grid_trading_strategy import GridTradingStrategy
            from strategies.plotter import Plotter

            # Create components for this pair
            balance_tracker = BalanceTracker(
                initial_balance=status.allocated_balance,
                initial_crypto_balance=0.0,
            )

            order_manager = OrderManager(
                config_manager=pair_config,
                exchange_service=self.exchange_service,
                balance_tracker=balance_tracker,
                pair=pair,
            )

            order_status_tracker = OrderStatusTracker(
                event_bus=self.event_bus,
                exchange_service=self.exchange_service,
                order_manager=order_manager,
            )

            grid_manager = GridManager(pair_config)

            strategy = GridTradingStrategy(
                config_manager=pair_config,
                exchange_service=self.exchange_service,
                event_bus=self.event_bus,
                order_manager=order_manager,
                balance_tracker=balance_tracker,
                order_status_tracker=order_status_tracker,
                grid_manager=grid_manager,
                trading_pair=pair,
                plotter=Plotter(),
            )

            self.pair_strategies[pair] = strategy
            strategy.initialize_strategy()

            # Start order tracking
            order_status_tracker.start_tracking()

            # Run the strategy
            await strategy.run()

        except Exception as e:
            self.logger.error(f"Error in {pair} strategy: {e}")
            status.status = "error"
        finally:
            if pair in self.pair_strategies:
                status.status = "stopped"

    def _create_pair_config(self, pair: str, balance: float):
        """Create a config manager instance for a specific pair."""
        # Clone the base config and modify for this pair
        import copy

        from config.config_manager import ConfigManager

        base_config = copy.deepcopy(self.config_manager.config)
        base_config["symbol"] = pair
        base_config["initial_balance"] = balance

        # Create a new config manager with modified config
        # This is a simplified approach - in production, might need a proper factory
        pair_config = ConfigManager.__new__(ConfigManager)
        pair_config._config = base_config
        pair_config._config_path = self.config_manager._config_path

        return pair_config

    async def stop(self):
        """Stop all pair strategies."""
        self.logger.info("Stopping multi-pair trading...")
        self.running = False

        for pair, strategy in self.pair_strategies.items():
            try:
                await strategy.stop()
                self.active_pairs[pair].status = "stopped"
                self.logger.info(f"  Stopped {pair}")
            except Exception as e:
                self.logger.error(f"Error stopping {pair}: {e}")

    def get_status(self) -> dict[str, Any]:
        """Get status of all pairs."""
        pairs_status = {}
        total_pnl = 0.0
        total_current = 0.0
        total_allocated = 0.0

        for pair, status in self.active_pairs.items():
            # Update from strategy if available
            if pair in self.pair_strategies:
                strategy = self.pair_strategies[pair]
                if hasattr(strategy, "balance_tracker"):
                    bt = strategy.balance_tracker
                    status.current_balance = bt.balance + bt.reserved_fiat
                    status.crypto_balance = bt.crypto_balance + bt.reserved_crypto

            status.pnl = status.current_balance - status.allocated_balance
            status.pnl_percent = (status.pnl / status.allocated_balance * 100) if status.allocated_balance > 0 else 0

            total_pnl += status.pnl
            total_current += status.current_balance
            total_allocated += status.allocated_balance

            pairs_status[pair] = {
                "pair": status.pair,
                "allocated": status.allocated_balance,
                "current": status.current_balance,
                "crypto": status.crypto_balance,
                "pnl": status.pnl,
                "pnl_percent": status.pnl_percent,
                "active_orders": status.active_orders,
                "filled_orders": status.filled_orders,
                "status": status.status,
            }

        return {
            "enabled": self.enabled,
            "running": self.running,
            "max_pairs": self.max_pairs,
            "active_pairs_count": len(self.active_pairs),
            "pairs": pairs_status,
            "summary": {
                "total_allocated": total_allocated,
                "total_current": total_current,
                "total_pnl": total_pnl,
                "total_pnl_percent": ((total_pnl / total_allocated * 100) if total_allocated > 0 else 0),
            },
        }

    async def replace_pair(self, old_pair: str, new_pair: str):
        """Replace an underperforming pair with a new one."""
        if old_pair not in self.active_pairs:
            self.logger.warning(f"Pair {old_pair} not found in active pairs")
            return False

        self.logger.info(f"Replacing {old_pair} with {new_pair}...")

        # Stop old pair strategy
        if old_pair in self.pair_strategies:
            await self.pair_strategies[old_pair].stop()
            del self.pair_strategies[old_pair]

        # Transfer allocation
        old_status = self.active_pairs.pop(old_pair)
        new_allocation = old_status.current_balance

        # Create new pair status
        self.active_pairs[new_pair] = PairStatus(
            pair=new_pair,
            allocated_balance=new_allocation,
            current_balance=new_allocation,
            crypto_balance=0.0,
            status="initialized",
        )

        # Start new pair strategy
        new_status = self.active_pairs[new_pair]
        asyncio.create_task(self._run_pair_strategy(new_pair, new_status))

        self.logger.info(f"Replaced {old_pair} → {new_pair} with ${new_allocation:.2f}")
        return True

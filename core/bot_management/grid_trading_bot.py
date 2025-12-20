import logging
import traceback
from typing import TYPE_CHECKING, Any

from config.config_manager import ConfigManager
from config.trading_mode import TradingMode
from core.bot_management.activity_monitor import ActivityMonitor
from core.bot_management.event_bus import EventBus, Events
from core.bot_management.multi_pair_manager import MultiPairManager
from core.grid_management.grid_manager import GridManager
from core.order_handling.balance_tracker import BalanceTracker
from core.order_handling.execution_strategy.order_execution_strategy_factory import (
    OrderExecutionStrategyFactory,
)
from core.order_handling.fee_calculator import FeeCalculator
from core.order_handling.order_book import OrderBook
from core.order_handling.order_manager import OrderManager
from core.order_handling.order_status_tracker import OrderStatusTracker
from core.services.exceptions import (
    DataFetchError,
    UnsupportedExchangeError,
    UnsupportedTimeframeError,
)
from core.services.exchange_service_factory import ExchangeServiceFactory
from core.validation.order_validator import OrderValidator
from strategies.grid_trading_strategy import GridTradingStrategy
from strategies.market_analyzer import MarketAnalyzer
from strategies.plotter import Plotter
from strategies.trading_performance_analyzer import TradingPerformanceAnalyzer

if TYPE_CHECKING:
    from strategies.strategy_type import StrategyType

from .notification.notification_handler import NotificationHandler


class GridTradingBot:
    def __init__(
        self,
        config_path: str,
        config_manager: ConfigManager,
        notification_handler: NotificationHandler,
        event_bus: EventBus,
        save_performance_results_path: str | None = None,
        no_plot: bool = False,
    ):
        try:
            self.logger = logging.getLogger(self.__class__.__name__)
            self.config_path = config_path
            self.config_manager = config_manager
            self.notification_handler = notification_handler
            self.event_bus = event_bus
            self.event_bus.subscribe(Events.STOP_BOT, self._handle_stop_bot_event)
            self.event_bus.subscribe(Events.START_BOT, self._handle_start_bot_event)
            self.save_performance_results_path = save_performance_results_path
            self.no_plot = no_plot
            self.trading_mode: TradingMode = self.config_manager.get_trading_mode()
            base_currency: str = self.config_manager.get_base_currency()
            quote_currency: str = self.config_manager.get_quote_currency()
            self.trading_pair = f"{base_currency}/{quote_currency}"
            strategy_type: StrategyType = self.config_manager.get_strategy_type()
            self.logger.info(
                f"Starting Grid Trading Bot in {self.trading_mode.value} mode with strategy: {strategy_type.value}",
            )
            self.is_running = False

            self.exchange_service = ExchangeServiceFactory.create_exchange_service(
                self.config_manager,
                self.trading_mode,
            )
            order_execution_strategy = OrderExecutionStrategyFactory.create(self.config_manager, self.exchange_service)
            grid_manager = GridManager(self.config_manager, strategy_type)
            order_validator = OrderValidator()
            fee_calculator = FeeCalculator(self.config_manager)

            self.balance_tracker = BalanceTracker(
                event_bus=self.event_bus,
                fee_calculator=fee_calculator,
                trading_mode=self.trading_mode,
                base_currency=base_currency,
                quote_currency=quote_currency,
            )
            order_book = OrderBook()

            self.order_status_tracker = OrderStatusTracker(
                order_book=order_book,
                order_execution_strategy=order_execution_strategy,
                event_bus=self.event_bus,
                polling_interval=5.0,
            )

            order_manager = OrderManager(
                self.config_manager,
                grid_manager,
                order_validator,
                self.balance_tracker,
                order_book,
                self.event_bus,
                order_execution_strategy,
                self.notification_handler,
                self.trading_mode,
                self.trading_pair,
                strategy_type,
            )

            trading_performance_analyzer = TradingPerformanceAnalyzer(self.config_manager, order_book)
            plotter = Plotter(grid_manager, order_book) if self.trading_mode == TradingMode.BACKTEST else None
            self.strategy = GridTradingStrategy(
                self.config_manager,
                self.event_bus,
                self.exchange_service,
                grid_manager,
                order_manager,
                self.balance_tracker,
                trading_performance_analyzer,
                self.trading_mode,
                self.trading_pair,
                plotter,
            )

            # Activity monitor for auto-switching stale pairs
            self.activity_monitor = None
            self.multi_pair_manager = None
            market_analyzer = None

            if self.trading_mode in (TradingMode.LIVE, TradingMode.PAPER_TRADING):
                market_analyzer = MarketAnalyzer(self.exchange_service, self.config_manager)

                # Activity monitor
                activity_config = self.config_manager.config.get("activity_monitor", {})
                if activity_config.get("enabled", False):
                    self.activity_monitor = ActivityMonitor(
                        exchange_service=self.exchange_service,
                        market_analyzer=market_analyzer,
                        event_bus=self.event_bus,
                        config=activity_config,
                    )
                    # Subscribe to switch events
                    self.event_bus.subscribe(Events.SWITCH_PAIR, self._handle_switch_pair)
                    # Subscribe to force exit events (stagnation)
                    self.event_bus.subscribe(Events.FORCE_EXIT_POSITION, self._handle_force_exit)

                # Multi-pair manager
                multi_pair_config = self.config_manager.config.get("multi_pair", {})
                if multi_pair_config.get("enabled", False):
                    self.multi_pair_manager = MultiPairManager(
                        config_manager=self.config_manager,
                        exchange_service=self.exchange_service,
                        event_bus=self.event_bus,
                        market_analyzer=market_analyzer,
                    )
                    self.logger.info("Multi-pair trading enabled")

        except (UnsupportedExchangeError, DataFetchError, UnsupportedTimeframeError) as e:
            self.logger.error(f"{type(e).__name__}: {e}")
            raise

        except Exception:
            self.logger.error("An unexpected error occurred.")
            self.logger.error(traceback.format_exc())
            raise

    async def initialize(self) -> None:
        """Initialize bot components (balances, etc.) before running."""
        if hasattr(self, "_initialized") and self._initialized:
            return

        self.logger.info("Initializing Grid Trading Bot components...")
        
        # Auto-select best pair on startup if enabled
        await self._auto_select_initial_pair()
        
        await self.balance_tracker.setup_balances(
            initial_balance=self.config_manager.get_initial_balance(),
            initial_crypto_balance=self.config_manager.get_initial_crypto_balance(),
            exchange_service=self.exchange_service,
        )
        self.strategy.initialize_strategy()
        self._initialized = True
        self.logger.info("Grid Trading Bot initialized.")

    async def _auto_select_initial_pair(self) -> None:
        """
        Auto-select the best trading pair on startup using the market scanner.
        Only runs if auto_select_on_startup is enabled in config.
        """
        scanner_config = self.config_manager.config.get("market_scanner", {})
        if not scanner_config.get("auto_select_on_startup", False):
            self.logger.info(f"Using configured pair: {self.trading_pair}")
            return
        
        self.logger.info("[AUTO-SELECT] Scanning for best trading pair on startup...")
        
        try:
            from strategies.market_analyzer import MarketAnalyzer
            
            analyzer = MarketAnalyzer(self.exchange_service, self.config_manager)
            
            # Get scan parameters from config
            quote_currency = scanner_config.get("quote_currency", "USD")
            min_price = scanner_config.get("min_price", 1.0)
            max_price = scanner_config.get("max_price", 20.0)
            timeframe = scanner_config.get("timeframe", "15m")
            
            # First try to get top gainers dynamically
            pairs = []
            if hasattr(self.exchange_service, "get_top_gainers"):
                self.logger.info("[AUTO-SELECT] Fetching top gainers from exchange...")
                top_gainers = await self.exchange_service.get_top_gainers(
                    quote_currency=quote_currency,
                    min_price=min_price,
                    max_price=max_price,
                    limit=10,
                )
                pairs = [g["pair"] for g in top_gainers]
            
            # Fallback to candidate_pairs from config
            if not pairs:
                pairs = scanner_config.get("candidate_pairs", [])
            
            if not pairs:
                self.logger.warning("[AUTO-SELECT] No pairs to scan, using configured pair")
                return
            
            self.logger.info(f"[AUTO-SELECT] Analyzing {len(pairs)} pairs: {pairs[:5]}...")
            
            # Run analysis
            results = await analyzer.find_best_trading_pairs(
                candidate_pairs=pairs,
                timeframe=timeframe,
                min_price=min_price,
                max_price=max_price,
            )
            
            if not results:
                self.logger.warning("[AUTO-SELECT] No pairs passed analysis, using configured pair")
                return
            
            # Pick the best one
            best = results[0]
            
            if best.pair != self.trading_pair:
                self.logger.info(
                    f"[AUTO-SELECT] Best pair: {best.pair} (score: {best.score:.1f}, signal: {best.signal})"
                )
                self.logger.info(f"[AUTO-SELECT] Switching from {self.trading_pair} to {best.pair}")
                
                # Update trading pair
                old_pair = self.trading_pair
                self.trading_pair = best.pair
                
                # Update config manager
                base, quote = best.pair.split("/")
                self.config_manager.config["pair"]["base_currency"] = base
                self.config_manager.config["pair"]["quote_currency"] = quote
                
                # Calculate new grid range based on current price (10% range)
                current_price = best.price  # CoinAnalysis uses 'price' not 'current_price'
                range_percent = self.config_manager.config.get("market_scanner", {}).get("range_percent", 0.10)
                new_lower = round(current_price * (1 - range_percent / 2), 4)
                new_upper = round(current_price * (1 + range_percent / 2), 4)
                
                # Update grid_strategy range (config uses 'grid_strategy.range.bottom/top')
                self.config_manager.config["grid_strategy"]["range"]["bottom"] = new_lower
                self.config_manager.config["grid_strategy"]["range"]["top"] = new_upper
                self.logger.info(f"[AUTO-SELECT] Grid range: ${new_lower:.4f} - ${new_upper:.4f} (around ${current_price:.4f})")
                
                # Reinitialize grid manager with new prices
                strategy_type = self.config_manager.get_strategy_type()
                self.grid_manager = GridManager(self.config_manager, strategy_type)
                self.grid_manager.initialize_grids_and_levels()
                self.logger.info(f"[AUTO-SELECT] Grid manager reinitialized for {best.pair}")
                
                # Update strategy references
                self.strategy.trading_pair = best.pair
                self.strategy.order_manager.trading_pair = best.pair
                self.strategy.grid_manager = self.grid_manager
                self.strategy.order_manager.grid_manager = self.grid_manager
                
                # Update balance tracker base currency for new pair
                self.balance_tracker.base_currency = base
                self.strategy.order_manager.balance_tracker.base_currency = base
                self.logger.info(f"[AUTO-SELECT] Updated balance tracker for {base}/{quote}")
                
                self.logger.info(f"[AUTO-SELECT] Successfully selected {best.pair} for trading")
            else:
                self.logger.info(f"[AUTO-SELECT] Configured pair {self.trading_pair} is already the best!")
                
        except Exception as e:
            self.logger.error(f"[AUTO-SELECT] Error during auto-selection: {e}")
            self.logger.info(f"[AUTO-SELECT] Falling back to configured pair: {self.trading_pair}")

    async def run(self) -> dict[str, Any] | None:
        try:
            self.is_running = True

            await self.initialize()

            self.order_status_tracker.start_tracking()

            # Start activity monitor if enabled
            if self.activity_monitor and self.activity_monitor.enabled:
                await self.activity_monitor.start(self.trading_pair)

            await self.strategy.run()

            if not self.no_plot:
                self.strategy.plot_results()

            return self._generate_and_log_performance()

        except Exception as e:
            self.logger.error(f"An unexpected error occurred {e}")
            self.logger.error(traceback.format_exc())
            raise

        finally:
            # Stop activity monitor
            if self.activity_monitor:
                await self.activity_monitor.stop()
            self.is_running = False

    async def _handle_stop_bot_event(self, reason: str) -> None:
        self.logger.info(f"Handling STOP_BOT event: {reason}")
        await self._stop()

    async def _handle_start_bot_event(self, reason: str) -> None:
        self.logger.info(f"Handling START_BOT event: {reason}")
        await self.restart()

    async def _handle_switch_pair(self, data: dict) -> None:
        """Handle switch to a new trading pair."""
        new_pair = data.get("new_pair")
        reason = data.get("reason", "Activity monitor triggered switch")

        self.logger.info(f"Switching trading pair from {self.trading_pair} to {new_pair}: {reason}")

        try:
            # Stop current trading
            await self._stop()

            # Update trading pair
            old_pair = self.trading_pair
            self.trading_pair = new_pair

            # Update config manager with new pair
            self.config_manager._config["symbol"] = new_pair

            # Reinitialize with new pair
            self._initialized = False
            await self.restart()

            # Restart activity monitor with new pair
            if self.activity_monitor and self.activity_monitor.enabled:
                await self.activity_monitor.start(new_pair)

            self.logger.info(f"Successfully switched from {old_pair} to {new_pair}")

        except Exception as e:
            self.logger.error(f"Error switching pair: {e}", exc_info=True)

    async def _handle_force_exit(self, data: dict) -> None:
        """
        Handle force exit of a position due to stagnation.
        Sells all crypto holdings for the current pair and prepares for switch.
        """
        pair = data.get("pair", self.trading_pair)
        reason = data.get("reason", "stagnation")
        exit_at_loss = data.get("exit_at_loss", True)
        max_loss_pct = data.get("max_loss_percent", 2.0)

        self.logger.warning(f"⚠️ FORCE EXIT triggered for {pair} due to {reason}")

        try:
            # Get current position info
            base_currency = pair.split("/")[0]
            quote_currency = pair.split("/")[1]
            
            # Get current balances
            crypto_balance = await self.balance_tracker.get_crypto_balance()
            current_price = await self._get_current_price(pair)
            
            if crypto_balance <= 0:
                self.logger.info(f"No {base_currency} to sell, skipping force exit")
                return
                
            position_value = crypto_balance * current_price
            
            # Calculate P&L if we have entry info
            entry_price = getattr(self.strategy, 'average_entry_price', None)
            if entry_price and entry_price > 0:
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
                
                # Check if loss is too high
                if not exit_at_loss and pnl_pct < 0:
                    self.logger.info(f"Position at loss ({pnl_pct:.2f}%), exit_at_loss=False, skipping")
                    return
                    
                if pnl_pct < -max_loss_pct:
                    self.logger.warning(
                        f"Loss ({pnl_pct:.2f}%) exceeds max ({max_loss_pct}%), "
                        f"holding position instead of force exit"
                    )
                    return
                    
                self.logger.info(f"Force exiting position at {pnl_pct:+.2f}% P&L")
            
            # Cancel all open orders first
            self.logger.info("Cancelling all open orders...")
            await self.order_manager.cancel_all_orders(pair)
            
            # Place market sell order
            self.logger.info(f"Selling {crypto_balance:.6f} {base_currency} at market price ${current_price:.4f}")
            
            sell_order = await self.order_manager.create_market_order(
                pair=pair,
                side="sell",
                amount=crypto_balance,
                reason="stagnation_exit"
            )
            
            if sell_order:
                self.logger.info(
                    f"✅ Force exit complete: Sold {crypto_balance:.6f} {base_currency} "
                    f"for ~${position_value:.2f}"
                )
            else:
                self.logger.error("Failed to execute force exit sell order")

        except Exception as e:
            self.logger.error(f"Error during force exit: {e}", exc_info=True)

    async def _get_current_price(self, pair: str) -> float:
        """Get current price for a trading pair."""
        try:
            ticker = await self.exchange_service.get_ticker(pair)
            return ticker.get("last") or ticker.get("close", 0)
        except Exception as e:
            self.logger.error(f"Error getting price for {pair}: {e}")
            return 0

    async def _stop(self) -> None:
        if not self.is_running:
            self.logger.info("Bot is not running. Nothing to stop.")
            return

        self.logger.info("Stopping Grid Trading Bot...")

        try:
            await self.order_status_tracker.stop_tracking()
            await self.strategy.stop()
            self.is_running = False

        except Exception as e:
            self.logger.error(f"Error while stopping components: {e}", exc_info=True)

        self.logger.info("Grid Trading Bot has been stopped.")

    async def restart(self) -> None:
        if self.is_running:
            self.logger.info("Bot is already running. Restarting...")
            await self._stop()

        self.logger.info("Restarting Grid Trading Bot...")
        self.is_running = True

        try:
            await self.initialize()
            self.order_status_tracker.start_tracking()
            await self.strategy.restart()

        except Exception as e:
            self.logger.error(f"Error while restarting components: {e}", exc_info=True)

        self.logger.info("Grid Trading Bot has been restarted.")

    def _generate_and_log_performance(self) -> dict[str, Any] | None:
        performance_summary, formatted_orders = self.strategy.generate_performance_report()
        return {
            "config": self.config_path,
            "performance_summary": performance_summary,
            "orders": formatted_orders,
        }

    async def get_bot_health_status(self) -> dict:
        health_status = {
            "strategy": await self._check_strategy_health(),
            "exchange_status": await self._get_exchange_status(),
        }

        health_status["overall"] = all(health_status.values())
        return health_status

    async def _check_strategy_health(self) -> bool:
        if not self.is_running:
            self.logger.warning("Bot has stopped unexpectedly.")
            return False
        return True

    async def _get_exchange_status(self) -> str:
        exchange_status = await self.exchange_service.get_exchange_status()
        return exchange_status.get("status", "unknown")

    def get_balances(self) -> dict[str, float]:
        return {
            "fiat": self.balance_tracker.balance,
            "reserved_fiat": self.balance_tracker.reserved_fiat,
            "crypto": self.balance_tracker.crypto_balance,
            "reserved_crypto": self.balance_tracker.reserved_crypto,
        }

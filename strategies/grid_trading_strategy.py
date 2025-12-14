import logging
import time

import numpy as np
import pandas as pd

from config.config_manager import ConfigManager
from config.trading_mode import TradingMode
from core.bot_management.event_bus import EventBus, Events
from core.grid_management.grid_manager import GridManager
from core.order_handling.balance_tracker import BalanceTracker
from core.order_handling.order_manager import OrderManager
from core.services.exchange_interface import ExchangeInterface
from strategies.plotter import Plotter
from strategies.trading_performance_analyzer import TradingPerformanceAnalyzer
from strategies.multi_timeframe_analyzer import (
    MultiTimeframeAnalyzer,
    GridTradingSignal,
    MarketCondition,
)

from .trading_strategy_interface import TradingStrategyInterface


class GridTradingStrategy(TradingStrategyInterface):
    TICKER_REFRESH_INTERVAL = 3  # in seconds

    def __init__(
        self,
        config_manager: ConfigManager,
        event_bus: EventBus,
        exchange_service: ExchangeInterface,
        grid_manager: GridManager,
        order_manager: OrderManager,
        balance_tracker: BalanceTracker,
        trading_performance_analyzer: TradingPerformanceAnalyzer,
        trading_mode: TradingMode,
        trading_pair: str,
        plotter: Plotter | None = None,
    ):
        super().__init__(config_manager, balance_tracker)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.event_bus = event_bus
        self.exchange_service = exchange_service
        self.grid_manager = grid_manager
        self.order_manager = order_manager
        self.trading_performance_analyzer = trading_performance_analyzer
        self.trading_mode = trading_mode
        self.trading_pair = trading_pair
        self.plotter = plotter
        self.data = self._initialize_historical_data()
        self.live_trading_metrics = []
        self._running = True
        
        # Multi-timeframe analysis
        self._mtf_analyzer = self._initialize_mtf_analyzer()
        self._last_mtf_analysis_time = 0
        self._mtf_analysis_result = None
        self._trading_paused_by_trend = False

    def _initialize_historical_data(self) -> pd.DataFrame | None:
        """
        Initializes historical market data (OHLCV).
        In LIVE or PAPER_TRADING mode returns None.
        """
        if self.trading_mode != TradingMode.BACKTEST:
            return None

        try:
            timeframe, start_date, end_date = self._extract_config()
            return self.exchange_service.fetch_ohlcv(self.trading_pair, timeframe, start_date, end_date)
        except Exception as e:
            self.logger.error(f"Failed to initialize data for backtest trading mode: {e}")
            return None

    def _initialize_mtf_analyzer(self) -> MultiTimeframeAnalyzer | None:
        """
        Initialize multi-timeframe analyzer if enabled.
        
        Returns:
            MultiTimeframeAnalyzer instance or None if disabled
        """
        if self.trading_mode == TradingMode.BACKTEST:
            return None  # MTF analysis not used in backtest
        
        if not self.config_manager.is_multi_timeframe_analysis_enabled():
            self.logger.info("Multi-timeframe analysis is disabled in config")
            return None
        
        try:
            timeframes = self.config_manager.get_mtf_timeframes()
            analyzer = MultiTimeframeAnalyzer(
                exchange_service=self.exchange_service,
                config_timeframes=timeframes,
            )
            self.logger.info(
                f"Multi-timeframe analyzer initialized with timeframes: "
                f"trend={timeframes.get('trend', '1d')}, "
                f"config={timeframes.get('config', '4h')}, "
                f"execution={timeframes.get('execution', '1h')}"
            )
            return analyzer
        except Exception as e:
            self.logger.error(f"Failed to initialize multi-timeframe analyzer: {e}")
            return None

    async def _run_mtf_analysis(self) -> bool:
        """
        Run multi-timeframe analysis if due.
        
        Returns:
            True if trading should continue, False if should pause
        """
        if self._mtf_analyzer is None:
            return True  # No analyzer = continue trading
        
        analysis_interval = self.config_manager.get_mtf_analysis_interval_minutes() * 60
        current_time = time.time()
        
        # Check if analysis is due
        if current_time - self._last_mtf_analysis_time < analysis_interval:
            # Use cached result
            if self._trading_paused_by_trend:
                return False
            return True
        
        try:
            # Get grid boundaries
            grid_top = max(self.grid_manager.price_grids)
            grid_bottom = min(self.grid_manager.price_grids)
            
            # Run analysis
            self.logger.info("Running scheduled multi-timeframe analysis...")
            result = await self._mtf_analyzer.analyze(
                self.trading_pair,
                grid_bottom,
                grid_top,
            )
            
            self._mtf_analysis_result = result
            self._last_mtf_analysis_time = current_time
            
            # Log recommendations
            for rec in result.recommendations:
                self.logger.info(f"[MTF] {rec}")
            
            # Check if we should pause trading
            if self.config_manager.should_pause_on_strong_trend():
                if result.grid_signal == GridTradingSignal.AVOID:
                    self.logger.warning(
                        f"[MTF] PAUSING grid trading - {result.market_condition.value} detected. "
                        f"Will resume when conditions improve."
                    )
                    self._trading_paused_by_trend = True
                    await self.event_bus.publish(Events.MTF_TRADING_PAUSED, {
                        "reason": result.market_condition.value,
                        "recommendations": result.recommendations,
                    })
                    return False
                elif self._trading_paused_by_trend:
                    # Check if conditions have improved
                    if result.grid_signal in [GridTradingSignal.IDEAL, GridTradingSignal.FAVORABLE]:
                        self.logger.info(
                            f"[MTF] RESUMING grid trading - conditions improved to {result.grid_signal.value}"
                        )
                        self._trading_paused_by_trend = False
                        await self.event_bus.publish(Events.MTF_TRADING_RESUMED, {
                            "signal": result.grid_signal.value,
                        })
            
            # Publish analysis result for dashboard/monitoring
            await self.event_bus.publish(Events.MTF_ANALYSIS_COMPLETE, {
                "primary_trend": result.primary_trend,
                "market_condition": result.market_condition.value,
                "grid_signal": result.grid_signal.value,
                "spacing_multiplier": result.recommended_spacing_multiplier,
                "recommended_bias": result.recommended_bias,
                "range_valid": result.range_valid,
                "confidence": result.confidence,
            })
            
            return not self._trading_paused_by_trend
            
        except Exception as e:
            self.logger.error(f"Multi-timeframe analysis failed: {e}", exc_info=True)
            return True  # Continue trading on analysis failure

    def _extract_config(self) -> tuple[str, str, str]:
        """
        Extracts configuration values for timeframe, start date, and end date.

        Returns:
            tuple: A tuple containing the timeframe, start date, and end date as strings.
        """
        timeframe = self.config_manager.get_timeframe()
        start_date = self.config_manager.get_start_date()
        end_date = self.config_manager.get_end_date()
        return timeframe, start_date, end_date

    def initialize_strategy(self):
        """
        Initializes the trading strategy by setting up the grid and levels.
        This method prepares the strategy to be ready for trading.
        """
        self.grid_manager.initialize_grids_and_levels()

    async def stop(self):
        """
        Stops the trading execution.

        This method halts all trading activities, closes active exchange
        connections, and updates the internal state to indicate the bot
        is no longer running.
        """
        self._running = False
        await self.exchange_service.close_connection()
        self.logger.info("Trading execution stopped.")

    async def restart(self):
        """
        Restarts the trading session. If the strategy is not running, starts it.
        """
        if not self._running:
            self.logger.info("Restarting trading session.")
            await self.run()

    async def run(self):
        """
        Starts the trading session based on the configured mode.

        For backtesting, this simulates the strategy using historical data.
        For live or paper trading, this interacts with the exchange to manage
        real-time trading.

        Raises:
            Exception: If any error occurs during the trading session.
        """
        self._running = True
        trigger_price = self.grid_manager.get_trigger_price()

        if self.trading_mode == TradingMode.BACKTEST:
            await self._run_backtest(trigger_price)
            self.logger.info("Ending backtest simulation")
            self._running = False
        else:
            await self._run_live_or_paper_trading(trigger_price)

    async def _run_live_or_paper_trading(self, trigger_price: float):
        """
        Executes live or paper trading sessions based on real-time ticker updates.

        The method listens for ticker updates, initializes grid orders when
        the trigger price is reached, and manages take-profit and stop-loss events.

        Args:
            trigger_price (float): The price at which grid orders are triggered.
        """
        mode_name = "live" if self.trading_mode == TradingMode.LIVE else "paper"
        self.logger.info(f"Starting {mode_name} trading")
        self.logger.info(f"[STATUS] ACTIVE PAIR: {self.trading_pair} | Mode: {mode_name.upper()}")
        last_price: float | None = None
        grid_orders_initialized = False
        last_status_log = 0  # Track when we last logged status
        status_log_interval = 300  # Log status every 5 minutes
        
        # Run initial multi-timeframe analysis before starting
        if self._mtf_analyzer:
            self.logger.info("Running initial multi-timeframe analysis...")
            should_trade = await self._run_mtf_analysis()
            if not should_trade:
                self.logger.warning(
                    "[MTF] Initial analysis suggests unfavorable conditions. "
                    "Bot will monitor and start when conditions improve."
                )

        async def on_ticker_update(current_price):
            nonlocal last_price, grid_orders_initialized, last_status_log
            try:
                if not self._running:
                    self.logger.info("Trading stopped; halting price updates.")
                    return
                
                # Run multi-timeframe analysis periodically
                if self._mtf_analyzer:
                    should_continue = await self._run_mtf_analysis()
                    if not should_continue and grid_orders_initialized:
                        # Trading paused by trend filter - just monitor
                        self.logger.debug("[MTF] Trading paused - monitoring only")
                        last_price = current_price
                        return

                account_value = self.balance_tracker.get_total_balance_value(current_price)
                self.live_trading_metrics.append((pd.Timestamp.now(), account_value, current_price))

                # Periodic status log
                current_time = time.time()
                if current_time - last_status_log >= status_log_interval:
                    fiat_balance = self.balance_tracker.balance
                    crypto_balance = self.balance_tracker.crypto_balance
                    mtf_status = ""
                    if self._mtf_analysis_result:
                        mtf_status = f" | MTF: {self._mtf_analysis_result.grid_signal.value}"
                    self.logger.info(
                        f"[STATUS] {self.trading_pair} @ ${current_price:.4f} | "
                        f"Balance: ${fiat_balance:.2f} + {crypto_balance:.4f} crypto | "
                        f"Value: ${account_value:.2f}{mtf_status}"
                    )
                    last_status_log = current_time

                grid_orders_initialized = await self._initialize_grid_orders_once(
                    current_price,
                    trigger_price,
                    grid_orders_initialized,
                    last_price,
                )

                if not grid_orders_initialized:
                    last_price = current_price
                    return

                if await self._handle_take_profit_stop_loss(current_price):
                    return

                last_price = current_price

            except Exception as e:
                self.logger.error(f"Error during ticker update: {e}", exc_info=True)

        try:
            await self.exchange_service.listen_to_ticker_updates(
                self.trading_pair,
                on_ticker_update,
                self.TICKER_REFRESH_INTERVAL,
            )

        except Exception as e:
            self.logger.error(f"Error in live/paper trading loop: {e}", exc_info=True)

        finally:
            self.logger.info("Exiting live/paper trading loop.")

    async def _run_backtest(self, trigger_price: float) -> None:
        """
        Executes the backtesting simulation based on historical OHLCV data.

        This method simulates trading using preloaded data, managing grid levels,
        executing orders, and updating account values over the timeframe.

        Args:
            trigger_price (float): The price at which grid orders are triggered.
        """
        if self.data is None:
            self.logger.error("No data available for backtesting.")
            return

        self.logger.info("Starting backtest simulation")
        self.data["account_value"] = np.nan
        self.close_prices = self.data["close"].values
        high_prices = self.data["high"].values
        low_prices = self.data["low"].values
        timestamps = self.data.index
        self.data.loc[timestamps[0], "account_value"] = self.balance_tracker.get_total_balance_value(
            price=self.close_prices[0],
        )
        grid_orders_initialized = False
        last_price = None

        for i, (current_price, high_price, low_price, timestamp) in enumerate(
            zip(self.close_prices, high_prices, low_prices, timestamps, strict=False),
        ):
            grid_orders_initialized = await self._initialize_grid_orders_once(
                current_price,
                trigger_price,
                grid_orders_initialized,
                last_price,
            )

            if not grid_orders_initialized:
                self.data.loc[timestamps[i], "account_value"] = self.balance_tracker.get_total_balance_value(
                    price=current_price,
                )
                last_price = current_price
                continue

            await self.order_manager.simulate_order_fills(high_price, low_price, timestamp)

            if await self._handle_take_profit_stop_loss(current_price):
                break

            self.data.loc[timestamp, "account_value"] = self.balance_tracker.get_total_balance_value(current_price)
            last_price = current_price

    async def _initialize_grid_orders_once(
        self,
        current_price: float,
        trigger_price: float,
        grid_orders_initialized: bool,
        last_price: float | None = None,
    ) -> bool:
        """
        Extracts configuration values for timeframe, start date, and end date.

        Returns:
            tuple: A tuple containing the timeframe, start date, and end date as strings.
        """
        if grid_orders_initialized:
            return True

        if last_price is None:
            self.logger.info(f"[INIT] First price update received: {current_price}. Waiting for next update.")
            return False

        # Get grid boundaries from price_grids list
        grid_top = max(self.grid_manager.price_grids)
        grid_bottom = min(self.grid_manager.price_grids)

        self.logger.info(
            f"[INIT] Checking trigger: price={current_price}, last_price={last_price}, "
            f"trigger={trigger_price:.2f}, grid=[{grid_bottom:.2f}-{grid_top:.2f}]"
        )

        # Check if price crossed trigger OR if price is already within the grid range
        price_crossed_trigger = last_price <= trigger_price <= current_price or last_price == trigger_price
        price_within_grid = grid_bottom <= current_price <= grid_top

        self.logger.info(f"[INIT] price_crossed_trigger={price_crossed_trigger}, price_within_grid={price_within_grid}")

        if price_crossed_trigger or price_within_grid:
            if price_within_grid and not price_crossed_trigger:
                self.logger.info(
                    f"Price {current_price} is within grid range [{grid_bottom}-{grid_top}]. Starting grid orders.",
                )
            else:
                self.logger.info(
                    f"Current price {current_price} reached trigger price {trigger_price}. Will perform initial purchase",
                )
            initial_purchase_success = await self.order_manager.perform_initial_purchase(current_price)
            if not initial_purchase_success:
                self.logger.error(
                    "Initial purchase failed. Cannot initialize grid orders without crypto balance. "
                    "Please check your balance or reduce the position size."
                )
                return False
            
            # Sync balances from exchange after initial purchase to ensure accurate state
            # This catches cases where orders were placed but parsing failed
            self.logger.info("Syncing balances from exchange after initial purchase...")
            sync_success = await self.balance_tracker.sync_balances_from_exchange(self.exchange_service)
            if not sync_success:
                self.logger.warning("Balance sync failed, proceeding with tracked balances.")
            
            # Verify we have crypto before placing grid orders
            if self.balance_tracker.crypto_balance <= 0:
                self.logger.error(
                    "No crypto balance available after initial purchase. "
                    "Cannot place sell orders. Check exchange for any executed orders."
                )
                return False
            
            # Apply volatility-based spacing adjustment if enabled
            if self._mtf_analysis_result and self.config_manager.is_volatility_spacing_enabled():
                multiplier = self._mtf_analysis_result.recommended_spacing_multiplier
                if multiplier != 1.0:
                    self.grid_manager.set_spacing_multiplier(multiplier)
                    self.logger.info(
                        f"[MTF] Applied volatility-based spacing: {multiplier:.2f}x multiplier"
                    )
            
            self.logger.info("Initial purchase done, will initialize grid orders")
            await self.order_manager.initialize_grid_orders(current_price)
            return True

        self.logger.info(
            f"Current price {current_price} did not cross trigger price {trigger_price}. Last price: {last_price}.",
        )
        return False

    def generate_performance_report(self) -> tuple[dict, list]:
        """
        Generates a performance report for the trading session.

        It evaluates the strategy's performance by analyzing
        the account value, fees, and final price over the given timeframe.

        Returns:
            tuple: A dictionary summarizing performance metrics and a list of formatted order details.
        """
        if self.trading_mode == TradingMode.BACKTEST:
            initial_price = self.close_prices[0]
            final_price = self.close_prices[-1]
            return self.trading_performance_analyzer.generate_performance_summary(
                self.data,
                initial_price,
                self.balance_tracker.get_adjusted_fiat_balance(),
                self.balance_tracker.get_adjusted_crypto_balance(),
                final_price,
                self.balance_tracker.total_fees,
            )
        else:
            if not self.live_trading_metrics:
                self.logger.warning("No account value data available for live/paper trading mode.")
                return {}, []

            live_data = pd.DataFrame(self.live_trading_metrics, columns=["timestamp", "account_value", "price"])
            live_data.set_index("timestamp", inplace=True)
            initial_price = live_data.iloc[0]["price"]
            final_price = live_data.iloc[-1]["price"]

            return self.trading_performance_analyzer.generate_performance_summary(
                live_data,
                initial_price,
                self.balance_tracker.get_adjusted_fiat_balance(),
                self.balance_tracker.get_adjusted_crypto_balance(),
                final_price,
                self.balance_tracker.total_fees,
            )

    def plot_results(self) -> None:
        """
        Plots the backtest results using the provided plotter.

        This method generates and displays visualizations of the trading
        strategy's performance during backtesting. If the bot is running
        in live or paper trading mode, plotting is not available.
        """
        if self.trading_mode == TradingMode.BACKTEST:
            self.plotter.plot_results(self.data)
        else:
            self.logger.info("Plotting is not available for live/paper trading mode.")

    async def _handle_take_profit_stop_loss(self, current_price: float) -> bool:
        """
        Handles take-profit or stop-loss events based on the current price.
        Publishes a STOP_BOT event if either condition is triggered.
        """
        tp_or_sl_triggered = await self._evaluate_tp_or_sl(current_price)
        if tp_or_sl_triggered:
            self.logger.info("Take-profit or stop-loss triggered, ending trading session.")
            await self.event_bus.publish(Events.STOP_BOT, "TP or SL hit.")
            return True
        return False

    async def _evaluate_tp_or_sl(self, current_price: float) -> bool:
        """
        Evaluates whether take-profit or stop-loss conditions are met.
        Returns True if any condition is triggered.
        """
        if self.balance_tracker.crypto_balance == 0:
            self.logger.debug("No crypto balance available; skipping TP/SL checks.")
            return False

        return await self._handle_take_profit(current_price) or await self._handle_stop_loss(current_price)

    async def _handle_take_profit(self, current_price: float) -> bool:
        """
        Handles take-profit logic and executes a TP order if conditions are met.
        Returns True if take-profit is triggered.
        """
        if (
            self.config_manager.is_take_profit_enabled()
            and current_price >= self.config_manager.get_take_profit_threshold()
        ):
            self.logger.info(f"Take-profit triggered at {current_price}. Executing TP order...")
            await self.order_manager.execute_take_profit_or_stop_loss_order(
                current_price=current_price,
                take_profit_order=True,
            )
            return True
        return False

    async def _handle_stop_loss(self, current_price: float) -> bool:
        """
        Handles stop-loss logic and executes an SL order if conditions are met.
        Returns True if stop-loss is triggered.
        """
        if (
            self.config_manager.is_stop_loss_enabled()
            and current_price <= self.config_manager.get_stop_loss_threshold()
        ):
            self.logger.info(f"Stop-loss triggered at {current_price}. Executing SL order...")
            await self.order_manager.execute_take_profit_or_stop_loss_order(
                current_price=current_price,
                stop_loss_order=True,
            )
            return True
        return False

    def get_formatted_orders(self):
        """
        Retrieves a formatted summary of all orders.

        Returns:
            list: A list of formatted orders.
        """
        return self.trading_performance_analyzer.get_formatted_orders()

    def get_mtf_analysis_status(self) -> dict | None:
        """
        Get the current multi-timeframe analysis status for dashboard/API.
        
        Returns:
            Dictionary with MTF analysis details, or None if not available
        """
        if self._mtf_analysis_result is None:
            return None
        
        result = self._mtf_analysis_result
        return {
            "enabled": self._mtf_analyzer is not None,
            "primary_trend": result.primary_trend,
            "trend_alignment": result.trend_alignment,
            "market_condition": result.market_condition.value,
            "grid_signal": result.grid_signal.value,
            "spacing_multiplier": result.recommended_spacing_multiplier,
            "recommended_bias": result.recommended_bias,
            "range_valid": result.range_valid,
            "suggested_range": {
                "bottom": result.suggested_range[0],
                "top": result.suggested_range[1],
            } if result.suggested_range[0] > 0 else None,
            "confidence": result.confidence,
            "trading_paused": self._trading_paused_by_trend,
            "last_analysis_time": self._last_mtf_analysis_time,
            "warnings": result.warnings,
            "recommendations": result.recommendations,
            "timeframe_details": {
                tf_name: {
                    "timeframe": analysis.timeframe,
                    "trend": analysis.trend,
                    "trend_strength": round(analysis.trend_strength, 1),
                    "rsi": round(analysis.rsi, 1),
                    "atr_percent": round(analysis.atr_percent, 2),
                    "volatility_percentile": round(analysis.volatility_percentile, 1),
                    "is_ranging": analysis.is_ranging,
                    "support": round(analysis.support_level, 4),
                    "resistance": round(analysis.resistance_level, 4),
                }
                for tf_name, analysis in result.analysis_details.items()
            } if result.analysis_details else {},
        }

"""
Rotation Bot Integration - Connects ProfitRotationManager with GridTradingBot.

This module acts as the glue between the profit rotation engine and the
existing grid trading bot, coordinating position exits, pair switches,
and grid reconfigurations.
"""

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from config.config_manager import ConfigManager
    from core.bot_management.event_bus import EventBus
    from core.bot_management.grid_trading_bot import GridTradingBot
    from core.bot_management.profit_rotation_manager import ProfitRotationManager


class RotationBotIntegration:
    """
    Coordinates profit rotation with grid trading bot operations.

    Responsibilities:
    - Listen for rotation events
    - Update bot configuration for new pairs
    - Restart grid with new pair when rotation occurs
    - Sync position data between rotation manager and bot
    """

    def __init__(
        self,
        bot: "GridTradingBot",
        rotation_manager: "ProfitRotationManager",
        config_manager: "ConfigManager",
        event_bus: "EventBus",
    ):
        self.bot = bot
        self.rotation_manager = rotation_manager
        self.config_manager = config_manager
        self.event_bus = event_bus
        self.logger = logging.getLogger(self.__class__.__name__)

        # Subscribe to rotation events
        self.event_bus.subscribe("profit_rotation_new_entry", self._handle_new_entry)
        self.event_bus.subscribe(
            "profit_rotation_completed", self._handle_rotation_completed
        )

        # Track bot state
        self.active = False
        self.current_pair = None

    async def start(self, initial_pair: str, initial_balance: float):
        """
        Start integrated bot with profit rotation.

        Args:
            initial_pair: Initial trading pair
            initial_balance: Initial capital
        """
        self.logger.info(
            f"Starting rotation-enabled bot: {initial_pair} with ${initial_balance:.2f}"
        )

        self.current_pair = initial_pair
        self.active = True

        # Start rotation manager monitoring
        await self.rotation_manager.start(initial_pair, initial_balance)

        # Initialize bot (but don't start trading yet - grid will be created separately)
        await self.bot.initialize()

        self.logger.info("✅ Rotation integration active")

    async def stop(self):
        """Stop the integrated bot and rotation manager."""
        self.logger.info("Stopping rotation integration...")
        self.active = False

        # Stop rotation manager
        await self.rotation_manager.stop()

        # Stop bot
        if hasattr(self.bot, "stop"):
            await self.bot.stop()

        self.logger.info("Rotation integration stopped")

    async def _handle_new_entry(self, event_data: dict):
        """
        Handle new entry event from rotation manager.

        This is called after a profitable exit when entering a new pair.
        """
        new_pair = event_data.get("pair")
        capital = event_data.get("capital")

        self.logger.info(f"🎯 New entry triggered: {new_pair} with ${capital:.2f}")

        try:
            # Step 1: Update bot configuration with new pair
            base, quote = new_pair.split("/")
            self.config_manager.config["pair"]["base_currency"] = base
            self.config_manager.config["pair"]["quote_currency"] = quote

            # Step 2: Reconfigure grid range for new pair
            await self._auto_configure_grid_range(new_pair)

            # Step 3: Update bot's trading pair
            self.bot.trading_pair = new_pair
            self.current_pair = new_pair

            # Step 4: Restart grid trading on new pair
            # Cancel existing grid orders
            await self._cancel_all_orders()

            # Give exchange a moment to process cancellations
            await asyncio.sleep(2)

            # Create new grid for new pair
            await self._create_new_grid(new_pair)

            self.logger.info(f"✅ Successfully entered {new_pair}")

        except Exception as e:
            self.logger.error(f"Error handling new entry: {e}", exc_info=True)
            # Notify user of failure
            await self.event_bus.publish(
                "rotation_entry_failed",
                {"pair": new_pair, "error": str(e)},
            )

    async def _handle_rotation_completed(self, event_data: dict):
        """Handle rotation completion event (for logging/notifications)."""
        from_pair = event_data.get("from_pair")
        to_pair = event_data.get("to_pair")
        profit = event_data.get("profit")
        profit_percent = event_data.get("profit_percent")

        message = (
            f"💰 ROTATION COMPLETE\n"
            f"From: {from_pair} → To: {to_pair}\n"
            f"Profit: ${profit:.2f} ({profit_percent:+.2f}%)"
        )

        self.logger.info(message)

        # Send notification if enabled
        if self.config_manager.config.get("notifications", {}).get("enabled"):
            await self.event_bus.publish(
                "notification",
                {
                    "title": "Profit Rotation Complete",
                    "message": message,
                    "level": "success",
                },
            )

    async def _cancel_all_orders(self):
        """Cancel all open orders for current pair."""
        if not self.current_pair:
            return

        try:
            open_orders = await self.bot.exchange_service.fetch_open_orders(
                self.current_pair
            )
            self.logger.info(
                f"Cancelling {len(open_orders)} orders for {self.current_pair}"
            )

            for order in open_orders:
                try:
                    await self.bot.exchange_service.cancel_order(
                        order["id"], self.current_pair
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to cancel order {order['id']}: {e}")

            await asyncio.sleep(1)  # Let cancellations process

        except Exception as e:
            self.logger.error(f"Error cancelling orders: {e}")

    async def _auto_configure_grid_range(self, pair: str):
        """
        Automatically configure grid range for new pair based on current price.

        Uses a percentage-based range around current price.
        """
        try:
            # Fetch current price
            ticker = await self.bot.exchange_service.fetch_ticker(pair)
            current_price = ticker.get("last", 0.0)

            if current_price <= 0:
                raise ValueError(f"Invalid price for {pair}: {current_price}")

            # Calculate range (±15% from current price by default)
            range_percent = 0.15  # 15% each side
            bottom = current_price * (1 - range_percent)
            top = current_price * (1 + range_percent)

            # Update config
            self.config_manager.config["grid_strategy"]["range"]["bottom"] = round(
                bottom, 4
            )
            self.config_manager.config["grid_strategy"]["range"]["top"] = round(top, 4)

            self.logger.info(
                f"Auto-configured grid range for {pair}: "
                f"${bottom:.4f} - ${top:.4f} (current: ${current_price:.4f})"
            )

        except Exception as e:
            self.logger.error(f"Error auto-configuring grid range: {e}")
            raise

    async def _create_new_grid(self, pair: str):
        """
        Create new grid for the specified pair.

        This triggers the bot's grid creation logic.
        """
        try:
            self.logger.info(f"Creating new grid for {pair}...")

            # Reinitialize grid manager with new pair/range
            if hasattr(self.bot, "grid_manager"):
                # Recreate grid levels
                await self.bot.grid_manager.initialize()

            # Restart order management
            if hasattr(self.bot, "order_manager"):
                await self.bot.order_manager.place_initial_grid_orders(pair)

            self.logger.info(f"✅ Grid created for {pair}")

        except Exception as e:
            self.logger.error(f"Error creating new grid: {e}", exc_info=True)
            raise

    def get_status(self) -> dict:
        """Get integration status."""
        return {
            "active": self.active,
            "current_pair": self.current_pair,
            "rotation_manager_status": self.rotation_manager.get_status(),
        }

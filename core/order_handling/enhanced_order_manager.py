"""
Enhanced Order Manager - Adds retry logic and better error handling.
"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from core.order_handling.order_manager import OrderManager
from core.order_handling.order import Order, OrderSide, OrderStatus
from core.order_handling.exceptions import OrderExecutionFailedError
from core.bot_management.notification.notification_content import NotificationType


class EnhancedOrderManager(OrderManager):
    """
    Extended order manager with automatic retry logic for cancelled/failed orders.
    """

    MAX_RETRIES = 3
    RETRY_DELAY_SECONDS = 5

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.retry_counts: dict[str, int] = {}  # Track retry attempts per order

    async def _on_order_cancelled(self, order: Order) -> None:
        """
        Enhanced handler for cancelled orders with automatic retry logic.

        Args:
            order: The cancelled Order instance.
        """
        grid_level = self.order_book.get_grid_level_for_order(order)

        if not grid_level:
            self.logger.warning(
                f"Cannot retry cancelled order {order.id} - no grid level found"
            )
            await self.notification_handler.async_send_notification(
                NotificationType.ORDER_CANCELLED,
                order_details=str(order),
            )
            return

        # Check retry count
        retry_count = self.retry_counts.get(order.id, 0)

        if retry_count >= self.MAX_RETRIES:
            self.logger.error(
                f"Order {order.id} cancelled after {retry_count} retries. "
                f"Giving up on grid level {grid_level.price}"
            )
            await self.notification_handler.async_send_notification(
                NotificationType.ORDER_FAILED,
                error_details=f"Order cancelled after {retry_count} retries at grid level {grid_level.price}",
            )
            return

        # Increment retry count
        self.retry_counts[order.id] = retry_count + 1

        # Calculate exponential backoff delay
        delay = self._get_exponential_backoff_delay(retry_count)

        self.logger.warning(
            f"Order {order.id} cancelled (attempt {retry_count + 1}/{self.MAX_RETRIES}). "
            f"Retrying in {delay}s..."
        )

        # Wait before retrying
        await asyncio.sleep(delay)

        # Retry placing the order
        try:
            await self._retry_order_placement(grid_level, order.side, order.quantity, order.price)

            self.logger.info(
                f"Successfully retried order at grid level {order.price} "
                f"(attempt {retry_count + 1})"
            )

        except Exception as e:
            self.logger.error(
                f"Failed to retry order at grid level {order.price}: {e}",
                exc_info=True,
            )

            # If this was the last retry, notify
            if retry_count + 1 >= self.MAX_RETRIES:
                await self.notification_handler.async_send_notification(
                    NotificationType.ORDER_FAILED,
                    error_details=f"Final retry failed for grid level {grid_level.price}: {e}",
                )

    def _get_exponential_backoff_delay(self, retry_count: int) -> int:
        """
        Calculate exponential backoff delay.

        Args:
            retry_count: Current retry attempt (0-indexed)

        Returns:
            Delay in seconds
        """
        return min(self.RETRY_DELAY_SECONDS * (2**retry_count), 60)  # Max 60 seconds

    async def _retry_order_placement(
        self,
        grid_level,
        side: OrderSide,
        quantity: float,
        price: float,
    ) -> Optional[Order]:
        """
        Retry placing an order at a grid level.

        Args:
            grid_level: GridLevel instance
            side: Buy or Sell
            quantity: Order quantity
            price: Order price

        Returns:
            New Order instance if successful, None otherwise
        """
        try:
            # Validate balance before retry
            if side == OrderSide.BUY:
                adjusted_quantity = self.order_validator.adjust_and_validate_buy_quantity(
                    balance=self.balance_tracker.balance,
                    order_quantity=quantity,
                    price=price,
                )
            else:
                adjusted_quantity = self.order_validator.adjust_and_validate_sell_quantity(
                    crypto_balance=self.balance_tracker.crypto_balance,
                    order_quantity=quantity,
                )

            # Place the order
            self.logger.info(
                f"Retrying {side.value} order at grid level {price} "
                f"for {adjusted_quantity} {self.trading_pair}"
            )

            order = await self.order_execution_strategy.execute_limit_order(
                side,
                self.trading_pair,
                adjusted_quantity,
                price,
            )

            if order is None:
                self.logger.error(f"Retry failed: No order returned for {price}")
                return None

            # Update tracking
            if side == OrderSide.BUY:
                self.balance_tracker.reserve_funds_for_buy(adjusted_quantity * price)
            else:
                self.balance_tracker.reserve_funds_for_sell(adjusted_quantity)

            self.grid_manager.mark_order_pending(grid_level, order)
            self.order_book.add_order(order, grid_level)

            # Clear retry count on success
            if order.id in self.retry_counts:
                del self.retry_counts[order.id]

            return order

        except OrderExecutionFailedError as e:
            self.logger.error(f"Order execution failed during retry: {e}")
            raise

        except Exception as e:
            self.logger.error(f"Unexpected error during order retry: {e}", exc_info=True)
            raise

    def get_retry_stats(self) -> dict:
        """Get statistics about order retries."""
        return {
            "active_retries": len(self.retry_counts),
            "max_retries_allowed": self.MAX_RETRIES,
            "orders_being_retried": list(self.retry_counts.keys()),
        }

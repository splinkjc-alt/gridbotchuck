"""
Paper Trading Order Execution Strategy

Simulates order execution without placing real trades.
Uses real market prices but keeps track of simulated positions locally.
Perfect for beta testing without risking real money.
"""

import logging
import time

from ..order import Order, OrderSide, OrderStatus, OrderType
from .order_execution_strategy_interface import OrderExecutionStrategyInterface


class PaperOrderExecutionStrategy(OrderExecutionStrategyInterface):
    """
    Paper trading execution - simulates trades without real money.

    Features:
    - Simulates order placement with realistic order IDs
    - Tracks simulated orders in memory
    - Limit orders fill when price crosses (simulated)
    - Market orders fill immediately at current price
    """

    def __init__(self, exchange_service=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange_service = exchange_service  # For fetching real prices
        self._simulated_orders: dict[str, Order] = {}
        self._order_counter = 0
        self.logger.info("PAPER TRADING MODE - No real trades will be executed")

    def _generate_order_id(self) -> str:
        """Generate a unique paper trading order ID."""
        self._order_counter += 1
        return f"paper-{int(time.time())}-{self._order_counter:04d}"

    async def execute_market_order(
        self,
        order_side: OrderSide,
        pair: str,
        quantity: float,
        price: float,
    ) -> Order | None:
        """
        Simulate a market order - fills immediately at given price.
        """
        order_id = self._generate_order_id()
        timestamp = int(time.time() * 1000)

        order = Order(
            identifier=order_id,
            status=OrderStatus.CLOSED,  # Market orders fill immediately
            order_type=OrderType.MARKET,
            side=order_side,
            price=price,
            average=price,
            amount=quantity,
            filled=quantity,
            remaining=0,
            timestamp=timestamp,
            datetime=time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            last_trade_timestamp=timestamp,
            symbol=pair,
            time_in_force="GTC",
        )

        self._simulated_orders[order_id] = order

        side_str = "BUY" if order_side == OrderSide.BUY else "SELL"
        self.logger.info(f"PAPER MARKET {side_str} {quantity:.6f} {pair} @ ${price:.4f} (Order: {order_id})")

        return order

    async def execute_limit_order(
        self,
        order_side: OrderSide,
        pair: str,
        quantity: float,
        price: float,
    ) -> Order | None:
        """
        Simulate a limit order - stays open until price crosses.
        """
        order_id = self._generate_order_id()
        timestamp = int(time.time() * 1000)

        order = Order(
            identifier=order_id,
            status=OrderStatus.OPEN,
            order_type=OrderType.LIMIT,
            side=order_side,
            price=price,
            average=price,
            amount=quantity,
            filled=0,
            remaining=quantity,
            timestamp=timestamp,
            datetime=time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            last_trade_timestamp=timestamp,
            symbol=pair,
            time_in_force="GTC",
        )

        self._simulated_orders[order_id] = order

        side_str = "BUY" if order_side == OrderSide.BUY else "SELL"
        self.logger.info(f"PAPER LIMIT {side_str} {quantity:.6f} {pair} @ ${price:.4f} (Order: {order_id})")

        return order

    async def get_order(
        self,
        order_id: str,
        pair: str,
    ) -> Order | None:
        """
        Get simulated order status.
        """
        if order_id in self._simulated_orders:
            return self._simulated_orders[order_id]

        # Return a placeholder if not found
        return None

    async def cancel_order(
        self,
        order_id: str,
        pair: str,
    ) -> bool:
        """
        Cancel a simulated order.
        """
        if order_id in self._simulated_orders:
            order = self._simulated_orders[order_id]
            order.status = OrderStatus.CANCELED
            self.logger.info(f"PAPER Order cancelled: {order_id}")
            return True
        return False

    def check_and_fill_orders(self, current_price: float, pair: str) -> list[Order]:
        """
        Check if any limit orders should be filled based on current price.
        Call this when price updates to simulate order fills.

        Returns list of orders that were filled.
        """
        filled_orders = []

        for _order_id, order in self._simulated_orders.items():
            if order.status != OrderStatus.OPEN:
                continue
            if order.symbol != pair:
                continue

            should_fill = False

            # Buy limit fills when price drops to or below limit price
            if (order.side == OrderSide.BUY and current_price <= order.price) or (
                order.side == OrderSide.SELL and current_price >= order.price
            ):
                should_fill = True

            if should_fill:
                order.status = OrderStatus.CLOSED
                order.filled = order.amount
                order.remaining = 0
                order.average = order.price  # Fill at limit price
                order.last_trade_timestamp = int(time.time() * 1000)
                filled_orders.append(order)

                side_str = "BUY" if order.side == OrderSide.BUY else "SELL"
                self.logger.info(f"PAPER ORDER FILLED {side_str} {order.amount:.6f} {pair} @ ${order.price:.4f}")

        return filled_orders

    def get_open_orders(self, pair: str | None = None) -> list[Order]:
        """Get all open simulated orders."""
        orders = []
        for order in self._simulated_orders.values():
            if order.status == OrderStatus.OPEN and (pair is None or order.symbol == pair):
                orders.append(order)
        return orders

    def get_all_orders(self) -> dict[str, Order]:
        """Get all simulated orders."""
        return self._simulated_orders.copy()

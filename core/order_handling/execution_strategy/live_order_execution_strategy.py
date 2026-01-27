import asyncio
import logging

from core.services.exceptions import DataFetchError
from core.services.exchange_interface import ExchangeInterface

from ..exceptions import OrderExecutionFailedError
from ..order import Order, OrderSide, OrderStatus, OrderType
from .order_execution_strategy_interface import OrderExecutionStrategyInterface


class LiveOrderExecutionStrategy(OrderExecutionStrategyInterface):
    def __init__(
        self,
        exchange_service: ExchangeInterface,
        max_retries: int = 1,  # Changed from 3 - market orders fill immediately
        retry_delay: int = 1,
        max_slippage: float = 0.01,
    ) -> None:
        self.exchange_service = exchange_service
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_slippage = max_slippage
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute_market_order(
        self,
        order_side: OrderSide,
        pair: str,
        quantity: float,
        price: float,
    ) -> Order | None:
        """Execute a market order. Market orders typically fill immediately."""
        try:
            self.logger.info(
                f"Placing market {order_side.name} order for {quantity} {pair} at ~${price}"
            )

            raw_order = await self.exchange_service.place_order(
                pair,
                OrderType.MARKET.value.lower(),
                order_side.name.lower(),
                quantity,
                price,
            )

            # Log raw response for debugging
            order_id = raw_order.get("id") if raw_order else None
            self.logger.info(
                f"Exchange response - Order ID: {order_id}, Status: {raw_order.get('status') if raw_order else 'None'}"
            )

            if not raw_order:
                self.logger.error("Exchange returned empty response for order")
                raise OrderExecutionFailedError(
                    "Exchange returned empty response",
                    order_side,
                    OrderType.MARKET,
                    pair,
                    quantity,
                    price,
                )

            order_result = await self._parse_order_result(raw_order)

            # Market orders should fill immediately
            if order_result.status == OrderStatus.CLOSED:
                self.logger.info(
                    f"Market order {order_result.identifier} filled successfully at ${order_result.average or order_result.price}"
                )
                return order_result

            # If somehow still open, wait briefly and check again
            if order_result.status == OrderStatus.OPEN:
                self.logger.info(
                    f"Order {order_result.identifier} still open, waiting for fill..."
                )
                await asyncio.sleep(2)

                try:
                    updated_order = await self.exchange_service.fetch_order(
                        order_result.identifier, pair
                    )
                    if updated_order:
                        order_result = await self._parse_order_result(updated_order)
                        if order_result.status == OrderStatus.CLOSED:
                            self.logger.info(
                                f"Order {order_result.identifier} now filled"
                            )
                            return order_result
                except Exception as e:
                    self.logger.warning(f"Could not recheck order status: {e}")

            # Return whatever we got - the order was placed
            self.logger.info(f"Returning order with status: {order_result.status}")
            return order_result

        except OrderExecutionFailedError:
            raise
        except Exception as e:
            self.logger.error(f"Error executing market order: {e!s}")
            raise OrderExecutionFailedError(
                f"Failed to execute market order: {e}",
                order_side,
                OrderType.MARKET,
                pair,
                quantity,
                price,
            ) from e

    async def execute_limit_order(
        self,
        order_side: OrderSide,
        pair: str,
        quantity: float,
        price: float,
    ) -> Order | None:
        try:
            raw_order = await self.exchange_service.place_order(
                pair,
                OrderType.LIMIT.value.lower(),
                order_side.name.lower(),
                quantity,
                price,
            )
            order_result = await self._parse_order_result(raw_order)
            return order_result

        except DataFetchError as e:
            self.logger.error(f"DataFetchError during order execution for {pair} - {e}")
            raise OrderExecutionFailedError(
                f"Failed to execute Limit order on {pair}: {e}",
                order_side,
                OrderType.LIMIT,
                pair,
                quantity,
                price,
            ) from e

        except Exception as e:
            self.logger.error(f"Unexpected error in execute_limit_order: {e}")
            raise OrderExecutionFailedError(
                f"Unexpected error during order execution: {e}",
                order_side,
                OrderType.LIMIT,
                pair,
                quantity,
                price,
            ) from e

    async def get_order(
        self,
        order_id: str,
        pair: str,
    ) -> Order | None:
        try:
            raw_order = await self.exchange_service.fetch_order(order_id, pair)
            order_result = await self._parse_order_result(raw_order)
            return order_result

        except DataFetchError as e:
            raise e

        except Exception as e:
            raise DataFetchError(
                f"Unexpected error during order status retrieval: {e!s}"
            ) from e

    async def _parse_order_result(
        self,
        raw_order_result: dict,
    ) -> Order:
        """
        Parses the raw order response from the exchange into an Order object.

        Args:
            raw_order_result: The raw response from the exchange.

        Returns:
            An Order object with standardized fields.
        """
        # Safely get values, handling None explicitly (dict.get returns None if key exists but value is None)
        status_str = raw_order_result.get("status") or "unknown"
        order_type_str = raw_order_result.get("type") or "unknown"
        side_str = raw_order_result.get("side") or "unknown"

        return Order(
            identifier=raw_order_result.get("id") or "",
            status=OrderStatus(status_str.lower()),
            order_type=OrderType(order_type_str.lower()),
            side=OrderSide(side_str.lower()),
            price=raw_order_result.get("price") or 0.0,
            average=raw_order_result.get("average"),
            amount=raw_order_result.get("amount") or 0.0,
            filled=raw_order_result.get("filled") or 0.0,
            remaining=raw_order_result.get("remaining") or 0.0,
            timestamp=raw_order_result.get("timestamp") or 0,
            datetime=raw_order_result.get("datetime"),
            last_trade_timestamp=raw_order_result.get("lastTradeTimestamp"),
            symbol=raw_order_result.get("symbol") or "",
            time_in_force=raw_order_result.get("timeInForce"),
            trades=raw_order_result.get("trades") or [],
            fee=raw_order_result.get("fee"),
            cost=raw_order_result.get("cost"),
            info=raw_order_result.get("info") or raw_order_result,
        )

    async def _adjust_price(
        self,
        order_side: OrderSide,
        price: float,
        attempt: int,
    ) -> float:
        adjustment = self.max_slippage / self.max_retries * attempt
        return (
            price * (1 + adjustment)
            if order_side == OrderSide.BUY
            else price * (1 - adjustment)
        )

    async def _handle_partial_fill(
        self,
        order: Order,
        pair: str,
    ) -> dict | None:
        self.logger.info(
            f"Order partially filled with {order.filled}. Attempting to cancel and retry full quantity."
        )

        if not await self._retry_cancel_order(order.identifier, pair):
            self.logger.error(
                f"Unable to cancel partially filled order {order.identifier} after retries."
            )

    async def _retry_cancel_order(
        self,
        order_id: str,
        pair: str,
    ) -> bool:
        for cancel_attempt in range(self.max_retries):
            try:
                cancel_result = await self.exchange_service.cancel_order(order_id, pair)

                if cancel_result["status"] == "canceled":
                    self.logger.info(f"Successfully canceled order {order_id}.")
                    return True

                self.logger.warning(
                    f"Cancel attempt {cancel_attempt + 1} for order {order_id} failed."
                )

            except Exception as e:
                self.logger.warning(
                    f"Error during cancel attempt {cancel_attempt + 1} for order {order_id}: {e!s}"
                )

            await asyncio.sleep(self.retry_delay)
        return False

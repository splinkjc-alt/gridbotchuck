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
        max_retries: int = 3,
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
        last_order_id = None
        
        for attempt in range(self.max_retries):
            try:
                # If we have a previous order ID from a failed parse, check its status first
                if last_order_id:
                    try:
                        self.logger.info(f"Checking status of previous order {last_order_id} before retry...")
                        order_status = await self.exchange_service.fetch_order_status(last_order_id, pair)
                        if order_status:
                            parsed_order = await self._parse_order_result(order_status)
                            if parsed_order.status == OrderStatus.CLOSED:
                                self.logger.info(f"Previous order {last_order_id} was actually filled. Returning it.")
                                return parsed_order
                            elif parsed_order.status == OrderStatus.OPEN:
                                self.logger.info(f"Previous order {last_order_id} is still open. Waiting for fill...")
                                await self._handle_partial_fill(parsed_order, pair)
                                continue
                    except Exception as status_error:
                        self.logger.warning(f"Could not check previous order status: {status_error}")
                
                raw_order = await self.exchange_service.place_order(
                    pair,
                    OrderType.MARKET.value.lower(),
                    order_side.name.lower(),
                    quantity,
                    price,
                )
                
                # Store order ID in case parsing fails
                if raw_order and isinstance(raw_order, dict):
                    last_order_id = raw_order.get("id")
                
                order_result = await self._parse_order_result(raw_order)

                if order_result.status == OrderStatus.CLOSED:
                    return order_result  # Order fully filled

                elif order_result.status == OrderStatus.OPEN:
                    await self._handle_partial_fill(order_result, pair)

                await asyncio.sleep(self.retry_delay)
                self.logger.info(f"Retrying order. Attempt {attempt + 1}/{self.max_retries}.")
                price = await self._adjust_price(order_side, price, attempt)

            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed with error: {e!s}")
                
                # If we got an order ID before the error, don't retry placing a new order
                # Instead, try to check if the order was actually placed
                if last_order_id:
                    self.logger.warning(
                        f"Order may have been placed (ID: {last_order_id}). "
                        "Will check status before retrying."
                    )
                
                await asyncio.sleep(self.retry_delay)

        raise OrderExecutionFailedError(
            "Failed to execute Market order after maximum retries.",
            order_side,
            OrderType.MARKET,
            pair,
            quantity,
            price,
        )

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
            raise DataFetchError(f"Unexpected error during order status retrieval: {e!s}") from e

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
        return price * (1 + adjustment) if order_side == OrderSide.BUY else price * (1 - adjustment)

    async def _handle_partial_fill(
        self,
        order: Order,
        pair: str,
    ) -> dict | None:
        self.logger.info(f"Order partially filled with {order.filled}. Attempting to cancel and retry full quantity.")

        if not await self._retry_cancel_order(order.identifier, pair):
            self.logger.error(f"Unable to cancel partially filled order {order.identifier} after retries.")

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

                self.logger.warning(f"Cancel attempt {cancel_attempt + 1} for order {order_id} failed.")

            except Exception as e:
                self.logger.warning(f"Error during cancel attempt {cancel_attempt + 1} for order {order_id}: {e!s}")

            await asyncio.sleep(self.retry_delay)
        return False

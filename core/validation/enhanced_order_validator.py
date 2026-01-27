"""
Enhanced Order Validator - Adds position size limits and risk checks.
"""

import logging

from core.validation.order_validator import OrderValidator


class PositionSizeTooLargeError(Exception):
    """Raised when order size exceeds maximum allowed percentage of portfolio."""

    pass


class EnhancedOrderValidator(OrderValidator):
    """
    Extended validator with position size limits and advanced risk checks.
    """

    def __init__(
        self,
        tolerance: float = 1e-6,
        threshold_ratio: float = 0.5,
        max_position_size_percent: float = 40.0,  # Max 40% of portfolio per order
        min_order_value: float = 5.0,  # Minimum order value in USD
    ):
        """
        Initialize enhanced validator.

        Args:
            tolerance: Minimum precision tolerance
            threshold_ratio: Threshold for insufficient balance errors
            max_position_size_percent: Maximum % of portfolio for single order
            min_order_value: Minimum order value in USD
        """
        super().__init__(tolerance, threshold_ratio)
        self.max_position_size_percent = max_position_size_percent
        self.min_order_value = min_order_value
        self.logger = logging.getLogger(self.__class__.__name__)

    def adjust_and_validate_buy_quantity(
        self,
        balance: float,
        order_quantity: float,
        price: float,
        total_portfolio_value: float | None = None,
    ) -> float:
        """
        Enhanced buy quantity validation with position size limits.

        Args:
            balance: Available fiat balance
            order_quantity: Requested buy quantity
            price: Asset price
            total_portfolio_value: Total portfolio value for position sizing (optional)

        Returns:
            Adjusted and validated buy order quantity

        Raises:
            PositionSizeTooLargeError: If order exceeds position size limit
            InsufficientBalanceError: If balance is insufficient
            InvalidOrderQuantityError: If quantity is invalid
        """
        # First do standard validation
        adjusted_quantity = super().adjust_and_validate_buy_quantity(
            balance, order_quantity, price
        )

        order_value = adjusted_quantity * price

        # Check minimum order value
        if order_value < self.min_order_value:
            self.logger.warning(
                f"Order value ${order_value:.2f} below minimum ${self.min_order_value:.2f}. "
                "Order will likely be rejected by exchange."
            )
            # Don't raise - let exchange reject if needed
            # This allows for partial fills in low-capital scenarios

        # Check position size limit if portfolio value provided
        if total_portfolio_value and total_portfolio_value > 0:
            position_percent = (order_value / total_portfolio_value) * 100

            if position_percent > self.max_position_size_percent:
                # Reduce order size to fit within limit
                max_order_value = total_portfolio_value * (
                    self.max_position_size_percent / 100
                )
                adjusted_quantity = max_order_value / price

                self.logger.warning(
                    f"Order size reduced from {order_quantity:.6f} to {adjusted_quantity:.6f} "
                    f"to stay within {self.max_position_size_percent}% position limit"
                )

                # Revalidate after adjustment
                if (
                    adjusted_quantity <= 0
                    or (adjusted_quantity * price) < self.min_order_value
                ):
                    raise PositionSizeTooLargeError(
                        f"Cannot create valid order within position size limit. "
                        f"Portfolio: ${total_portfolio_value:.2f}, "
                        f"Max position: {self.max_position_size_percent}%"
                    )

        return adjusted_quantity

    def adjust_and_validate_sell_quantity(
        self,
        crypto_balance: float,
        order_quantity: float,
        price: float | None = None,
        total_portfolio_value: float | None = None,
    ) -> float:
        """
        Enhanced sell quantity validation with position size limits.

        Args:
            crypto_balance: Available crypto balance
            order_quantity: Requested sell quantity
            price: Asset price (for value checks)
            total_portfolio_value: Total portfolio value (optional)

        Returns:
            Adjusted and validated sell order quantity
        """
        # Do standard validation
        adjusted_quantity = super().adjust_and_validate_sell_quantity(
            crypto_balance, order_quantity
        )

        # Check minimum order value if price provided
        if price and (adjusted_quantity * price) < self.min_order_value:
            self.logger.warning(
                f"Sell order value ${adjusted_quantity * price:.2f} "
                f"below minimum ${self.min_order_value:.2f}"
            )

        # Check position size if both price and portfolio value provided
        if price and total_portfolio_value and total_portfolio_value > 0:
            order_value = adjusted_quantity * price
            position_percent = (order_value / total_portfolio_value) * 100

            if position_percent > self.max_position_size_percent:
                # Reduce sell quantity
                max_order_value = total_portfolio_value * (
                    self.max_position_size_percent / 100
                )
                adjusted_quantity = max_order_value / price

                self.logger.warning(
                    f"Sell order reduced to stay within {self.max_position_size_percent}% limit"
                )

        return adjusted_quantity

    def validate_portfolio_allocation(
        self,
        num_pairs: int,
        total_balance: float,
        min_balance_per_pair: float,
    ) -> tuple[bool, str]:
        """
        Validate multi-pair portfolio allocation.

        Args:
            num_pairs: Number of pairs to trade
            total_balance: Total available balance
            min_balance_per_pair: Minimum balance required per pair

        Returns:
            (is_valid, message) tuple
        """
        required_balance = num_pairs * min_balance_per_pair

        if total_balance < required_balance:
            return (
                False,
                f"Insufficient balance for {num_pairs} pairs. "
                f"Need ${required_balance:.2f}, have ${total_balance:.2f}. "
                f"Minimum ${min_balance_per_pair:.2f} per pair required.",
            )

        # Check if each pair would get enough
        balance_per_pair = total_balance / num_pairs

        if balance_per_pair < min_balance_per_pair:
            suggested_pairs = int(total_balance / min_balance_per_pair)
            return (
                False,
                f"Balance ${total_balance:.2f} only supports {suggested_pairs} pairs "
                f"with minimum ${min_balance_per_pair:.2f} each",
            )

        # Check if we'd have meaningful position sizes
        if balance_per_pair < self.min_order_value * 3:  # At least 3 orders per pair
            return (
                False,
                f"Each pair would only get ${balance_per_pair:.2f}, "
                f"not enough for meaningful grid trading (need ~${self.min_order_value * 3:.2f} minimum)",
            )

        return (True, f"Valid allocation: ${balance_per_pair:.2f} per pair")

    def get_recommended_grid_count(
        self,
        balance_per_pair: float,
        price_range_percent: float = 20.0,
    ) -> int:
        """
        Recommend number of grid levels based on available balance.

        Args:
            balance_per_pair: Balance allocated to this pair
            price_range_percent: Expected price range %

        Returns:
            Recommended number of grid levels
        """
        # Calculate how many orders we can afford
        max_orders = int(balance_per_pair / self.min_order_value)

        # For grid trading, use half for buy, half for sell
        grids_per_side = max_orders // 2

        # Limit to reasonable range
        recommended_grids = max(2, min(grids_per_side, 10))

        return recommended_grids

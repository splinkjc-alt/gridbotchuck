from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


class ExchangeInterface(ABC):
    @abstractmethod
    async def get_balance(self) -> dict[str, Any]:
        """Fetches the account balance, returning a dictionary with fiat and crypto balances."""
        pass

    @abstractmethod
    async def place_order(
        self,
        pair: str,
        order_side: str,
        order_type: str,
        amount: float,
        price: float | None = None,
    ) -> dict[str, str | float]:
        """Places an order, returning a dictionary with order details including id and status."""
        pass

    @abstractmethod
    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """
        Fetches historical OHLCV data as a list of dictionaries, each containing open, high, low,
        close, and volume for the specified time period.
        """
        pass

    @abstractmethod
    async def fetch_ohlcv_simple(
        self,
        pair: str,
        timeframe: str,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Fetches recent OHLCV candles without date range (simpler API for market scanning).

        Args:
            pair: Trading pair (e.g., 'BTC/USD')
            timeframe: Candle timeframe (e.g., '15m', '1h')
            limit: Number of candles to fetch

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        pass

    @abstractmethod
    async def get_available_pairs(
        self,
        quote_currency: str = "USD",
    ) -> list[str]:
        """
        Gets all available trading pairs for a quote currency.

        Args:
            quote_currency: The quote currency to filter by (e.g., 'USD', 'USDT')

        Returns:
            List of trading pair symbols (e.g., ['BTC/USD', 'ETH/USD'])
        """
        pass

    @abstractmethod
    async def get_current_price(
        self,
        pair: str,
    ) -> float:
        """Fetches the current market price for the specified trading pair."""
        pass

    @abstractmethod
    async def cancel_order(
        self,
        order_id: str,
        pair: str,
    ) -> dict[str, str | float]:
        """Attempts to cancel an order by ID, returning the result of the cancellation."""
        pass

    @abstractmethod
    async def get_exchange_status(self) -> dict:
        """Fetches current exchange status."""
        pass

    @abstractmethod
    async def close_connection(self) -> None:
        """Close current exchange connection."""
        pass

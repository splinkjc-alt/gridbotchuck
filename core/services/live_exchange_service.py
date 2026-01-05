import asyncio
from collections.abc import Callable
import logging
import os
from typing import Any

from ccxt.base.errors import BaseError, ExchangeError, NetworkError, OrderNotFound
import ccxt.pro as ccxtpro
import pandas as pd

from config.config_manager import ConfigManager

from .exceptions import (
    DataFetchError,
    MissingEnvironmentVariableError,
    OrderCancellationError,
    UnsupportedExchangeError,
)
from .exchange_interface import ExchangeInterface


class LiveExchangeService(ExchangeInterface):
    def __init__(
        self,
        config_manager: ConfigManager,
        is_paper_trading_activated: bool,
    ):
        self.config_manager = config_manager
        self.is_paper_trading_activated = is_paper_trading_activated
        self.logger = logging.getLogger(self.__class__.__name__)
        self.exchange_name = self.config_manager.get_exchange_name()
        self.api_key = self._get_env_variable("EXCHANGE_API_KEY")
        self.secret_key = self._get_env_variable("EXCHANGE_SECRET_KEY")
        self.exchange = self._initialize_exchange()
        self.connection_active = False

    def _get_env_variable(self, key: str) -> str:
        # First try exchange-specific key (e.g., COINBASE_API_KEY, KRAKEN_API_KEY)
        # Remove "EXCHANGE_" prefix from key to avoid redundancy
        key_suffix = key.replace("EXCHANGE_", "")
        exchange_specific_key = f"{self.exchange_name.upper()}_{key_suffix}"
        value = os.getenv(exchange_specific_key)

        # Fall back to generic key (e.g., EXCHANGE_API_KEY)
        if value is None:
            value = os.getenv(key)

        if value is None:
            raise MissingEnvironmentVariableError(
                f"Missing required environment variable: {exchange_specific_key} or {key}"
            )

        # For Coinbase secret keys, convert literal \n to actual newlines
        if self.exchange_name.lower() == "coinbase" and "SECRET" in key:
            value = value.replace("\\n", "\n")

        return value

    def _initialize_exchange(self) -> None:
        try:
            exchange = getattr(ccxtpro, self.exchange_name)(
                {
                    "apiKey": self.api_key,
                    "secret": self.secret_key,
                    "enableRateLimit": True,
                    "timeout": 30000,  # 30 second timeout for API calls
                },
            )

            if self.is_paper_trading_activated:
                self._enable_sandbox_mode(exchange)
            return exchange
        except AttributeError:
            raise UnsupportedExchangeError(f"The exchange '{self.exchange_name}' is not supported.") from None

    # ...existing code...
    def _enable_sandbox_mode(self, exchange) -> None:
        if self.exchange_name == "binance":
            exchange.urls["api"] = "https://testnet.binance.vision/api"
        elif self.exchange_name == "kraken":
            # Kraken has no spot sandbox - use live API for paper trading
            # Paper trading is simulated locally, not on exchange
            self.logger.info("Kraken does not have a spot sandbox. Using live API for price data only.")
        elif self.exchange_name == "bitmex":
            exchange.urls["api"] = "https://testnet.bitmex.com"
        elif self.exchange_name == "bybit":
            exchange.set_sandbox_mode(True)
        else:
            self.logger.warning(f"No sandbox mode available for {self.exchange_name}. Running in live mode.")

    # ...existing code...

    async def _subscribe_to_ticker_updates(
        self,
        pair: str,
        on_ticker_update: Callable[[float], None],
        update_interval: float,
        max_retries: int = 5,
    ) -> None:
        self.connection_active = True
        retry_count = 0

        while self.connection_active:
            try:
                ticker = await self.exchange.watch_ticker(pair)
                current_price: float = ticker["last"]
                self.logger.info(f"Connected to WebSocket for {pair} ticker current price: {current_price}")

                if not self.connection_active:
                    break

                await on_ticker_update(current_price)
                await asyncio.sleep(update_interval)
                retry_count = 0  # Reset retry count after a successful operation

            except (NetworkError, ExchangeError, OSError) as e:
                retry_count += 1
                retry_interval = min(retry_count * 5, 60)
                self.logger.error(
                    f"Error connecting to WebSocket for {pair}: {e}. "
                    f"Retrying in {retry_interval} seconds ({retry_count}/{max_retries}).",
                )

                if retry_count >= max_retries:
                    self.logger.error("Max retries reached. Stopping WebSocket connection.")
                    self.connection_active = False
                    break

                await asyncio.sleep(retry_interval)

            except asyncio.CancelledError:
                self.logger.error(f"WebSocket subscription for {pair} was cancelled.")
                self.connection_active = False
                break

            except Exception as e:
                self.logger.error(f"WebSocket connection error: {e}. Reconnecting...")
                await asyncio.sleep(5)

            finally:
                if not self.connection_active:
                    try:
                        self.logger.info("Connection to Websocket no longer active.")
                        await self.exchange.close()

                    except Exception as e:
                        self.logger.error(f"Error while closing WebSocket connection: {e}", exc_info=True)

    async def listen_to_ticker_updates(
        self,
        pair: str,
        on_price_update: Callable[[float], None],
        update_interval: float,
    ) -> None:
        await self._subscribe_to_ticker_updates(pair, on_price_update, update_interval)

    async def close_connection(self) -> None:
        self.connection_active = False
        self.logger.info("Closing WebSocket connection...")

    async def get_balance(self) -> dict[str, Any]:
        try:
            balance = await self.exchange.fetch_balance()
            return balance

        except BaseError as e:
            raise DataFetchError(f"Error fetching balance: {e!s}") from e

    async def get_current_price(self, pair: str) -> float:
        try:
            ticker = await self.exchange.fetch_ticker(pair)
            return ticker["last"]

        except BaseError as e:
            raise DataFetchError(f"Error fetching current price: {e!s}") from e

    async def place_order(
        self,
        pair: str,
        order_type: str,
        order_side: str,
        amount: float,
        price: float | None = None,
    ) -> dict[str, str | float]:
        try:
            order = await self.exchange.create_order(pair, order_type, order_side, amount, price)
            return order

        except NetworkError as e:
            raise DataFetchError(f"Network issue occurred while placing order: {e!s}") from e

        except BaseError as e:
            raise DataFetchError(f"Error placing order: {e!s}") from e

        except Exception as e:
            raise DataFetchError(f"Unexpected error placing order: {e!s}") from e

    async def fetch_order(
        self,
        order_id: str,
        pair: str,
    ) -> dict[str, str | float]:
        try:
            return await self.exchange.fetch_order(order_id, pair)

        except NetworkError as e:
            raise DataFetchError(f"Network issue occurred while fetching order status: {e!s}") from e

        except BaseError as e:
            raise DataFetchError(f"Exchange-specific error occurred: {e!s}") from e

        except Exception as e:
            raise DataFetchError(f"Failed to fetch order status: {e!s}") from e

    async def cancel_order(
        self,
        order_id: str,
        pair: str,
    ) -> dict:
        try:
            self.logger.info(f"Attempting to cancel order {order_id} for pair {pair}")
            cancellation_result = await self.exchange.cancel_order(order_id, pair)

            if cancellation_result["status"] in ["canceled", "closed"]:
                self.logger.info(f"Order {order_id} successfully canceled.")
                return cancellation_result
            else:
                self.logger.warning(f"Order {order_id} cancellation status: {cancellation_result['status']}")
                return cancellation_result

        except OrderNotFound:
            raise OrderCancellationError(
                f"Order {order_id} not found for cancellation. It may already be completed or canceled.",
            ) from None

        except NetworkError as e:
            raise OrderCancellationError(f"Network error while canceling order {order_id}: {e!s}") from e

        except BaseError as e:
            raise OrderCancellationError(f"Exchange error while canceling order {order_id}: {e!s}") from e

        except Exception as e:
            raise OrderCancellationError(f"Unexpected error while canceling order {order_id}: {e!s}") from e

    async def get_exchange_status(self) -> dict:
        try:
            status = await self.exchange.fetch_status()
            return {
                "status": status.get("status", "unknown"),
                "updated": status.get("updated"),
                "eta": status.get("eta"),
                "url": status.get("url"),
                "info": status.get("info", "No additional info available"),
            }

        except AttributeError:
            return {"status": "unsupported", "info": "fetch_status not supported by this exchange."}

        except Exception as e:
            return {"status": "error", "info": f"Failed to fetch exchange status: {e}"}

    def fetch_ohlcv(
        self,
        pair: str,
        timeframe: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        raise NotImplementedError("fetch_ohlcv is not used in live or paper trading mode.")

    async def fetch_ohlcv_simple(
        self,
        pair: str,
        timeframe: str,
        limit: int = 100,
    ) -> pd.DataFrame:
        """
        Fetches recent OHLCV candles for market scanning.
        Uses ccxt's fetch_ohlcv with limit parameter.
        """
        try:
            # Use sync fetch_ohlcv from ccxt (not the async watch_ohlcv)
            ohlcv = await self.exchange.fetch_ohlcv(pair, timeframe, limit=limit)

            if not ohlcv or len(ohlcv) == 0:
                self.logger.warning(f"No OHLCV data returned for {pair}")
                return pd.DataFrame()

            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")

            return df

        except Exception as e:
            self.logger.error(f"Error fetching OHLCV for {pair}: {e}")
            raise DataFetchError(f"Error fetching OHLCV for {pair}: {e}") from e

    async def get_available_pairs(
        self,
        quote_currency: str = "USD",
    ) -> list[str]:
        """
        Gets all available trading pairs for a quote currency from Kraken.
        Filters for active spot markets only.
        """
        try:
            # Load markets if not already loaded
            if not self.exchange.markets:
                await self.exchange.load_markets()

            pairs = []
            for symbol, market in self.exchange.markets.items():
                # Filter for spot markets with the specified quote currency
                if market.get("quote") == quote_currency and market.get("spot", False) and market.get("active", True):
                    pairs.append(symbol)

            self.logger.info(f"Found {len(pairs)} {quote_currency} pairs on {self.exchange_name}")
            return sorted(pairs)

        except Exception as e:
            self.logger.error(f"Error fetching available pairs: {e}")
            raise DataFetchError(f"Error fetching available pairs: {e}") from e

    async def get_pairs_in_price_range(
        self,
        quote_currency: str = "USD",
        min_price: float = 1.0,
        max_price: float = 20.0,
    ) -> list[tuple[str, float]]:
        """
        Gets all available trading pairs within a price range.

        Returns:
            List of tuples (pair, current_price) sorted by price
        """
        try:
            pairs = await self.get_available_pairs(quote_currency)
            filtered_pairs = []

            for pair in pairs:
                try:
                    price = await self.get_current_price(pair)
                    if min_price <= price <= max_price:
                        filtered_pairs.append((pair, price))
                        self.logger.debug(f"{pair}: ${price:.4f} - IN RANGE")
                    else:
                        self.logger.debug(f"{pair}: ${price:.4f} - out of range")
                except Exception as e:
                    self.logger.debug(f"Could not get price for {pair}: {e}")
                    continue

            # Sort by price
            filtered_pairs.sort(key=lambda x: x[1])

            self.logger.info(f"Found {len(filtered_pairs)} pairs in ${min_price}-${max_price} range")
            return filtered_pairs

        except Exception as e:
            self.logger.error(f"Error filtering pairs by price: {e}")
            raise DataFetchError(f"Error filtering pairs by price: {e}") from e

    async def get_top_gainers(
        self,
        quote_currency: str = "USD",
        min_price: float = 1.0,
        max_price: float = 20.0,
        limit: int = 15,
        min_change_pct: float = 0.0,
    ) -> list[dict]:
        """
        Gets top gaining pairs by 24h % change.
        Fetches all tickers at once (much faster than individual calls).

        Args:
            quote_currency: Quote currency to filter by (e.g., "USD")
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of pairs to return
            min_change_pct: Minimum 24h change % (default 0 = only positive)

        Returns:
            List of dicts with pair info sorted by % change descending
        """
        # Stablecoins and fiat-pegged tokens to exclude (no meaningful price movement)
        EXCLUDED_BASES = {  # noqa: N806
            # USD Stablecoins
            "USDT",
            "USDC",
            "USDD",
            "TUSD",
            "BUSD",
            "DAI",
            "FRAX",
            "USDP",
            "GUSD",
            "PYUSD",
            "FDUSD",
            "USDS",
            "USD1",
            "USD",
            "CRVUSD",
            "GHO",
            "LUSD",
            "SUSD",
            "MIM",
            "USDZ",
            "USDY",
            "USDQ",
            "USDK",
            "HUSD",
            "CUSD",
            "ZUSD",
            "MUSD",
            "DUSD",
            "OUSD",
            # Euro stablecoins
            "EUR",
            "EUROP",
            "EURQ",
            "EURT",
            "EURS",
            "AEUR",
            "EURC",
            # Other fiat stablecoins
            "GBP",
            "TGBP",
            "GBPT",
            "JPY",
            "CHF",
            "CAD",
            "AUD",
            # Commodity-backed (stable)
            "PAXG",
            "XAUT",
            # Wrapped versions (track underlying)
            "WBTC",
            "WETH",
            "STETH",
            "CBETH",
            "RETH",
        }

        try:
            self.logger.info(f"Fetching top gainers for {quote_currency} pairs...")

            # Load markets if not already loaded
            if not self.exchange.markets:
                await self.exchange.load_markets()

            # Fetch all tickers at once - MUCH faster than individual calls
            tickers = await self.exchange.fetch_tickers()

            gainers = []
            for symbol, ticker in tickers.items():
                # Check if it's a valid market we know about
                if symbol not in self.exchange.markets:
                    continue

                market = self.exchange.markets[symbol]

                # Filter: USD quote, spot market, active
                if (
                    market.get("quote") != quote_currency
                    or not market.get("spot", False)
                    or not market.get("active", True)
                ):
                    continue

                # Exclude stablecoins and fiat-pegged tokens
                base_currency = market.get("base", "")
                if base_currency in EXCLUDED_BASES:
                    continue

                # Get price and change
                price = ticker.get("last") or ticker.get("close")
                change_pct = ticker.get("percentage")  # 24h change %

                if price is None or change_pct is None:
                    continue

                # Filter by price range and positive change
                if min_price <= price <= max_price and change_pct >= min_change_pct:
                    gainers.append(
                        {
                            "pair": symbol,
                            "price": price,
                            "change_pct": change_pct,
                            "volume": ticker.get("quoteVolume") or ticker.get("baseVolume") or 0,
                            "high_24h": ticker.get("high"),
                            "low_24h": ticker.get("low"),
                        }
                    )

            # Sort by % change descending (biggest gainers first)
            gainers.sort(key=lambda x: x["change_pct"], reverse=True)

            # Take top N
            top_gainers = gainers[:limit]

            self.logger.info(f"Found {len(gainers)} positive gainers in price range, returning top {len(top_gainers)}")

            for g in top_gainers:
                self.logger.info(f"  {g['pair']}: ${g['price']:.4f} (+{g['change_pct']:.2f}%)")

            return top_gainers

        except Exception as e:
            self.logger.error(f"Error fetching top gainers: {e}")
            raise DataFetchError(f"Error fetching top gainers: {e}") from e

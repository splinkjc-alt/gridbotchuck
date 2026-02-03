"""
REST API Server for controlling and monitoring the grid trading bot.
Allows control via web browser and mobile devices.
"""

import asyncio
from datetime import UTC, datetime
import json
import logging
import os
from pathlib import Path

from aiohttp import web
from aiohttp_cors import setup as setup_cors

from core.bot_management.event_bus import Events
from core.security.api_auth import APIAuth, create_api_auth_middleware
from core.security.cors_config import setup_cors_secure
from core.security.rate_limiter import RateLimiter, create_rate_limit_middleware
from core.security.security_headers import security_headers_middleware


class BotAPIServer:
    """
    REST API server for bot control and monitoring.
    Provides endpoints for:
    - Starting/stopping the bot
    - Pausing/resuming trading
    - Monitoring bot status
    - Viewing real-time metrics
    - Adjusting settings
    """

    def __init__(self, bot, event_bus, config_manager, port: int = 8080):
        self.bot = bot
        self.event_bus = event_bus
        self.config_manager = config_manager
        self.port = port
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize security components
        self.api_auth = APIAuth()
        self.rate_limiter = RateLimiter(
            requests_per_minute=60,  # 60 requests per minute per IP
            burst_size=10  # Allow bursts of 10 requests
        )
        
        # Create app with middlewares
        self.app = web.Application(
            middlewares=[
                create_api_auth_middleware(self.api_auth),
                create_rate_limit_middleware(self.rate_limiter),
                security_headers_middleware,
            ]
        )
        
        self.runner = None
        self.site = None

        # Backtest state
        self.backtest_running = False
        self.backtest_status = "idle"
        self.backtest_progress = 0
        self.backtest_results = None
        self.backtest_trades = []
        self.backtest_task = None

        self.setup_routes()

    def setup_routes(self):
        """Configure all API routes."""
        # Health check
        self.app.router.add_get("/api/health", self.handle_health)

        # Bot control
        self.app.router.add_post("/api/bot/start", self.handle_bot_start)
        self.app.router.add_post("/api/bot/stop", self.handle_bot_stop)
        self.app.router.add_post("/api/bot/pause", self.handle_bot_pause)
        self.app.router.add_post("/api/bot/resume", self.handle_bot_resume)

        # Bot status
        self.app.router.add_get("/api/bot/status", self.handle_bot_status)
        self.app.router.add_get("/api/bot/metrics", self.handle_bot_metrics)
        self.app.router.add_get("/api/bot/orders", self.handle_bot_orders)

        # Configuration
        self.app.router.add_get("/api/config", self.handle_get_config)
        self.app.router.add_post("/api/config/update", self.handle_update_config)

        # Market Scanner
        self.app.router.add_get("/api/market/pairs", self.handle_get_pairs)
        self.app.router.add_post("/api/market/scan", self.handle_market_scan)
        self.app.router.add_get(
            "/api/market/scan/results", self.handle_get_scan_results
        )
        self.app.router.add_post("/api/market/select", self.handle_select_pair)
        self.app.router.add_get(
            "/api/market/scanner-config", self.handle_get_scanner_config
        )
        self.app.router.add_post(
            "/api/market/scanner-config", self.handle_update_scanner_config
        )

        # Multi-pair trading
        self.app.router.add_get("/api/multi-pair/status", self.handle_multi_pair_status)
        self.app.router.add_post("/api/multi-pair/start", self.handle_multi_pair_start)
        self.app.router.add_post("/api/multi-pair/stop", self.handle_multi_pair_stop)

        # Multi-timeframe analysis
        self.app.router.add_get("/api/mtf/status", self.handle_mtf_status)
        self.app.router.add_post("/api/mtf/analyze", self.handle_mtf_analyze)

        # Chuck AI Features - Smart Scan & Auto-Portfolio
        self.app.router.add_post("/api/chuck/smart-scan", self.handle_chuck_smart_scan)
        self.app.router.add_get(
            "/api/chuck/smart-scan/results", self.handle_chuck_scan_results
        )
        self.app.router.add_get(
            "/api/chuck/portfolio/status", self.handle_chuck_portfolio_status
        )
        self.app.router.add_post(
            "/api/chuck/portfolio/start", self.handle_chuck_portfolio_start
        )
        self.app.router.add_post(
            "/api/chuck/portfolio/stop", self.handle_chuck_portfolio_stop
        )
        self.app.router.add_post(
            "/api/chuck/entry-signal", self.handle_chuck_entry_signal
        )

        # Get absolute path to dashboard folder
        dashboard_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "web",
            "dashboard",
        )

        # Handle root path - serve index.html
        self.app.router.add_get("/", self.handle_dashboard)
        self.app.router.add_get("/index.html", self.handle_dashboard)

        # Handle backtest page
        self.app.router.add_get("/backtest.html", self.handle_backtest_page)

        # Handle settings page
        self.app.router.add_get("/settings.html", self.handle_settings_page)

        # Backtest API endpoints
        self.app.router.add_post("/api/backtest/run", self.handle_backtest_run)
        self.app.router.add_get("/api/backtest/status", self.handle_backtest_status)
        self.app.router.add_post("/api/backtest/stop", self.handle_backtest_stop)
        self.app.router.add_get("/api/backtest/results", self.handle_backtest_results)

        # Settings API endpoints
        self.app.router.add_post("/api/settings", self.handle_save_settings)
        self.app.router.add_post("/api/test-exchange", self.handle_test_exchange)

        # Serve static files (dashboard) - use /static prefix to avoid conflict
        if os.path.exists(dashboard_path):
            self.app.router.add_static(
                "/static", path=dashboard_path, name="dashboard_static"
            )
            # Also serve CSS/JS directly from root for simpler paths
            self.app.router.add_get("/styles.css", self.handle_static_file)
            self.app.router.add_get("/script.js", self.handle_static_file)
            self.app.router.add_get("/backtest.css", self.handle_static_file)
            self.app.router.add_get("/backtest.js", self.handle_static_file)
            self.app.router.add_get("/settings.css", self.handle_static_file)
            self.app.router.add_get("/settings.js", self.handle_static_file)
        else:
            self.logger.warning(f"Dashboard folder not found at {dashboard_path}")

        # Setup CORS with secure defaults
        setup_cors_secure(self.app)

    async def handle_health(self, request):
        """Health check endpoint."""
        return web.json_response(
            {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}
        )

    async def handle_bot_start(self, request):
        """Start the bot."""
        try:
            if hasattr(self.bot, "is_running") and self.bot.is_running:
                return web.json_response(
                    {"success": False, "message": "Bot is already running"},
                    status=400,
                )

            # Trigger bot restart
            await self.event_bus.publish(Events.START_BOT, "web_api")
            self.logger.info("Bot start requested via API")

            return web.json_response(
                {
                    "success": True,
                    "message": "Bot starting...",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            self.logger.error(f"Error starting bot: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_bot_stop(self, request):
        """Stop the bot."""
        try:
            if hasattr(self.bot, "is_running") and not self.bot.is_running:
                return web.json_response(
                    {"success": False, "message": "Bot is not running"},
                    status=400,
                )

            # Trigger bot stop
            await self.event_bus.publish(Events.STOP_BOT, "web_api")
            self.logger.info("Bot stop requested via API")

            return web.json_response(
                {
                    "success": True,
                    "message": "Bot stopping...",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            self.logger.error(f"Error stopping bot: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_bot_pause(self, request):
        """Pause the bot (keep orders in place)."""
        try:
            await self.event_bus.publish("BOT_PAUSE", {"initiated_by": "web_api"})
            self.logger.info("Bot pause requested via API")

            return web.json_response(
                {
                    "success": True,
                    "message": "Bot pausing...",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            self.logger.error(f"Error pausing bot: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_bot_resume(self, request):
        """Resume the bot."""
        try:
            await self.event_bus.publish("BOT_RESUME", {"initiated_by": "web_api"})
            self.logger.info("Bot resume requested via API")

            return web.json_response(
                {
                    "success": True,
                    "message": "Bot resuming...",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            self.logger.error(f"Error resuming bot: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_bot_status(self, request):
        """Get current bot status."""
        try:
            # Get trading pair from config
            base_currency = self.config_manager.get_base_currency()
            quote_currency = self.config_manager.get_quote_currency()
            trading_pair = f"{base_currency}/{quote_currency}"

            status = {
                "running": self.bot.is_running,
                "trading_mode": str(self.bot.trading_mode),
                "trading_pair": trading_pair,
                "timestamp": datetime.now(UTC).isoformat(),
            }

            # Add balance info if available
            if hasattr(self.bot, "balance_tracker"):
                balance_tracker = self.bot.balance_tracker

                # Get current price for total value calculation
                current_price = 0.0
                if hasattr(self.bot, "exchange_service"):
                    try:
                        current_price = (
                            await self.bot.exchange_service.get_current_price()
                        )
                    except Exception:
                        current_price = getattr(self.bot, "_last_price", 0.0)

                status["balance"] = {
                    "fiat": balance_tracker.get_adjusted_fiat_balance(),
                    "crypto": balance_tracker.get_adjusted_crypto_balance(),
                    "total_value": balance_tracker.get_total_balance_value(
                        current_price
                    )
                    if current_price > 0
                    else 0.0,
                }

            # Add grid info if available
            if hasattr(self.bot, "grid_manager"):
                grid_manager = self.bot.grid_manager
                status["grid"] = {
                    "central_price": grid_manager.central_price,
                    "num_grids": len(grid_manager.grid_levels),
                    "buy_grids": len(grid_manager.sorted_buy_grids),
                    "sell_grids": len(grid_manager.sorted_sell_grids),
                }

            return web.json_response(status)

        except Exception as e:
            self.logger.error(f"Error getting bot status: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_bot_metrics(self, request):
        """Get bot trading metrics."""
        try:
            metrics = {
                "timestamp": datetime.now(UTC).isoformat(),
                "trades": 0,
                "wins": 0,
                "losses": 0,
                "total_fees": 0,
            }

            # Add order info if available
            if hasattr(self.bot, "order_manager"):
                order_manager = self.bot.order_manager
                orders = (
                    order_manager.orders if hasattr(order_manager, "orders") else []
                )
                metrics["total_orders"] = len(orders)
                metrics["open_orders"] = sum(1 for o in orders if not o.is_filled)
                metrics["filled_orders"] = sum(1 for o in orders if o.is_filled)

            # Add fee info if available
            if hasattr(self.bot, "balance_tracker"):
                metrics["total_fees"] = self.bot.balance_tracker.total_fees

            return web.json_response(metrics)

        except Exception as e:
            self.logger.error(f"Error getting bot metrics: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_bot_orders(self, request):
        """Get list of orders."""
        try:
            orders = []

            if hasattr(self.bot, "order_manager"):
                order_manager = self.bot.order_manager
                all_orders = (
                    order_manager.orders if hasattr(order_manager, "orders") else []
                )

                for order in all_orders[:50]:  # Limit to last 50 orders
                    orders.append(
                        {
                            "id": order.order_id
                            if hasattr(order, "order_id")
                            else "N/A",
                            "side": str(order.side)
                            if hasattr(order, "side")
                            else "N/A",
                            "price": order.price if hasattr(order, "price") else 0,
                            "quantity": order.quantity
                            if hasattr(order, "quantity")
                            else 0,
                            "status": order.status
                            if hasattr(order, "status")
                            else "N/A",
                            "timestamp": str(order.timestamp)
                            if hasattr(order, "timestamp")
                            else "N/A",
                        }
                    )

            return web.json_response({"orders": orders, "total": len(orders)})

        except Exception as e:
            self.logger.error(f"Error getting orders: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_get_config(self, request):
        """Get current configuration."""
        try:
            config = {
                "trading_mode": str(self.config_manager.get_trading_mode()),
                "trading_pair": f"{self.config_manager.get_base_currency()}/{self.config_manager.get_quote_currency()}",
                "timeframe": self.config_manager.get_timeframe(),
                "initial_balance": self.config_manager.get_initial_balance(),
                "grid_config": {
                    "type": str(self.config_manager.get_strategy_type()),
                    "spacing": str(self.config_manager.get_spacing_type()),
                    "num_grids": self.config_manager.get_num_grids(),
                    "bottom_range": self.config_manager.get_bottom_range(),
                    "top_range": self.config_manager.get_top_range(),
                },
                "risk_management": {
                    "take_profit_enabled": self.config_manager.is_take_profit_enabled(),
                    "take_profit_threshold": self.config_manager.get_take_profit_threshold(),
                    "stop_loss_enabled": self.config_manager.is_stop_loss_enabled(),
                    "stop_loss_threshold": self.config_manager.get_stop_loss_threshold(),
                },
            }

            return web.json_response(config)

        except Exception as e:
            self.logger.error(f"Error getting config: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_update_config(self, request):
        """Update configuration (limited fields only) and save to file."""
        try:
            data = await request.json()

            # Allowed top-level keys and their allowed sub-keys
            allowed_updates = {
                "take_profit_enabled": None,  # Direct value
                "stop_loss_enabled": None,  # Direct value
                "exchange": ["name", "trading_mode"],  # Nested object
                "pair": ["quote_currency", "base_currency"],  # Nested object
                "trading_settings": [
                    "period",
                    "initial_capital",
                ],  # Nested object for backtest
                "grid_strategy": [
                    "range",
                    "num_grids",
                    "spacing",
                    "type",
                ],  # Grid config
            }

            updated_fields = []

            for key, value in data.items():
                if key in allowed_updates:
                    allowed_subkeys = allowed_updates[key]

                    if allowed_subkeys is None:
                        # Direct value update
                        self.logger.info(f"Updated config: {key} = {value}")
                        updated_fields.append(key)
                    elif isinstance(value, dict):
                        # Nested object - validate subkeys
                        for subkey in value:
                            if subkey not in allowed_subkeys:
                                return web.json_response(
                                    {
                                        "success": False,
                                        "message": f"Cannot update {key}.{subkey}",
                                    },
                                    status=400,
                                )
                        self.logger.info(f"Updated config: {key} = {value}")
                        updated_fields.append(key)
                    else:
                        return web.json_response(
                            {"success": False, "message": f"Invalid value for {key}"},
                            status=400,
                        )
                else:
                    return web.json_response(
                        {"success": False, "message": f"Cannot update {key}"},
                        status=400,
                    )

            # Save updates to config file
            if updated_fields:
                config_path = Path("config/config.json")
                if config_path.exists():
                    with open(config_path) as f:
                        config = json.load(f)

                    # Deep merge the updates
                    for key, value in data.items():
                        if (
                            isinstance(value, dict)
                            and key in config
                            and isinstance(config[key], dict)
                        ):
                            config[key].update(value)
                        else:
                            config[key] = value

                    with open(config_path, "w") as f:
                        json.dump(config, f, indent=2)

                    self.logger.info(
                        f"Config file saved with updates: {updated_fields}"
                    )

            return web.json_response(
                {
                    "success": True,
                    "message": "Configuration updated and saved",
                    "updated": updated_fields,
                }
            )

        except Exception as e:
            self.logger.error(f"Error updating config: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_get_pairs(self, request):
        """Get available trading pairs within price range."""
        try:
            # Get query parameters
            quote = request.query.get("quote", "USD")
            min_price = float(request.query.get("min_price", "1.0"))
            max_price = float(request.query.get("max_price", "20.0"))

            # Check if exchange service is available
            if not hasattr(self.bot, "exchange_service"):
                return web.json_response(
                    {"success": False, "message": "Exchange service not available"},
                    status=503,
                )

            exchange_service = self.bot.exchange_service

            # Get pairs in price range
            if hasattr(exchange_service, "get_pairs_in_price_range"):
                pairs_with_prices = await exchange_service.get_pairs_in_price_range(
                    quote_currency=quote,
                    min_price=min_price,
                    max_price=max_price,
                )
                pairs = [
                    {"pair": pair, "price": round(price, 4)}
                    for pair, price in pairs_with_prices
                ]
            else:
                # Fallback: just get all pairs
                all_pairs = await exchange_service.get_available_pairs(quote)
                pairs = [{"pair": p, "price": None} for p in all_pairs]

            return web.json_response(
                {
                    "success": True,
                    "pairs": pairs,
                    "count": len(pairs),
                    "filters": {
                        "quote_currency": quote,
                        "min_price": min_price,
                        "max_price": max_price,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error getting pairs: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_market_scan(self, request):
        """Scan markets and rank coins by trading potential."""
        try:
            # Get request body (optional)
            try:
                body = await request.json()
            except Exception:
                body = {}

            # Get parameters from body or use defaults
            pairs = body.get("pairs")
            min_price = float(body.get("min_price", 1.0))
            max_price = float(body.get("max_price", 20.0))
            timeframe = body.get("timeframe", "15m")
            quote_currency = body.get("quote_currency", "USD")
            ema_fast_period = int(body.get("ema_fast_period", 9))
            ema_slow_period = int(body.get("ema_slow_period", 21))
            top_gainers_limit = int(body.get("top_gainers_limit", 15))

            # Check if exchange service is available
            if not hasattr(self.bot, "exchange_service"):
                return web.json_response(
                    {"success": False, "message": "Exchange service not available"},
                    status=503,
                )

            exchange_service = self.bot.exchange_service

            # If no pairs specified, get top gainers (fastest method!)
            top_gainers_info = []
            if not pairs:
                if hasattr(exchange_service, "get_top_gainers"):
                    # Use new fast method - fetches all tickers at once
                    self.logger.info(f"Fetching top {top_gainers_limit} gainers...")
                    top_gainers_info = await exchange_service.get_top_gainers(
                        quote_currency=quote_currency,
                        min_price=min_price,
                        max_price=max_price,
                        limit=top_gainers_limit,
                        min_change_pct=0.0,  # Only positive gainers
                    )
                    pairs = [g["pair"] for g in top_gainers_info]
                elif hasattr(exchange_service, "get_pairs_in_price_range"):
                    pairs_with_prices = await exchange_service.get_pairs_in_price_range(
                        quote_currency=quote_currency,
                        min_price=min_price,
                        max_price=max_price,
                    )
                    pairs = [pair for pair, _ in pairs_with_prices]
                else:
                    pairs = await exchange_service.get_available_pairs(quote_currency)

            if not pairs:
                return web.json_response(
                    {
                        "success": True,
                        "message": "No pairs found matching criteria (positive gainers in price range)",
                        "results": [],
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

            self.logger.info(
                f"Starting scan of {len(pairs)} top gaining pairs: {pairs}"
            )

            # Create MarketAnalyzer and run scan
            from strategies.market_analyzer import MarketAnalyzer

            analyzer = MarketAnalyzer(exchange_service, self.config_manager)
            results = await analyzer.find_best_trading_pairs(
                candidate_pairs=pairs,
                timeframe=timeframe,
                min_price=min_price,
                max_price=max_price,
                ema_fast_period=ema_fast_period,
                ema_slow_period=ema_slow_period,
                pair_info=top_gainers_info if top_gainers_info else None,
            )

            self.logger.info(f"Scan complete, got {len(results)} results")

            # Convert results to JSON-serializable format
            results_json = [r.to_dict() for r in results]

            # Cache results for later retrieval
            self._last_scan_results = {
                "results": results_json,
                "timestamp": datetime.now(UTC).isoformat(),
                "params": {
                    "pairs_scanned": len(pairs),
                    "timeframe": timeframe,
                    "min_price": min_price,
                    "max_price": max_price,
                    "ema_fast_period": ema_fast_period,
                    "ema_slow_period": ema_slow_period,
                },
            }

            return web.json_response(
                {
                    "success": True,
                    "results": results_json,
                    "count": len(results_json),
                    "params": {
                        "pairs_scanned": len(pairs),
                        "timeframe": timeframe,
                        "min_price": min_price,
                        "max_price": max_price,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error scanning markets: {e}", exc_info=True)
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_get_scan_results(self, request):
        """Get the last scan results (cached)."""
        try:
            if hasattr(self, "_last_scan_results") and self._last_scan_results:
                return web.json_response(
                    {
                        "success": True,
                        **self._last_scan_results,
                    }
                )
            else:
                return web.json_response(
                    {
                        "success": True,
                        "message": "No scan results available. Run a scan first.",
                        "results": [],
                    }
                )

        except Exception as e:
            self.logger.error(f"Error getting scan results: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_select_pair(self, request):
        """Select a coin from scan results to use for trading."""
        try:
            body = await request.json()
            pair = body.get("pair")

            if not pair:
                return web.json_response(
                    {"success": False, "message": "No pair specified"},
                    status=400,
                )

            # Parse pair into base and quote currencies
            if "/" not in pair:
                return web.json_response(
                    {
                        "success": False,
                        "message": "Invalid pair format. Expected 'BASE/QUOTE'",
                    },
                    status=400,
                )

            base_currency, quote_currency = pair.split("/")

            # Update the config file
            import json

            config_path = "config/config.json"

            with open(config_path) as f:
                config = json.load(f)

            # Store old pair for logging
            old_pair = (
                f"{config['pair']['base_currency']}/{config['pair']['quote_currency']}"
            )

            # Update pair
            config["pair"]["base_currency"] = base_currency
            config["pair"]["quote_currency"] = quote_currency

            # Write back
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            self.logger.info(f"Trading pair updated: {old_pair} -> {pair}")

            # Publish event for bot to pick up new pair
            await self.event_bus.publish(
                "CONFIG_UPDATED",
                {
                    "field": "trading_pair",
                    "old_value": old_pair,
                    "new_value": pair,
                },
            )

            return web.json_response(
                {
                    "success": True,
                    "message": f"Trading pair updated to {pair}",
                    "pair": {
                        "base_currency": base_currency,
                        "quote_currency": quote_currency,
                    },
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error selecting pair: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_get_scanner_config(self, request):
        """Get scanner configuration (EMA periods, auto-scan settings)."""
        try:
            # Load scanner config from file or use defaults
            import json

            config_path = "config/config.json"

            with open(config_path) as f:
                config = json.load(f)

            scanner_config = config.get("market_scanner", {})

            # Ensure all expected fields exist with defaults
            defaults = {
                "enabled": True,
                "quote_currency": "USD",
                "min_price": 1.0,
                "max_price": 20.0,
                "timeframe": "15m",
                "ema_fast_period": 9,
                "ema_slow_period": 21,
                "auto_scan_enabled": False,
                "auto_scan_interval_minutes": 5,
            }

            for key, default_value in defaults.items():
                if key not in scanner_config:
                    scanner_config[key] = default_value

            # Return config directly (not nested) for easier JS access
            return web.json_response(scanner_config)

        except Exception as e:
            self.logger.error(f"Error getting scanner config: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_update_scanner_config(self, request):
        """Update scanner configuration (EMA periods, auto-scan settings)."""
        try:
            body = await request.json()

            import json

            config_path = "config/config.json"

            with open(config_path) as f:
                config = json.load(f)

            if "market_scanner" not in config:
                config["market_scanner"] = {}

            # Allowed fields to update
            allowed_fields = [
                "min_price",
                "max_price",
                "timeframe",
                "ema_fast_period",
                "ema_slow_period",
                "auto_scan_enabled",
                "auto_scan_interval_minutes",
            ]

            updated_fields = []
            for field in allowed_fields:
                if field in body:
                    config["market_scanner"][field] = body[field]
                    updated_fields.append(field)

            # Write back
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

            self.logger.info(f"Scanner config updated: {updated_fields}")

            return web.json_response(
                {
                    "success": True,
                    "message": f"Scanner config updated: {', '.join(updated_fields)}",
                    "config": config["market_scanner"],
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error updating scanner config: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_multi_pair_status(self, request):
        """Get multi-pair trading status."""
        try:
            if hasattr(self.bot, "multi_pair_manager") and self.bot.multi_pair_manager:
                status = self.bot.multi_pair_manager.get_status()
            else:
                config = self.config_manager.config.get("multi_pair", {})
                status = {
                    "enabled": config.get("enabled", False),
                    "running": False,
                    "max_pairs": config.get("max_pairs", 2),
                    "active_pairs_count": 0,
                    "pairs": {},
                    "summary": {
                        "total_allocated": 0,
                        "total_current": 0,
                        "total_pnl": 0,
                        "total_pnl_percent": 0,
                    },
                }

            return web.json_response(
                {
                    "success": True,
                    "data": status,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )
        except Exception as e:
            self.logger.error(f"Error getting multi-pair status: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_multi_pair_start(self, request):
        """Start multi-pair trading."""
        try:
            data = await request.json()
            pairs = data.get("pairs", [])  # Optional specific pairs

            if (
                not hasattr(self.bot, "multi_pair_manager")
                or not self.bot.multi_pair_manager
            ):
                return web.json_response(
                    {"success": False, "message": "Multi-pair manager not initialized"},
                    status=400,
                )

            await self.bot.multi_pair_manager.initialize(pairs if pairs else None)
            # Start in background
            import asyncio

            asyncio.create_task(self.bot.multi_pair_manager.start())

            return web.json_response(
                {
                    "success": True,
                    "message": "Multi-pair trading started",
                    "pairs": list(self.bot.multi_pair_manager.active_pairs.keys()),
                }
            )
        except Exception as e:
            self.logger.error(f"Error starting multi-pair trading: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_multi_pair_stop(self, request):
        """Stop multi-pair trading."""
        try:
            if (
                not hasattr(self.bot, "multi_pair_manager")
                or not self.bot.multi_pair_manager
            ):
                return web.json_response(
                    {"success": False, "message": "Multi-pair manager not initialized"},
                    status=400,
                )

            await self.bot.multi_pair_manager.stop()
            return web.json_response(
                {"success": True, "message": "Multi-pair trading stopped"}
            )
        except Exception as e:
            self.logger.error(f"Error stopping multi-pair trading: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_dashboard(self, request):
        """Serve the dashboard HTML."""
        try:
            # Use current working directory as base
            dashboard_path = os.path.join(os.getcwd(), "web", "dashboard", "index.html")
            self.logger.debug(f"Serving dashboard from: {dashboard_path}")
            with open(dashboard_path, encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html")
        except FileNotFoundError as e:
            self.logger.error(f"Dashboard not found at {dashboard_path}: {e}")
            return web.Response(
                text=f"Dashboard not found: {dashboard_path}", status=404
            )
        except Exception as e:
            self.logger.error(f"Error serving dashboard: {e}")
            return web.Response(text=str(e), status=500)

    async def handle_backtest_page(self, request):
        """Serve the backtest HTML page."""
        try:
            backtest_path = os.path.join(
                os.getcwd(), "web", "dashboard", "backtest.html"
            )
            self.logger.debug(f"Serving backtest page from: {backtest_path}")
            with open(backtest_path, encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html")
        except FileNotFoundError as e:
            self.logger.error(f"Backtest page not found at {backtest_path}: {e}")
            return web.Response(
                text=f"Backtest page not found: {backtest_path}", status=404
            )
        except Exception as e:
            self.logger.error(f"Error serving backtest page: {e}")
            return web.Response(text=str(e), status=500)

    async def handle_settings_page(self, request):
        """Serve the settings HTML page."""
        try:
            settings_path = os.path.join(
                os.getcwd(), "web", "dashboard", "settings.html"
            )
            self.logger.debug(f"Serving settings page from: {settings_path}")
            with open(settings_path, encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type="text/html")
        except FileNotFoundError as e:
            self.logger.error(f"Settings page not found at {settings_path}: {e}")
            return web.Response(
                text=f"Settings page not found: {settings_path}", status=404
            )
        except Exception as e:
            self.logger.error(f"Error serving settings page: {e}")
            return web.Response(text=str(e), status=500)

    async def handle_save_settings(self, request):
        """Save settings from the settings page."""
        try:
            data = await request.json()
            self.logger.info(f"Received settings update: {list(data.keys())}")

            # Store settings for the bot to use
            # In a real implementation, this would update config files
            return web.json_response(
                {"status": "success", "message": "Settings saved successfully"}
            )
        except Exception as e:
            self.logger.error(f"Error saving settings: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_test_exchange(self, request):
        """Test exchange API connection."""
        try:
            import ccxt.async_support as ccxt

            data = await request.json()
            exchange_name = data.get("exchange", "").lower()
            api_key = data.get("api_key", "")
            api_secret = data.get("api_secret", "")
            passphrase = data.get("passphrase")

            if not exchange_name or not api_key or not api_secret:
                return web.json_response(
                    {"status": "error", "message": "Missing required fields"},
                    status=400,
                )

            # Map exchange names to CCXT
            exchange_map = {
                "kraken": "kraken",
                "coinbase": "coinbase",
                "binance": "binance",
                "binanceus": "binanceus",
                "kucoin": "kucoin",
                "bybit": "bybit",
                "okx": "okx",
                "gateio": "gateio",
            }

            ccxt_exchange = exchange_map.get(exchange_name)
            if not ccxt_exchange:
                return web.json_response(
                    {
                        "status": "error",
                        "message": f"Unsupported exchange: {exchange_name}",
                    },
                    status=400,
                )

            # Create exchange instance
            exchange_class = getattr(ccxt, ccxt_exchange)
            config = {"apiKey": api_key, "secret": api_secret, "enableRateLimit": True}

            # Add passphrase for exchanges that require it
            if passphrase and exchange_name in ["kucoin", "okx"]:
                config["password"] = passphrase

            exchange = exchange_class(config)

            try:
                # Test by fetching balance
                balance = await exchange.fetch_balance()

                # Calculate total USD value
                total_usd = 0
                if "total" in balance:
                    for currency, amount in balance["total"].items():
                        if (
                            amount
                            and amount > 0
                            and currency in ["USD", "USDT", "USDC"]
                        ):
                            total_usd += amount

                return web.json_response(
                    {
                        "status": "success",
                        "message": "Connection successful",
                        "balance": total_usd,
                    }
                )
            finally:
                await exchange.close()

        except ccxt.AuthenticationError:
            return web.json_response(
                {
                    "status": "error",
                    "message": "Authentication failed: Invalid API credentials",
                },
                status=401,
            )
        except ccxt.NetworkError as e:
            return web.json_response(
                {"status": "error", "message": f"Network error: {e!s}"}, status=503
            )
        except Exception as e:
            self.logger.error(f"Exchange test error: {e}")
            return web.json_response({"status": "error", "message": str(e)}, status=500)

    async def handle_backtest_run(self, request):
        """Run a backtest with provided configuration."""

        try:
            data = await request.json()

            if self.backtest_running:
                return web.json_response(
                    {"success": False, "message": "Backtest already running"},
                    status=400,
                )

            # Extract backtest config
            pair = data.get("pair", "BTC/USD")
            start_date = data.get("start_date", "")
            end_date = data.get("end_date", "")
            capital = float(data.get("capital", 1000))
            grid_levels = int(data.get("grid_levels", 10))
            strategy = data.get("strategy", "BASIC_GRID")
            price_range_low = float(data.get("price_range_low", 0))
            price_range_high = float(data.get("price_range_high", 0))

            self.logger.info(
                f"Starting backtest: {pair} from {start_date} to {end_date}"
            )

            # Reset state
            self.backtest_running = True
            self.backtest_status = "running"
            self.backtest_progress = 0
            self.backtest_results = None
            self.backtest_trades = []

            # Start backtest in background
            self.backtest_task = asyncio.create_task(
                self._run_backtest(
                    pair,
                    start_date,
                    end_date,
                    capital,
                    grid_levels,
                    strategy,
                    price_range_low,
                    price_range_high,
                )
            )

            return web.json_response(
                {"success": True, "message": "Backtest started", "status": "running"}
            )

        except Exception as e:
            self.logger.error(f"Error starting backtest: {e}")
            self.backtest_running = False
            self.backtest_status = "error"
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def _run_backtest(
        self,
        pair: str,
        start_date: str,
        end_date: str,
        capital: float,
        grid_levels: int,
        strategy: str,
        price_range_low: float,
        price_range_high: float,
    ):
        """Execute backtest simulation."""
        from datetime import datetime, timedelta

        import numpy as np
        import pandas as pd

        try:
            self.backtest_progress = 5
            self.logger.info(f"Fetching historical data for {pair}...")

            ohlcv_data = None

            # Try to fetch real data using ccxt
            try:
                import ccxt

                # Get exchange from config
                exchange_id = (
                    self.config_manager.get("exchange", {})
                    .get("name", "kraken")
                    .lower()
                )
                exchange_class = getattr(ccxt, exchange_id)
                exchange = exchange_class({"enableRateLimit": True})

                self.backtest_progress = 10

                # Parse dates
                start_dt = datetime.fromisoformat(start_date.replace("T", " "))
                datetime.fromisoformat(end_date.replace("T", " "))
                since = int(start_dt.timestamp() * 1000)

                # Fetch OHLCV
                self.logger.info(f"Fetching from {exchange_id} for {pair}...")
                raw_ohlcv = exchange.fetch_ohlcv(pair, "1h", since=since, limit=500)

                if raw_ohlcv and len(raw_ohlcv) > 0:
                    ohlcv_data = pd.DataFrame(
                        raw_ohlcv,
                        columns=["timestamp", "open", "high", "low", "close", "volume"],
                    )
                    ohlcv_data["timestamp"] = pd.to_datetime(
                        ohlcv_data["timestamp"], unit="ms"
                    )
                    self.logger.info(
                        f"Fetched {len(ohlcv_data)} candles from {exchange_id}"
                    )

            except Exception as e:
                self.logger.warning(f"Could not fetch from exchange: {e}")
                ohlcv_data = None

            self.backtest_progress = 15

            # Generate synthetic data if we couldn't fetch real data
            if ohlcv_data is None or len(ohlcv_data) == 0:
                self.logger.info("Generating synthetic data for backtest demo...")

                start = datetime.fromisoformat(start_date.replace("T", " "))
                end = datetime.fromisoformat(end_date.replace("T", " "))
                hours = max(int((end - start).total_seconds() / 3600), 24)

                base_price = (
                    100
                    if price_range_low == 0
                    else (price_range_low + price_range_high) / 2
                )
                # Create more realistic price movement
                np.random.seed(42)  # Reproducible results
                returns = np.random.randn(hours) * 0.02  # 2% volatility
                prices = base_price * np.exp(np.cumsum(returns))

                ohlcv_data = pd.DataFrame(
                    {
                        "timestamp": [start + timedelta(hours=i) for i in range(hours)],
                        "open": prices,
                        "high": prices * (1 + np.abs(np.random.randn(hours)) * 0.01),
                        "low": prices * (1 - np.abs(np.random.randn(hours)) * 0.01),
                        "close": np.roll(prices, -1),
                        "volume": np.random.uniform(1000, 10000, hours),
                    }
                )
                ohlcv_data["close"].iloc[-1] = ohlcv_data["open"].iloc[-1]
                self.logger.info(f"Generated {len(ohlcv_data)} synthetic candles")

            self.backtest_progress = 20

            if len(ohlcv_data) == 0:
                raise ValueError("No historical data available")

            # Calculate grid levels
            if price_range_low == 0 or price_range_high == 0:
                price_range_low = float(ohlcv_data["low"].min()) * 0.95
                price_range_high = float(ohlcv_data["high"].max()) * 1.05

            grid_spacing = (price_range_high - price_range_low) / grid_levels
            grid_prices = [
                price_range_low + i * grid_spacing for i in range(grid_levels + 1)
            ]

            self.logger.info(
                f"Grid: {grid_levels} levels from ${price_range_low:.2f} to ${price_range_high:.2f}"
            )

            # Simulate trading
            balance_quote = capital  # Quote currency (USD)
            balance_base = 0.0  # Base currency
            trades = []
            equity_history = []
            initial_equity = capital

            # Track grid state
            grid_state = dict.fromkeys(grid_prices, "empty")

            self.backtest_progress = 30
            total_candles = len(ohlcv_data)

            for i, (idx, row) in enumerate(ohlcv_data.iterrows()):
                price = float(row["close"])
                timestamp = row.get("timestamp", idx)

                # Update progress
                progress = 30 + int(60 * i / total_candles)
                self.backtest_progress = min(progress, 90)

                # Check grid levels for buy/sell signals
                for grid_price in grid_prices:
                    if grid_state[grid_price] == "empty" and price <= grid_price:
                        # Buy signal
                        buy_amount = (capital / grid_levels) / price
                        if balance_quote >= buy_amount * price:
                            balance_quote -= buy_amount * price
                            balance_base += buy_amount
                            grid_state[grid_price] = "filled"
                            trades.append(
                                {
                                    "timestamp": str(timestamp),
                                    "type": "buy",
                                    "price": price,
                                    "amount": buy_amount,
                                    "value": buy_amount * price,
                                    "grid_level": grid_price,
                                }
                            )

                    elif (
                        grid_state[grid_price] == "filled"
                        and price >= grid_price * 1.01
                    ):
                        # Sell signal (1% profit target)
                        sell_amount = (capital / grid_levels) / grid_price
                        if balance_base >= sell_amount:
                            balance_base -= sell_amount
                            balance_quote += sell_amount * price
                            grid_state[grid_price] = "empty"
                            trades.append(
                                {
                                    "timestamp": str(timestamp),
                                    "type": "sell",
                                    "price": price,
                                    "amount": sell_amount,
                                    "value": sell_amount * price,
                                    "grid_level": grid_price,
                                    "profit": (price - grid_price) * sell_amount,
                                }
                            )

                # Calculate equity
                current_equity = balance_quote + (balance_base * price)
                equity_history.append(
                    {
                        "timestamp": str(timestamp),
                        "equity": current_equity,
                        "price": price,
                    }
                )

                # Small delay to prevent blocking
                if i % 100 == 0:
                    await asyncio.sleep(0.01)

            self.backtest_progress = 95

            # Calculate final results
            final_price = float(ohlcv_data["close"].iloc[-1])
            final_equity = balance_quote + (balance_base * final_price)
            total_return = ((final_equity - initial_equity) / initial_equity) * 100

            buy_trades = [t for t in trades if t["type"] == "buy"]
            sell_trades = [t for t in trades if t["type"] == "sell"]
            total_profit = sum(t.get("profit", 0) for t in sell_trades)

            # Calculate max drawdown
            peak = initial_equity
            max_drawdown = 0
            for eq in equity_history:
                if eq["equity"] > peak:
                    peak = eq["equity"]
                drawdown = (peak - eq["equity"]) / peak * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown

            self.backtest_results = {
                "pair": pair,
                "period": f"{start_date} to {end_date}",
                "initial_capital": capital,
                "final_equity": round(final_equity, 2),
                "total_return": round(total_return, 2),
                "total_profit": round(total_profit, 2),
                "total_trades": len(trades),
                "buy_trades": len(buy_trades),
                "sell_trades": len(sell_trades),
                "win_rate": round(len(sell_trades) / max(len(trades), 1) * 100, 1),
                "max_drawdown": round(max_drawdown, 2),
                "grid_levels": grid_levels,
                "price_range": f"${price_range_low:.2f} - ${price_range_high:.2f}",
                "equity_history": equity_history[-100:],  # Last 100 points for chart
                "trades": trades[-50:],  # Last 50 trades
            }

            self.backtest_trades = trades
            self.backtest_progress = 100
            self.backtest_status = "complete"
            self.backtest_running = False

            self.logger.info(
                f"Backtest complete: {len(trades)} trades, return: {total_return:.2f}%"
            )

        except Exception as e:
            self.logger.error(f"Backtest error: {e}", exc_info=True)
            self.backtest_status = "error"
            self.backtest_results = {"error": str(e)}
            self.backtest_running = False

    async def handle_backtest_status(self, request):
        """Get current backtest status."""
        return web.json_response(
            {
                "running": self.backtest_running,
                "status": self.backtest_status,
                "progress": self.backtest_progress,
            }
        )

    async def handle_backtest_stop(self, request):
        """Stop running backtest."""
        if self.backtest_task and not self.backtest_task.done():
            self.backtest_task.cancel()
        self.backtest_running = False
        self.backtest_status = "stopped"
        return web.json_response({"success": True, "message": "Backtest stopped"})

    async def handle_backtest_results(self, request):
        """Get backtest results."""
        if self.backtest_results:
            return web.json_response(
                {"success": True, "results": self.backtest_results}
            )
        else:
            return web.json_response(
                {"success": False, "message": "No results available"}
            )

    async def handle_static_file(self, request):
        """Serve static CSS/JS files."""
        try:
            filename = request.path.lstrip("/")
            file_path = os.path.join(os.getcwd(), "web", "dashboard", filename)

            content_types = {
                ".css": "text/css",
                ".js": "application/javascript",
                ".html": "text/html",
            }
            ext = os.path.splitext(filename)[1]
            content_type = content_types.get(ext, "text/plain")

            with open(file_path, encoding="utf-8") as f:
                return web.Response(text=f.read(), content_type=content_type)
        except FileNotFoundError:
            return web.Response(text=f"File not found: {filename}", status=404)
        except Exception as e:
            self.logger.error(f"Error serving static file: {e}")
            return web.Response(text=str(e), status=500)

    async def start(self):
        """Start the API server."""
        try:
            # Start rate limiter cleanup task
            self.rate_limiter.start_cleanup()
            
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, "127.0.0.1", self.port)
            await self.site.start()
            self.logger.info(f"Bot API Server started on http://127.0.0.1:{self.port}")
            self.logger.info(f"API Key required for endpoints (except /api/health)")
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            raise

    async def stop(self):
        """Stop the API server."""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            self.logger.info("Bot API Server stopped")
        except Exception as e:
            self.logger.error(f"Error stopping API server: {e}")

    async def handle_mtf_status(self, request):
        """Get multi-timeframe analysis status."""
        try:
            # Check if MTF analysis is enabled
            if not self.config_manager.is_multi_timeframe_analysis_enabled():
                return web.json_response(
                    {
                        "enabled": False,
                        "message": "Multi-timeframe analysis is disabled in config",
                    }
                )

            # Get status from active trading strategy if available
            if hasattr(self, "trading_strategy") and self.trading_strategy:
                mtf_status = self.trading_strategy.get_mtf_analysis_status()
                if mtf_status:
                    return web.json_response(
                        {"enabled": True, "status": "active", "analysis": mtf_status}
                    )

            # Check via grid trading bot
            if hasattr(self.bot, "trading_strategy") and self.bot.trading_strategy:
                strategy = self.bot.trading_strategy
                if hasattr(strategy, "get_mtf_analysis_status"):
                    mtf_status = strategy.get_mtf_analysis_status()
                    if mtf_status:
                        return web.json_response(
                            {
                                "enabled": True,
                                "status": "active",
                                "analysis": mtf_status,
                            }
                        )

            return web.json_response(
                {
                    "enabled": True,
                    "status": "waiting",
                    "message": "Multi-timeframe analysis enabled but no analysis run yet",
                }
            )

        except Exception as e:
            self.logger.error(f"Error getting MTF status: {e}")
            return web.json_response({"error": str(e)}, status=500)

    async def handle_mtf_analyze(self, request):
        """Trigger a manual multi-timeframe analysis."""
        try:
            if not self.config_manager.is_multi_timeframe_analysis_enabled():
                return web.json_response(
                    {
                        "success": False,
                        "message": "Multi-timeframe analysis is disabled in config",
                    },
                    status=400,
                )

            # Get the trading strategy
            strategy = None
            if hasattr(self.bot, "trading_strategy"):
                strategy = self.bot.trading_strategy

            if (
                not strategy
                or not hasattr(strategy, "_mtf_analyzer")
                or not strategy._mtf_analyzer
            ):
                return web.json_response(
                    {
                        "success": False,
                        "message": "Multi-timeframe analyzer not initialized",
                    },
                    status=400,
                )

            # Force analysis by resetting the last analysis time
            strategy._last_mtf_analysis_time = 0

            # Get grid bounds
            grid_top = max(strategy.grid_manager.price_grids)
            grid_bottom = min(strategy.grid_manager.price_grids)

            # Run analysis
            result = await strategy._mtf_analyzer.analyze(
                strategy.trading_pair, grid_bottom, grid_top
            )

            # Update cached result
            strategy._mtf_analysis_result = result
            strategy._last_mtf_analysis_time = __import__("time").time()

            return web.json_response(
                {
                    "success": True,
                    "analysis": {
                        "primary_trend": result.primary_trend,
                        "market_condition": result.market_condition.value,
                        "grid_signal": result.grid_signal.value,
                        "spacing_multiplier": result.recommended_spacing_multiplier,
                        "recommended_bias": result.recommended_bias,
                        "range_valid": result.range_valid,
                        "confidence": result.confidence,
                        "warnings": result.warnings,
                        "recommendations": result.recommendations,
                    },
                }
            )

        except Exception as e:
            self.logger.error(f"Error running MTF analysis: {e}")
            return web.json_response({"error": str(e)}, status=500)

    # =====================================================
    # Chuck AI Features - Smart Scan & Auto-Portfolio
    # =====================================================

    async def handle_chuck_smart_scan(self, request):
        """Run the Chuck AI smart pair scanner."""
        try:
            data = await request.json()

            quote_currency = data.get("quote_currency", "USD")
            num_pairs = data.get("num_pairs", 10)
            min_price = data.get("min_price", 0.01)
            max_price = data.get("max_price", 100.0)
            min_volume = data.get("min_volume", 100000)

            # Import scanner
            from strategies.pair_scanner import PairScanner

            # Get exchange service
            if not hasattr(self.bot, "exchange_service"):
                return web.json_response(
                    {"success": False, "message": "Exchange service not available"},
                    status=400,
                )

            scanner = PairScanner(self.bot.exchange_service)

            self.logger.info(
                f"Starting Chuck smart scan for {num_pairs} {quote_currency} pairs..."
            )

            # Run scan
            results = await scanner.scan_pairs(
                quote_currency=quote_currency,
                min_price=min_price,
                max_price=max_price,
                min_volume_24h=min_volume,
                max_results=num_pairs,
            )

            # Store results for later retrieval
            self._chuck_scan_results = results

            return web.json_response(
                {
                    "success": True,
                    "message": f"Scan complete. Found {len(results)} pairs.",
                    "count": len(results),
                    "results": [r.to_dict() for r in results],
                }
            )

        except Exception as e:
            self.logger.error(f"Error in Chuck smart scan: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_chuck_scan_results(self, request):
        """Get the last Chuck scan results."""
        try:
            results = getattr(self, "_chuck_scan_results", [])
            return web.json_response(
                {
                    "success": True,
                    "count": len(results),
                    "results": [r.to_dict() for r in results],
                }
            )
        except Exception as e:
            self.logger.error(f"Error getting Chuck scan results: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_chuck_portfolio_status(self, request):
        """Get Chuck auto-portfolio status."""
        try:
            manager = getattr(self, "_chuck_portfolio_manager", None)

            if manager is None:
                return web.json_response(
                    {
                        "success": True,
                        "running": False,
                        "message": "Auto-portfolio not started",
                        "state": None,
                    }
                )

            return web.json_response(
                {
                    "success": True,
                    "running": manager.state.is_running,
                    "state": manager.get_state(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error getting Chuck portfolio status: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_chuck_portfolio_start(self, request):
        """Start Chuck auto-portfolio manager."""
        try:
            data = await request.json()

            total_capital = data.get("total_capital", 500.0)
            max_positions = data.get("max_positions", 5)
            min_entry_score = data.get("min_entry_score", 65.0)
            scan_interval = data.get("scan_interval", 300)
            quote_currency = data.get("quote_currency", "USD")
            num_pairs = data.get("num_pairs", 10)

            # Import manager
            from strategies.auto_portfolio_manager import AutoPortfolioManager

            if not hasattr(self.bot, "exchange_service"):
                return web.json_response(
                    {"success": False, "message": "Exchange service not available"},
                    status=400,
                )

            # Check if already running
            existing = getattr(self, "_chuck_portfolio_manager", None)
            if existing and existing.state.is_running:
                return web.json_response(
                    {"success": False, "message": "Auto-portfolio already running"},
                    status=400,
                )

            # Create manager
            manager = AutoPortfolioManager(
                exchange_service=self.bot.exchange_service,
                total_capital=total_capital,
                max_positions=max_positions,
                min_entry_score=min_entry_score,
                scan_interval=scan_interval,
            )

            self._chuck_portfolio_manager = manager

            # Start in background task
            import asyncio

            asyncio.create_task(
                manager.start(
                    quote_currency=quote_currency,
                    num_pairs=num_pairs,
                )
            )

            self.logger.info(
                f"Chuck auto-portfolio started: ${total_capital}, {max_positions} positions"
            )

            return web.json_response(
                {
                    "success": True,
                    "message": "Auto-portfolio manager started",
                    "config": {
                        "total_capital": total_capital,
                        "max_positions": max_positions,
                        "min_entry_score": min_entry_score,
                        "scan_interval": scan_interval,
                    },
                }
            )

        except Exception as e:
            self.logger.error(f"Error starting Chuck portfolio: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_chuck_portfolio_stop(self, request):
        """Stop Chuck auto-portfolio manager."""
        try:
            manager = getattr(self, "_chuck_portfolio_manager", None)

            if manager is None or not manager.state.is_running:
                return web.json_response(
                    {"success": False, "message": "Auto-portfolio not running"},
                    status=400,
                )

            await manager.stop()

            return web.json_response(
                {
                    "success": True,
                    "message": "Auto-portfolio manager stopped",
                    "final_state": manager.get_state(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error stopping Chuck portfolio: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_chuck_entry_signal(self, request):
        """Analyze entry signal for a specific pair."""
        try:
            data = await request.json()

            pair = data.get("pair")
            grid_top = data.get("grid_top")
            grid_bottom = data.get("grid_bottom")

            if not all([pair, grid_top, grid_bottom]):
                return web.json_response(
                    {
                        "success": False,
                        "message": "Missing required fields: pair, grid_top, grid_bottom",
                    },
                    status=400,
                )

            # Import analyzer
            from strategies.entry_signals import EntrySignalAnalyzer

            if not hasattr(self.bot, "exchange_service"):
                return web.json_response(
                    {"success": False, "message": "Exchange service not available"},
                    status=400,
                )

            # Fetch OHLCV data
            ohlcv = await self.bot.exchange_service.fetch_ohlcv_simple(pair, "1h", 100)

            if ohlcv is None or len(ohlcv) < 24:
                return web.json_response(
                    {"success": False, "message": f"Insufficient data for {pair}"},
                    status=400,
                )

            # Analyze
            analyzer = EntrySignalAnalyzer()
            signal = analyzer.analyze_entry(
                pair=pair,
                ohlcv_data=ohlcv,
                grid_top=float(grid_top),
                grid_bottom=float(grid_bottom),
            )

            return web.json_response(
                {
                    "success": True,
                    "signal": signal.to_dict(),
                }
            )

        except Exception as e:
            self.logger.error(f"Error analyzing entry signal: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

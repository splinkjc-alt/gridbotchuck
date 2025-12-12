"""
REST API Server for controlling and monitoring the grid trading bot.
Allows control via web browser and mobile devices.
"""

from datetime import UTC, datetime
import logging
import os

from aiohttp import web
from aiohttp_cors import setup as setup_cors

from core.bot_management.event_bus import Events


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
        self.app = web.Application()
        self.runner = None
        self.site = None
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
        self.app.router.add_get("/api/market/scan/results", self.handle_get_scan_results)
        self.app.router.add_post("/api/market/select", self.handle_select_pair)
        self.app.router.add_get("/api/market/scanner-config", self.handle_get_scanner_config)
        self.app.router.add_post("/api/market/scanner-config", self.handle_update_scanner_config)

        # Multi-pair trading
        self.app.router.add_get("/api/multi-pair/status", self.handle_multi_pair_status)
        self.app.router.add_post("/api/multi-pair/start", self.handle_multi_pair_start)
        self.app.router.add_post("/api/multi-pair/stop", self.handle_multi_pair_stop)

        # Get absolute path to dashboard folder
        dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web", "dashboard")

        # Handle root path - serve index.html
        self.app.router.add_get("/", self.handle_dashboard)

        # Serve static files (dashboard) - use /static prefix to avoid conflict
        if os.path.exists(dashboard_path):
            self.app.router.add_static("/static", path=dashboard_path, name="dashboard_static")
            # Also serve CSS/JS directly from root for simpler paths
            self.app.router.add_get("/styles.css", self.handle_static_file)
            self.app.router.add_get("/script.js", self.handle_static_file)
        else:
            self.logger.warning(f"Dashboard folder not found at {dashboard_path}")

        # Setup CORS for mobile/cross-origin requests
        setup_cors(self.app)

    async def handle_health(self, request):
        """Health check endpoint."""
        return web.json_response({"status": "ok", "timestamp": datetime.now(UTC).isoformat()})

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
                {"success": True, "message": "Bot starting...", "timestamp": datetime.now(UTC).isoformat()}
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
                {"success": True, "message": "Bot stopping...", "timestamp": datetime.now(UTC).isoformat()}
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
                {"success": True, "message": "Bot pausing...", "timestamp": datetime.now(UTC).isoformat()}
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
                {"success": True, "message": "Bot resuming...", "timestamp": datetime.now(UTC).isoformat()}
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
                        current_price = await self.bot.exchange_service.get_current_price()
                    except Exception:
                        current_price = getattr(self.bot, "_last_price", 0.0)

                status["balance"] = {
                    "fiat": balance_tracker.get_adjusted_fiat_balance(),
                    "crypto": balance_tracker.get_adjusted_crypto_balance(),
                    "total_value": balance_tracker.get_total_balance_value(current_price) if current_price > 0 else 0.0,
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
                orders = order_manager.orders if hasattr(order_manager, "orders") else []
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
                all_orders = order_manager.orders if hasattr(order_manager, "orders") else []

                for order in all_orders[:50]:  # Limit to last 50 orders
                    orders.append(
                        {
                            "id": order.order_id if hasattr(order, "order_id") else "N/A",
                            "side": str(order.side) if hasattr(order, "side") else "N/A",
                            "price": order.price if hasattr(order, "price") else 0,
                            "quantity": order.quantity if hasattr(order, "quantity") else 0,
                            "status": order.status if hasattr(order, "status") else "N/A",
                            "timestamp": str(order.timestamp) if hasattr(order, "timestamp") else "N/A",
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
        """Update configuration (limited fields only)."""
        try:
            data = await request.json()

            # Only allow safe updates
            allowed_updates = ["take_profit_enabled", "stop_loss_enabled"]

            for key, value in data.items():
                if key in allowed_updates:
                    self.logger.info(f"Updated config: {key} = {value}")
                else:
                    return web.json_response(
                        {"success": False, "message": f"Cannot update {key}"},
                        status=400,
                    )

            return web.json_response({"success": True, "message": "Configuration updated"})

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
                pairs = [{"pair": pair, "price": round(price, 4)} for pair, price in pairs_with_prices]
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

            self.logger.info(f"Starting scan of {len(pairs)} top gaining pairs: {pairs}")

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
                    {"success": False, "message": "Invalid pair format. Expected 'BASE/QUOTE'"},
                    status=400,
                )

            base_currency, quote_currency = pair.split("/")

            # Update the config file
            import json

            config_path = "config/config.json"

            with open(config_path) as f:
                config = json.load(f)

            # Store old pair for logging
            old_pair = f"{config['pair']['base_currency']}/{config['pair']['quote_currency']}"

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

            return web.json_response({"success": True, "data": status, "timestamp": datetime.now(UTC).isoformat()})
        except Exception as e:
            self.logger.error(f"Error getting multi-pair status: {e}")
            return web.json_response({"success": False, "message": str(e)}, status=500)

    async def handle_multi_pair_start(self, request):
        """Start multi-pair trading."""
        try:
            data = await request.json()
            pairs = data.get("pairs", [])  # Optional specific pairs

            if not hasattr(self.bot, "multi_pair_manager") or not self.bot.multi_pair_manager:
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
            if not hasattr(self.bot, "multi_pair_manager") or not self.bot.multi_pair_manager:
                return web.json_response(
                    {"success": False, "message": "Multi-pair manager not initialized"},
                    status=400,
                )

            await self.bot.multi_pair_manager.stop()
            return web.json_response({"success": True, "message": "Multi-pair trading stopped"})
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
            return web.Response(text=f"Dashboard not found: {dashboard_path}", status=404)
        except Exception as e:
            self.logger.error(f"Error serving dashboard: {e}")
            return web.Response(text=str(e), status=500)

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
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, "127.0.0.1", self.port)
            await self.site.start()
            self.logger.info(f"Bot API Server started on http://127.0.0.1:{self.port}")
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

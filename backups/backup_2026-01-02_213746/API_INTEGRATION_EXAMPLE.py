"""
Example: How to integrate the API dashboard with your bot

This file shows the minimal changes needed to add web control to main.py
"""

# =============================================================================
# BEFORE (Original main.py structure)
# =============================================================================

"""
async def run_bot(
    config_path: str,
    profile: bool = False,
    save_performance_results_path: str | None = None,
    no_plot: bool = False,
) -> dict[str, Any] | None:
    config_manager = initialize_config(config_path)
    config_name = generate_config_name(config_manager)
    setup_logging(config_manager.get_logging_level(), config_manager.should_log_to_file(), config_name)
    event_bus = EventBus()
    notification_handler = initialize_notification_handler(config_manager, event_bus)
    bot = GridTradingBot(...)
    bot_controller = BotController(bot, event_bus)
    health_check = HealthCheck(bot, notification_handler, event_bus)

    # ... rest of original code
"""

# =============================================================================
# AFTER (With API Integration - Changes Highlighted)
# =============================================================================

"""
# STEP 1: Add import at the top of main.py
from core.bot_management.bot_api_integration import BotAPIIntegration

# STEP 2: Modify run_bot function
async def run_bot(
    config_path: str,
    profile: bool = False,
    save_performance_results_path: str | None = None,
    no_plot: bool = False,
    api_port: int = 8080,  # ADD THIS PARAMETER
) -> dict[str, Any] | None:
    config_manager = initialize_config(config_path)
    config_name = generate_config_name(config_manager)
    setup_logging(config_manager.get_logging_level(), config_manager.should_log_to_file(), config_name)
    event_bus = EventBus()
    notification_handler = initialize_notification_handler(config_manager, event_bus)
    bot = GridTradingBot(...)
    bot_controller = BotController(bot, event_bus)
    health_check = HealthCheck(bot, notification_handler, event_bus)

    # ADD THIS BLOCK: Initialize API server
    api_integration = BotAPIIntegration(
        bot=bot,
        event_bus=event_bus,
        config_manager=config_manager,
        port=api_port
    )
    await api_integration.start()

    if profile:
        cProfile.runctx("asyncio.run(bot.run())", globals(), locals(), "profile_results.prof")
        return None

    try:
        if bot.trading_mode in {TradingMode.LIVE, TradingMode.PAPER_TRADING}:
            bot_task = asyncio.create_task(bot.run(), name="BotTask")
            bot_controller_task = asyncio.create_task(bot_controller.command_listener(), name="BotControllerTask")
            health_check_task = asyncio.create_task(health_check.start(), name="HealthCheckTask")
            # REST OF CODE UNCHANGED
            await asyncio.gather(bot_task, bot_controller_task, health_check_task)
        else:
            await bot.run()

    except asyncio.CancelledError:
        logging.info("Cancellation received. Shutting down gracefully.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

    finally:
        try:
            # ADD THIS LINE: Stop API server
            await api_integration.stop()
            await event_bus.shutdown()

        except Exception as e:
            logging.error(f"Error during shutdown: {e}", exc_info=True)
"""

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
From command line:

# Basic usage (API on default port 8080)
python main.py backtest --config config/config.json

# With custom API port
python main.py backtest --config config/config.json --api-port 9090

# Check if API is working
curl http://localhost:8080/api/health
"""

# =============================================================================
# FILE STRUCTURE REQUIRED
# =============================================================================

"""
grid_trading_bot-master/
│
├── main.py                              (Modified)
├── requirements.txt                     (Add: aiohttp, aiohttp-cors)
│
├── core/
│   └── bot_management/
│       ├── bot_api_server.py           (NEW)
│       ├── bot_api_integration.py      (NEW)
│       ├── grid_trading_bot.py         (Existing)
│       ├── event_bus.py                (Existing)
│       └── ...
│
├── web/
│   └── dashboard/
│       ├── index.html                  (NEW)
│       ├── styles.css                  (NEW)
│       └── script.js                   (NEW)
│
└── config/
    └── config.json                     (Existing)
"""

# =============================================================================
# API ENDPOINTS AVAILABLE
# =============================================================================

"""
Health Check:
  GET /api/health

Bot Control:
  POST /api/bot/start
  POST /api/bot/stop
  POST /api/bot/pause
  POST /api/bot/resume

Status & Monitoring:
  GET /api/bot/status
  GET /api/bot/metrics
  GET /api/bot/orders

Configuration:
  GET /api/config
  POST /api/config/update

Dashboard:
  GET /                       (Serves dashboard)
"""

# =============================================================================
# EXAMPLE: PROGRAMMATIC CONTROL VIA API
# =============================================================================

"""
import aiohttp
import asyncio

async def control_bot():
    async with aiohttp.ClientSession() as session:
        # Start the bot
        async with session.post('http://localhost:8080/api/bot/start') as resp:
            result = await resp.json()
            print(f"Start: {result}")

        # Wait and check status
        await asyncio.sleep(2)
        async with session.get('http://localhost:8080/api/bot/status') as resp:
            status = await resp.json()
            print(f"Bot Running: {status['running']}")

        # Get metrics
        async with session.get('http://localhost:8080/api/bot/metrics') as resp:
            metrics = await resp.json()
            print(f"Total Orders: {metrics['total_orders']}")

        # Stop the bot
        async with session.post('http://localhost:8080/api/bot/stop') as resp:
            result = await resp.json()
            print(f"Stop: {result}")

# Run example
asyncio.run(control_bot())
"""

# =============================================================================
# TESTING THE DASHBOARD
# =============================================================================

"""
1. Start the bot:
   python main.py backtest --config config/config.json

2. Open browser:
   http://localhost:8080

3. Click buttons to control bot:
   - Green "Start Bot" button
   - Yellow "Pause" button
   - Cyan "Resume" button
   - Red "Stop Bot" button

4. Monitor in real-time:
   - Status indicator (top right)
   - Balance updates
   - Order list
   - Performance metrics

5. On mobile (same network):
   - Find your IP: ipconfig
   - Open: http://192.168.1.100:8080
   - Same controls available
"""

# =============================================================================
# CUSTOMIZATION
# =============================================================================

"""
Change API port:
  In main.py: BotAPIIntegration(..., port=9090)

Change refresh interval:
  In web/dashboard/script.js: const REFRESH_INTERVAL = 5000;  // 5 seconds

Add authentication:
  In bot_api_server.py: Add Bearer token validation

Change dashboard theme:
  In web/dashboard/styles.css: Modify CSS variables at top

Customize dashboard HTML:
  In web/dashboard/index.html: Add new sections
"""

# =============================================================================
# REQUIREMENTS TO ADD
# =============================================================================

"""
Add to requirements.txt:

aiohttp>=3.8.0
aiohttp-cors>=0.7.0
"""

# =============================================================================
# VERIFICATION
# =============================================================================

"""
After integration, you should see in console:

1. Bot initialization logs
2. "Bot API Server started on http://0.0.0.0:8080"
3. "Access dashboard at: http://localhost:8080"

Then open http://localhost:8080 and verify:
- Dashboard loads without errors
- Connection status shows "Connected"
- Start/Stop buttons are clickable
- Status updates every 2 seconds
"""

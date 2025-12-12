# Quick Start: Web Dashboard Control

## 🚀 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install aiohttp aiohttp-cors
```

### Step 2: Update your main.py

Replace the `run_bot` function with this version that includes API support:

```python
from core.bot_management.bot_api_integration import BotAPIIntegration

async def run_bot(
    config_path: str,
    profile: bool = False,
    save_performance_results_path: str | None = None,
    no_plot: bool = False,
    api_port: int = 8080,  # Add this parameter
) -> dict[str, Any] | None:
    config_manager = initialize_config(config_path)
    config_name = generate_config_name(config_manager)
    setup_logging(config_manager.get_logging_level(), config_manager.should_log_to_file(), config_name)
    event_bus = EventBus()
    notification_handler = initialize_notification_handler(config_manager, event_bus)
    bot = GridTradingBot(
        config_path,
        config_manager,
        notification_handler,
        event_bus,
        save_performance_results_path,
        no_plot,
    )
    bot_controller = BotController(bot, event_bus)
    health_check = HealthCheck(bot, notification_handler, event_bus)
    
    # Add API Integration for web control
    api_integration = BotAPIIntegration(bot, event_bus, config_manager, port=api_port)
    await api_integration.start()

    if profile:
        cProfile.runctx("asyncio.run(bot.run())", globals(), locals(), "profile_results.prof")
        return None

    try:
        if bot.trading_mode in {TradingMode.LIVE, TradingMode.PAPER_TRADING}:
            bot_task = asyncio.create_task(bot.run(), name="BotTask")
            bot_controller_task = asyncio.create_task(bot_controller.command_listener(), name="BotControllerTask")
            health_check_task = asyncio.create_task(health_check.start(), name="HealthCheckTask")
            await asyncio.gather(bot_task, bot_controller_task, health_check_task)
        else:
            await bot.run()

    except asyncio.CancelledError:
        logging.info("Cancellation received. Shutting down gracefully.")

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

    finally:
        try:
            await api_integration.stop()  # Stop API server
            await event_bus.shutdown()
        except Exception as e:
            logging.error(f"Error during shutdown: {e}", exc_info=True)
```

### Step 3: Run the Bot

```bash
python main.py backtest --config config/config.json
```

### Step 4: Open Dashboard

**Desktop:**
```
http://localhost:8080
```

**Mobile (on same network):**
1. Find your computer IP: `ipconfig` (Windows)
2. Open: `http://<YOUR_IP>:8080`

Example: `http://192.168.1.100:8080`

---

## 📱 Dashboard Controls Explained

### Control Buttons
```
▶ Start Bot      - Begin trading
⏸ Pause         - Pause trading (orders remain)
⏩ Resume        - Continue from pause
⏹ Stop Bot      - Stop all trading
```

### Status Section
Real-time updates showing:
- **Bot Status**: Running/Stopped
- **Balance**: Cash and crypto amounts
- **Grid Info**: Current price levels

### Metrics
- Total orders placed and filled
- Trading fees accumulated
- Open order count

### Orders Table
Recent trades with price, quantity, and status

---

## 🔌 API Endpoints (Programmatic Control)

### Start Bot
```bash
curl -X POST http://localhost:8080/api/bot/start
```

### Stop Bot
```bash
curl -X POST http://localhost:8080/api/bot/stop
```

### Get Status
```bash
curl http://localhost:8080/api/bot/status
```

### Get Metrics
```bash
curl http://localhost:8080/api/bot/metrics
```

---

## 🌐 Network Access

### To access from phone on same WiFi:

**Windows:**
```powershell
ipconfig
# Look for "IPv4 Address" under your network adapter
# Example: 192.168.1.100
```

**Mac/Linux:**
```bash
ifconfig
# Look for inet address
```

Then on phone, visit:
```
http://192.168.1.100:8080
```

### To change port (if 8080 is busy):
```python
# In main.py
api_integration = BotAPIIntegration(bot, event_bus, config_manager, port=9090)
```

---

## ✅ Verification Checklist

- [ ] `pip install aiohttp aiohttp-cors` completed
- [ ] main.py updated with API integration
- [ ] Web files in `web/dashboard/` folder
- [ ] Bot starts with `python main.py ...`
- [ ] Console shows "Bot API Server started on http://0.0.0.0:8080"
- [ ] Dashboard loads at http://localhost:8080
- [ ] Start/Stop buttons work
- [ ] Status updates in real-time
- [ ] Works on phone on same network

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8080 already in use | Change port: `BotAPIIntegration(..., port=9090)` |
| Dashboard won't load | Check if API server started in console |
| Phone can't access | Use correct IP, not localhost; same WiFi network |
| Buttons don't work | Check browser console (F12) for errors |
| Updates are slow | Normal - updates every 2 seconds |

---

## 📊 What You Can Do Now

✅ **Monitor** bot status from anywhere on your network
✅ **Control** bot with Start/Stop/Pause buttons
✅ **Track** balance and trading metrics in real-time
✅ **View** recent orders and fees
✅ **Adjust** risk settings (TP/SL) from dashboard
✅ **Use** on phone, tablet, or desktop

---

## 🔐 Security Note

⚠️ This dashboard is for **local network use only**. 

For remote/internet access, add authentication:
```python
# Add to bot_api_server.py handle_bot_start()
auth_header = request.headers.get('Authorization')
if auth_header != 'Bearer YOUR_SECRET_TOKEN':
    return web.json_response({'error': 'Unauthorized'}, status=401)
```

---

## 📞 Still Need Help?

1. Check console output for error messages
2. Review `WEB_DASHBOARD_GUIDE.md` for detailed docs
3. Verify all files exist in correct locations
4. Check firewall settings allow port 8080

Happy trading! 🚀

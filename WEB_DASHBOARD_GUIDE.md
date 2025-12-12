# Grid Trading Bot - Web Control Dashboard

## Overview
Control your trading bot from any device with a web browser - desktop, tablet, or mobile phone. The dashboard provides real-time monitoring and control with an on/off switch functionality.

## Features

### ✅ Bot Control
- **Start Bot**: Begin trading immediately
- **Stop Bot**: Halt all trading operations
- **Pause Bot**: Suspend trading while keeping orders in place
- **Resume Bot**: Continue trading from pause state

### 📊 Real-Time Monitoring
- Bot status (Running/Stopped)
- Trading pair and mode
- Account balance (Fiat + Crypto)
- Total portfolio value
- Grid configuration details
- Recent orders list

### 📈 Performance Metrics
- Total orders placed
- Open orders count
- Filled orders count
- Total trading fees

### ⚙️ Configuration Management
- Enable/disable take-profit
- Enable/disable stop-loss
- View strategy type and grid spacing
- View TP/SL thresholds

### 📱 Mobile-Responsive Design
- Works on phones (iOS/Android)
- Optimized for tablets
- Responsive layout for all screen sizes
- Touch-friendly buttons and controls

## Installation & Setup

### 1. Dependencies
The dashboard requires `aiohttp` and `aiohttp_cors` for the REST API server:

```bash
pip install aiohttp aiohttp_cors
```

### 2. Folder Structure
Ensure the web dashboard files are in place:
```
grid_trading_bot-master/
├── web/
│   └── dashboard/
│       ├── index.html
│       ├── styles.css
│       └── script.js
└── core/
    └── bot_management/
        ├── bot_api_server.py
        ├── bot_api_integration.py
        └── ...
```

### 3. Integration with main.py

Update `main.py` to include API server support:

```python
from core.bot_management.bot_api_integration import BotAPIIntegration

async def run_bot(...):
    config_manager = initialize_config(config_path)
    event_bus = EventBus()
    notification_handler = initialize_notification_handler(config_manager, event_bus)
    bot = GridTradingBot(...)
    
    # Add API integration
    api_integration = BotAPIIntegration(bot, event_bus, config_manager, port=8080)
    await api_integration.start()
    
    try:
        if bot.trading_mode in {TradingMode.LIVE, TradingMode.PAPER_TRADING}:
            bot_task = asyncio.create_task(bot.run(), name="BotTask")
            api_task = asyncio.create_task(api_integration.start(), name="APITask")
            # ... other tasks ...
            await asyncio.gather(bot_task, api_task, ...)
    finally:
        await api_integration.stop()
```

## Usage

### Access the Dashboard

**On Desktop:**
```
http://localhost:8080
```

**On Mobile (Local Network):**
Find your computer's IP address:
- Windows: `ipconfig` → IPv4 Address
- Mac/Linux: `ifconfig`

Then access from phone:
```
http://<YOUR_IP>:8080
```

Example:
```
http://192.168.1.100:8080
```

### Control the Bot

1. **Start Trading**: Click the green "▶ Start Bot" button
2. **Monitor**: Watch real-time status and balance updates
3. **Pause if Needed**: Click "⏸ Pause" to suspend trading temporarily
4. **Resume**: Click "⏩ Resume" to continue
5. **Stop**: Click the red "⏹ Stop Bot" to halt trading

### Monitor Performance

The dashboard displays:
- **Status**: Current bot operational state
- **Balance**: Fiat and crypto holdings
- **Grid Info**: Central price and grid levels
- **Orders**: List of recent trades
- **Metrics**: Total orders, fees, fill rates

## API Endpoints

The API server provides REST endpoints that can be accessed programmatically:

### Health Check
```bash
GET /api/health
```

### Bot Control
```bash
POST /api/bot/start      # Start bot
POST /api/bot/stop       # Stop bot
POST /api/bot/pause      # Pause bot
POST /api/bot/resume     # Resume bot
```

### Status & Metrics
```bash
GET /api/bot/status      # Get bot status
GET /api/bot/metrics     # Get trading metrics
GET /api/bot/orders      # Get recent orders
GET /api/config          # Get configuration
```

### Configuration
```bash
POST /api/config/update  # Update settings
```

### Example API Call (Python)
```python
import aiohttp

async with aiohttp.ClientSession() as session:
    # Start bot
    async with session.post('http://localhost:8080/api/bot/start') as resp:
        data = await resp.json()
        print(data)  # {'success': True, 'message': 'Bot starting...'}
    
    # Get status
    async with session.get('http://localhost:8080/api/bot/status') as resp:
        status = await resp.json()
        print(f"Bot running: {status['running']}")
```

### Example API Call (cURL)
```bash
# Start bot
curl -X POST http://localhost:8080/api/bot/start

# Get bot status
curl http://localhost:8080/api/bot/status

# Get metrics
curl http://localhost:8080/api/bot/metrics
```

## Dashboard Features in Detail

### Control Panel
Large, responsive buttons for quick bot control:
- Color-coded for easy identification (Green/Yellow/Cyan/Red)
- Icons for visual clarity
- Touch-optimized sizing

### Status Display
Real-time information including:
- Bot running status with color indicator
- Trading mode and pair
- Last update timestamp
- Balance breakdown

### Metrics Dashboard
Quick overview of trading performance:
- Total orders placed
- Open vs filled orders
- Accumulated trading fees

### Orders Table
Recent orders with:
- Order ID and side (BUY/SELL)
- Price and quantity
- Status and timestamp
- Scrollable table for mobile

### Configuration Panel
Manage risk settings:
- Enable/disable take-profit
- Enable/disable stop-loss
- View current thresholds
- Real-time updates

### Status Log
Activity log showing:
- Timestamps of all actions
- Success/error indicators
- Color-coded entries
- Auto-scrolling

## Troubleshooting

### Dashboard won't load
- Ensure API server is running on port 8080
- Check firewall settings
- Verify web files are in correct location

### Can't connect from phone
- Use correct IP address instead of localhost
- Ensure phone and computer are on same network
- Check Windows Firewall allows port 8080

### API endpoints returning errors
- Check bot logs for errors
- Verify bot is properly initialized
- Ensure required modules are imported

### Port already in use
- Change port in main.py: `BotAPIIntegration(..., port=9090)`
- Or kill process using port: `lsof -i :8080` (Mac/Linux)

## Security Notes

⚠️ **Important**: This dashboard is designed for **local network use only**.

For production/remote access:
1. Add authentication (JWT tokens)
2. Use HTTPS with self-signed certificates
3. Restrict API endpoints with rate limiting
4. Add request validation and sanitization
5. Use a reverse proxy (nginx)

Basic authentication example:
```python
# In bot_api_server.py
async def handle_bot_start(self, request):
    token = request.headers.get('Authorization')
    if not self._validate_token(token):
        return web.json_response({'error': 'Unauthorized'}, status=401)
    # ... rest of code
```

## Browser Compatibility

✅ **Tested and Working:**
- Chrome/Chromium (Desktop, Android)
- Safari (Desktop, iOS)
- Firefox (Desktop)
- Edge (Desktop)

✅ **Responsive on:**
- Desktop (1920x1080+)
- Tablets (iPad, Android tablets)
- Mobile phones (320px+)

## Performance

- **Update Frequency**: 2-second refresh interval
- **Auto-pause**: Updates pause when tab not visible
- **Lightweight**: ~50KB total assets
- **No external dependencies**: Pure HTML/CSS/JavaScript

## Future Enhancements

Planned features:
- [ ] WebSocket for real-time updates
- [ ] Historical price charts
- [ ] Advanced order filtering
- [ ] User authentication
- [ ] Email/SMS notifications via API
- [ ] Mobile app (PWA)
- [ ] Dark/Light theme toggle
- [ ] Multi-pair monitoring

---

**Need Help?** Check the bot logs and API server output for detailed error messages.

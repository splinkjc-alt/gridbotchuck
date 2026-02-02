# Grid Trading Bot - Mobile App Development Specification

## 🎯 Project Overview

**Product Name:** Grid Trading Bot
**Current Platform:** Python desktop application with web dashboard
**Target Mobile Platform:** Android (Kotlin/Java via Android Studio)
**Backend:** Python asyncio server with aiohttp REST API
**Exchange:** Kraken (via CCXT library)

The mobile app will be a **companion app** that connects to the running bot's REST API to monitor and control trading operations.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        MOBILE APP (Android)                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ Dashboard   │  │  Scanner    │  │  Settings/Config        │  │
│  │ Fragment    │  │  Fragment   │  │  Fragment               │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
│                           │                                      │
│                    ┌──────▼──────┐                              │
│                    │ API Client  │  (Retrofit/OkHttp)           │
│                    │ Repository  │                              │
│                    └──────┬──────┘                              │
└───────────────────────────┼─────────────────────────────────────┘
                            │ HTTP/JSON (REST API)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PYTHON BACKEND (Desktop/Server)              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   BotAPIServer (aiohttp)                   │ │
│  │                   Port: 8080 (configurable)                │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│  ┌───────────────┬───────────┼───────────┬──────────────────┐   │
│  │               │           │           │                  │   │
│  ▼               ▼           ▼           ▼                  ▼   │
│ GridTradingBot  OrderManager  BalanceTracker  MarketAnalyzer    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              ExchangeService (CCXT - Kraken)               │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📡 REST API Specification

**Base URL:** `http://{HOST}:8080/api`

### Bot Control Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `POST` | `/bot/start` | Start the trading bot | None | `{success: bool, message: str}` |
| `POST` | `/bot/stop` | Stop the trading bot | None | `{success: bool, message: str}` |
| `POST` | `/bot/pause` | Pause trading (keep orders) | None | `{success: bool, message: str}` |
| `POST` | `/bot/resume` | Resume trading | None | `{success: bool, message: str}` |
| `GET` | `/bot/status` | Get current bot status | None | See Status Response |
| `GET` | `/bot/metrics` | Get performance metrics | None | See Metrics Response |
| `GET` | `/bot/orders` | Get active orders | None | See Orders Response |
| `GET` | `/bot/pnl` | Get profit/loss data | None | See P&L Response |

### Configuration Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/config` | Get current configuration | None | Full config object |
| `POST` | `/config/update` | Update configuration | Partial config | `{success: bool}` |

### Market Scanner Endpoints

| Method | Endpoint | Description | Request Body | Response |
|--------|----------|-------------|--------------|----------|
| `GET` | `/market/pairs` | Get available trading pairs | None | `{pairs: [...]}` |
| `POST` | `/market/scan` | Scan markets for opportunities | See Scan Request | See Scan Response |
| `GET` | `/market/scan/results` | Get cached scan results | None | Cached results |
| `POST` | `/market/select` | Select a pair to trade | `{pair: "XXX/USD"}` | `{success: bool}` |

### Multi-Timeframe Analysis

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| `GET` | `/mtf/status` | Get MTF analysis status | See MTF Response |
| `POST` | `/mtf/analyze` | Trigger new analysis | Analysis results |

---

## 📊 API Response Models

### Status Response
```json
{
  "success": true,
  "status": "running",           // "running" | "stopped" | "paused" | "error"
  "pair": "LINK/USD",
  "mode": "live",                // "live" | "paper"
  "current_price": 12.53,
  "grid_range": {
    "low": 11.219,
    "high": 13.7122
  },
  "uptime_seconds": 3600
}
```

### Metrics Response
```json
{
  "success": true,
  "total_trades": 15,
  "profitable_trades": 12,
  "win_rate": 0.80,
  "total_profit_usd": 5.23,
  "total_profit_percent": 3.1,
  "current_drawdown": 0.5
}
```

### Orders Response
```json
{
  "success": true,
  "orders": [
    {
      "id": "ORDER123",
      "type": "limit",
      "side": "buy",              // "buy" | "sell"
      "price": 11.50,
      "amount": 2.5,
      "filled": 0.0,
      "status": "open",           // "open" | "filled" | "cancelled"
      "timestamp": "2025-12-19T20:00:00Z"
    }
  ],
  "count": 5
}
```

### P&L Response
```json
{
  "success": true,
  "realized_pnl": 5.23,
  "unrealized_pnl": 1.50,
  "total_pnl": 6.73,
  "total_pnl_percent": 4.0,
  "starting_value": 169.00,
  "current_value": 175.73,
  "base_balance": 13.1,
  "quote_balance": 5.00
}
```

### Scan Request
```json
{
  "min_price": 1.0,
  "max_price": 20.0,
  "timeframe": "15m",
  "quote_currency": "USD",
  "ema_fast_period": 9,
  "ema_slow_period": 21,
  "top_gainers_limit": 15
}
```

### Scan Response
```json
{
  "success": true,
  "results": [
    {
      "pair": "LINK/USD",
      "price": 12.53,
      "change_24h": 5.2,
      "volume_24h": 2876693,
      "score": 85.5,
      "signal": "bullish",        // "bullish" | "bearish" | "neutral"
      "volatility": 0.15,
      "ema_trend": "up",
      "recommendation": "Good for grid trading"
    }
  ],
  "count": 10,
  "timestamp": "2025-12-19T20:00:00Z"
}
```

### MTF (Multi-Timeframe) Response
```json
{
  "success": true,
  "analysis": {
    "primary_trend": "bearish",    // "bullish" | "bearish" | "neutral"
    "market_condition": "ranging", // "trending" | "ranging"
    "grid_signal": "ideal",        // "ideal" | "caution" | "avoid"
    "spacing_multiplier": 0.90,
    "recommended_bias": "neutral",
    "range_valid": true,
    "confidence": 100.0
  },
  "recommendations": [
    "Ideal conditions for grid trading",
    "Low volatility - consider tighter spacing"
  ]
}
```

### Configuration Object
```json
{
  "exchange": "kraken",
  "trading_pair": "LINK/USD",
  "trading_mode": "live",
  "grid": {
    "num_grids": 3,
    "grid_low": 11.219,
    "grid_high": 13.7122,
    "spacing_type": "geometric"   // "geometric" | "arithmetic"
  },
  "capital": {
    "initial_capital": 5.0,
    "initial_crypto_balance": 13.1
  },
  "strategy": {
    "name": "hedged_grid",
    "profit_rotation_enabled": true,
    "multi_pair_enabled": true
  },
  "risk": {
    "max_position_size": 100,
    "stop_loss_percent": 10.0
  }
}
```

---

## 🎨 Mobile App UI Screens

### 1. Dashboard Screen (Main)
- **Bot Status Card**: Running/Stopped indicator, current pair, price
- **P&L Summary Card**: Total profit, unrealized gains, percentages
- **Quick Actions**: Start/Stop/Pause buttons
- **Active Orders List**: Scrollable list of open orders
- **MTF Signal Badge**: Current market analysis signal

### 2. Market Scanner Screen
- **Filter Controls**: Price range sliders, timeframe picker
- **Scan Button**: Trigger market scan
- **Results Table**: Scrollable list with scores, signals
- **Select Pair Action**: Tap to switch trading pair

### 3. Settings Screen
- **Connection Settings**: Bot IP/hostname, port
- **Trading Parameters**: Grid size, range, capital
- **Notifications**: Push notification preferences
- **Theme**: Light/Dark mode

### 4. Orders Screen
- **Order History**: Filled orders with P&L per trade
- **Active Orders**: Current limit orders on exchange
- **Order Details**: Tap for full order info

---

## 🔧 Android Implementation Guide

### Recommended Tech Stack
```
- Language: Kotlin
- Architecture: MVVM with Repository pattern
- UI: Jetpack Compose (or XML with ViewBinding)
- Networking: Retrofit2 + OkHttp3 + Moshi/Gson
- Async: Kotlin Coroutines + Flow
- DI: Hilt (or Koin)
- Navigation: Jetpack Navigation Component
```

### Project Structure
```
app/
├── src/main/java/com/gridbot/
│   ├── data/
│   │   ├── api/
│   │   │   ├── BotApiService.kt      # Retrofit interface
│   │   │   └── models/               # API response models
│   │   ├── repository/
│   │   │   └── BotRepository.kt      # Data layer
│   │   └── local/
│   │       └── PreferencesManager.kt # SharedPrefs wrapper
│   ├── domain/
│   │   ├── models/                   # Domain models
│   │   └── usecases/                 # Business logic
│   ├── ui/
│   │   ├── dashboard/
│   │   │   ├── DashboardScreen.kt
│   │   │   └── DashboardViewModel.kt
│   │   ├── scanner/
│   │   │   ├── ScannerScreen.kt
│   │   │   └── ScannerViewModel.kt
│   │   ├── settings/
│   │   │   ├── SettingsScreen.kt
│   │   │   └── SettingsViewModel.kt
│   │   └── theme/
│   │       └── Theme.kt
│   └── di/
│       └── AppModule.kt              # Hilt modules
└── build.gradle.kts
```

### Retrofit API Service (Kotlin)
```kotlin
interface BotApiService {
    @GET("bot/status")
    suspend fun getBotStatus(): Response<BotStatusResponse>

    @GET("bot/metrics")
    suspend fun getMetrics(): Response<MetricsResponse>

    @GET("bot/orders")
    suspend fun getOrders(): Response<OrdersResponse>

    @GET("bot/pnl")
    suspend fun getPnL(): Response<PnLResponse>

    @POST("bot/start")
    suspend fun startBot(): Response<ActionResponse>

    @POST("bot/stop")
    suspend fun stopBot(): Response<ActionResponse>

    @POST("bot/pause")
    suspend fun pauseBot(): Response<ActionResponse>

    @POST("bot/resume")
    suspend fun resumeBot(): Response<ActionResponse>

    @GET("config")
    suspend fun getConfig(): Response<ConfigResponse>

    @POST("config/update")
    suspend fun updateConfig(@Body config: ConfigUpdate): Response<ActionResponse>

    @POST("market/scan")
    suspend fun scanMarkets(@Body request: ScanRequest): Response<ScanResponse>

    @GET("market/scan/results")
    suspend fun getScanResults(): Response<ScanResponse>

    @POST("market/select")
    suspend fun selectPair(@Body request: SelectPairRequest): Response<ActionResponse>

    @GET("mtf/status")
    suspend fun getMtfStatus(): Response<MtfResponse>
}
```

### Data Models (Kotlin)
```kotlin
data class BotStatusResponse(
    val success: Boolean,
    val status: String,
    val pair: String,
    val mode: String,
    @SerializedName("current_price") val currentPrice: Double,
    @SerializedName("grid_range") val gridRange: GridRange
)

data class GridRange(
    val low: Double,
    val high: Double
)

data class PnLResponse(
    val success: Boolean,
    @SerializedName("realized_pnl") val realizedPnl: Double,
    @SerializedName("unrealized_pnl") val unrealizedPnl: Double,
    @SerializedName("total_pnl") val totalPnl: Double,
    @SerializedName("total_pnl_percent") val totalPnlPercent: Double,
    @SerializedName("current_value") val currentValue: Double
)

data class ScanResult(
    val pair: String,
    val price: Double,
    @SerializedName("change_24h") val change24h: Double,
    val score: Double,
    val signal: String,
    val recommendation: String
)

data class ScanRequest(
    @SerializedName("min_price") val minPrice: Double = 1.0,
    @SerializedName("max_price") val maxPrice: Double = 20.0,
    val timeframe: String = "15m",
    @SerializedName("quote_currency") val quoteCurrency: String = "USD"
)
```

---

## 🔒 Security Considerations

1. **Network Security**
   - Use HTTPS when exposing API over internet
   - Implement API key authentication (add to bot)
   - Consider VPN/Tailscale for remote access

2. **Local Network**
   - App works best on same WiFi as bot
   - Use mDNS/Bonjour for discovery (optional)

3. **No API Keys in App**
   - Exchange API keys stay on the bot server
   - Mobile app only controls the bot, not the exchange directly

---

## 📱 Key Features for Mobile App

### Must Have (MVP)
- [ ] Connect to bot via IP/hostname
- [ ] View bot status (running/stopped)
- [ ] View current P&L and balances
- [ ] Start/Stop/Pause bot
- [ ] View active orders
- [ ] View MTF analysis signal

### Nice to Have (v2)
- [ ] Market scanner with results
- [ ] Push notifications on order fills
- [ ] Configuration editing
- [ ] Price charts
- [ ] Order history with trade log

### Future (v3)
- [ ] Multi-bot support
- [ ] Portfolio overview across bots
- [ ] Advanced analytics
- [ ] Widgets for home screen

---

## 🚀 Getting Started

### Prerequisites
1. Android Studio (latest stable)
2. Python bot running with API enabled
3. Both devices on same network (for local dev)

### Quick Test
```bash
# Verify bot API is accessible from phone
curl http://<BOT_IP>:8080/api/bot/status
```

### Connection Flow
1. App prompts for bot address (IP:port)
2. App tests connection with `/api/health` endpoint
3. On success, save to preferences
4. Start polling `/api/bot/status` every 2 seconds

---

## 📁 Related Files in Codebase

| File | Purpose |
|------|---------|
| `core/bot_management/bot_api_server.py` | REST API implementation |
| `core/bot_management/grid_trading_bot.py` | Main bot orchestrator |
| `core/order_handling/order_manager.py` | Order placement logic |
| `strategies/grid_trading_strategy.py` | Trading strategy |
| `strategies/market_analyzer.py` | Market scanning logic |
| `config/config.json` | Bot configuration |
| `web/dashboard/script.js` | Reference for API calls |
| `web/dashboard/index.html` | Reference for UI layout |

---

## 💡 Tips for AI Assistant

1. **API is already built** - Just consume the endpoints listed above
2. **Polling recommended** - Use 1-2 second intervals for status
3. **WebSocket optional** - REST polling works fine for mobile
4. **Error handling** - Bot may be offline, handle gracefully
5. **Config changes** - Some require bot restart to take effect
6. **Scanner takes time** - Market scan can take 30-90 seconds

---

*Document created: December 19, 2025*
*For Grid Trading Bot v1.0*

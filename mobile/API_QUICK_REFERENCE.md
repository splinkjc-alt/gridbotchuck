# Grid Trading Bot - API Quick Reference

## Connection
```
Base URL: http://{IP}:8080/api
Default Port: 8080
Protocol: HTTP (REST/JSON)
```

## Endpoints at a Glance

### Health Check
```http
GET /api/health
Response: {"status": "ok", "version": "1.0.0"}
```

### Bot Control
```http
GET  /api/bot/status     → Bot state, pair, price, grid range
GET  /api/bot/metrics    → Trade count, win rate, profit
GET  /api/bot/orders     → Active limit orders
GET  /api/bot/pnl        → Realized + unrealized P&L
POST /api/bot/start      → Start trading
POST /api/bot/stop       → Stop trading, cancel orders
POST /api/bot/pause      → Pause (keep orders)
POST /api/bot/resume     → Resume trading
```

### Configuration
```http
GET  /api/config          → Full configuration object
POST /api/config/update   → Partial config update
```

### Market Scanner
```http
GET  /api/market/pairs        → Available trading pairs
POST /api/market/scan         → Scan markets (takes 30-90s)
GET  /api/market/scan/results → Cached scan results
POST /api/market/select       → Select pair: {"pair": "LINK/USD"}
```

### Multi-Timeframe Analysis
```http
GET  /api/mtf/status   → Current MTF analysis
POST /api/mtf/analyze  → Trigger new analysis
```

### Multi-Pair Mode
```http
GET /api/multi-pair/status → Multi-pair trading status
```

---

## Common Response Shapes

### Success Action
```json
{"success": true, "message": "Bot started"}
```

### Error Response
```json
{"success": false, "error": "Bot already running"}
```

### Bot Status (GET /api/bot/status)
```json
{
  "success": true,
  "status": "running",
  "pair": "LINK/USD",
  "mode": "live",
  "current_price": 12.53,
  "grid_range": {"low": 11.22, "high": 13.71}
}
```

### P&L (GET /api/bot/pnl)
```json
{
  "success": true,
  "realized_pnl": 5.23,
  "unrealized_pnl": 1.50,
  "total_pnl": 6.73,
  "total_pnl_percent": 4.0,
  "base_balance": 13.1,
  "quote_balance": 5.00
}
```

### MTF Status (GET /api/mtf/status)
```json
{
  "success": true,
  "analysis": {
    "grid_signal": "ideal",
    "primary_trend": "bearish",
    "market_condition": "ranging",
    "confidence": 100.0
  }
}
```

---

## Polling Strategy

| Endpoint | Recommended Interval |
|----------|---------------------|
| `/api/bot/status` | 2 seconds |
| `/api/bot/pnl` | 5 seconds |
| `/api/bot/orders` | 5 seconds |
| `/api/mtf/status` | 30 seconds |
| `/api/bot/metrics` | 10 seconds |

---

## Android Retrofit Interface

```kotlin
interface GridBotApi {
    @GET("health")
    suspend fun health(): Response<HealthResponse>

    @GET("bot/status")
    suspend fun getStatus(): Response<StatusResponse>

    @GET("bot/pnl")
    suspend fun getPnL(): Response<PnLResponse>

    @GET("bot/orders")
    suspend fun getOrders(): Response<OrdersResponse>

    @POST("bot/start")
    suspend fun start(): Response<ActionResponse>

    @POST("bot/stop")
    suspend fun stop(): Response<ActionResponse>

    @POST("bot/pause")
    suspend fun pause(): Response<ActionResponse>

    @POST("bot/resume")
    suspend fun resume(): Response<ActionResponse>

    @GET("mtf/status")
    suspend fun getMtfStatus(): Response<MtfResponse>

    @POST("market/scan")
    suspend fun scanMarkets(@Body req: ScanRequest): Response<ScanResponse>
}
```

---

## Testing with cURL

```bash
# Test connection
curl http://192.168.1.100:8080/api/health

# Get status
curl http://192.168.1.100:8080/api/bot/status

# Start bot
curl -X POST http://192.168.1.100:8080/api/bot/start

# Stop bot
curl -X POST http://192.168.1.100:8080/api/bot/stop

# Scan markets
curl -X POST http://192.168.1.100:8080/api/market/scan \
  -H "Content-Type: application/json" \
  -d '{"min_price": 1, "max_price": 20}'
```

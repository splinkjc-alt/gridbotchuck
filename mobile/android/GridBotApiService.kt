// Grid Trading Bot - Retrofit API Service
// Copy to: app/src/main/java/com/gridbot/data/api/GridBotApiService.kt

package com.gridbot.data.api

import com.gridbot.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface GridBotApiService {
    
    // ============== Health Check ==============
    
    @GET("health")
    suspend fun checkHealth(): Response<HealthResponse>
    
    // ============== Bot Control ==============
    
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
    
    // ============== Configuration ==============
    
    @GET("config")
    suspend fun getConfig(): Response<ConfigResponse>
    
    @POST("config/update")
    suspend fun updateConfig(@Body config: Map<String, Any>): Response<ActionResponse>
    
    // ============== Market Scanner ==============
    
    @GET("market/pairs")
    suspend fun getAvailablePairs(): Response<Map<String, List<String>>>
    
    @POST("market/scan")
    suspend fun scanMarkets(@Body request: ScanRequest): Response<ScanResponse>
    
    @GET("market/scan/results")
    suspend fun getCachedScanResults(): Response<ScanResponse>
    
    @POST("market/select")
    suspend fun selectPair(@Body request: SelectPairRequest): Response<ActionResponse>
    
    // ============== Multi-Timeframe Analysis ==============
    
    @GET("mtf/status")
    suspend fun getMtfStatus(): Response<MtfResponse>
    
    @POST("mtf/analyze")
    suspend fun triggerMtfAnalysis(): Response<MtfResponse>
    
    // ============== Multi-Pair Mode ==============
    
    @GET("multi-pair/status")
    suspend fun getMultiPairStatus(): Response<Map<String, Any>>
}

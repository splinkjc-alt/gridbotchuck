// Grid Trading Bot - Android Kotlin Data Models
// Copy these to your Android Studio project

package com.gridbot.data.models

import com.google.gson.annotations.SerializedName

// ============== API Responses ==============

data class HealthResponse(
    val status: String,
    val version: String
)

data class ActionResponse(
    val success: Boolean,
    val message: String? = null,
    val error: String? = null
)

// ============== Bot Status ==============

data class BotStatusResponse(
    val success: Boolean,
    val status: String,  // "running" | "stopped" | "paused" | "error"
    val pair: String,
    val mode: String,    // "live" | "paper"
    @SerializedName("current_price")
    val currentPrice: Double,
    @SerializedName("grid_range")
    val gridRange: GridRange,
    @SerializedName("uptime_seconds")
    val uptimeSeconds: Long? = null
)

data class GridRange(
    val low: Double,
    val high: Double
)

// ============== Metrics ==============

data class MetricsResponse(
    val success: Boolean,
    @SerializedName("total_trades")
    val totalTrades: Int,
    @SerializedName("profitable_trades")
    val profitableTrades: Int,
    @SerializedName("win_rate")
    val winRate: Double,
    @SerializedName("total_profit_usd")
    val totalProfitUsd: Double,
    @SerializedName("total_profit_percent")
    val totalProfitPercent: Double,
    @SerializedName("current_drawdown")
    val currentDrawdown: Double
)

// ============== P&L ==============

data class PnLResponse(
    val success: Boolean,
    @SerializedName("realized_pnl")
    val realizedPnl: Double,
    @SerializedName("unrealized_pnl")
    val unrealizedPnl: Double,
    @SerializedName("total_pnl")
    val totalPnl: Double,
    @SerializedName("total_pnl_percent")
    val totalPnlPercent: Double,
    @SerializedName("starting_value")
    val startingValue: Double,
    @SerializedName("current_value")
    val currentValue: Double,
    @SerializedName("base_balance")
    val baseBalance: Double,
    @SerializedName("quote_balance")
    val quoteBalance: Double
)

// ============== Orders ==============

data class OrdersResponse(
    val success: Boolean,
    val orders: List<Order>,
    val count: Int
)

data class Order(
    val id: String,
    val type: String,     // "limit" | "market"
    val side: String,     // "buy" | "sell"
    val price: Double,
    val amount: Double,
    val filled: Double,
    val status: String,   // "open" | "filled" | "cancelled"
    val timestamp: String
)

// ============== MTF Analysis ==============

data class MtfResponse(
    val success: Boolean,
    val analysis: MtfAnalysis,
    val recommendations: List<String>? = null
)

data class MtfAnalysis(
    @SerializedName("primary_trend")
    val primaryTrend: String,       // "bullish" | "bearish" | "neutral"
    @SerializedName("market_condition")
    val marketCondition: String,    // "trending" | "ranging"
    @SerializedName("grid_signal")
    val gridSignal: String,         // "ideal" | "caution" | "avoid"
    @SerializedName("spacing_multiplier")
    val spacingMultiplier: Double,
    @SerializedName("recommended_bias")
    val recommendedBias: String,
    @SerializedName("range_valid")
    val rangeValid: Boolean,
    val confidence: Double
)

// ============== Market Scanner ==============

data class ScanRequest(
    @SerializedName("min_price")
    val minPrice: Double = 1.0,
    @SerializedName("max_price")
    val maxPrice: Double = 20.0,
    val timeframe: String = "15m",
    @SerializedName("quote_currency")
    val quoteCurrency: String = "USD",
    @SerializedName("ema_fast_period")
    val emaFastPeriod: Int = 9,
    @SerializedName("ema_slow_period")
    val emaSlowPeriod: Int = 21,
    @SerializedName("top_gainers_limit")
    val topGainersLimit: Int = 15
)

data class ScanResponse(
    val success: Boolean,
    val results: List<ScanResult>,
    val count: Int,
    val timestamp: String? = null,
    val error: String? = null
)

data class ScanResult(
    val pair: String,
    val price: Double,
    @SerializedName("change_24h")
    val change24h: Double,
    @SerializedName("volume_24h")
    val volume24h: Double,
    val score: Double,
    val signal: String,          // "bullish" | "bearish" | "neutral"
    val volatility: Double,
    @SerializedName("ema_trend")
    val emaTrend: String,
    val recommendation: String
)

data class SelectPairRequest(
    val pair: String
)

// ============== Configuration ==============

data class ConfigResponse(
    val success: Boolean,
    val config: BotConfig
)

data class BotConfig(
    val exchange: String,
    @SerializedName("trading_pair")
    val tradingPair: String,
    @SerializedName("trading_mode")
    val tradingMode: String,
    val grid: GridConfig,
    val capital: CapitalConfig,
    val strategy: StrategyConfig,
    val risk: RiskConfig
)

data class GridConfig(
    @SerializedName("num_grids")
    val numGrids: Int,
    @SerializedName("grid_low")
    val gridLow: Double,
    @SerializedName("grid_high")
    val gridHigh: Double,
    @SerializedName("spacing_type")
    val spacingType: String   // "geometric" | "arithmetic"
)

data class CapitalConfig(
    @SerializedName("initial_capital")
    val initialCapital: Double,
    @SerializedName("initial_crypto_balance")
    val initialCryptoBalance: Double
)

data class StrategyConfig(
    val name: String,
    @SerializedName("profit_rotation_enabled")
    val profitRotationEnabled: Boolean,
    @SerializedName("multi_pair_enabled")
    val multiPairEnabled: Boolean
)

data class RiskConfig(
    @SerializedName("max_position_size")
    val maxPositionSize: Double,
    @SerializedName("stop_loss_percent")
    val stopLossPercent: Double
)

// ============== Enums for Type Safety ==============

enum class BotStatus {
    RUNNING, STOPPED, PAUSED, ERROR;

    companion object {
        fun fromString(value: String): BotStatus {
            return when (value.lowercase()) {
                "running" -> RUNNING
                "stopped" -> STOPPED
                "paused" -> PAUSED
                else -> ERROR
            }
        }
    }
}

enum class TradingMode {
    LIVE, PAPER;

    companion object {
        fun fromString(value: String): TradingMode {
            return if (value.lowercase() == "paper") PAPER else LIVE
        }
    }
}

enum class GridSignal {
    IDEAL, CAUTION, AVOID;

    companion object {
        fun fromString(value: String): GridSignal {
            return when (value.lowercase()) {
                "ideal" -> IDEAL
                "caution" -> CAUTION
                else -> AVOID
            }
        }
    }
}

enum class MarketSignal {
    BULLISH, BEARISH, NEUTRAL;

    companion object {
        fun fromString(value: String): MarketSignal {
            return when (value.lowercase()) {
                "bullish" -> BULLISH
                "bearish" -> BEARISH
                else -> NEUTRAL
            }
        }
    }
}

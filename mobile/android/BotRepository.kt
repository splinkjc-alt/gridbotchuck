// Grid Trading Bot - Repository Pattern Implementation
// Copy to: app/src/main/java/com/gridbot/data/repository/BotRepository.kt

package com.gridbot.data.repository

import com.gridbot.data.api.GridBotApiService
import com.gridbot.data.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.delay
import javax.inject.Inject
import javax.inject.Singleton

sealed class Result<out T> {
    data class Success<T>(val data: T) : Result<T>()
    data class Error(val message: String, val exception: Throwable? = null) : Result<Nothing>()
    object Loading : Result<Nothing>()
}

@Singleton
class BotRepository @Inject constructor(
    private val apiService: GridBotApiService
) {

    // ============== Connection ==============

    suspend fun testConnection(): Result<HealthResponse> {
        return try {
            val response = apiService.checkHealth()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Connection failed: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Cannot connect to bot: ${e.message}", e)
        }
    }

    // ============== Bot Status Polling ==============

    fun pollBotStatus(intervalMs: Long = 2000): Flow<Result<BotStatusResponse>> = flow {
        while (true) {
            emit(getBotStatus())
            delay(intervalMs)
        }
    }.flowOn(Dispatchers.IO)

    suspend fun getBotStatus(): Result<BotStatusResponse> {
        return try {
            val response = apiService.getBotStatus()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to get status: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error getting status: ${e.message}", e)
        }
    }

    // ============== P&L Polling ==============

    fun pollPnL(intervalMs: Long = 5000): Flow<Result<PnLResponse>> = flow {
        while (true) {
            emit(getPnL())
            delay(intervalMs)
        }
    }.flowOn(Dispatchers.IO)

    suspend fun getPnL(): Result<PnLResponse> {
        return try {
            val response = apiService.getPnL()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to get P&L: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error getting P&L: ${e.message}", e)
        }
    }

    // ============== Bot Control ==============

    suspend fun startBot(): Result<ActionResponse> {
        return try {
            val response = apiService.startBot()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to start bot: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error starting bot: ${e.message}", e)
        }
    }

    suspend fun stopBot(): Result<ActionResponse> {
        return try {
            val response = apiService.stopBot()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to stop bot: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error stopping bot: ${e.message}", e)
        }
    }

    suspend fun pauseBot(): Result<ActionResponse> {
        return try {
            val response = apiService.pauseBot()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to pause bot: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error pausing bot: ${e.message}", e)
        }
    }

    suspend fun resumeBot(): Result<ActionResponse> {
        return try {
            val response = apiService.resumeBot()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to resume bot: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error resuming bot: ${e.message}", e)
        }
    }

    // ============== Orders ==============

    suspend fun getOrders(): Result<OrdersResponse> {
        return try {
            val response = apiService.getOrders()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to get orders: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error getting orders: ${e.message}", e)
        }
    }

    // ============== MTF Analysis ==============

    fun pollMtfStatus(intervalMs: Long = 30000): Flow<Result<MtfResponse>> = flow {
        while (true) {
            emit(getMtfStatus())
            delay(intervalMs)
        }
    }.flowOn(Dispatchers.IO)

    suspend fun getMtfStatus(): Result<MtfResponse> {
        return try {
            val response = apiService.getMtfStatus()
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to get MTF status: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error getting MTF status: ${e.message}", e)
        }
    }

    // ============== Market Scanner ==============

    suspend fun scanMarkets(request: ScanRequest = ScanRequest()): Result<ScanResponse> {
        return try {
            val response = apiService.scanMarkets(request)
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to scan markets: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error scanning markets: ${e.message}", e)
        }
    }

    suspend fun selectPair(pair: String): Result<ActionResponse> {
        return try {
            val response = apiService.selectPair(SelectPairRequest(pair))
            if (response.isSuccessful && response.body() != null) {
                Result.Success(response.body()!!)
            } else {
                Result.Error("Failed to select pair: ${response.code()}")
            }
        } catch (e: Exception) {
            Result.Error("Error selecting pair: ${e.message}", e)
        }
    }
}

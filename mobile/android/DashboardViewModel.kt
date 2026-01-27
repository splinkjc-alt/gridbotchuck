// Grid Trading Bot - Dashboard ViewModel
// Copy to: app/src/main/java/com/gridbot/ui/dashboard/DashboardViewModel.kt

package com.gridbot.ui.dashboard

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.gridbot.data.models.*
import com.gridbot.data.repository.BotRepository
import com.gridbot.data.repository.Result
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import javax.inject.Inject

data class DashboardUiState(
    val isConnected: Boolean = false,
    val isLoading: Boolean = true,
    val errorMessage: String? = null,

    // Bot Status
    val botStatus: String = "unknown",
    val tradingPair: String = "-",
    val tradingMode: String = "-",
    val currentPrice: Double = 0.0,
    val gridLow: Double = 0.0,
    val gridHigh: Double = 0.0,

    // P&L
    val totalPnl: Double = 0.0,
    val totalPnlPercent: Double = 0.0,
    val realizedPnl: Double = 0.0,
    val unrealizedPnl: Double = 0.0,
    val baseBalance: Double = 0.0,
    val quoteBalance: Double = 0.0,

    // MTF Analysis
    val gridSignal: String = "unknown",
    val marketCondition: String = "unknown",
    val primaryTrend: String = "unknown",

    // Orders
    val activeOrders: List<Order> = emptyList(),
    val orderCount: Int = 0
)

@HiltViewModel
class DashboardViewModel @Inject constructor(
    private val repository: BotRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(DashboardUiState())
    val uiState: StateFlow<DashboardUiState> = _uiState.asStateFlow()

    private var isPolling = false

    init {
        startPolling()
    }

    fun startPolling() {
        if (isPolling) return
        isPolling = true

        // Poll bot status every 2 seconds
        viewModelScope.launch {
            repository.pollBotStatus(2000).collect { result ->
                when (result) {
                    is Result.Success -> {
                        _uiState.update { state ->
                            state.copy(
                                isConnected = true,
                                isLoading = false,
                                errorMessage = null,
                                botStatus = result.data.status,
                                tradingPair = result.data.pair,
                                tradingMode = result.data.mode,
                                currentPrice = result.data.currentPrice,
                                gridLow = result.data.gridRange.low,
                                gridHigh = result.data.gridRange.high
                            )
                        }
                    }
                    is Result.Error -> {
                        _uiState.update { state ->
                            state.copy(
                                isConnected = false,
                                isLoading = false,
                                errorMessage = result.message
                            )
                        }
                    }
                    is Result.Loading -> {
                        _uiState.update { it.copy(isLoading = true) }
                    }
                }
            }
        }

        // Poll P&L every 5 seconds
        viewModelScope.launch {
            repository.pollPnL(5000).collect { result ->
                when (result) {
                    is Result.Success -> {
                        _uiState.update { state ->
                            state.copy(
                                totalPnl = result.data.totalPnl,
                                totalPnlPercent = result.data.totalPnlPercent,
                                realizedPnl = result.data.realizedPnl,
                                unrealizedPnl = result.data.unrealizedPnl,
                                baseBalance = result.data.baseBalance,
                                quoteBalance = result.data.quoteBalance
                            )
                        }
                    }
                    else -> { /* Handled by status polling */ }
                }
            }
        }

        // Poll MTF status every 30 seconds
        viewModelScope.launch {
            repository.pollMtfStatus(30000).collect { result ->
                when (result) {
                    is Result.Success -> {
                        _uiState.update { state ->
                            state.copy(
                                gridSignal = result.data.analysis.gridSignal,
                                marketCondition = result.data.analysis.marketCondition,
                                primaryTrend = result.data.analysis.primaryTrend
                            )
                        }
                    }
                    else -> { /* Handled by status polling */ }
                }
            }
        }
    }

    fun stopPolling() {
        isPolling = false
    }

    // ============== Bot Control Actions ==============

    fun startBot() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (val result = repository.startBot()) {
                is Result.Success -> {
                    _uiState.update { it.copy(isLoading = false) }
                    // Status will update via polling
                }
                is Result.Error -> {
                    _uiState.update { it.copy(
                        isLoading = false,
                        errorMessage = result.message
                    )}
                }
                else -> {}
            }
        }
    }

    fun stopBot() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (val result = repository.stopBot()) {
                is Result.Success -> {
                    _uiState.update { it.copy(isLoading = false) }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(
                        isLoading = false,
                        errorMessage = result.message
                    )}
                }
                else -> {}
            }
        }
    }

    fun pauseBot() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (val result = repository.pauseBot()) {
                is Result.Success -> {
                    _uiState.update { it.copy(isLoading = false) }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(
                        isLoading = false,
                        errorMessage = result.message
                    )}
                }
                else -> {}
            }
        }
    }

    fun resumeBot() {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true) }
            when (val result = repository.resumeBot()) {
                is Result.Success -> {
                    _uiState.update { it.copy(isLoading = false) }
                }
                is Result.Error -> {
                    _uiState.update { it.copy(
                        isLoading = false,
                        errorMessage = result.message
                    )}
                }
                else -> {}
            }
        }
    }

    fun refreshOrders() {
        viewModelScope.launch {
            when (val result = repository.getOrders()) {
                is Result.Success -> {
                    _uiState.update { state ->
                        state.copy(
                            activeOrders = result.data.orders,
                            orderCount = result.data.count
                        )
                    }
                }
                else -> {}
            }
        }
    }

    fun clearError() {
        _uiState.update { it.copy(errorMessage = null) }
    }
}

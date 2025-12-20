// Grid Trading Bot - Dashboard Screen (Jetpack Compose)
// Copy to: app/src/main/java/com/gridbot/ui/dashboard/DashboardScreen.kt

package com.gridbot.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.gridbot.data.models.Order

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val uiState by viewModel.uiState.collectAsState()
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Grid Trading Bot") },
                actions = {
                    // Connection indicator
                    Icon(
                        imageVector = if (uiState.isConnected) Icons.Default.Cloud else Icons.Default.CloudOff,
                        contentDescription = "Connection status",
                        tint = if (uiState.isConnected) Color.Green else Color.Red
                    )
                    Spacer(modifier = Modifier.width(16.dp))
                }
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // Error message
            uiState.errorMessage?.let { error ->
                item {
                    Card(
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.errorContainer)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(error, color = MaterialTheme.colorScheme.onErrorContainer)
                            IconButton(onClick = { viewModel.clearError() }) {
                                Icon(Icons.Default.Close, "Dismiss")
                            }
                        }
                    }
                }
            }
            
            // Status Card
            item {
                StatusCard(
                    status = uiState.botStatus,
                    pair = uiState.tradingPair,
                    mode = uiState.tradingMode,
                    price = uiState.currentPrice,
                    gridLow = uiState.gridLow,
                    gridHigh = uiState.gridHigh,
                    gridSignal = uiState.gridSignal
                )
            }
            
            // P&L Card
            item {
                PnLCard(
                    totalPnl = uiState.totalPnl,
                    totalPnlPercent = uiState.totalPnlPercent,
                    realizedPnl = uiState.realizedPnl,
                    unrealizedPnl = uiState.unrealizedPnl,
                    baseBalance = uiState.baseBalance,
                    quoteBalance = uiState.quoteBalance,
                    pair = uiState.tradingPair
                )
            }
            
            // Control Buttons
            item {
                ControlButtons(
                    status = uiState.botStatus,
                    isLoading = uiState.isLoading,
                    onStart = { viewModel.startBot() },
                    onStop = { viewModel.stopBot() },
                    onPause = { viewModel.pauseBot() },
                    onResume = { viewModel.resumeBot() }
                )
            }
            
            // Active Orders
            item {
                Text(
                    "Active Orders (${uiState.orderCount})",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
            }
            
            items(uiState.activeOrders) { order ->
                OrderItem(order = order)
            }
        }
    }
}

@Composable
fun StatusCard(
    status: String,
    pair: String,
    mode: String,
    price: Double,
    gridLow: Double,
    gridHigh: Double,
    gridSignal: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text(pair, fontSize = 24.sp, fontWeight = FontWeight.Bold)
                    Text(
                        mode.uppercase(),
                        color = if (mode == "live") Color(0xFFFF6B6B) else Color.Gray,
                        fontSize = 12.sp
                    )
                }
                
                StatusBadge(status = status)
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Current Price
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Current Price", color = Color.Gray)
                Text("$${String.format("%.4f", price)}", fontWeight = FontWeight.Bold)
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // Grid Range
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Grid Range", color = Color.Gray)
                Text("$${String.format("%.2f", gridLow)} - $${String.format("%.2f", gridHigh)}")
            }
            
            Spacer(modifier = Modifier.height(8.dp))
            
            // MTF Signal
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("Grid Signal", color = Color.Gray)
                SignalBadge(signal = gridSignal)
            }
        }
    }
}

@Composable
fun StatusBadge(status: String) {
    val (color, icon) = when (status.lowercase()) {
        "running" -> Pair(Color(0xFF4CAF50), Icons.Default.PlayArrow)
        "paused" -> Pair(Color(0xFFFF9800), Icons.Default.Pause)
        "stopped" -> Pair(Color(0xFFF44336), Icons.Default.Stop)
        else -> Pair(Color.Gray, Icons.Default.HelpOutline)
    }
    
    Surface(
        color = color.copy(alpha = 0.2f),
        shape = RoundedCornerShape(16.dp)
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 6.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(icon, status, tint = color, modifier = Modifier.size(16.dp))
            Spacer(modifier = Modifier.width(4.dp))
            Text(status.uppercase(), color = color, fontSize = 12.sp, fontWeight = FontWeight.Bold)
        }
    }
}

@Composable
fun SignalBadge(signal: String) {
    val color = when (signal.lowercase()) {
        "ideal" -> Color(0xFF4CAF50)
        "caution" -> Color(0xFFFF9800)
        "avoid" -> Color(0xFFF44336)
        else -> Color.Gray
    }
    
    Surface(
        color = color.copy(alpha = 0.2f),
        shape = RoundedCornerShape(8.dp)
    ) {
        Text(
            signal.uppercase(),
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
            color = color,
            fontSize = 12.sp,
            fontWeight = FontWeight.Bold
        )
    }
}

@Composable
fun PnLCard(
    totalPnl: Double,
    totalPnlPercent: Double,
    realizedPnl: Double,
    unrealizedPnl: Double,
    baseBalance: Double,
    quoteBalance: Double,
    pair: String
) {
    val isProfit = totalPnl >= 0
    val pnlColor = if (isProfit) Color(0xFF4CAF50) else Color(0xFFF44336)
    val baseCurrency = pair.split("/").firstOrNull() ?: "CRYPTO"
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text("Profit & Loss", fontWeight = FontWeight.Bold, fontSize = 16.sp)
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Total P&L
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center
            ) {
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text(
                        "${if (isProfit) "+" else ""}$${String.format("%.2f", totalPnl)}",
                        fontSize = 28.sp,
                        fontWeight = FontWeight.Bold,
                        color = pnlColor
                    )
                    Text(
                        "${if (isProfit) "+" else ""}${String.format("%.2f", totalPnlPercent)}%",
                        color = pnlColor
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
            Divider()
            Spacer(modifier = Modifier.height(16.dp))
            
            // Realized / Unrealized
            Row(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("Realized", color = Color.Gray, fontSize = 12.sp)
                    Text("$${String.format("%.2f", realizedPnl)}", fontWeight = FontWeight.Medium)
                }
                Column(modifier = Modifier.weight(1f)) {
                    Text("Unrealized", color = Color.Gray, fontSize = 12.sp)
                    Text("$${String.format("%.2f", unrealizedPnl)}", fontWeight = FontWeight.Medium)
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Balances
            Row(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.weight(1f)) {
                    Text("$baseCurrency Balance", color = Color.Gray, fontSize = 12.sp)
                    Text(String.format("%.4f", baseBalance), fontWeight = FontWeight.Medium)
                }
                Column(modifier = Modifier.weight(1f)) {
                    Text("USD Balance", color = Color.Gray, fontSize = 12.sp)
                    Text("$${String.format("%.2f", quoteBalance)}", fontWeight = FontWeight.Medium)
                }
            }
        }
    }
}

@Composable
fun ControlButtons(
    status: String,
    isLoading: Boolean,
    onStart: () -> Unit,
    onStop: () -> Unit,
    onPause: () -> Unit,
    onResume: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            when (status.lowercase()) {
                "stopped" -> {
                    Button(
                        onClick = onStart,
                        enabled = !isLoading,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4CAF50))
                    ) {
                        Icon(Icons.Default.PlayArrow, "Start")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("START")
                    }
                }
                "running" -> {
                    Button(
                        onClick = onPause,
                        enabled = !isLoading,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFFF9800))
                    ) {
                        Icon(Icons.Default.Pause, "Pause")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("PAUSE")
                    }
                    
                    Button(
                        onClick = onStop,
                        enabled = !isLoading,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF44336))
                    ) {
                        Icon(Icons.Default.Stop, "Stop")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("STOP")
                    }
                }
                "paused" -> {
                    Button(
                        onClick = onResume,
                        enabled = !isLoading,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4CAF50))
                    ) {
                        Icon(Icons.Default.PlayArrow, "Resume")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("RESUME")
                    }
                    
                    Button(
                        onClick = onStop,
                        enabled = !isLoading,
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFF44336))
                    ) {
                        Icon(Icons.Default.Stop, "Stop")
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("STOP")
                    }
                }
            }
            
            if (isLoading) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp))
            }
        }
    }
}

@Composable
fun OrderItem(order: Order) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = if (order.side == "buy") 
                Color(0xFF4CAF50).copy(alpha = 0.1f) 
            else 
                Color(0xFFF44336).copy(alpha = 0.1f)
        )
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column {
                Text(
                    order.side.uppercase(),
                    color = if (order.side == "buy") Color(0xFF4CAF50) else Color(0xFFF44336),
                    fontWeight = FontWeight.Bold
                )
                Text("${order.amount} @ $${order.price}", fontSize = 14.sp)
            }
            
            Text(order.status.uppercase(), color = Color.Gray, fontSize = 12.sp)
        }
    }
}

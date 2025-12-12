// API Configuration
const API_BASE_URL = window.location.origin + '/api';
const REFRESH_INTERVAL = 2000; // 2 seconds

// Global state
let botStatus = {
  running: false,
  trading_mode: '',
  trading_pair: '',
  timestamp: ''
};

let refreshInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  console.log('Dashboard initialized');
  console.log('API Base URL:', API_BASE_URL);
  loadConfig();
  updateStatus();
  updateMetrics();
  startAutoRefresh();
  loadScannerConfig();
});

// Auto-refresh status
function startAutoRefresh() {
  refreshInterval = setInterval(() => {
    updateStatus();
    updateMetrics();
    updateOrders();
  }, REFRESH_INTERVAL);
}

function stopAutoRefresh() {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}

// Update bot status
async function updateStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/bot/status`);

    if (!response.ok) {
      console.error(`API Error: ${response.status} ${response.statusText}`);
      setConnectionStatus(false);
      addLog(`API Error: ${response.status}`, 'error');
      return;
    }

    const data = await response.json();

    // Update connection status
    setConnectionStatus(true);

    // Update bot status display
    botStatus = data;
    document.getElementById('bot-status').textContent = data.running ? 'Running' : 'Stopped';
    document.getElementById('bot-status').className = data.running ? 'value status-running' : 'value status-stopped';
    document.getElementById('trading-mode').textContent = data.trading_mode || '--';
    document.getElementById('trading-pair').textContent = data.trading_pair || '--';
    document.getElementById('last-update').textContent = formatTime(data.timestamp);

    // Update balance if available
    if (data.balance) {
      document.getElementById('fiat-balance').textContent = '$' + formatNumber(data.balance.fiat, 2);
      document.getElementById('crypto-balance').textContent = formatNumber(data.balance.crypto, 6) + ' coins';
      document.getElementById('total-value').textContent = '$' + formatNumber(data.balance.total_value, 2);
    }

    // Update grid info if available
    if (data.grid) {
      document.getElementById('central-price').textContent = '$' + formatNumber(data.grid.central_price, 2);
      document.getElementById('total-grids').textContent = data.grid.num_grids;
      document.getElementById('buy-grids').textContent = data.grid.buy_grids;
      document.getElementById('sell-grids').textContent = data.grid.sell_grids;
    }

    updateFooterTime();
    addLog('Status updated', 'info');
  } catch (error) {
    console.error('Error updating status:', error);
    setConnectionStatus(false);
    addLog(`Connection error: ${error.message}`, 'error');
  }
}

// Update metrics
async function updateMetrics() {
  try {
    const response = await fetch(`${API_BASE_URL}/bot/metrics`);
    const data = await response.json();

    if (!response.ok) return;

    document.getElementById('total-orders').textContent = data.total_orders || '0';
    document.getElementById('open-orders').textContent = data.open_orders || '0';
    document.getElementById('filled-orders').textContent = data.filled_orders || '0';
    document.getElementById('total-fees').textContent = '$' + formatNumber(data.total_fees || 0, 4);
  } catch (error) {
    console.error('Error updating metrics:', error);
  }
}

// Update orders
async function updateOrders() {
  try {
    const response = await fetch(`${API_BASE_URL}/bot/orders`);
    const data = await response.json();

    if (!response.ok) return;

    const tbody = document.getElementById('orders-tbody');
    tbody.innerHTML = '';

    if (!data.orders || data.orders.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="no-data">No orders yet</td></tr>';
      return;
    }

    data.orders.forEach(order => {
      const row = document.createElement('tr');
      row.innerHTML = `
                <td>${order.id}</td>
                <td>${order.side}</td>
                <td>$${formatNumber(order.price, 2)}</td>
                <td>${formatNumber(order.quantity, 6)}</td>
                <td>${order.status}</td>
                <td>${order.timestamp}</td>
            `;
      tbody.appendChild(row);
    });
  } catch (error) {
    console.error('Error updating orders:', error);
  }
}

// Load configuration
async function loadConfig() {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    if (!response.ok) {
      console.warn('Failed to load config:', response.status);
      return;
    }
    const data = await response.json();

    if (!data.grid_config) {
      console.warn('No grid config in response');
      return;
    }

    document.getElementById('strategy-type').textContent = data.grid_config.type || '--';
    document.getElementById('grid-spacing').textContent = data.grid_config.spacing || '--';

    if (data.risk_management) {
      const tpCheckbox = document.getElementById('take-profit-toggle');
      const slCheckbox = document.getElementById('stop-loss-toggle');

      if (tpCheckbox) tpCheckbox.checked = data.risk_management.take_profit_enabled;
      if (slCheckbox) slCheckbox.checked = data.risk_management.stop_loss_enabled;

      document.getElementById('tp-threshold').textContent = '$' + formatNumber(data.risk_management.take_profit_threshold, 2);
      document.getElementById('sl-threshold').textContent = '$' + formatNumber(data.risk_management.stop_loss_threshold, 2);
    }
  } catch (error) {
    console.error('Error loading config:', error);
  }
}

// Bot control functions
async function startBot() {
  try {
    addLog('Starting bot...', 'info');
    const response = await fetch(`${API_BASE_URL}/bot/start`, { method: 'POST' });
    const data = await response.json();

    if (data.success) {
      addLog('Bot started successfully', 'success');
    } else {
      addLog('Failed to start bot: ' + data.message, 'error');
    }
    updateStatus();
  } catch (error) {
    addLog('Error starting bot: ' + error.message, 'error');
  }
}

async function stopBot() {
  if (!confirm('Are you sure you want to stop the bot?')) return;

  try {
    addLog('Stopping bot...', 'info');
    const response = await fetch(`${API_BASE_URL}/bot/stop`, { method: 'POST' });
    const data = await response.json();

    if (data.success) {
      addLog('Bot stopped successfully', 'success');
    } else {
      addLog('Failed to stop bot: ' + data.message, 'error');
    }
    updateStatus();
  } catch (error) {
    addLog('Error stopping bot: ' + error.message, 'error');
  }
}

async function pauseBot() {
  try {
    addLog('Pausing bot...', 'info');
    const response = await fetch(`${API_BASE_URL}/bot/pause`, { method: 'POST' });
    const data = await response.json();

    if (data.success) {
      addLog('Bot paused successfully', 'success');
    } else {
      addLog('Failed to pause bot: ' + data.message, 'error');
    }
    updateStatus();
  } catch (error) {
    addLog('Error pausing bot: ' + error.message, 'error');
  }
}

async function resumeBot() {
  try {
    addLog('Resuming bot...', 'info');
    const response = await fetch(`${API_BASE_URL}/bot/resume`, { method: 'POST' });
    const data = await response.json();

    if (data.success) {
      addLog('Bot resumed successfully', 'success');
    } else {
      addLog('Failed to resume bot: ' + data.message, 'error');
    }
    updateStatus();
  } catch (error) {
    addLog('Error resuming bot: ' + error.message, 'error');
  }
}

async function updateConfig() {
  try {
    const config = {
      take_profit_enabled: document.getElementById('take-profit-toggle').checked,
      stop_loss_enabled: document.getElementById('stop-loss-toggle').checked
    };

    const response = await fetch(`${API_BASE_URL}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });

    const data = await response.json();
    if (data.success) {
      addLog('Configuration updated', 'success');
    } else {
      addLog('Failed to update config: ' + data.message, 'error');
    }
  } catch (error) {
    addLog('Error updating config: ' + error.message, 'error');
  }
}

// ==========================================
// Market Scanner Functions
// ==========================================

let scanResults = [];
let isScanning = false;

async function scanMarkets() {
  if (isScanning) {
    addLog('Scan already in progress...', 'warning');
    return;
  }

  const scanBtn = document.getElementById('btn-scan');
  const scanStatus = document.getElementById('scan-status');

  try {
    isScanning = true;
    scanBtn.disabled = true;
    scanBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Scanning...</span>';
    scanStatus.textContent = 'Scanning markets... This may take a minute.';
    scanStatus.className = 'scan-status scanning';

    addLog('Starting market scan...', 'info');

    // Get filter values
    const minPrice = parseFloat(document.getElementById('min-price').value) || 1.0;
    const maxPrice = parseFloat(document.getElementById('max-price').value) || 20.0;
    const timeframe = document.getElementById('scan-timeframe').value || '15m';
    const emaFast = parseInt(document.getElementById('ema-fast-period')?.value) || 9;
    const emaSlow = parseInt(document.getElementById('ema-slow-period')?.value) || 21;

    const response = await fetch(`${API_BASE_URL}/market/scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        min_price: minPrice,
        max_price: maxPrice,
        timeframe: timeframe,
        quote_currency: 'USD',
        ema_fast_period: emaFast,
        ema_slow_period: emaSlow
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.message || 'Scan failed');
    }

    if (data.success) {
      scanResults = data.results || [];
      renderScanResults(scanResults);

      const msg = `Scan complete! Found ${scanResults.length} coins in $${minPrice}-$${maxPrice} range (EMA ${emaFast}/${emaSlow})`;
      scanStatus.textContent = msg;
      scanStatus.className = 'scan-status success';
      addLog(msg, 'success');

      if (scanResults.length > 0) {
        addLog(`Top pick: ${scanResults[0].pair} (Score: ${scanResults[0].score.toFixed(1)}, Signal: ${scanResults[0].signal})`, 'success');
      }
    } else {
      throw new Error(data.message || 'Scan failed');
    }

  } catch (error) {
    console.error('Scan error:', error);
    scanStatus.textContent = `Scan failed: ${error.message}`;
    scanStatus.className = 'scan-status error';
    addLog(`Scan error: ${error.message}`, 'error');
  } finally {
    isScanning = false;
    scanBtn.disabled = false;
    scanBtn.innerHTML = '<span class="btn-icon">🔍</span><span class="btn-text">Scan Markets</span>';
  }
}

function renderScanResults(results) {
  const tbody = document.getElementById('scanner-tbody');
  const countSpan = document.getElementById('results-count');

  tbody.innerHTML = '';
  countSpan.textContent = `(${results.length} results)`;

  if (!results || results.length === 0) {
    tbody.innerHTML = '<tr><td colspan="9" class="no-data">No coins found matching criteria</td></tr>';
    return;
  }

  results.forEach((coin, index) => {
    const row = document.createElement('tr');
    row.className = getSignalClass(coin.signal);

    // Determine signal emoji and color
    const signalEmoji = getSignalEmoji(coin.signal);
    const scoreColor = getScoreColor(coin.score);

    // EMA status
    const emaStatus = coin.flags.ema_bullish_cross ? '🔥 Cross!' :
      (coin.flags.price_above_emas ? '✅ Above' : '❌ Below');

    // CCI status
    const cciStatus = coin.flags.cci_bullish ? '✅' : '❌';
    const cciValue = coin.indicators.cci.toFixed(0);

    // MACD status
    const macdStatus = coin.flags.macd_bullish ? '✅' : '❌';

    row.innerHTML = `
      <td class="rank">#${index + 1}</td>
      <td class="pair"><strong>${coin.pair}</strong></td>
      <td class="price">$${coin.price.toFixed(4)}</td>
      <td class="score" style="color: ${scoreColor}"><strong>${coin.score.toFixed(1)}</strong></td>
      <td class="signal">${signalEmoji} ${formatSignal(coin.signal)}</td>
      <td class="ema">${emaStatus}</td>
      <td class="cci">${cciStatus} ${cciValue}</td>
      <td class="macd">${macdStatus}</td>
      <td class="actions">
        <button class="btn btn-small btn-info" onclick="showCoinDetails(${index})">📊 Details</button>
        <button class="btn btn-small btn-success" onclick="selectCoin('${coin.pair}')">✓ Select</button>
      </td>
    `;

    tbody.appendChild(row);
  });
}

function getSignalEmoji(signal) {
  switch (signal) {
    case 'strong_bullish': return '🚀';
    case 'bullish': return '📈';
    case 'neutral': return '➡️';
    case 'bearish': return '📉';
    case 'strong_bearish': return '💀';
    default: return '❓';
  }
}

function formatSignal(signal) {
  return signal.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}

function getSignalClass(signal) {
  switch (signal) {
    case 'strong_bullish': return 'signal-strong-bullish';
    case 'bullish': return 'signal-bullish';
    case 'neutral': return 'signal-neutral';
    case 'bearish': return 'signal-bearish';
    case 'strong_bearish': return 'signal-strong-bearish';
    default: return '';
  }
}

function getScoreColor(score) {
  if (score >= 75) return '#00c853';  // Bright green
  if (score >= 60) return '#64dd17';  // Light green
  if (score >= 45) return '#ffc107';  // Yellow
  if (score >= 30) return '#ff9800';  // Orange
  return '#f44336';  // Red
}

function showCoinDetails(index) {
  const coin = scanResults[index];
  if (!coin) return;

  const modal = document.getElementById('coin-details-modal');
  const pairName = document.getElementById('modal-pair-name');
  const details = document.getElementById('indicator-details');

  pairName.textContent = `${coin.pair} - Detailed Analysis`;

  details.innerHTML = `
    <div class="detail-section">
      <h4>📊 Overall</h4>
      <div class="detail-item"><label>Price:</label><span>$${coin.price.toFixed(4)}</span></div>
      <div class="detail-item"><label>Score:</label><span style="color: ${getScoreColor(coin.score)}">${coin.score.toFixed(2)}/100</span></div>
      <div class="detail-item"><label>Signal:</label><span>${getSignalEmoji(coin.signal)} ${formatSignal(coin.signal)}</span></div>
    </div>
    
    <div class="detail-section">
      <h4>📈 Moving Averages (EMA)</h4>
      <div class="detail-item"><label>EMA 9:</label><span>$${coin.indicators.ema_9.toFixed(4)}</span></div>
      <div class="detail-item"><label>EMA 21:</label><span>$${coin.indicators.ema_21.toFixed(4)}</span></div>
      <div class="detail-item"><label>Bullish Cross:</label><span>${coin.flags.ema_bullish_cross ? '✅ Yes!' : '❌ No'}</span></div>
      <div class="detail-item"><label>Price Above EMAs:</label><span>${coin.flags.price_above_emas ? '✅ Yes' : '❌ No'}</span></div>
      <div class="detail-item"><label>EMA Score:</label><span>${coin.scores.ema_crossover.toFixed(1)}</span></div>
    </div>
    
    <div class="detail-section">
      <h4>⚡ CCI Momentum</h4>
      <div class="detail-item"><label>CCI Value:</label><span>${coin.indicators.cci.toFixed(2)}</span></div>
      <div class="detail-item"><label>Bullish:</label><span>${coin.flags.cci_bullish ? '✅ Yes' : '❌ No'}</span></div>
      <div class="detail-item"><label>CCI Score:</label><span>${coin.scores.cci.toFixed(1)}</span></div>
    </div>
    
    <div class="detail-section">
      <h4>📊 MACD</h4>
      <div class="detail-item"><label>MACD Line:</label><span>${coin.indicators.macd.toFixed(6)}</span></div>
      <div class="detail-item"><label>Signal Line:</label><span>${coin.indicators.macd_signal.toFixed(6)}</span></div>
      <div class="detail-item"><label>Bullish:</label><span>${coin.flags.macd_bullish ? '✅ Yes' : '❌ No'}</span></div>
      <div class="detail-item"><label>MACD Score:</label><span>${coin.scores.macd.toFixed(1)}</span></div>
    </div>
    
    <div class="detail-section">
      <h4>📉 Other Indicators</h4>
      <div class="detail-item"><label>RSI:</label><span>${coin.indicators.rsi.toFixed(2)}</span></div>
      <div class="detail-item"><label>Volume Score:</label><span>${coin.scores.volume.toFixed(1)}</span></div>
      <div class="detail-item"><label>Bollinger Score:</label><span>${coin.scores.bollinger.toFixed(1)}</span></div>
      <div class="detail-item"><label>Candlestick Score:</label><span>${coin.scores.candlestick.toFixed(1)}</span></div>
    </div>
  `;

  modal.classList.remove('hidden');
}

function closeModal() {
  document.getElementById('coin-details-modal').classList.add('hidden');
}

async function selectCoin(pair) {
  try {
    addLog(`Selecting ${pair} for trading...`, 'info');

    const response = await fetch(`${API_BASE_URL}/market/select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pair: pair })
    });

    const data = await response.json();

    if (response.ok && data.status === 'success') {
      addLog(`✓ Selected ${pair} for trading`, 'success');
      closeModal();
      // Refresh status to show new trading pair
      await updateStatus();
      await loadConfig();
    } else {
      addLog(`Failed to select pair: ${data.message || 'Unknown error'}`, 'error');
    }
  } catch (error) {
    console.error('Error selecting coin:', error);
    addLog(`Error selecting pair: ${error.message}`, 'error');
  }
}

// ==========================================
// Auto-Scan Timer
// ==========================================
let autoScanInterval = null;
let autoScanMinutes = 5;

function startAutoScan() {
  if (autoScanInterval) {
    clearInterval(autoScanInterval);
  }

  autoScanMinutes = parseInt(document.getElementById('auto-scan-interval')?.value || 5);
  const intervalMs = autoScanMinutes * 60 * 1000;

  addLog(`Auto-scan started (every ${autoScanMinutes} minutes)`, 'info');
  document.getElementById('auto-scan-status').textContent = `On (${autoScanMinutes}m)`;
  document.getElementById('auto-scan-status').className = 'auto-scan-active';

  autoScanInterval = setInterval(async () => {
    addLog('Auto-scan triggered...', 'info');
    await scanMarkets();
  }, intervalMs);

  // Save setting
  saveAutoScanConfig();
}

function stopAutoScan() {
  if (autoScanInterval) {
    clearInterval(autoScanInterval);
    autoScanInterval = null;
  }
  addLog('Auto-scan stopped', 'info');
  document.getElementById('auto-scan-status').textContent = 'Off';
  document.getElementById('auto-scan-status').className = 'auto-scan-inactive';

  saveAutoScanConfig();
}

function toggleAutoScan() {
  if (autoScanInterval) {
    stopAutoScan();
  } else {
    startAutoScan();
  }
}

async function saveAutoScanConfig() {
  try {
    const config = {
      auto_scan_enabled: autoScanInterval !== null,
      auto_scan_interval_minutes: autoScanMinutes
    };

    await fetch(`${API_BASE_URL}/market/scanner-config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
  } catch (error) {
    console.error('Error saving auto-scan config:', error);
  }
}

async function loadScannerConfig() {
  try {
    const response = await fetch(`${API_BASE_URL}/market/scanner-config`);
    if (response.ok) {
      const config = await response.json();

      // Set EMA periods if available
      if (config.ema_fast_period) {
        const emaFastInput = document.getElementById('ema-fast-period');
        if (emaFastInput) emaFastInput.value = config.ema_fast_period;
      }
      if (config.ema_slow_period) {
        const emaSlowInput = document.getElementById('ema-slow-period');
        if (emaSlowInput) emaSlowInput.value = config.ema_slow_period;
      }

      // Set auto-scan interval
      if (config.auto_scan_interval_minutes) {
        autoScanMinutes = config.auto_scan_interval_minutes;
        const intervalInput = document.getElementById('auto-scan-interval');
        if (intervalInput) intervalInput.value = autoScanMinutes;
      }

      // Start auto-scan if enabled
      if (config.auto_scan_enabled) {
        startAutoScan();
      }
    }
  } catch (error) {
    console.error('Error loading scanner config:', error);
  }
}

// Close modal when clicking outside
window.onclick = function (event) {
  const modal = document.getElementById('coin-details-modal');
  if (event.target === modal) {
    closeModal();
  }
}

// ==========================================
// Utility functions
// ==========================================
function setConnectionStatus(connected) {
  const indicator = document.getElementById('status-indicator');
  const text = document.getElementById('connection-text');

  if (connected) {
    indicator.classList.add('connected');
    indicator.classList.remove('disconnected');
    text.textContent = 'Connected';
  } else {
    indicator.classList.remove('connected');
    indicator.classList.add('disconnected');
    text.textContent = 'Disconnected';
  }
}

function formatNumber(num, decimals = 2) {
  if (typeof num !== 'number') return '0';
  return num.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

function formatTime(timestamp) {
  if (!timestamp) return '--:--:--';
  const date = new Date(timestamp);
  return date.toLocaleTimeString();
}

function updateFooterTime() {
  const now = new Date();
  document.getElementById('footer-time').textContent = now.toLocaleTimeString();
}

function addLog(message, type = 'info') {
  const logsDisplay = document.getElementById('logs-display');
  const entry = document.createElement('div');
  entry.className = 'log-entry ' + type;

  const time = new Date().toLocaleTimeString();
  entry.textContent = `[${time}] ${message}`;

  logsDisplay.appendChild(entry);

  // Keep only last 50 logs
  while (logsDisplay.children.length > 50) {
    logsDisplay.removeChild(logsDisplay.firstChild);
  }

  // Auto-scroll to bottom
  logsDisplay.parentElement.scrollTop = logsDisplay.parentElement.scrollHeight;
}

// Load config on startup
loadConfig();

// Handle page visibility (pause updates when tab is not visible)
document.addEventListener('visibilitychange', () => {
  if (document.hidden) {
    stopAutoRefresh();
  } else {
    updateStatus();
    startAutoRefresh();
  }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
  stopAutoRefresh();
});
// =====================================================
// MULTI-PAIR TRADING FUNCTIONS
// =====================================================

// Start multi-pair trading
async function startMultiPair() {
  const btn = document.getElementById('btn-start-multi');
  btn.disabled = true;
  btn.querySelector('.btn-text').textContent = 'Starting...';

  try {
    const maxPairs = parseInt(document.getElementById('max-pairs').value) || 2;

    const response = await fetch(`${API_BASE_URL}/multi-pair/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ max_pairs: maxPairs })
    });

    const data = await response.json();

    if (data.success) {
      addLog(`Multi-pair trading started with ${data.pairs?.length || 0} pairs`, 'success');
      updateMultiPairStatus();
    } else {
      addLog(`Failed to start multi-pair: ${data.message}`, 'error');
    }
  } catch (error) {
    console.error('Error starting multi-pair:', error);
    addLog('Error starting multi-pair trading', 'error');
  } finally {
    btn.disabled = false;
    btn.querySelector('.btn-text').textContent = 'Start Multi-Pair';
  }
}

// Stop multi-pair trading
async function stopMultiPair() {
  const btn = document.getElementById('btn-stop-multi');
  btn.disabled = true;
  btn.querySelector('.btn-text').textContent = 'Stopping...';

  try {
    const response = await fetch(`${API_BASE_URL}/multi-pair/stop`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });

    const data = await response.json();

    if (data.success) {
      addLog('Multi-pair trading stopped', 'info');
      updateMultiPairStatus();
    } else {
      addLog(`Failed to stop multi-pair: ${data.message}`, 'error');
    }
  } catch (error) {
    console.error('Error stopping multi-pair:', error);
    addLog('Error stopping multi-pair trading', 'error');
  } finally {
    btn.disabled = false;
    btn.querySelector('.btn-text').textContent = 'Stop All';
  }
}

// Update multi-pair status display
async function updateMultiPairStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/multi-pair/status`);
    const data = await response.json();

    if (!data.success) return;

    const status = data.data;
    const statusText = document.getElementById('multi-status-text');
    const summaryDiv = document.getElementById('multi-pair-summary');
    const gridDiv = document.getElementById('multi-pair-grid');

    // Update status text
    if (status.running) {
      statusText.textContent = `Running (${status.active_pairs_count} pairs)`;
      statusText.className = 'status-value running';
      summaryDiv.style.display = 'flex';
    } else if (status.enabled) {
      statusText.textContent = 'Enabled (Idle)';
      statusText.className = 'status-value idle';
      summaryDiv.style.display = 'none';
    } else {
      statusText.textContent = 'Disabled';
      statusText.className = 'status-value disabled';
      summaryDiv.style.display = 'none';
    }

    // Update summary
    if (status.summary) {
      document.getElementById('multi-total-allocated').textContent =
        '$' + formatNumber(status.summary.total_allocated, 2);
      document.getElementById('multi-current-value').textContent =
        '$' + formatNumber(status.summary.total_current, 2);

      const pnl = status.summary.total_pnl;
      const pnlPct = status.summary.total_pnl_percent;
      const pnlElem = document.getElementById('multi-total-pnl');
      pnlElem.textContent = `$${formatNumber(pnl, 2)} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)`;
      pnlElem.className = pnl >= 0 ? 'summary-value pnl-positive' : 'summary-value pnl-negative';
    }

    // Update pair cards
    if (status.pairs && Object.keys(status.pairs).length > 0) {
      gridDiv.innerHTML = Object.values(status.pairs).map(pair => `
        <div class="pair-card ${pair.status}">
          <div class="pair-header">
            <span class="pair-name">${pair.pair}</span>
            <span class="pair-status-badge ${pair.status}">${pair.status}</span>
          </div>
          <div class="pair-details">
            <div class="pair-row">
              <span>Allocated:</span>
              <span>$${formatNumber(pair.allocated, 2)}</span>
            </div>
            <div class="pair-row">
              <span>Current:</span>
              <span>$${formatNumber(pair.current, 2)}</span>
            </div>
            <div class="pair-row">
              <span>Crypto:</span>
              <span>${formatNumber(pair.crypto, 6)}</span>
            </div>
            <div class="pair-row pnl-row">
              <span>P&L:</span>
              <span class="${pair.pnl >= 0 ? 'pnl-positive' : 'pnl-negative'}">
                $${formatNumber(pair.pnl, 2)} (${pair.pnl_percent >= 0 ? '+' : ''}${pair.pnl_percent.toFixed(2)}%)
              </span>
            </div>
            <div class="pair-row">
              <span>Orders:</span>
              <span>${pair.filled_orders} filled / ${pair.active_orders} active</span>
            </div>
          </div>
        </div>
      `).join('');
    } else {
      gridDiv.innerHTML = '<p class="no-data">Enable multi-pair trading to see active pairs</p>';
    }

  } catch (error) {
    console.error('Error updating multi-pair status:', error);
  }
}

// Add multi-pair status to auto-refresh
const originalStartAutoRefresh = startAutoRefresh;
startAutoRefresh = function () {
  refreshInterval = setInterval(() => {
    updateStatus();
    updateMetrics();
    updateOrders();
    updateMultiPairStatus();
    updatePriceChart();
    updatePnLDashboard();
  }, REFRESH_INTERVAL);
};

// ============================================
// LIVE PRICE CHART
// ============================================

let priceChart = null;
let priceHistory = [];
let startTime = Date.now();
let startBalance = null;

// Initialize Chart
function initPriceChart() {
  const ctx = document.getElementById('priceChart');
  if (!ctx) return;

  priceChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Price',
        data: [],
        borderColor: '#3b82f6',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        borderWidth: 2,
        fill: true,
        tension: 0.4,
        pointRadius: 0,
        pointHoverRadius: 6,
        pointHoverBackgroundColor: '#3b82f6',
        pointHoverBorderColor: '#fff',
        pointHoverBorderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        intersect: false,
        mode: 'index'
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(30, 41, 59, 0.95)',
          titleColor: '#f1f5f9',
          bodyColor: '#f1f5f9',
          borderColor: '#334155',
          borderWidth: 1,
          padding: 12,
          displayColors: false,
          callbacks: {
            label: function (context) {
              return `Price: $${context.parsed.y.toFixed(2)}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: {
            color: 'rgba(51, 65, 85, 0.5)',
            drawBorder: false
          },
          ticks: {
            color: '#94a3b8',
            maxTicksLimit: 8
          }
        },
        y: {
          grid: {
            color: 'rgba(51, 65, 85, 0.5)',
            drawBorder: false
          },
          ticks: {
            color: '#94a3b8',
            callback: function (value) {
              return '$' + value.toFixed(2);
            }
          }
        }
      }
    }
  });
}

// Update price chart with new data
function updatePriceChart() {
  const priceElement = document.getElementById('header-price');
  if (!priceElement || !priceChart) return;

  // Get current price from status
  const currentPrice = parseFloat(priceElement.textContent.replace('$', ''));
  if (isNaN(currentPrice) || currentPrice === 0) return;

  const now = new Date();
  const timeLabel = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });

  // Add to history (keep last 60 points for 2 minute view at 2s intervals)
  priceHistory.push({ time: timeLabel, price: currentPrice });
  if (priceHistory.length > 60) {
    priceHistory.shift();
  }

  // Update chart
  priceChart.data.labels = priceHistory.map(p => p.time);
  priceChart.data.datasets[0].data = priceHistory.map(p => p.price);
  priceChart.update('none');
}

// Update header with live price
function updateHeaderPrice(price, previousPrice) {
  const priceEl = document.getElementById('header-price');
  const changeEl = document.getElementById('header-change');

  if (priceEl) {
    priceEl.textContent = '$' + formatNumber(price, 2);
  }

  if (changeEl && previousPrice && previousPrice > 0) {
    const change = ((price - previousPrice) / previousPrice) * 100;
    changeEl.textContent = (change >= 0 ? '+' : '') + change.toFixed(2) + '%';
    changeEl.className = 'price-change ' + (change >= 0 ? 'positive' : 'negative');
  }
}

// ============================================
// P&L DASHBOARD
// ============================================

function updatePnLDashboard() {
  // Total Portfolio
  const totalValueEl = document.getElementById('total-value');
  const pnlTotalEl = document.getElementById('pnl-total');
  if (totalValueEl && pnlTotalEl) {
    pnlTotalEl.textContent = totalValueEl.textContent;
  }

  // Session P&L
  const currentTotal = parseFloat((document.getElementById('total-value')?.textContent || '0').replace(/[$,]/g, ''));
  if (startBalance === null && currentTotal > 0) {
    startBalance = currentTotal;
  }

  if (startBalance && currentTotal) {
    const sessionPnL = currentTotal - startBalance;
    const sessionPercent = ((sessionPnL / startBalance) * 100);

    const pnlSessionEl = document.getElementById('pnl-session');
    const pnlPercentEl = document.getElementById('pnl-percent');

    if (pnlSessionEl) {
      pnlSessionEl.textContent = (sessionPnL >= 0 ? '+' : '') + '$' + formatNumber(Math.abs(sessionPnL), 2);
      pnlSessionEl.className = 'pnl-value ' + (sessionPnL >= 0 ? 'positive' : 'negative');
    }
    if (pnlPercentEl) {
      pnlPercentEl.textContent = '(' + (sessionPercent >= 0 ? '+' : '') + sessionPercent.toFixed(2) + '%)';
    }
  }

  // Trades count
  const filledOrdersEl = document.getElementById('filled-orders');
  const pnlTradesEl = document.getElementById('pnl-trades');
  if (filledOrdersEl && pnlTradesEl) {
    pnlTradesEl.textContent = filledOrdersEl.textContent;
  }

  // Uptime
  const uptimeEl = document.getElementById('pnl-uptime');
  if (uptimeEl) {
    const elapsed = Date.now() - startTime;
    const hours = Math.floor(elapsed / 3600000);
    const minutes = Math.floor((elapsed % 3600000) / 60000);
    const seconds = Math.floor((elapsed % 60000) / 1000);
    uptimeEl.textContent =
      String(hours).padStart(2, '0') + ':' +
      String(minutes).padStart(2, '0') + ':' +
      String(seconds).padStart(2, '0');
  }
}

// Chart range buttons
document.addEventListener('DOMContentLoaded', () => {
  // Initialize price chart
  if (typeof Chart !== 'undefined') {
    initPriceChart();
  }

  // Chart range button handlers
  document.querySelectorAll('.chart-btn').forEach(btn => {
    btn.addEventListener('click', function () {
      document.querySelectorAll('.chart-btn').forEach(b => b.classList.remove('active'));
      this.classList.add('active');
      // Range functionality can be extended here
    });
  });
});

// Helper functions for footer
function showAbout() {
  alert('GridBot Pro v2.0\\n\\nAutomated cryptocurrency grid trading bot.\\n\\nFeatures:\\n• Multi-pair trading\\n• Market scanner with technical indicators\\n• Real-time price monitoring\\n• Configurable grid strategies');
}

function showHelp() {
  alert('GridBot Pro Help\\n\\n1. Set up your API keys in config.json\\n2. Configure grid parameters\\n3. Click Start Bot to begin trading\\n4. Monitor your positions in real-time\\n\\nFor support, check the documentation.');
}
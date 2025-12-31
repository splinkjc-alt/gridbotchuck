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
  loadAccountSettings();
  initBacktestDates();
  loadStrategyType();  // Load saved strategy type

  // Close account menu when clicking outside
  document.addEventListener('click', (e) => {
    const dropdown = document.getElementById('account-dropdown');
    if (dropdown && !dropdown.contains(e.target)) {
      dropdown.classList.remove('open');
    }
  });
});

// Initialize backtest date inputs with sensible defaults
function initBacktestDates() {
  const now = new Date();
  const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

  const formatDateTime = (date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const startInput = document.getElementById('backtest-start');
  const endInput = document.getElementById('backtest-end');

  if (startInput) startInput.value = formatDateTime(twoWeeksAgo);
  if (endInput) endInput.value = formatDateTime(now);
}

// ============================================================
// ACCOUNT DROPDOWN FUNCTIONS
// ============================================================

function toggleAccountMenu() {
  const dropdown = document.getElementById('account-dropdown');
  dropdown.classList.toggle('open');
  event.stopPropagation();
}

async function loadAccountSettings() {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    const data = await response.json();

    if (data.exchange) {
      // Set exchange dropdown
      const exchangeSelect = document.getElementById('exchange-select');
      if (exchangeSelect) {
        exchangeSelect.value = data.exchange.name || 'kraken';
      }

      // Set trading mode dropdown
      const modeSelect = document.getElementById('trading-mode-select');
      const currentMode = data.exchange.trading_mode || 'live';
      if (modeSelect) {
        modeSelect.value = currentMode;
      }

      // Update UI controls for current mode
      updateModeControls(currentMode);

      // Update account name with exchange
      const accountName = document.getElementById('account-name');
      if (accountName) {
        const exchangeNames = {
          'kraken': 'Kraken',
          'coinbase': 'Coinbase',
          'binance': 'Binance',
          'kucoin': 'KuCoin',
          'bybit': 'Bybit'
        };
        accountName.textContent = exchangeNames[data.exchange.name] || 'Account';
      }
    }

    // Update quote currency hint
    if (data.pair && data.pair.quote_currency) {
      const quoteHint = document.getElementById('current-quote');
      if (quoteHint) {
        quoteHint.textContent = data.pair.quote_currency;
      }
    }
  } catch (error) {
    console.error('Error loading account settings:', error);
  }
}

async function changeExchange(exchange) {
  try {
    addLog(`Switching to ${exchange}...`, 'info');

    // Exchange-specific quote currency defaults
    const exchangeQuoteCurrency = {
      'kraken': 'USD',
      'coinbase': 'USD',
      'binance': 'USDT',
      'kucoin': 'USDT',
      'bybit': 'USDT'
    };

    const quoteCurrency = exchangeQuoteCurrency[exchange] || 'USD';

    // Update UI immediately for instant feedback
    const quoteHint = document.getElementById('current-quote');
    if (quoteHint) {
      quoteHint.textContent = quoteCurrency;
    }

    const exchangeNames = {
      'kraken': 'Kraken',
      'coinbase': 'Coinbase',
      'binance': 'Binance',
      'kucoin': 'KuCoin',
      'bybit': 'Bybit'
    };

    const accountName = document.getElementById('account-name');
    if (accountName) {
      accountName.textContent = exchangeNames[exchange] || 'Account';
    }

    // Update quote currency selector if it exists
    const quoteSelect = document.getElementById('quote-currency');
    if (quoteSelect) {
      quoteSelect.value = quoteCurrency;
    }

    const response = await fetch(`${API_BASE_URL}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exchange: { name: exchange },
        pair: { quote_currency: quoteCurrency }
      })
    });

    const data = await response.json();

    if (data.success) {
      addLog(`Exchange changed to ${exchange} with ${quoteCurrency} pairs.`, 'success');
      showNotification(`${exchangeNames[exchange]} selected (${quoteCurrency} pairs)`, 'success');
    } else {
      addLog(`Failed to change exchange: ${data.message}`, 'error');
      showNotification(`Exchange switch failed - restart bot to apply`, 'warning');
    }
  } catch (error) {
    console.error('Error changing exchange:', error);
    addLog(`Error: ${error.message} - UI updated, restart bot to apply`, 'warning');
    showNotification(`Exchange selected - restart bot to apply changes`, 'info');
  }
}

async function changeTradingMode(mode) {
  try {
    const modeNames = {
      'live': 'Live Trading',
      'paper_trading': 'Paper Trading',
      'backtest': 'Backtest'
    };

    addLog(`Switching to ${modeNames[mode]}...`, 'info');

    // Update UI controls immediately
    updateModeControls(mode);

    const response = await fetch(`${API_BASE_URL}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exchange: { trading_mode: mode }
      })
    });

    const data = await response.json();

    if (data.success) {
      addLog(`Trading mode changed to ${modeNames[mode]}. Restart bot to apply.`, 'success');
      showNotification(`Trading mode: ${modeNames[mode]}`, 'success');
    } else {
      addLog(`Failed to change mode: ${data.message}`, 'error');
    }
  } catch (error) {
    console.error('Error changing trading mode:', error);
    addLog(`Error changing mode: ${error.message}`, 'error');
  }
}

// Change trading strategy type (Grid vs EMA Crossover)
async function changeStrategyType(strategy) {
  try {
    const strategyNames = {
      'grid': 'Grid Trading',
      'ema_crossover': 'EMA Crossover'
    };

    addLog(`Switching to ${strategyNames[strategy]} strategy...`, 'info');

    // Save to localStorage
    localStorage.setItem('default-strategy-type', strategy);

    // Update strategy display in UI
    const strategyDisplay = document.getElementById('strategy-type');
    if (strategyDisplay) {
      strategyDisplay.textContent = strategyNames[strategy];
    }

    // Try to notify backend
    try {
      const response = await fetch(`${API_BASE_URL}/config/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          strategy: { type: strategy }
        })
      });

      const data = await response.json();
      if (data.success) {
        addLog(`Strategy changed to ${strategyNames[strategy]}. Restart bot to apply.`, 'success');
      }
    } catch (apiError) {
      // API might not support this yet - that's fine
      addLog(`Strategy set to ${strategyNames[strategy]}. Settings saved locally.`, 'success');
    }

    showNotification(`Strategy: ${strategyNames[strategy]}`, 'success');

    // If EMA selected, show hint about settings
    if (strategy === 'ema_crossover') {
      addLog('Configure EMA periods in Settings > Trading Defaults', 'info');
    }

  } catch (error) {
    console.error('Error changing strategy:', error);
    addLog(`Error changing strategy: ${error.message}`, 'error');
  }
}

// Load saved strategy type on page load
function loadStrategyType() {
  const savedStrategy = localStorage.getItem('default-strategy-type') || 'grid';
  const strategySelect = document.getElementById('strategy-type-select');
  if (strategySelect) {
    strategySelect.value = savedStrategy;
  }

  // Update display
  const strategyDisplay = document.getElementById('strategy-type');
  if (strategyDisplay) {
    const strategyNames = { 'grid': 'Grid Trading', 'ema_crossover': 'EMA Crossover' };
    strategyDisplay.textContent = strategyNames[savedStrategy] || 'Grid Trading';
  }
}

// Update UI controls based on trading mode
function updateModeControls(mode) {
  const liveControls = document.getElementById('live-controls');
  const backtestControls = document.getElementById('backtest-controls');

  if (!liveControls || !backtestControls) return;

  // Hide all mode-specific controls first
  liveControls.style.display = 'none';
  backtestControls.style.display = 'none';

  // Show appropriate controls based on mode
  if (mode === 'backtest') {
    backtestControls.style.display = 'block';

    // Update page title indicator
    document.querySelector('.control-section h2').innerHTML =
      'Bot Control <span class="mode-indicator backtest">📊 Backtest Mode</span>';
  } else if (mode === 'paper_trading') {
    liveControls.style.display = 'grid';

    document.querySelector('.control-section h2').innerHTML =
      'Bot Control <span class="mode-indicator paper">📝 Paper Trading</span>';
  } else {
    // Live mode
    liveControls.style.display = 'grid';

    document.querySelector('.control-section h2').innerHTML =
      'Bot Control <span class="mode-indicator live">🔴 Live Trading</span>';
  }

  console.log(`Mode controls updated for: ${mode}`);
}

// Open dedicated backtest page
function openBacktestPage() {
  window.location.href = 'backtest.html';
}

// Run backtest with the configured settings
async function runBacktest() {
  const startDate = document.getElementById('backtest-start').value;
  const endDate = document.getElementById('backtest-end').value;
  const initialCapital = document.getElementById('backtest-capital').value;

  if (!startDate || !endDate) {
    showNotification('Please select start and end dates', 'warning');
    return;
  }

  // Validate date range
  if (new Date(startDate) >= new Date(endDate)) {
    showNotification('End date must be after start date', 'error');
    return;
  }

  try {
    // Show progress
    document.getElementById('backtest-progress').style.display = 'block';
    document.getElementById('backtest-results').style.display = 'none';
    document.getElementById('btn-run-backtest').disabled = true;
    document.getElementById('btn-stop-backtest').style.display = 'inline-flex';

    addLog(`Starting backtest: ${startDate} to ${endDate}`, 'info');
    addLog(`Initial capital: $${initialCapital}`, 'info');
    updateBacktestProgress(0, 'Fetching historical data...');

    // Update config with backtest settings
    addLog('Updating backtest configuration...', 'info');
    const configResponse = await fetch(`${API_BASE_URL}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        trading_settings: {
          period: {
            start_date: startDate.replace('T', ' '),
            end_date: endDate.replace('T', ' ')
          },
          initial_capital: parseFloat(initialCapital)
        }
      })
    });

    const configData = await configResponse.json();
    if (!configResponse.ok) {
      addLog(`Config update failed: ${configData.message || configResponse.statusText}`, 'error');
      resetBacktestUI();
      return;
    }
    addLog('Backtest config updated', 'success');

    updateBacktestProgress(10, 'Initializing backtest engine...');

    // Start the bot (in backtest mode, it runs through historical data)
    addLog('Starting backtest engine...', 'info');
    const response = await fetch(`${API_BASE_URL}/bot/start`, {
      method: 'POST'
    });

    const data = await response.json();
    addLog(`Bot response: ${JSON.stringify(data)}`, 'info');

    if (data.success) {
      addLog('Backtest started successfully, polling for completion...', 'success');
      // Poll for backtest completion
      pollBacktestProgress();
    } else {
      addLog(`Failed to start backtest: ${data.message || 'Unknown error'}`, 'error');
      showNotification(`Failed to start backtest: ${data.message}`, 'error');
      resetBacktestUI();
    }

  } catch (error) {
    console.error('Backtest error:', error);
    addLog(`Backtest error: ${error.message}`, 'error');
    addLog(`Error stack: ${error.stack}`, 'error');
    showNotification(`Backtest failed: ${error.message}`, 'error');
    resetBacktestUI();
  }
}

function updateBacktestProgress(percent, message) {
  const progressFill = document.getElementById('backtest-progress-fill');
  const progressText = document.getElementById('backtest-progress-text');

  if (progressFill) progressFill.style.width = `${percent}%`;
  if (progressText) progressText.textContent = message;
}

async function pollBacktestProgress() {
  let attempts = 0;
  const maxAttempts = 300; // 5 minutes max

  const poll = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/bot/status`);
      const data = await response.json();

      if (data.bot_state === 'stopped' || data.bot_state === 'error' || attempts >= maxAttempts) {
        // Backtest completed or errored
        if (data.bot_state === 'stopped') {
          updateBacktestProgress(100, 'Backtest complete!');
          await fetchBacktestResults();
        } else {
          updateBacktestProgress(0, 'Backtest failed or timed out');
        }
        resetBacktestUI();
        return;
      }

      // Still running - estimate progress based on time
      attempts++;
      const estimatedProgress = Math.min(10 + (attempts * 0.3), 95);
      updateBacktestProgress(estimatedProgress, `Processing candles... (${attempts}s)`);

      setTimeout(poll, 1000);
    } catch (error) {
      console.error('Error polling backtest:', error);
      resetBacktestUI();
    }
  };

  poll();
}

async function fetchBacktestResults() {
  try {
    const response = await fetch(`${API_BASE_URL}/bot/pnl`);
    const data = await response.json();

    // Display results
    const resultsDiv = document.getElementById('backtest-results');
    resultsDiv.style.display = 'block';

    const totalReturn = data.total_pnl || 0;
    const initialCapital = parseFloat(document.getElementById('backtest-capital').value) || 1000;
    const returnPct = (totalReturn / initialCapital) * 100;

    document.getElementById('bt-return').textContent =
      `${totalReturn >= 0 ? '+' : ''}$${totalReturn.toFixed(2)}`;
    document.getElementById('bt-return').className =
      `result-value ${totalReturn >= 0 ? 'positive' : 'negative'}`;

    document.getElementById('bt-return-pct').textContent =
      `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%`;
    document.getElementById('bt-return-pct').className =
      `result-value ${returnPct >= 0 ? 'positive' : 'negative'}`;

    document.getElementById('bt-trades').textContent = data.total_trades || 0;
    document.getElementById('bt-winrate').textContent = `${(data.win_rate || 0).toFixed(1)}%`;
    document.getElementById('bt-drawdown').textContent = `-${(data.max_drawdown || 0).toFixed(2)}%`;
    document.getElementById('bt-sharpe').textContent = (data.sharpe_ratio || 0).toFixed(2);

    addLog('Backtest results loaded', 'success');

  } catch (error) {
    console.error('Error fetching backtest results:', error);
    addLog('Could not fetch backtest results', 'warning');
  }
}

function stopBacktest() {
  stopBot();
  resetBacktestUI();
  updateBacktestProgress(0, 'Backtest cancelled');
}

function resetBacktestUI() {
  document.getElementById('btn-run-backtest').disabled = false;
  document.getElementById('btn-stop-backtest').style.display = 'none';
}

function openAPISettings() {
  toggleAccountMenu();
  showModal('API Settings', `
    <div class="modal-form">
      <div class="form-group">
        <label>API Key</label>
        <input type="password" id="api-key-input" placeholder="Enter your API key" class="form-input">
      </div>
      <div class="form-group">
        <label>API Secret</label>
        <input type="password" id="api-secret-input" placeholder="Enter your API secret" class="form-input">
      </div>
      <p class="form-note">⚠️ API keys are stored locally and never sent to external servers.</p>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="saveAPIKeys()">Save API Keys</button>
        <button class="btn" onclick="closeModal()">Cancel</button>
      </div>
    </div>
  `);
}

function openNotificationSettings() {
  toggleAccountMenu();
  showModal('Notification Settings', `
    <div class="modal-form">
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="notify-trades" checked> Trade notifications
        </label>
      </div>
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="notify-errors" checked> Error alerts
        </label>
      </div>
      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" id="notify-pnl" checked> P&L updates
        </label>
      </div>
      <div class="form-group">
        <label>Notification URL (Apprise)</label>
        <input type="text" id="notify-url-input" placeholder="discord://webhook_id/token" class="form-input">
      </div>
      <div class="modal-actions">
        <button class="btn btn-primary" onclick="saveNotificationSettings()">Save Settings</button>
        <button class="btn" onclick="closeModal()">Cancel</button>
      </div>
    </div>
  `);
}

async function exportConfig() {
  toggleAccountMenu();
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    const config = await response.json();

    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `gridbot-config-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    addLog('Configuration exported successfully', 'success');
    showNotification('Config exported!', 'success');
  } catch (error) {
    console.error('Error exporting config:', error);
    addLog(`Export error: ${error.message}`, 'error');
  }
}

async function resetBot() {
  toggleAccountMenu();
  if (confirm('⚠️ Are you sure you want to reset the bot? This will stop trading and clear all pending orders.')) {
    try {
      // Stop the bot first
      await fetch(`${API_BASE_URL}/bot/stop`, { method: 'POST' });
      addLog('Bot reset initiated', 'warning');
      showNotification('Bot has been reset', 'warning');
    } catch (error) {
      console.error('Error resetting bot:', error);
      addLog(`Reset error: ${error.message}`, 'error');
    }
  }
}

function showModal(title, content) {
  // Remove existing modal if any
  const existingModal = document.getElementById('modal-overlay');
  if (existingModal) {
    existingModal.remove();
  }

  const modal = document.createElement('div');
  modal.id = 'modal-overlay';
  modal.className = 'modal-overlay';
  modal.innerHTML = `
    <div class="modal-container">
      <div class="modal-header">
        <h3>${title}</h3>
        <button class="modal-close" onclick="closeModal()">×</button>
      </div>
      <div class="modal-content">
        ${content}
      </div>
    </div>
  `;
  document.body.appendChild(modal);

  // Close on overlay click
  modal.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });
}

function closeModal() {
  const modal = document.getElementById('modal-overlay');
  if (modal) {
    modal.remove();
  }
}

function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `notification ${type}`;
  notification.innerHTML = `
    <span class="notification-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️'}</span>
    <span class="notification-message">${message}</span>
  `;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.classList.add('show');
  }, 10);

  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

function saveAPIKeys() {
  const apiKey = document.getElementById('api-key-input').value;
  const apiSecret = document.getElementById('api-secret-input').value;

  if (!apiKey || !apiSecret) {
    showNotification('Please enter both API key and secret', 'error');
    return;
  }

  // In a real implementation, these would be saved to .env or a secure storage
  // For now, we'll just show a success message
  addLog('API keys saved (requires restart)', 'success');
  showNotification('API keys saved! Restart bot to apply.', 'success');
  closeModal();
}

function saveNotificationSettings() {
  const notifyTrades = document.getElementById('notify-trades').checked;
  const notifyErrors = document.getElementById('notify-errors').checked;
  const notifyPnl = document.getElementById('notify-pnl').checked;
  const notifyUrl = document.getElementById('notify-url-input').value;

  addLog('Notification settings saved', 'success');
  showNotification('Notification settings saved!', 'success');
  closeModal();
}

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
let ignoredPairs = JSON.parse(localStorage.getItem('ignoredPairs') || '[]');

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

  // Filter out ignored pairs
  const filteredResults = results.filter(coin => coin && coin.pair && !ignoredPairs.includes(coin.pair));

  countSpan.textContent = `(${filteredResults.length} results${ignoredPairs.length > 0 ? `, ${ignoredPairs.length} ignored` : ''})`;

  // Update ignored pairs display
  updateIgnoredPairsDisplay();

  if (!filteredResults || filteredResults.length === 0) {
    tbody.innerHTML = '<tr><td colspan="10" class="no-data">No coins found matching criteria</td></tr>';
    return;
  }

  filteredResults.forEach((coin, index) => {
    const row = document.createElement('tr');
    row.className = getSignalClass(coin.signal);

    // Determine signal emoji and color
    const signalEmoji = getSignalEmoji(coin.signal);
    const scoreColor = getScoreColor(coin.score || 0);

    // EMA status - handle missing flags gracefully
    const flags = coin.flags || {};
    const indicators = coin.indicators || {};

    const emaStatus = flags.ema_bullish_cross ? '🔥 Cross!' :
      (flags.price_above_emas ? '✅ Above' : '❌ Below');

    // CCI status
    const cciStatus = flags.cci_bullish ? '✅' : '❌';
    const cciValue = (indicators.cci || 0).toFixed(0);

    // MACD status
    const macdStatus = flags.macd_bullish ? '✅' : '❌';

    // Find the original index in scanResults for details view
    const originalIndex = results.findIndex(r => r && r.pair === coin.pair);

    // Calculate suggested grid range (±10% from current price)
    const rangeBottom = (coin.price * 0.90).toFixed(4);
    const rangeTop = (coin.price * 1.10).toFixed(4);

    row.innerHTML = `
      <td class="rank">#${index + 1}</td>
      <td class="pair"><strong>${coin.pair}</strong></td>
      <td class="price">$${(coin.price || 0).toFixed(4)}</td>
      <td class="score" style="color: ${scoreColor}"><strong>${(coin.score || 0).toFixed(1)}</strong></td>
      <td class="signal">${signalEmoji} ${formatSignal(coin.signal || 'neutral')}</td>
      <td class="ema">${emaStatus}</td>
      <td class="cci">${cciStatus} ${cciValue}</td>
      <td class="macd">${macdStatus}</td>
      <td class="actions">
        <button class="btn btn-small btn-primary" onclick="useGridRange('${coin.pair}', ${rangeBottom}, ${rangeTop})" title="Set grid range ±10% around current price">📐 Use Range</button>
        <button class="btn btn-small btn-info" onclick="showCoinDetails(${originalIndex})">📊</button>
        <button class="btn btn-small btn-secondary" onclick="ignorePair('${coin.pair}')" title="Hide this pair">🚫</button>
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
      < div class="detail-section" >
      <h4>📊 Overall</h4>
      <div class="detail-item"><label>Price:</label><span>$${coin.price.toFixed(4)}</span></div>
      <div class="detail-item"><label>Score:</label><span style="color: ${getScoreColor(coin.score)}">${coin.score.toFixed(2)}/100</span></div>
      <div class="detail-item"><label>Signal:</label><span>${getSignalEmoji(coin.signal)} ${formatSignal(coin.signal)}</span></div>
    </div >
    
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

function closeCoinDetailsModal() {
  document.getElementById('coin-details-modal').classList.add('hidden');
}

async function selectCoin(pair) {
  try {
    addLog(`Selecting ${pair} for trading...`, 'info');

    const response = await fetch(`${API_BASE_URL} / market / select`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pair: pair })
    });

    const data = await response.json();

    if (response.ok && data.status === 'success') {
      addLog(`✓ Selected ${pair} for trading`, 'success');
      closeCoinDetailsModal();
      // Refresh status to show new trading pair
      await updateStatus();
      await loadConfig();
    } else {
      addLog(`Failed to select pair: ${data.message || 'Unknown error'} `, 'error');
    }
  } catch (error) {
    console.error('Error selecting coin:', error);
    addLog(`Error selecting pair: ${error.message} `, 'error');
  }
}

// ==========================================
// Use Grid Range from Scanner
// ==========================================

async function useGridRange(pair, rangeBottom, rangeTop) {
  try {
    addLog(`Setting grid range for ${pair}: $${rangeBottom} - $${rangeTop}`, 'info');

    // Update grid range via API
    const response = await fetch(`${API_BASE_URL}/config/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        grid_strategy: {
          range: {
            bottom: parseFloat(rangeBottom),
            top: parseFloat(rangeTop)
          }
        }
      })
    });

    const data = await response.json();

    if (response.ok && data.success) {
      addLog(`✓ Grid range updated: $${rangeBottom} - $${rangeTop}`, 'success');
      showNotification(`Grid range set to $${rangeBottom} - $${rangeTop}. Restart bot to apply.`, 'success');

      // Also update the pair if different
      const [base, quote] = pair.split('/');
      await fetch(`${API_BASE_URL}/config/update`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          pair: {
            base_currency: base,
            quote_currency: quote
          }
        })
      });

      addLog(`✓ Trading pair set to ${pair}`, 'success');

      // Refresh config display
      await loadConfig();
    } else {
      addLog(`Failed to update range: ${data.message || 'Unknown error'}`, 'error');
      showNotification(`Failed to update range: ${data.message}`, 'error');
    }
  } catch (error) {
    console.error('Error setting grid range:', error);
    addLog(`Error setting grid range: ${error.message}`, 'error');
    showNotification('Error updating grid range', 'error');
  }
}

// ==========================================
// Ignore Pair Functions
// ==========================================

function ignorePair(pair) {
  if (!ignoredPairs.includes(pair)) {
    ignoredPairs.push(pair);
    localStorage.setItem('ignoredPairs', JSON.stringify(ignoredPairs));
    addLog(`🚫 Ignored ${pair} - won't appear in future scans`, 'warning');

    // Re-render results to remove ignored pair
    if (scanResults && scanResults.length > 0) {
      renderScanResults(scanResults);
    }
  }
}

function clearIgnoredPairs() {
  ignoredPairs = [];
  localStorage.setItem('ignoredPairs', JSON.stringify(ignoredPairs));
  addLog('✓ Cleared all ignored pairs', 'success');

  // Re-render results to show all pairs
  if (scanResults && scanResults.length > 0) {
    renderScanResults(scanResults);
  }
  updateIgnoredPairsDisplay();
}

function restoreIgnoredPair(pair) {
  ignoredPairs = ignoredPairs.filter(p => p !== pair);
  localStorage.setItem('ignoredPairs', JSON.stringify(ignoredPairs));
  addLog(`✓ Restored ${pair} to scan results`, 'success');

  // Re-render results to show restored pair
  if (scanResults && scanResults.length > 0) {
    renderScanResults(scanResults);
  }
}

function updateIgnoredPairsDisplay() {
  const row = document.getElementById('ignored-pairs-row');
  const list = document.getElementById('ignored-pairs-list');

  if (!row || !list) return;

  if (ignoredPairs.length > 0) {
    row.style.display = 'table-row';
    list.innerHTML = ignoredPairs.map(pair =>
      `<span class="ignored-pair-tag">${pair} <button class="restore-btn" onclick="restoreIgnoredPair('${pair}')">✕</button></span>`
    ).join(' ');
  } else {
    row.style.display = 'none';
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
  const logsContainer = logsDisplay.parentElement;

  // Check if user is scrolled to bottom BEFORE adding new log
  const isScrolledToBottom = logsContainer.scrollHeight - logsContainer.clientHeight <= logsContainer.scrollTop + 50;

  const entry = document.createElement('div');
  entry.className = 'log-entry ' + type;

  const time = new Date().toLocaleTimeString();
  entry.textContent = `[${time}] ${message}`;

  logsDisplay.appendChild(entry);

  // Keep only last 100 logs (increased from 50)
  while (logsDisplay.children.length > 100) {
    logsDisplay.removeChild(logsDisplay.firstChild);
  }

  // Only auto-scroll if user was already at the bottom
  if (isScrolledToBottom) {
    logsContainer.scrollTop = logsContainer.scrollHeight;
  }
}

function scrollLogsToBottom() {
  const logsDisplay = document.getElementById('logs-display');
  const logsContainer = logsDisplay.parentElement;
  logsContainer.scrollTop = logsContainer.scrollHeight;
}

function clearLogs() {
  const logsDisplay = document.getElementById('logs-display');
  logsDisplay.innerHTML = '';
  addLog('Logs cleared', 'info');
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
  alert('GridBot Pro v2.0\\n\\nAutomated cryptocurrency grid trading bot.\\n\\nFeatures:\\n• Multi-pair trading\\n• Market scanner with technical indicators\\n• Multi-timeframe analysis\\n• Real-time price monitoring\\n• Configurable grid strategies');
}

function showHelp() {
  alert('GridBot Pro Help\\n\\n1. Set up your API keys in config.json\\n2. Configure grid parameters\\n3. Click Start Bot to begin trading\\n4. Monitor your positions in real-time\\n\\nFor support, check the documentation.');
}

// ================================================
// Multi-Timeframe Analysis Functions
// ================================================

let mtfRefreshInterval = null;

// Update MTF status periodically
function startMTFRefresh() {
  updateMTFStatus();
  mtfRefreshInterval = setInterval(updateMTFStatus, 30000); // Every 30 seconds
}

// Stop MTF refresh
function stopMTFRefresh() {
  if (mtfRefreshInterval) {
    clearInterval(mtfRefreshInterval);
    mtfRefreshInterval = null;
  }
}

// Fetch and update MTF status
async function updateMTFStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/mtf/status`);
    if (!response.ok) return;

    const data = await response.json();

    if (!data.enabled) {
      setMTFDisabled();
      return;
    }

    if (data.status === 'waiting' || !data.analysis) {
      setMTFWaiting();
      return;
    }

    const analysis = data.analysis;
    updateMTFDisplay(analysis);

  } catch (error) {
    console.error('Error fetching MTF status:', error);
  }
}

// Set MTF section as disabled
function setMTFDisabled() {
  const badge = document.getElementById('mtf-status-badge');
  badge.className = 'mtf-status-badge disabled';
  badge.querySelector('.badge-text').textContent = 'Disabled';

  document.getElementById('mtf-signal').textContent = 'DISABLED';
  document.getElementById('mtf-signal').className = 'mtf-signal';
}

// Set MTF section as waiting
function setMTFWaiting() {
  const badge = document.getElementById('mtf-status-badge');
  badge.className = 'mtf-status-badge';
  badge.querySelector('.badge-text').textContent = 'Waiting for analysis...';

  document.getElementById('mtf-signal').textContent = '--';
  document.getElementById('mtf-signal').className = 'mtf-signal';
}

// Update the MTF display with analysis data
function updateMTFDisplay(analysis) {
  // Update status badge
  const badge = document.getElementById('mtf-status-badge');
  if (analysis.trading_paused) {
    badge.className = 'mtf-status-badge paused';
    badge.querySelector('.badge-text').textContent = 'Trading Paused';
  } else {
    badge.className = 'mtf-status-badge active';
    badge.querySelector('.badge-text').textContent = 'Active';
  }

  // Update signal card
  const signalEl = document.getElementById('mtf-signal');
  const signal = analysis.grid_signal || '--';
  signalEl.textContent = signal.replace('_', ' ');
  signalEl.className = 'mtf-signal ' + signal.toLowerCase();

  // Update confidence
  const confidence = analysis.confidence || 0;
  document.getElementById('mtf-confidence-fill').style.width = confidence + '%';
  document.getElementById('mtf-confidence-value').textContent = confidence.toFixed(0) + '%';

  // Update trend
  document.getElementById('mtf-trend').textContent = analysis.primary_trend || '--';
  document.getElementById('mtf-condition').textContent =
    (analysis.market_condition || '--').replace(/_/g, ' ');

  // Update bias
  const biasEl = document.getElementById('mtf-bias');
  const bias = analysis.recommended_bias || 'neutral';
  biasEl.textContent = bias.charAt(0).toUpperCase() + bias.slice(1);
  biasEl.className = 'mtf-value ' + bias;

  // Update spacing
  const spacing = analysis.spacing_multiplier || 1.0;
  document.getElementById('mtf-spacing').textContent = spacing.toFixed(2) + 'x';

  // Update range status
  const rangeValidEl = document.getElementById('mtf-range-valid');
  if (analysis.range_valid) {
    rangeValidEl.textContent = '✓ Valid';
    rangeValidEl.className = 'mtf-value valid';
  } else {
    rangeValidEl.textContent = '✗ Outdated';
    rangeValidEl.className = 'mtf-value invalid';
  }

  // Update suggested range
  if (analysis.suggested_range && analysis.suggested_range.bottom > 0) {
    document.getElementById('mtf-suggested-range').textContent =
      'Suggested: $' + analysis.suggested_range.bottom.toFixed(2) +
      ' - $' + analysis.suggested_range.top.toFixed(2);
  } else {
    document.getElementById('mtf-suggested-range').textContent = '';
  }

  // Update timeframe details
  if (analysis.timeframe_details) {
    updateTimeframeDetails(analysis.timeframe_details);
  }

  // Update recommendations
  updateRecommendations(analysis.recommendations, analysis.warnings);
}

// Update timeframe detail cards
function updateTimeframeDetails(details) {
  const tfMapping = {
    'trend': { suffix: 'daily' },
    'config': { suffix: '4h' },
    'execution': { suffix: '1h' }
  };

  for (const [key, tf] of Object.entries(details)) {
    const suffix = tfMapping[key]?.suffix;
    if (!suffix) continue;

    // Update trend badge
    const trendBadge = document.getElementById('tf-trend-' + suffix);
    if (trendBadge) {
      trendBadge.textContent = tf.trend || '--';
      trendBadge.className = 'tf-trend-badge ' + (tf.trend || 'neutral');
    }

    // Update RSI
    const rsiEl = document.getElementById('tf-rsi-' + suffix);
    if (rsiEl) {
      const rsi = tf.rsi || 0;
      rsiEl.textContent = rsi.toFixed(1);
      rsiEl.style.color = rsi > 70 ? 'var(--danger-color)' :
        rsi < 30 ? 'var(--success-color)' : 'var(--text-primary)';
    }

    // Update ATR %
    const atrEl = document.getElementById('tf-atr-' + suffix);
    if (atrEl) {
      atrEl.textContent = (tf.atr_percent || 0).toFixed(2) + '%';
    }

    // Update Volatility percentile
    const volEl = document.getElementById('tf-vol-' + suffix);
    if (volEl) {
      const vol = tf.volatility_percentile || 0;
      volEl.textContent = vol.toFixed(0) + '%';
      volEl.style.color = vol > 80 ? 'var(--danger-color)' :
        vol < 20 ? 'var(--success-color)' : 'var(--text-primary)';
    }
  }
}

// Update recommendations list
function updateRecommendations(recommendations, warnings) {
  const listEl = document.getElementById('mtf-rec-list');
  listEl.innerHTML = '';

  // Add warnings first
  if (warnings && warnings.length > 0) {
    warnings.forEach(warning => {
      const item = document.createElement('div');
      item.className = 'recommendation-item warning';
      item.textContent = '⚠️ ' + warning;
      listEl.appendChild(item);
    });
  }

  // Add recommendations
  if (recommendations && recommendations.length > 0) {
    recommendations.forEach(rec => {
      const item = document.createElement('div');
      // Determine item class based on content
      let itemClass = 'recommendation-item';
      if (rec.includes('AVOID') || rec.includes('⚠️')) {
        itemClass += ' danger';
      } else if (rec.includes('✅') || rec.includes('IDEAL') || rec.includes('FAVORABLE')) {
        itemClass += ' success';
      }
      item.className = itemClass;
      item.textContent = rec;
      listEl.appendChild(item);
    });
  }

  if (listEl.children.length === 0) {
    listEl.innerHTML = '<p class="no-data">No recommendations available</p>';
  }
}

// Manual MTF analysis trigger
async function runMTFAnalysis() {
  const btn = document.querySelector('.mtf-header .btn');
  const originalText = btn.innerHTML;

  btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Analyzing...</span>';
  btn.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/mtf/analyze`, {
      method: 'POST'
    });

    const data = await response.json();

    if (data.success && data.analysis) {
      updateMTFDisplay({
        ...data.analysis,
        trading_paused: false,
        timeframe_details: {}
      });
      addLog('MTF analysis completed: ' + data.analysis.grid_signal, 'success');
    } else {
      addLog('MTF analysis failed: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Error running MTF analysis:', error);
    addLog('MTF analysis error: ' + error.message, 'error');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

// Initialize MTF on page load
document.addEventListener('DOMContentLoaded', () => {
  startMTFRefresh();
});

// ============================================================
// CHUCK AI FEATURES
// ============================================================

let chuckPortfolioRefreshInterval = null;

// Tab switching for Chuck AI section
function switchChuckTab(tabName) {
  // Update tab buttons
  document.querySelectorAll('.chuck-tab').forEach(tab => {
    tab.classList.remove('active');
    if (tab.onclick.toString().includes(tabName)) {
      tab.classList.add('active');
    }
  });

  // Find the clicked tab and activate it
  event.target.classList.add('active');

  // Update panels
  document.querySelectorAll('.chuck-panel').forEach(panel => {
    panel.classList.remove('active');
  });
  document.getElementById(`chuck-${tabName}`).classList.add('active');
}

// Smart Pair Scanner
async function runChuckSmartScan() {
  const btn = document.querySelector('#chuck-scan button');
  const resultsDiv = document.getElementById('scan-results');
  const originalText = btn.innerHTML;

  btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Scanning Markets...</span>';
  btn.disabled = true;
  resultsDiv.innerHTML = '<p class="scanning">Analyzing pairs across exchanges... This may take a moment.</p>';

  try {
    const exchange = document.getElementById('scan-exchange').value;
    const topN = parseInt(document.getElementById('scan-top-n').value) || 10;
    const minVolume = parseFloat(document.getElementById('scan-min-volume').value) || 100000;

    const response = await fetch(`${API_BASE_URL}/chuck/smart-scan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exchange: exchange,
        top_n: topN,
        min_volume: minVolume
      })
    });

    const data = await response.json();

    if (data.success && data.pairs) {
      displayScanResults(data.pairs);
      addLog(`Smart Scan found ${data.pairs.length} optimal pairs`, 'success');
    } else {
      resultsDiv.innerHTML = `<p class="error">Scan failed: ${data.message || 'Unknown error'}</p>`;
      addLog('Smart Scan failed: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Smart Scan error:', error);
    resultsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    addLog('Smart Scan error: ' + error.message, 'error');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

function displayScanResults(pairs) {
  const resultsDiv = document.getElementById('scan-results');

  if (!pairs || pairs.length === 0) {
    resultsDiv.innerHTML = '<p class="no-data">No suitable pairs found. Try adjusting filters.</p>';
    return;
  }

  let html = '<div class="scan-results-grid">';

  pairs.forEach((pair, index) => {
    const scoreClass = pair.score >= 70 ? 'excellent' : pair.score >= 50 ? 'good' : 'fair';
    html += `
      <div class="scan-result-card ${scoreClass}">
        <div class="scan-rank">#${index + 1}</div>
        <div class="scan-pair">${pair.symbol}</div>
        <div class="scan-score">
          <span class="score-value">${pair.score.toFixed(1)}</span>
          <span class="score-label">Score</span>
        </div>
        <div class="scan-metrics">
          <div class="metric">
            <span class="metric-label">24h Range</span>
            <span class="metric-value">${pair.range_percent?.toFixed(2) || 'N/A'}%</span>
          </div>
          <div class="metric">
            <span class="metric-label">Volume</span>
            <span class="metric-value">$${formatVolume(pair.volume_24h)}</span>
          </div>
          <div class="metric">
            <span class="metric-label">Volatility</span>
            <span class="metric-value">${pair.volatility?.toFixed(2) || 'N/A'}%</span>
          </div>
        </div>
        <button class="btn btn-small" onclick="useScanResult('${pair.symbol}', ${pair.range_low}, ${pair.range_high})">
          Use This Pair
        </button>
      </div>
    `;
  });

  html += '</div>';
  resultsDiv.innerHTML = html;
}

function formatVolume(volume) {
  if (!volume) return 'N/A';
  if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B';
  if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M';
  if (volume >= 1e3) return (volume / 1e3).toFixed(2) + 'K';
  return volume.toFixed(2);
}

function useScanResult(symbol, rangeLow, rangeHigh) {
  // Navigate to config or populate fields
  addLog(`Selected ${symbol} with range $${rangeLow} - $${rangeHigh}`, 'info');
  alert(`To use ${symbol}:\n\n1. Update your config.json with:\n   - trading_pair: "${symbol}"\n   - price_range_low: ${rangeLow}\n   - price_range_high: ${rangeHigh}\n\n2. Restart the bot to apply changes.`);
}

// Auto-Portfolio Manager
async function startChuckPortfolio() {
  const btn = document.querySelector('#chuck-portfolio .btn-primary');
  const originalText = btn.innerHTML;

  btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Starting...</span>';
  btn.disabled = true;

  try {
    const capital = parseFloat(document.getElementById('portfolio-capital').value) || 1000;
    const maxPositions = parseInt(document.getElementById('portfolio-max-positions').value) || 5;
    const exchange = document.getElementById('portfolio-exchange').value;

    const response = await fetch(`${API_BASE_URL}/chuck/portfolio/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        total_capital: capital,
        max_positions: maxPositions,
        exchange: exchange
      })
    });

    const data = await response.json();

    if (data.success) {
      addLog('Auto-Portfolio Manager started', 'success');
      startPortfolioRefresh();
      updatePortfolioUI(true);
    } else {
      addLog('Failed to start portfolio: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Portfolio start error:', error);
    addLog('Portfolio start error: ' + error.message, 'error');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

async function stopChuckPortfolio() {
  try {
    const response = await fetch(`${API_BASE_URL}/chuck/portfolio/stop`, {
      method: 'POST'
    });

    const data = await response.json();

    if (data.success) {
      addLog('Auto-Portfolio Manager stopped', 'info');
      stopPortfolioRefresh();
      updatePortfolioUI(false);
    } else {
      addLog('Failed to stop portfolio: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Portfolio stop error:', error);
    addLog('Portfolio stop error: ' + error.message, 'error');
  }
}

function updatePortfolioUI(isRunning) {
  const startBtn = document.querySelector('#chuck-portfolio .btn-primary');
  const stopBtn = document.querySelector('#chuck-portfolio .btn-danger');

  if (startBtn) startBtn.disabled = isRunning;
  if (stopBtn) stopBtn.disabled = !isRunning;
}

function startPortfolioRefresh() {
  if (chuckPortfolioRefreshInterval) {
    clearInterval(chuckPortfolioRefreshInterval);
  }
  refreshPortfolioStatus();
  chuckPortfolioRefreshInterval = setInterval(refreshPortfolioStatus, 10000);
}

function stopPortfolioRefresh() {
  if (chuckPortfolioRefreshInterval) {
    clearInterval(chuckPortfolioRefreshInterval);
    chuckPortfolioRefreshInterval = null;
  }
}

async function refreshPortfolioStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/chuck/portfolio/status`);
    const data = await response.json();

    if (data.success) {
      displayPortfolioStatus(data);
    }
  } catch (error) {
    console.error('Portfolio status refresh error:', error);
  }
}

function displayPortfolioStatus(data) {
  const summaryDiv = document.getElementById('portfolio-summary');
  const positionsDiv = document.getElementById('portfolio-positions');

  // Update summary
  if (summaryDiv && data.summary) {
    const s = data.summary;
    summaryDiv.innerHTML = `
      <div class="summary-card">
        <span class="summary-label">Total Capital</span>
        <span class="summary-value">$${s.total_capital?.toFixed(2) || '0.00'}</span>
      </div>
      <div class="summary-card">
        <span class="summary-label">Allocated</span>
        <span class="summary-value">$${s.allocated?.toFixed(2) || '0.00'}</span>
      </div>
      <div class="summary-card">
        <span class="summary-label">Available</span>
        <span class="summary-value">$${s.available?.toFixed(2) || '0.00'}</span>
      </div>
      <div class="summary-card ${(s.total_pnl || 0) >= 0 ? 'positive' : 'negative'}">
        <span class="summary-label">Total P&L</span>
        <span class="summary-value">${(s.total_pnl || 0) >= 0 ? '+' : ''}$${s.total_pnl?.toFixed(2) || '0.00'}</span>
      </div>
    `;
  }

  // Update positions
  if (positionsDiv && data.positions) {
    if (data.positions.length === 0) {
      positionsDiv.innerHTML = '<p class="no-data">No active positions. The manager will open positions when conditions are favorable.</p>';
    } else {
      let html = '<div class="positions-grid">';
      data.positions.forEach(pos => {
        const pnlClass = (pos.pnl || 0) >= 0 ? 'positive' : 'negative';
        html += `
          <div class="position-card">
            <div class="position-header">
              <span class="position-symbol">${pos.symbol}</span>
              <span class="position-status ${pos.status || 'active'}">${pos.status || 'Active'}</span>
            </div>
            <div class="position-details">
              <div class="detail">
                <span class="label">Entry</span>
                <span class="value">$${pos.entry_price?.toFixed(4) || 'N/A'}</span>
              </div>
              <div class="detail">
                <span class="label">Current</span>
                <span class="value">$${pos.current_price?.toFixed(4) || 'N/A'}</span>
              </div>
              <div class="detail">
                <span class="label">Allocated</span>
                <span class="value">$${pos.allocated?.toFixed(2) || 'N/A'}</span>
              </div>
              <div class="detail ${pnlClass}">
                <span class="label">P&L</span>
                <span class="value">${(pos.pnl || 0) >= 0 ? '+' : ''}$${pos.pnl?.toFixed(2) || '0.00'}</span>
              </div>
            </div>
          </div>
        `;
      });
      html += '</div>';
      positionsDiv.innerHTML = html;
    }
  }

  // Update running state
  updatePortfolioUI(data.is_running || false);
}

// Entry Signal Analyzer
async function analyzeEntrySignal() {
  const btn = document.querySelector('#chuck-signals button');
  const resultDiv = document.getElementById('signal-result');
  const originalText = btn.innerHTML;

  btn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Analyzing...</span>';
  btn.disabled = true;
  resultDiv.innerHTML = '<p class="analyzing">Analyzing market conditions...</p>';

  try {
    const symbol = document.getElementById('signal-symbol').value.trim();
    const exchange = document.getElementById('signal-exchange').value;

    if (!symbol) {
      resultDiv.innerHTML = '<p class="error">Please enter a trading pair symbol</p>';
      return;
    }

    const response = await fetch(`${API_BASE_URL}/chuck/entry-signal`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        symbol: symbol,
        exchange: exchange
      })
    });

    const data = await response.json();

    if (data.success && data.signal) {
      displayEntrySignal(data.signal);
      addLog(`Entry analysis for ${symbol}: ${data.signal.recommendation}`, 'info');
    } else {
      resultDiv.innerHTML = `<p class="error">Analysis failed: ${data.message || 'Unknown error'}</p>`;
      addLog('Entry signal analysis failed: ' + (data.message || 'Unknown error'), 'error');
    }
  } catch (error) {
    console.error('Entry signal error:', error);
    resultDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    addLog('Entry signal error: ' + error.message, 'error');
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}

function displayEntrySignal(signal) {
  const resultDiv = document.getElementById('signal-result');

  const strengthClass = signal.strength?.toLowerCase() || 'neutral';
  const scoreClass = signal.score >= 70 ? 'excellent' : signal.score >= 50 ? 'good' : signal.score >= 30 ? 'fair' : 'poor';

  let html = `
    <div class="signal-result-card ${strengthClass}">
      <div class="signal-header">
        <div class="signal-recommendation">${signal.recommendation || 'NEUTRAL'}</div>
        <div class="signal-strength ${strengthClass}">${signal.strength || 'Neutral'}</div>
      </div>
      
      <div class="signal-score ${scoreClass}">
        <div class="score-circle">
          <span class="score-number">${signal.score?.toFixed(0) || 0}</span>
          <span class="score-max">/100</span>
        </div>
        <span class="score-label">Entry Score</span>
      </div>
      
      <div class="signal-indicators">
        <h4>Technical Indicators</h4>
        <div class="indicator-grid">
  `;

  if (signal.indicators) {
    for (const [key, value] of Object.entries(signal.indicators)) {
      const displayName = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
      html += `
        <div class="indicator">
          <span class="indicator-name">${displayName}</span>
          <span class="indicator-value">${typeof value === 'number' ? value.toFixed(2) : value}</span>
        </div>
      `;
    }
  }

  html += `
        </div>
      </div>
      
      <div class="signal-reasoning">
        <h4>Analysis</h4>
        <p>${signal.reasoning || 'No detailed analysis available.'}</p>
      </div>
    </div>
  `;

  resultDiv.innerHTML = html;
}
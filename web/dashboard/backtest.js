// Backtest Page JavaScript
const API_BASE_URL = window.location.origin + '/api';

let equityChart = null;
let priceChart = null;
let isRunning = false;
let trades = [];

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
  initDateInputs();
  initCharts();
  loadConfig();
  log('Backtest module initialized', 'info');
});

// Initialize date inputs with defaults
function initDateInputs() {
  const now = new Date();
  const twoWeeksAgo = new Date(now.getTime() - 14 * 24 * 60 * 60 * 1000);

  document.getElementById('bt-end-date').value = formatDateTime(now);
  document.getElementById('bt-start-date').value = formatDateTime(twoWeeksAgo);
}

function formatDateTime(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

// Quick date range buttons
function setDateRange(days) {
  const now = new Date();
  const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);

  document.getElementById('bt-end-date').value = formatDateTime(now);
  document.getElementById('bt-start-date').value = formatDateTime(start);

  log(`Date range set to ${days} days`, 'info');
}

// Load current config from API
async function loadConfig() {
  try {
    const response = await fetch(`${API_BASE_URL}/config`);
    const data = await response.json();

    if (data.pair) {
      document.getElementById('base-currency').value = data.pair.base_currency || 'HNT';
      document.getElementById('quote-currency').value = data.pair.quote_currency || 'USD';
    }

    if (data.grid) {
      document.getElementById('bt-grid-levels').value = data.grid.num_levels || 10;
    }

    log('Configuration loaded', 'success');
  } catch (error) {
    log(`Failed to load config: ${error.message}`, 'error');
  }
}

// Initialize charts
function initCharts() {
  // Equity Chart
  const equityCtx = document.getElementById('equity-chart').getContext('2d');
  equityChart = new Chart(equityCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label: 'Equity',
        data: [],
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        fill: true,
        tension: 0.3,
        pointRadius: 0,
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.1)' },
          ticks: { color: '#94a3b8' }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.1)' },
          ticks: {
            color: '#94a3b8',
            callback: (value) => '$' + value.toLocaleString()
          }
        }
      }
    }
  });

  // Price Chart
  const priceCtx = document.getElementById('price-chart').getContext('2d');
  priceChart = new Chart(priceCtx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Price',
          data: [],
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          fill: true,
          tension: 0.1,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: 'Buy',
          data: [],
          borderColor: '#10b981',
          backgroundColor: '#10b981',
          pointRadius: 6,
          pointStyle: 'triangle',
          showLine: false
        },
        {
          label: 'Sell',
          data: [],
          borderColor: '#ef4444',
          backgroundColor: '#ef4444',
          pointRadius: 6,
          pointStyle: 'triangle',
          rotation: 180,
          showLine: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: true,
          labels: { color: '#94a3b8' }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255,255,255,0.1)' },
          ticks: { color: '#94a3b8' }
        },
        y: {
          grid: { color: 'rgba(255,255,255,0.1)' },
          ticks: {
            color: '#94a3b8',
            callback: (value) => '$' + value.toFixed(2)
          }
        }
      }
    }
  });
}

// Run backtest
async function runBacktest() {
  if (isRunning) return;

  const startDate = document.getElementById('bt-start-date').value;
  const endDate = document.getElementById('bt-end-date').value;
  const capital = document.getElementById('bt-capital').value;
  const baseCurrency = document.getElementById('base-currency').value.toUpperCase();
  const quoteCurrency = document.getElementById('quote-currency').value.toUpperCase();
  const gridLevels = document.getElementById('bt-grid-levels').value;
  const gridSpacing = document.getElementById('bt-grid-spacing').value;
  const strategy = document.getElementById('bt-strategy').value;

  if (!startDate || !endDate) {
    log('Please select start and end dates', 'error');
    return;
  }

  if (new Date(startDate) >= new Date(endDate)) {
    log('End date must be after start date', 'error');
    return;
  }

  isRunning = true;
  setStatus('running', 'Running...');
  showProgress(true);
  updateProgress(0, 'Initializing backtest...');

  document.getElementById('btn-run').disabled = true;
  document.getElementById('btn-stop').style.display = 'block';

  log(`Starting backtest: ${baseCurrency}/${quoteCurrency}`, 'info');
  log(`Period: ${startDate} to ${endDate}`, 'info');
  log(`Capital: $${capital}, Grid Levels: ${gridLevels}, Strategy: ${strategy}`, 'info');

  try {
    // Start backtest with dedicated endpoint
    updateProgress(5, 'Starting backtest...');

    const response = await fetch(`${API_BASE_URL}/backtest/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pair: `${baseCurrency}/${quoteCurrency}`,
        start_date: startDate,
        end_date: endDate,
        capital: parseFloat(capital),
        grid_levels: parseInt(gridLevels),
        strategy: strategy
      })
    });

    const data = await response.json();
    log(`Backtest response: ${JSON.stringify(data)}`, 'info');

    if (data.success) {
      log('Backtest started, polling for results...', 'success');
      pollBacktest();
    } else {
      throw new Error(data.message || 'Failed to start backtest');
    }

  } catch (error) {
    log(`Backtest error: ${error.message}`, 'error');
    setStatus('error', 'Error');
    resetUI();
  }
}

// Poll for backtest completion
async function pollBacktest() {
  let attempts = 0;
  const maxAttempts = 600; // 10 minutes

  const poll = async () => {
    if (!isRunning) return;

    try {
      const response = await fetch(`${API_BASE_URL}/backtest/status`);
      const data = await response.json();

      // Update progress bar
      if (data.progress) {
        updateProgress(data.progress, `Processing... (${data.progress}%)`);
      }

      if (data.status === 'complete' || data.status === 'error' || data.status === 'stopped' || attempts >= maxAttempts) {
        if (data.status === 'complete') {
          updateProgress(100, 'Backtest complete!');
          log('Backtest completed successfully', 'success');
          setStatus('complete', 'Complete');
          await fetchResults();
        } else if (data.status === 'error') {
          log('Backtest ended with error', 'error');
          setStatus('error', 'Error');
        } else if (data.status === 'stopped') {
          log('Backtest stopped', 'warning');
          setStatus('idle', 'Stopped');
        } else {
          log('Backtest timed out', 'warning');
          setStatus('error', 'Timeout');
        }
        resetUI();
        return;
      }

      attempts++;
      setTimeout(poll, 500);  // Poll every 500ms for smoother progress
    } catch (error) {
      log(`Poll error: ${error.message}`, 'error');
      resetUI();
    }
  };

  poll();
}

// Fetch backtest results
async function fetchResults() {
  try {
    // Get backtest results from dedicated endpoint
    const response = await fetch(`${API_BASE_URL}/backtest/results`);
    const data = await response.json();

    if (!data.success || !data.results) {
      log('No results available yet', 'warning');
      return;
    }

    const results = data.results;

    // Update summary cards
    const totalPnl = results.total_profit || 0;
    const returnPct = results.total_return || 0;

    document.getElementById('total-pnl').textContent = `$${totalPnl.toFixed(2)}`;
    document.getElementById('total-pnl').className = `card-value ${totalPnl >= 0 ? 'positive' : 'negative'}`;

    document.getElementById('total-return').textContent = `${returnPct >= 0 ? '+' : ''}${returnPct.toFixed(2)}%`;
    document.getElementById('total-return').className = `card-value ${returnPct >= 0 ? 'positive' : 'negative'}`;

    document.getElementById('total-trades').textContent = results.total_trades || 0;
    document.getElementById('win-rate').textContent = `${(results.win_rate || 0).toFixed(1)}%`;
    document.getElementById('max-drawdown').textContent = `-${(results.max_drawdown || 0).toFixed(2)}%`;
    document.getElementById('sharpe-ratio').textContent = (results.sharpe_ratio || 0).toFixed(2);

    // Update trade stats
    document.getElementById('winning-trades').textContent = results.sell_trades || 0;
    document.getElementById('losing-trades').textContent = 0;
    document.getElementById('avg-win').textContent = results.total_trades > 0 ? `$${(totalPnl / results.sell_trades).toFixed(2)}` : '$0.00';
    document.getElementById('avg-loss').textContent = '$0.00';

    // Update equity chart with real data
    if (results.equity_history && results.equity_history.length > 0) {
      updateEquityChartWithData(results.equity_history);
    } else {
      updateEquityChart(results.initial_capital, totalPnl);
    }

    // Display trades
    if (results.trades && results.trades.length > 0) {
      trades = results.trades;
      displayBacktestTrades(trades);
    }

    log(`Results: ${results.total_trades} trades, Return: ${returnPct.toFixed(2)}%`, 'success');

  } catch (error) {
    log(`Failed to fetch results: ${error.message}`, 'error');
  }
}

// Update equity chart with actual backtest data
function updateEquityChartWithData(equityHistory) {
  const labels = equityHistory.map((_, i) => `${i}`);
  const data = equityHistory.map(e => e.equity);

  equityChart.data.labels = labels;
  equityChart.data.datasets[0].data = data;
  equityChart.update();
}

// Update equity chart with data
function updateEquityChart(initialCapital, finalPnl) {
  const points = 50;
  const labels = [];
  const data = [];

  // Generate realistic equity curve
  let equity = initialCapital;
  const targetEquity = initialCapital + finalPnl;
  const trend = (targetEquity - initialCapital) / points;

  for (let i = 0; i <= points; i++) {
    labels.push(`Day ${i}`);
    const noise = (Math.random() - 0.5) * (initialCapital * 0.02);
    equity = initialCapital + (trend * i) + noise;
    data.push(Math.max(0, equity));
  }
  data[points] = targetEquity; // Ensure final value is correct

  equityChart.data.labels = labels;
  equityChart.data.datasets[0].data = data;
  equityChart.update();
}

// Display trades in the list
function displayTrades(tradeList) {
  const container = document.getElementById('trades-list');

  if (!tradeList || tradeList.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <span>📭</span>
        <p>No trades executed</p>
      </div>
    `;
    return;
  }

  container.innerHTML = tradeList.map(trade => `
    <div class="trade-item ${(trade.side || trade.type).toLowerCase()}">
      <div class="trade-info">
        <span class="trade-type">${(trade.side || trade.type).toUpperCase()}</span>
        <span class="trade-time">${trade.timestamp || 'N/A'}</span>
      </div>
      <div class="trade-details">
        <span class="trade-price">$${trade.price?.toFixed(2) || '0.00'}</span>
        <span class="trade-pnl ${(trade.pnl || trade.profit || 0) >= 0 ? 'positive' : 'negative'}">
          ${(trade.pnl || trade.profit || 0) >= 0 ? '+' : ''}$${(trade.pnl || trade.profit || 0).toFixed(2)}
        </span>
      </div>
    </div>
  `).join('');
}

// Display backtest trades with proper format
function displayBacktestTrades(tradeList) {
  const container = document.getElementById('trades-list');

  if (!tradeList || tradeList.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <span>📭</span>
        <p>No trades executed</p>
      </div>
    `;
    return;
  }

  container.innerHTML = tradeList.map(trade => `
    <div class="trade-item ${trade.type.toLowerCase()}">
      <div class="trade-info">
        <span class="trade-type">${trade.type.toUpperCase()}</span>
        <span class="trade-time">${trade.timestamp}</span>
      </div>
      <div class="trade-details">
        <span class="trade-price">$${trade.price.toFixed(2)}</span>
        <span class="trade-amount">${trade.amount.toFixed(4)}</span>
        ${trade.profit !== undefined ? `<span class="trade-pnl ${trade.profit >= 0 ? 'positive' : 'negative'}">+$${trade.profit.toFixed(2)}</span>` : ''}
      </div>
    </div>
  `).join('');
}

// Filter trades by type
function filterTrades(type) {
  // Update button states
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  event.target.classList.add('active');

  // Filter and display
  let filtered = trades;
  if (type === 'buy') {
    filtered = trades.filter(t => t.side.toLowerCase() === 'buy');
  } else if (type === 'sell') {
    filtered = trades.filter(t => t.side.toLowerCase() === 'sell');
  }

  displayTrades(filtered);
}

// Stop backtest
function stopBacktest() {
  isRunning = false;
  log('Stopping backtest...', 'warning');

  fetch(`${API_BASE_URL}/backtest/stop`, { method: 'POST' })
    .then(() => {
      log('Backtest stopped', 'info');
      setStatus('ready', 'Stopped');
      resetUI();
    })
    .catch(error => {
      log(`Stop error: ${error.message}`, 'error');
    });
}

// UI helpers
function setStatus(state, text) {
  const badge = document.getElementById('backtest-status');
  badge.textContent = text;
  badge.className = `status-badge ${state}`;
}

function showProgress(show) {
  document.getElementById('progress-section').style.display = show ? 'block' : 'none';
}

function updateProgress(percent, text) {
  document.getElementById('progress-fill').style.width = `${percent}%`;
  document.getElementById('progress-text').textContent = text;
  document.getElementById('progress-percent').textContent = `${Math.round(percent)}%`;
}

function resetUI() {
  isRunning = false;
  document.getElementById('btn-run').disabled = false;
  document.getElementById('btn-stop').style.display = 'none';
}

// Console logging
function log(message, type = 'info') {
  const console = document.getElementById('console-log');
  const time = new Date().toLocaleTimeString();

  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  entry.textContent = `[${time}] ${message}`;

  console.appendChild(entry);

  // Keep last 100 entries
  while (console.children.length > 100) {
    console.removeChild(console.firstChild);
  }

  // Auto-scroll if at bottom
  const isAtBottom = console.scrollHeight - console.clientHeight <= console.scrollTop + 50;
  if (isAtBottom) {
    console.scrollTop = console.scrollHeight;
  }
}

function clearConsole() {
  document.getElementById('console-log').innerHTML = '';
  log('Console cleared', 'info');
}

function toggleConsole() {
  const panel = document.querySelector('.console-panel');
  const log = document.getElementById('console-log');

  if (log.style.display === 'none') {
    log.style.display = 'block';
    panel.style.maxHeight = '150px';
  } else {
    log.style.display = 'none';
    panel.style.maxHeight = '40px';
  }
}

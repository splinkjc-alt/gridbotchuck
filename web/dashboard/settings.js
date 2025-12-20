// Settings Page JavaScript

const API_BASE_URL = 'http://localhost:8080';

// All settings keys for storage
const SETTINGS_KEYS = {
  profile: ['user-name', 'user-email', 'user-phone', 'timezone'],
  exchanges: {
    kraken: ['kraken-enabled', 'kraken-api-key', 'kraken-api-secret'],
    coinbase: ['coinbase-enabled', 'coinbase-api-key', 'coinbase-api-secret'],
    binance: ['binance-enabled', 'binance-api-key', 'binance-api-secret'],
    binanceus: ['binanceus-enabled', 'binanceus-api-key', 'binanceus-api-secret'],
    kucoin: ['kucoin-enabled', 'kucoin-api-key', 'kucoin-api-secret', 'kucoin-passphrase'],
    bybit: ['bybit-enabled', 'bybit-api-key', 'bybit-api-secret'],
    okx: ['okx-enabled', 'okx-api-key', 'okx-api-secret', 'okx-passphrase'],
    gateio: ['gateio-enabled', 'gateio-api-key', 'gateio-api-secret']
  },
  notifications: [
    'telegram-bot-token', 'telegram-chat-id',
    'notify-telegram-trades', 'notify-telegram-errors', 'notify-telegram-signals',
    'discord-webhook', 'notify-discord-trades', 'notify-discord-signals',
    'notify-email-trades', 'notify-email-errors', 'notify-email-daily'
  ],
  trading: [
    'default-grid-levels', 'default-spacing', 'default-order-size', 'default-strategy',
    'default-stop-loss', 'default-take-profit', 'max-position-size', 'max-daily-loss'
  ],
  security: [
    'dashboard-password', 'require-confirm-trades', 'ip-whitelist-enabled'
  ],
  advanced: [
    'api-base-url', 'api-timeout', 'refresh-interval',
    'debug-mode', 'verbose-logging', 'save-trade-history', 'log-retention',
    'max-chart-points', 'scanner-batch-size'
  ]
};

// Track unsaved changes
let hasUnsavedChanges = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  loadAllSettings();
  setupNavigation();
  setupChangeTracking();
  updateExchangeStatuses();
});

// Navigation between sections
function setupNavigation() {
  const navItems = document.querySelectorAll('.settings-nav li');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const section = item.dataset.section;

      // Update nav active state
      navItems.forEach(i => i.classList.remove('active'));
      item.classList.add('active');

      // Show corresponding section
      document.querySelectorAll('.settings-section').forEach(s => s.classList.remove('active'));
      document.getElementById(`section-${section}`).classList.add('active');
    });
  });
}

// Track changes to show unsaved indicator
function setupChangeTracking() {
  const inputs = document.querySelectorAll('input, select');

  inputs.forEach(input => {
    input.addEventListener('change', () => {
      markUnsaved();
    });
    input.addEventListener('input', () => {
      markUnsaved();
    });
  });

  // Warn before leaving with unsaved changes
  window.addEventListener('beforeunload', (e) => {
    if (hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = '';
    }
  });
}

function markUnsaved() {
  hasUnsavedChanges = true;
  const status = document.getElementById('save-status');
  status.textContent = '● Unsaved changes';
  status.className = 'save-status unsaved';
}

function markSaved() {
  hasUnsavedChanges = false;
  const status = document.getElementById('save-status');
  status.textContent = '✓ All changes saved';
  status.className = 'save-status saved';

  setTimeout(() => {
    status.textContent = '';
  }, 3000);
}

// Load all settings from localStorage
function loadAllSettings() {
  // Profile settings
  SETTINGS_KEYS.profile.forEach(key => {
    const element = document.getElementById(key);
    if (element) {
      element.value = localStorage.getItem(key) || '';
    }
  });

  // Exchange settings
  Object.values(SETTINGS_KEYS.exchanges).flat().forEach(key => {
    const element = document.getElementById(key);
    if (element) {
      if (element.type === 'checkbox') {
        element.checked = localStorage.getItem(key) === 'true';
      } else {
        element.value = localStorage.getItem(key) || '';
      }
    }
  });

  // Notification settings
  SETTINGS_KEYS.notifications.forEach(key => {
    const element = document.getElementById(key);
    if (element) {
      if (element.type === 'checkbox') {
        element.checked = localStorage.getItem(key) === 'true';
      } else {
        element.value = localStorage.getItem(key) || '';
      }
    }
  });

  // Trading defaults
  SETTINGS_KEYS.trading.forEach(key => {
    const element = document.getElementById(key);
    if (element) {
      const saved = localStorage.getItem(key);
      if (saved) element.value = saved;
    }
  });

  // Security settings
  SETTINGS_KEYS.security.forEach(key => {
    const element = document.getElementById(key);
    if (element) {
      if (element.type === 'checkbox') {
        element.checked = localStorage.getItem(key) === 'true';
      } else {
        element.value = localStorage.getItem(key) || '';
      }
    }
  });

  // Advanced settings
  SETTINGS_KEYS.advanced.forEach(key => {
    const element = document.getElementById(key);
    if (element) {
      if (element.type === 'checkbox') {
        element.checked = localStorage.getItem(key) === 'true';
      } else {
        const saved = localStorage.getItem(key);
        if (saved) element.value = saved;
      }
    }
  });
}

// Save all settings to localStorage
function saveAllSettings() {
  try {
    // Profile settings
    SETTINGS_KEYS.profile.forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        localStorage.setItem(key, element.value);
      }
    });

    // Exchange settings
    Object.values(SETTINGS_KEYS.exchanges).flat().forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        if (element.type === 'checkbox') {
          localStorage.setItem(key, element.checked);
        } else {
          localStorage.setItem(key, element.value);
        }
      }
    });

    // Notification settings
    SETTINGS_KEYS.notifications.forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        if (element.type === 'checkbox') {
          localStorage.setItem(key, element.checked);
        } else {
          localStorage.setItem(key, element.value);
        }
      }
    });

    // Trading defaults
    SETTINGS_KEYS.trading.forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        localStorage.setItem(key, element.value);
      }
    });

    // Security settings
    SETTINGS_KEYS.security.forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        if (element.type === 'checkbox') {
          localStorage.setItem(key, element.checked);
        } else {
          localStorage.setItem(key, element.value);
        }
      }
    });

    // Advanced settings
    SETTINGS_KEYS.advanced.forEach(key => {
      const element = document.getElementById(key);
      if (element) {
        if (element.type === 'checkbox') {
          localStorage.setItem(key, element.checked);
        } else {
          localStorage.setItem(key, element.value);
        }
      }
    });

    markSaved();
    showToast('Settings saved successfully!', 'success');
    updateExchangeStatuses();

    // Also sync with backend if available
    syncSettingsWithBackend();

  } catch (error) {
    console.error('Error saving settings:', error);
    showToast('Error saving settings: ' + error.message, 'error');
  }
}

// Update exchange connection statuses
function updateExchangeStatuses() {
  const exchanges = ['kraken', 'coinbase', 'binance', 'binanceus', 'kucoin', 'bybit', 'okx', 'gateio'];

  exchanges.forEach(exchange => {
    const statusEl = document.getElementById(`${exchange}-status`);
    const apiKey = localStorage.getItem(`${exchange}-api-key`);
    const enabled = localStorage.getItem(`${exchange}-enabled`) === 'true';

    if (statusEl) {
      if (apiKey && enabled) {
        statusEl.textContent = 'Configured ✓';
        statusEl.className = 'exchange-status connected';
      } else if (apiKey) {
        statusEl.textContent = 'Configured (disabled)';
        statusEl.className = 'exchange-status';
      } else {
        statusEl.textContent = 'Not configured';
        statusEl.className = 'exchange-status';
      }
    }
  });
}

// Toggle password visibility
function toggleVisibility(inputId) {
  const input = document.getElementById(inputId);
  if (input) {
    input.type = input.type === 'password' ? 'text' : 'password';
  }
}

// Test exchange connection
async function testConnection(exchange) {
  const apiKey = document.getElementById(`${exchange}-api-key`).value;
  const apiSecret = document.getElementById(`${exchange}-api-secret`).value;

  if (!apiKey || !apiSecret) {
    showToast('Please enter API key and secret first', 'warning');
    return;
  }

  showToast(`Testing ${exchange} connection...`, 'info');

  try {
    const response = await fetch(`${API_BASE_URL}/api/test-exchange`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        exchange: exchange,
        api_key: apiKey,
        api_secret: apiSecret,
        passphrase: document.getElementById(`${exchange}-passphrase`)?.value
      })
    });

    const data = await response.json();

    if (response.ok && data.status === 'success') {
      showToast(`${exchange} connection successful! Balance: $${data.balance?.toFixed(2) || 'N/A'}`, 'success');
      const statusEl = document.getElementById(`${exchange}-status`);
      if (statusEl) {
        statusEl.textContent = 'Connected ✓';
        statusEl.className = 'exchange-status connected';
      }
    } else {
      showToast(`${exchange} connection failed: ${data.message || 'Unknown error'}`, 'error');
      const statusEl = document.getElementById(`${exchange}-status`);
      if (statusEl) {
        statusEl.textContent = 'Connection failed';
        statusEl.className = 'exchange-status error';
      }
    }
  } catch (error) {
    console.error('Connection test error:', error);
    showToast(`Connection test failed: ${error.message}`, 'error');
  }
}

// Test Telegram notification
async function testTelegram() {
  const botToken = document.getElementById('telegram-bot-token').value;
  const chatId = document.getElementById('telegram-chat-id').value;

  if (!botToken || !chatId) {
    showToast('Please enter bot token and chat ID', 'warning');
    return;
  }

  showToast('Sending test message to Telegram...', 'info');

  try {
    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: '🤖 Grid Trading Bot - Test notification\n\nYour Telegram notifications are working correctly!',
        parse_mode: 'HTML'
      })
    });

    const data = await response.json();

    if (data.ok) {
      showToast('Test message sent successfully!', 'success');
    } else {
      showToast(`Telegram error: ${data.description}`, 'error');
    }
  } catch (error) {
    console.error('Telegram test error:', error);
    showToast(`Failed to send test message: ${error.message}`, 'error');
  }
}

// Test Discord webhook
async function testDiscord() {
  const webhookUrl = document.getElementById('discord-webhook').value;

  if (!webhookUrl) {
    showToast('Please enter Discord webhook URL', 'warning');
    return;
  }

  showToast('Sending test message to Discord...', 'info');

  try {
    const response = await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        embeds: [{
          title: '🤖 Grid Trading Bot',
          description: 'Test notification - Your Discord webhook is working correctly!',
          color: 0x4CAF50,
          timestamp: new Date().toISOString()
        }]
      })
    });

    if (response.ok || response.status === 204) {
      showToast('Test message sent successfully!', 'success');
    } else {
      showToast('Discord webhook error', 'error');
    }
  } catch (error) {
    console.error('Discord test error:', error);
    showToast(`Failed to send test message: ${error.message}`, 'error');
  }
}

// Export settings to JSON file
function exportSettings() {
  const settings = {};

  // Gather all settings
  const allKeys = [
    ...SETTINGS_KEYS.profile,
    ...Object.values(SETTINGS_KEYS.exchanges).flat(),
    ...SETTINGS_KEYS.notifications,
    ...SETTINGS_KEYS.trading,
    ...SETTINGS_KEYS.security,
    ...SETTINGS_KEYS.advanced
  ];

  allKeys.forEach(key => {
    const value = localStorage.getItem(key);
    if (value !== null) {
      settings[key] = value;
    }
  });

  // Create download
  const blob = new Blob([JSON.stringify(settings, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `grid-bot-settings-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);

  showToast('Settings exported successfully!', 'success');
}

// Import settings from JSON file
function importSettings() {
  document.getElementById('import-file').click();
}

function handleImport(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (e) => {
    try {
      const settings = JSON.parse(e.target.result);

      // Validate and import
      Object.entries(settings).forEach(([key, value]) => {
        localStorage.setItem(key, value);
      });

      loadAllSettings();
      updateExchangeStatuses();
      showToast('Settings imported successfully!', 'success');

    } catch (error) {
      console.error('Import error:', error);
      showToast('Invalid settings file', 'error');
    }
  };
  reader.readAsText(file);

  // Reset file input
  event.target.value = '';
}

// Clear all data
function clearAllData() {
  if (!confirm('Are you sure you want to clear all settings? This cannot be undone.')) {
    return;
  }

  if (!confirm('This will delete all your API keys and settings. Are you absolutely sure?')) {
    return;
  }

  // Clear all settings keys
  const allKeys = [
    ...SETTINGS_KEYS.profile,
    ...Object.values(SETTINGS_KEYS.exchanges).flat(),
    ...SETTINGS_KEYS.notifications,
    ...SETTINGS_KEYS.trading,
    ...SETTINGS_KEYS.security,
    ...SETTINGS_KEYS.advanced,
    'ignoredPairs' // Also clear ignored pairs
  ];

  allKeys.forEach(key => {
    localStorage.removeItem(key);
  });

  // Reload page
  showToast('All data cleared', 'success');
  setTimeout(() => {
    location.reload();
  }, 1000);
}

// Sync settings with backend
async function syncSettingsWithBackend() {
  try {
    // Get active exchange settings
    const activeExchange = getActiveExchange();

    if (activeExchange) {
      const response = await fetch(`${API_BASE_URL}/api/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          exchange: activeExchange.name,
          api_key: activeExchange.apiKey,
          api_secret: activeExchange.apiSecret,
          passphrase: activeExchange.passphrase,
          trading_defaults: {
            grid_levels: parseInt(localStorage.getItem('default-grid-levels')) || 10,
            spacing: localStorage.getItem('default-spacing') || 'ARITHMETIC',
            order_size: parseFloat(localStorage.getItem('default-order-size')) || 10,
            strategy: localStorage.getItem('default-strategy') || 'SIMPLE_GRID'
          }
        })
      });

      if (!response.ok) {
        console.warn('Failed to sync settings with backend');
      }
    }
  } catch (error) {
    console.warn('Backend sync error:', error);
    // Don't show error - backend might not be running
  }
}

// Get the active (first enabled) exchange
function getActiveExchange() {
  const exchanges = ['kraken', 'coinbase', 'binance', 'binanceus', 'kucoin', 'bybit', 'okx', 'gateio'];

  for (const exchange of exchanges) {
    const enabled = localStorage.getItem(`${exchange}-enabled`) === 'true';
    const apiKey = localStorage.getItem(`${exchange}-api-key`);
    const apiSecret = localStorage.getItem(`${exchange}-api-secret`);

    if (enabled && apiKey && apiSecret) {
      return {
        name: exchange,
        apiKey: apiKey,
        apiSecret: apiSecret,
        passphrase: localStorage.getItem(`${exchange}-passphrase`) || null
      };
    }
  }

  return null;
}

// Toast notification
function showToast(message, type = 'info') {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.className = `toast ${type}`;

  setTimeout(() => {
    toast.classList.add('hidden');
  }, 4000);
}

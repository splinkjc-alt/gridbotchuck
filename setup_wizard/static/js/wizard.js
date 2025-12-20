/**
 * GridBot Chuck - Setup Wizard JavaScript
 */

// Configuration state
const config = {
    exchange: 'kraken',
    apiKey: '',
    apiSecret: '',
    capital: 55,
    tradingMode: 'paper',
    riskProfile: 'balanced',
    autoStart: true,
    profitTarget: 3.0,
    maxRotations: 10
};

let currentStep = 1;
let connectionTested = false;

// Navigation
function nextStep() {
    // Validate current step
    if (!validateStep(currentStep)) {
        return;
    }

    // Move to next step
    currentStep++;
    if (currentStep > 4) currentStep = 4;

    updateStepDisplay();

    // If moving to review step, update summary
    if (currentStep === 4) {
        updateSummary();
    }
}

function prevStep() {
    currentStep--;
    if (currentStep < 1) currentStep = 1;
    updateStepDisplay();
}

function updateStepDisplay() {
    // Hide all steps
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });

    // Show current step
    document.getElementById(`step-${currentStep}`).classList.add('active');

    // Update progress bar
    document.querySelectorAll('.progress-step').forEach((step, index) => {
        const stepNum = index + 1;
        if (stepNum < currentStep) {
            step.classList.add('completed');
            step.classList.remove('active');
        } else if (stepNum === currentStep) {
            step.classList.add('active');
            step.classList.remove('completed');
        } else {
            step.classList.remove('active', 'completed');
        }
    });

    // Scroll to top
    window.scrollTo(0, 0);
}

// Validation
function validateStep(step) {
    switch (step) {
        case 1:
            return true;

        case 2:
            if (!config.apiKey || !config.apiSecret) {
                showError('Please enter your API credentials');
                return false;
            }
            if (!connectionTested) {
                showError('Please test your connection first');
                return false;
            }
            return true;

        case 3:
            if (config.capital < 20) {
                showError('Minimum capital is $20');
                return false;
            }
            return true;

        default:
            return true;
    }
}

function showError(message) {
    alert(message); // TODO: Make this prettier
}

// Exchange Setup Functions
async function testConnection() {
    const testBtn = document.getElementById('testBtn');
    const resultDiv = document.getElementById('connectionResult');
    const nextBtn = document.getElementById('nextBtn2');

    // Get values
    config.exchange = document.getElementById('exchange').value;
    config.apiKey = document.getElementById('apiKey').value.trim();
    config.apiSecret = document.getElementById('apiSecret').value.trim();

    if (!config.apiKey || !config.apiSecret) {
        resultDiv.className = 'connection-result error';
        resultDiv.textContent = '❌ Please enter both API key and secret';
        resultDiv.style.display = 'block';
        return;
    }

    // Show loading state
    testBtn.querySelector('.btn-text').style.display = 'none';
    testBtn.querySelector('.spinner').style.display = 'inline';
    testBtn.disabled = true;

    try {
        // Test connection via Electron API
        const result = await window.electronAPI.testConnection({
            exchange: config.exchange,
            apiKey: config.apiKey,
            apiSecret: config.apiSecret
        });

        if (result.success) {
            resultDiv.className = 'connection-result success';
            resultDiv.textContent = '✅ ' + result.message;
            connectionTested = true;
            nextBtn.disabled = false;
        } else {
            resultDiv.className = 'connection-result error';
            resultDiv.textContent = '❌ ' + result.message;
            connectionTested = false;
        }
        resultDiv.style.display = 'block';

    } catch (error) {
        resultDiv.className = 'connection-result error';
        resultDiv.textContent = '❌ Connection failed: ' + error.message;
        resultDiv.style.display = 'block';
        connectionTested = false;

    } finally {
        // Reset button state
        testBtn.querySelector('.btn-text').style.display = 'inline';
        testBtn.querySelector('.spinner').style.display = 'none';
        testBtn.disabled = false;
    }
}

function togglePassword(inputId) {
    const input = document.getElementById(inputId);
    input.type = input.type === 'password' ? 'text' : 'password';
}

// Trading Configuration
document.addEventListener('DOMContentLoaded', () => {
    // Risk profile selector
    document.querySelectorAll('.risk-option input').forEach(radio => {
        radio.addEventListener('change', (e) => {
            document.querySelectorAll('.risk-option').forEach(opt => {
                opt.classList.remove('active');
            });
            e.target.closest('.risk-option').classList.add('active');

            config.riskProfile = e.target.value;

            // Update profit targets based on risk
            switch (config.riskProfile) {
                case 'conservative':
                    config.profitTarget = 5.0;
                    config.maxRotations = 3;
                    break;
                case 'balanced':
                    config.profitTarget = 3.0;
                    config.maxRotations = 10;
                    break;
                case 'aggressive':
                    config.profitTarget = 2.0;
                    config.maxRotations = 15;
                    break;
            }
        });
    });

    // Capital input
    const capitalInput = document.getElementById('capital');
    if (capitalInput) {
        capitalInput.addEventListener('change', (e) => {
            config.capital = parseFloat(e.target.value);
        });
    }

    // Trading mode
    const tradingModeSelect = document.getElementById('tradingMode');
    if (tradingModeSelect) {
        tradingModeSelect.addEventListener('change', (e) => {
            config.tradingMode = e.target.value;

            // Show warning for live trading
            if (config.tradingMode === 'live') {
                if (!confirm('⚠️ WARNING: Live trading uses real money. Are you sure you want to continue?\n\nWe strongly recommend starting with Paper Trading first.')) {
                    e.target.value = 'paper';
                    config.tradingMode = 'paper';
                }
            }
        });
    }

    // Auto-start checkbox
    const autoStartCheckbox = document.getElementById('autoStart');
    if (autoStartCheckbox) {
        autoStartCheckbox.addEventListener('change', (e) => {
            config.autoStart = e.target.checked;
        });
    }
});

// Update Summary
function updateSummary() {
    // Exchange info
    document.getElementById('summary-exchange').textContent =
        config.exchange.charAt(0).toUpperCase() + config.exchange.slice(1);
    document.getElementById('summary-apikey').textContent =
        config.apiKey.substring(0, 8) + '...';

    // Trading info
    document.getElementById('summary-capital').textContent = `$${config.capital}`;
    document.getElementById('summary-mode').textContent =
        config.tradingMode === 'paper' ? 'Paper Trading' : 'Live Trading';
    document.getElementById('summary-risk').textContent =
        config.riskProfile.charAt(0).toUpperCase() + config.riskProfile.slice(1);

    // Profit rotation info
    document.getElementById('summary-target').textContent = `$${config.profitTarget}`;
    document.getElementById('summary-rotations').textContent = `${config.maxRotations}/day`;
}

// Complete Setup
async function completeSetup() {
    const finishBtn = document.getElementById('finishBtn');

    // Show loading state
    finishBtn.querySelector('.btn-text').style.display = 'none';
    finishBtn.querySelector('.spinner').style.display = 'inline';
    finishBtn.disabled = true;

    try {
        // Send configuration to Electron
        const result = await window.electronAPI.completeSetup(config);

        if (result.success) {
            // Success! App will now load dashboard
            console.log('Setup completed successfully');
        } else {
            throw new Error(result.error || 'Setup failed');
        }

    } catch (error) {
        alert('Setup failed: ' + error.message);

        // Reset button state
        finishBtn.querySelector('.btn-text').style.display = 'inline';
        finishBtn.querySelector('.spinner').style.display = 'none';
        finishBtn.disabled = false;
    }
}

// Helper Functions
function openExchangeGuide() {
    const guides = {
        kraken: 'https://support.kraken.com/hc/en-us/articles/360000919966-How-to-generate-an-API-key-pair-',
        binance: 'https://www.binance.com/en/support/faq/how-to-create-api-360002502072',
        coinbase: 'https://help.coinbase.com/en/pro/other-topics/api/how-do-i-create-an-api-key-for-coinbase-pro'
    };

    const url = guides[config.exchange] || guides.kraken;

    // Open in external browser
    if (window.electronAPI && window.electronAPI.openExternal) {
        window.electronAPI.openExternal(url);
    } else {
        window.open(url, '_blank');
    }
}

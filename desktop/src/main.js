/**
 * GridBot Chuck - Main Electron Process
 *
 * This is the main entry point for the desktop application.
 * Handles window management, system tray, and bot process control.
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const Store = require('electron-store');
const axios = require('axios');

// Handle EPIPE errors globally
process.on('uncaughtException', (error) => {
    // Silently ignore EPIPE errors which occur when writing to closed pipes
    if (error.code === 'EPIPE') {
        return;
    }
    // Log other errors if stdout is writable
    if (process.stderr.writable) {
        console.error('Uncaught exception:', error);
    }
});

// Handle unhandled promise rejections
process.on('unhandledRejection', (reason, promise) => {
    if (process.stderr.writable) {
        console.error('Unhandled promise rejection:', reason);
    }
});

// Configuration store
const store = new Store();

// Global references
let mainWindow = null;
let tray = null;
let botProcess = null;
let botApiUrl = 'http://localhost:8080';
let isFirstRun = !store.get('setupCompleted', false);

/**
 * Create the main application window
 */
function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 1000,
        minHeight: 600,
        icon: path.join(__dirname, '../assets/icon.png'),
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        show: false,
        backgroundColor: '#1a1a2e',
        titleBarStyle: 'default',
        autoHideMenuBar: false
    });

    // Load setup wizard on first run, otherwise load dashboard
    if (isFirstRun) {
        loadSetupWizard();
    } else {
        loadDashboard();
    }

    // Show window when ready
    mainWindow.once('ready-to-show', () => {
        if (mainWindow && !mainWindow.isDestroyed()) {
            mainWindow.show();
        }
    });

    // Minimize to tray instead of closing
    mainWindow.on('close', (event) => {
        if (!app.isQuitting && mainWindow && !mainWindow.isDestroyed()) {
            event.preventDefault();
            mainWindow.hide();
            return false;
        }
    });

    // Create application menu
    createMenu();
}

/**
 * Load the setup wizard
 */
function loadSetupWizard() {
    if (!mainWindow || mainWindow.isDestroyed()) {
        if (process.stdout.writable) {
            console.log('Window not available for loading setup wizard');
        }
        return;
    }
    const wizardPath = path.join(__dirname, '../../setup_wizard/templates/index.html');
    mainWindow.loadFile(wizardPath).catch(err => {
        if (process.stdout.writable && mainWindow && !mainWindow.isDestroyed()) {
            console.log('Could not load setup wizard:', err.message);
        }
    });
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.setTitle('GridBot Chuck - Setup Wizard');
    }
}

/**
 * Load the main dashboard
 */
function loadDashboard() {
    if (!mainWindow || mainWindow.isDestroyed()) {
        if (process.stdout.writable) {
            console.log('Window not available for loading dashboard');
        }
        return;
    }

    // Load local dashboard file directly (skip bot server for now)
    const dashboardPath = path.join(__dirname, '../../web/dashboard/index.html');
    mainWindow.loadFile(dashboardPath).catch(err => {
        if (process.stdout.writable && mainWindow && !mainWindow.isDestroyed()) {
            console.log('Could not load dashboard:', err.message);
        }
    });

    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.setTitle('GridBot Chuck - Dashboard');
    }
}

/**
 * Create system tray icon and menu
 */
function createTray() {
    try {
        const iconPath = path.join(__dirname, '../assets/tray-icon.png');

        // Check if icon exists, otherwise skip tray for now
        if (!require('fs').existsSync(iconPath)) {
            if (process.stdout.writable) {
                console.log('Tray icon not found, skipping tray creation. Add icons to desktop/assets/ later.');
            }
            return;
        }

        tray = new Tray(iconPath);

        updateTrayMenu();

        tray.on('click', () => {
            if (mainWindow && !mainWindow.isDestroyed()) {
                if (mainWindow.isVisible()) {
                    mainWindow.hide();
                } else {
                    mainWindow.show();
                }
            }
        });

        tray.setToolTip('GridBot Chuck');
    } catch (error) {
        if (process.stdout.writable) {
            console.log('Could not create tray icon:', error.message);
            console.log('App will work without tray icon. Add proper icons later.');
        }
    }
}

/**
 * Update tray menu based on bot status
 */
function updateTrayMenu() {
    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'GridBot Chuck',
            enabled: false,
            icon: path.join(__dirname, '../assets/icon-small.png')
        },
        { type: 'separator' },
        {
            label: 'Open Dashboard',
            click: () => {
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.show();
                    mainWindow.focus();
                }
            }
        },
        { type: 'separator' },
        {
            label: botProcess ? 'Stop Bot' : 'Start Bot',
            click: () => {
                if (botProcess) {
                    stopBot();
                } else {
                    startBot();
                }
            }
        },
        {
            label: 'Restart Bot',
            click: () => {
                restartBot();
            },
            enabled: botProcess !== null
        },
        { type: 'separator' },
        {
            label: 'Settings',
            click: () => {
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.show();
                    mainWindow.webContents.send('navigate-to', 'settings');
                }
            }
        },
        {
            label: 'View Logs',
            click: () => {
                if (mainWindow && !mainWindow.isDestroyed()) {
                    mainWindow.show();
                    mainWindow.webContents.send('navigate-to', 'logs');
                }
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                app.isQuitting = true;
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
}

/**
 * Create application menu bar
 */
function createMenu() {
    const template = [
        {
            label: 'File',
            submenu: [
                {
                    label: 'Settings',
                    accelerator: 'CmdOrCtrl+,',
                    click: () => {
                        if (mainWindow && !mainWindow.isDestroyed()) {
                            mainWindow.webContents.send('navigate-to', 'settings');
                        }
                    }
                },
                { type: 'separator' },
                {
                    label: 'Quit',
                    accelerator: 'CmdOrCtrl+Q',
                    click: () => {
                        app.isQuitting = true;
                        app.quit();
                    }
                }
            ]
        },
        {
            label: 'Bot',
            submenu: [
                {
                    label: 'Start',
                    click: () => startBot(),
                    enabled: botProcess === null
                },
                {
                    label: 'Stop',
                    click: () => stopBot(),
                    enabled: botProcess !== null
                },
                {
                    label: 'Restart',
                    click: () => restartBot(),
                    enabled: botProcess !== null
                }
            ]
        },
        {
            label: 'View',
            submenu: [
                {
                    label: 'Dashboard',
                    click: () => {
                        if (mainWindow && !mainWindow.isDestroyed()) {
                            mainWindow.webContents.send('navigate-to', 'dashboard');
                        }
                    }
                },
                {
                    label: 'Logs',
                    click: () => {
                        if (mainWindow && !mainWindow.isDestroyed()) {
                            mainWindow.webContents.send('navigate-to', 'logs');
                        }
                    }
                },
                { type: 'separator' },
                { role: 'reload' },
                { role: 'toggleDevTools' }
            ]
        },
        {
            label: 'Help',
            submenu: [
                {
                    label: 'Documentation',
                    click: async () => {
                        const { shell } = require('electron');
                        await shell.openExternal('https://github.com/your-repo/gridbotchuck/wiki');
                    }
                },
                {
                    label: 'Report Issue',
                    click: async () => {
                        const { shell } = require('electron');
                        await shell.openExternal('https://github.com/your-repo/gridbotchuck/issues');
                    }
                },
                { type: 'separator' },
                {
                    label: 'About',
                    click: () => {
                        dialog.showMessageBox(mainWindow, {
                            type: 'info',
                            title: 'About GridBot Chuck',
                            message: 'GridBot Chuck v1.0.0',
                            detail: 'Automated Crypto Grid Trading Bot\n\nCopyright © 2024\nLicensed under MIT',
                            buttons: ['OK']
                        });
                    }
                }
            ]
        }
    ];

    const menu = Menu.buildFromTemplate(template);
    Menu.setApplicationMenu(menu);
}

/**
 * Start the bot process
 */
function startBot() {
    if (botProcess) {
        if (process.stdout.writable) {
            console.log('Bot is already running');
        }
        return;
    }

    if (process.stdout.writable) {
        console.log('Starting bot...');
    }

    // Get bot directory path
    const botDir = app.isPackaged
        ? path.join(process.resourcesPath, 'bot')
        : path.join(__dirname, '../..');

    // Get Python executable path
    const pythonPath = process.platform === 'win32'
        ? path.join(botDir, '.venv', 'Scripts', 'python.exe')
        : path.join(botDir, '.venv', 'bin', 'python');

    // Get main.py path
    const mainPyPath = path.join(botDir, 'main.py');

    // Get config path
    const configPath = store.get('configPath', path.join(botDir, 'config', 'config.json'));

    // Start bot process
    botProcess = spawn(pythonPath, [mainPyPath, '--config', configPath], {
        cwd: botDir,
        stdio: ['ignore', 'pipe', 'pipe']
    });

    // Handle bot output
    botProcess.stdout.on('data', (data) => {
        try {
            const logMessage = `Bot: ${data.toString()}`;
            // Only log if we can safely write to stdout
            if (process.stdout.writable) {
                console.log(logMessage);
            }
            // Send to window if it exists and is not destroyed
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('bot-log', data.toString());
            }
        } catch (error) {
            // Silently ignore EPIPE errors
            if (error.code !== 'EPIPE') {
                console.error('Error handling bot output:', error.message);
            }
        }
    });

    botProcess.stderr.on('data', (data) => {
        try {
            const errorMessage = `Bot Error: ${data.toString()}`;
            // Only log if we can safely write to stderr
            if (process.stderr.writable) {
                console.error(errorMessage);
            }
            // Send to window if it exists and is not destroyed
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('bot-error', data.toString());
            }
        } catch (error) {
            // Silently ignore EPIPE errors
            if (error.code !== 'EPIPE') {
                console.error('Error handling bot error output:', error.message);
            }
        }
    });

    botProcess.on('close', (code) => {
        try {
            if (process.stdout.writable) {
                console.log(`Bot process exited with code ${code}`);
            }
            botProcess = null;
            if (tray) {
                updateTrayMenu();
            }
            if (mainWindow && !mainWindow.isDestroyed()) {
                mainWindow.webContents.send('bot-status', 'stopped');
            }
        } catch (error) {
            if (error.code !== 'EPIPE') {
                console.error('Error handling bot close:', error.message);
            }
        }
    });

    if (tray) {
        updateTrayMenu();
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('bot-status', 'running');
    }

    // Update tray icon to show running status
    if (tray) {
        try {
            tray.setImage(path.join(__dirname, '../assets/tray-icon-active.png'));
        } catch (error) {
            // Ignore tray icon errors
        }
    }
}

/**
 * Stop the bot process
 */
function stopBot() {
    if (!botProcess) {
        if (process.stdout.writable) {
            console.log('Bot is not running');
        }
        return;
    }

    if (process.stdout.writable) {
        console.log('Stopping bot...');
    }

    // Send graceful shutdown signal
    botProcess.kill('SIGTERM');

    // Force kill after 10 seconds if still running
    setTimeout(() => {
        if (botProcess) {
            if (process.stdout.writable) {
                console.log('Force killing bot process');
            }
            botProcess.kill('SIGKILL');
        }
    }, 10000);

    botProcess = null;
    if (tray) {
        updateTrayMenu();
    }
    if (mainWindow && !mainWindow.isDestroyed()) {
        mainWindow.webContents.send('bot-status', 'stopped');
    }

    // Update tray icon to show stopped status
    if (tray) {
        try {
            tray.setImage(path.join(__dirname, '../assets/tray-icon.png'));
        } catch (error) {
            // Ignore tray icon errors
        }
    }
}

/**
 * Restart the bot process
 */
function restartBot() {
    if (process.stdout.writable) {
        console.log('Restarting bot...');
    }
    stopBot();
    setTimeout(() => {
        startBot();
    }, 2000);
}

/**
 * IPC Handlers
 */

// Setup wizard completion
ipcMain.handle('setup-complete', async (event, config) => {
    try {
        // Save configuration
        const configPath = path.join(__dirname, '../../config/config.json');
        store.set('configPath', configPath);
        store.set('setupCompleted', true);
        isFirstRun = false;

        // Save API keys to .env
        const envPath = path.join(__dirname, '../../.env');
        const envContent = `EXCHANGE_API_KEY=${config.apiKey}\nEXCHANGE_SECRET_KEY=${config.apiSecret}\n`;
        require('fs').writeFileSync(envPath, envContent);

        // Load dashboard
        loadDashboard();

        // Start bot if configured to auto-start
        if (config.autoStart) {
            setTimeout(() => startBot(), 2000);
        }

        return { success: true };
    } catch (error) {
        if (process.stderr.writable) {
            console.error('Setup error:', error);
        }
        return { success: false, error: error.message };
    }
});

// Test API connection
ipcMain.handle('test-connection', async (event, credentials) => {
    try {
        const ccxt = require('ccxt');

        // Validate inputs
        if (!credentials.exchange || !credentials.apiKey || !credentials.apiSecret) {
            return { success: false, message: 'Missing required credentials' };
        }

        // Check if exchange is supported
        if (!ccxt.exchanges.includes(credentials.exchange)) {
            return { success: false, message: `Exchange '${credentials.exchange}' is not supported` };
        }

        // Create exchange instance
        const ExchangeClass = ccxt[credentials.exchange];
        const exchange = new ExchangeClass({
            apiKey: credentials.apiKey,
            secret: credentials.apiSecret,
            enableRateLimit: true,
            timeout: 10000
        });

        // Test the connection by fetching balance
        const balance = await exchange.fetchBalance();

        // If we get here, the connection was successful
        return {
            success: true,
            message: `Connected successfully to ${credentials.exchange}!`
        };
    } catch (error) {
        // Handle specific error cases
        if (error.message.includes('Invalid API-key')) {
            return { success: false, message: 'Invalid API key or secret' };
        } else if (error.message.includes('EAPI:Invalid key')) {
            return { success: false, message: 'Invalid API credentials for this exchange' };
        } else if (error.message.includes('authentication')) {
            return { success: false, message: 'Authentication failed - check your API credentials' };
        } else if (error.message.includes('timeout')) {
            return { success: false, message: 'Connection timeout - please try again' };
        } else if (error.message.includes('NetworkError')) {
            return { success: false, message: 'Network error - check your internet connection' };
        } else {
            return { success: false, message: `Connection failed: ${error.message}` };
        }
    }
});

// Get bot status
ipcMain.handle('get-bot-status', async () => {
    return {
        running: botProcess !== null,
        apiUrl: botApiUrl
    };
});

// Start/stop bot from renderer
ipcMain.handle('start-bot', async () => {
    startBot();
    return { success: true };
});

ipcMain.handle('stop-bot', async () => {
    stopBot();
    return { success: true };
});

/**
 * App lifecycle events
 */

app.whenReady().then(() => {
    createWindow();
    createTray();

    // Auto-start bot if not first run
    if (!isFirstRun && store.get('autoStartBot', false)) {
        setTimeout(() => startBot(), 3000);
    }

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    // Don't quit on window close, keep running in tray
    if (process.platform !== 'darwin' && !app.isQuitting) {
        return;
    }
});

app.on('before-quit', () => {
    app.isQuitting = true;
    if (botProcess) {
        stopBot();
    }
});

// Prevent multiple instances
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.show();
            mainWindow.focus();
        }
    });
}

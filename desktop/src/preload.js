/**
 * GridBot Chuck - Preload Script
 *
 * Provides secure bridge between Electron main process and renderer.
 * Exposes limited API to frontend code.
 */

const { contextBridge, ipcRenderer, shell } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    // Setup wizard
    completeSetup: (config) => ipcRenderer.invoke('setup-complete', config),
    testConnection: (credentials) => ipcRenderer.invoke('test-connection', credentials),
    openExternal: (url) => shell.openExternal(url),

    // Bot control
    getBotStatus: () => ipcRenderer.invoke('get-bot-status'),
    startBot: () => ipcRenderer.invoke('start-bot'),
    stopBot: () => ipcRenderer.invoke('stop-bot'),

    // Event listeners
    onBotStatus: (callback) => {
        ipcRenderer.on('bot-status', (event, status) => callback(status));
    },
    onBotLog: (callback) => {
        ipcRenderer.on('bot-log', (event, log) => callback(log));
    },
    onBotError: (callback) => {
        ipcRenderer.on('bot-error', (event, error) => callback(error));
    },
    onNavigate: (callback) => {
        ipcRenderer.on('navigate-to', (event, page) => callback(page));
    },

    // Remove listeners
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    }
});

// Expose platform info
contextBridge.exposeInMainWorld('platform', {
    os: process.platform,
    arch: process.arch,
    version: process.getSystemVersion()
});

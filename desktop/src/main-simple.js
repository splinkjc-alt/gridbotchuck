/**
 * Simple Electron Test - Minimal version to verify setup works
 */

const { app, BrowserWindow } = require('electron');
const path = require('path');

let mainWindow = null;

function createWindow() {
    console.log('Creating window...');

    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true
        }
    });

    // Load a simple HTML string for testing
    mainWindow.loadURL('data:text/html,<html><body><h1>GridBot Chuck - Test</h1><p>If you see this, Electron is working!</p></body></html>');

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    console.log('Window created successfully!');
}

app.whenReady().then(() => {
    console.log('App ready, creating window...');
    createWindow();
});

app.on('window-all-closed', () => {
    app.quit();
});

console.log('Electron app starting...');

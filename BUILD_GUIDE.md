# GridBot Chuck - Build Guide

## 🎯 Overview

This guide explains how to build GridBot Chuck into a **professional, downloadable Windows application** that users can install with one click - no coding required!

---

## 📦 What We've Built

### 1. **Electron Desktop App** ✅
**Location:** `desktop/`

**Features:**
- Auto-launches bot and dashboard
- System tray icon with controls
- Start/stop buttons (no terminal needed)
- Minimizes to tray
- Professional UI
- Single instance enforcement

**Files:**
- `desktop/package.json` - Electron dependencies
- `desktop/src/main.js` - Main process (530 lines)
- `desktop/src/preload.js` - Security bridge

---

### 2. **Setup Wizard** ✅
**Location:** `setup_wizard/`

**Features:**
- 4-step guided setup
- API key configuration
- Connection testing
- Risk profile selector (Conservative/Balanced/Aggressive)
- Visual, modern UI
- No JSON editing required

**Files:**
- `setup_wizard/templates/index.html` - Wizard UI (400+ lines)
- `setup_wizard/static/css/wizard.css` - Styling (700+ lines)
- `setup_wizard/static/js/wizard.js` - Logic (300+ lines)

**Wizard Steps:**
1. **Welcome** - Feature overview
2. **Exchange** - API key setup + connection test
3. **Trading** - Capital, mode, risk profile
4. **Review** - Summary + Start trading

---

### 3. **Windows Installer** ✅
**Location:** `installer/windows/`

**Features:**
- One-click .exe installer
- Bundles Python + Electron
- Desktop shortcut creation
- Start menu entry
- Professional uninstaller

**Files:**
- `installer/windows/build_windows.py` - Build script (350+ lines)
- `installer/windows/gridbot.spec` - PyInstaller config (auto-generated)
- `installer/windows/installer.nsi` - NSIS script (auto-generated)

---

## 🛠️ Prerequisites

Before building, install these tools:

### 1. Node.js & npm
```bash
# Download from: https://nodejs.org/
# Version 18.x or higher
node --version
npm --version
```

### 2. Python & pip
```bash
# You already have this (your bot is Python)
python --version  # Should be 3.10+
```

### 3. PyInstaller
```bash
pip install pyinstaller
```

### 4. NSIS (Windows only)
```bash
# Download from: https://nsis.sourceforge.io/Download
# Install to default location: C:\Program Files (x86)\NSIS\
```

---

## 🚀 Build Instructions

### Option A: Automated Build (Recommended)

**One command builds everything:**

```bash
cd "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master"
python installer/windows/build_windows.py
```

**This will:**
1. ✅ Clean previous builds
2. ✅ Bundle Python bot with PyInstaller
3. ✅ Build Electron app
4. ✅ Create NSIS installer
5. ✅ Output: `dist/GridBotChuck-Setup-1.0.0.exe`

**Time:** ~5-10 minutes

---

### Option B: Manual Build (Step-by-Step)

#### Step 1: Build Python Bot

```bash
cd "C:\Users\splin\OneDrive\Documents\grid_trading_bot-master"

# Create PyInstaller spec (first time only)
pyinstaller --name="GridBotChuck" \
            --onedir \
            --windowed \
            --icon="desktop/assets/icon.ico" \
            --add-data="config;config" \
            --add-data="strategies;strategies" \
            --add-data="web;web" \
            --add-data="setup_wizard;setup_wizard" \
            main.py
```

**Output:** `dist/GridBotChuck/` (folder with bot executable)

#### Step 2: Build Electron App

```bash
cd desktop

# Install dependencies (first time only)
npm install

# Build for Windows
npm run build:win
```

**Output:** `desktop/dist/win-unpacked/` (Electron app folder)

#### Step 3: Create Installer

```bash
# Run NSIS compiler
"C:\Program Files (x86)\NSIS\makensis.exe" installer/windows/installer.nsi
```

**Output:** `dist/GridBotChuck-Setup-1.0.0.exe`

---

## 📂 Build Output Structure

After successful build:

```
dist/
├── GridBotChuck/                      # Python bot bundle
│   ├── GridBotChuck.exe              # Bot executable
│   ├── config/                        # Config files
│   ├── strategies/                    # Trading strategies
│   ├── web/                           # Dashboard
│   └── ... (Python dependencies)
│
└── GridBotChuck-Setup-1.0.0.exe      # 🎯 FINAL INSTALLER
```

---

## 🧪 Testing the Build

### Test on Clean Machine

**IMPORTANT:** Test the installer on a machine WITHOUT Python/Node installed.

1. **Copy installer** to test machine:
   ```
   dist/GridBotChuck-Setup-1.0.0.exe
   ```

2. **Run installer**:
   - Double-click the .exe
   - Follow installation wizard
   - Choose install location
   - Create shortcuts

3. **Launch app**:
   - Desktop shortcut OR
   - Start menu → GridBot Chuck

4. **Complete setup wizard**:
   - Enter API keys
   - Select trading mode (Paper recommended)
   - Choose risk profile
   - Click "Start Trading"

5. **Verify functionality**:
   - ✅ Dashboard opens
   - ✅ Bot starts automatically
   - ✅ System tray icon appears
   - ✅ Can stop/start from tray
   - ✅ Logs are visible
   - ✅ No errors in console

---

## 🔧 Troubleshooting Build Issues

### Issue: "PyInstaller not found"
**Solution:**
```bash
pip install pyinstaller
```

### Issue: "npm command not found"
**Solution:**
Install Node.js from https://nodejs.org/

### Issue: "NSIS not found"
**Solution:**
1. Install NSIS from https://nsis.sourceforge.io/
2. Add to PATH: `C:\Program Files (x86)\NSIS\`
3. Restart terminal

### Issue: "Module not found" during PyInstaller
**Solution:**
Add missing module to `hiddenimports` in `gridbot.spec`:
```python
hiddenimports=[
    'ccxt',
    'aiosqlite',
    'your_missing_module',  # Add here
],
```

### Issue: Electron build fails
**Solution:**
```bash
cd desktop
rm -rf node_modules
npm install
npm run build:win
```

### Issue: Installer too large (> 200MB)
**Solution:**
This is normal! Includes:
- Python runtime (~50MB)
- All dependencies (~80MB)
- Electron app (~70MB)

To reduce size:
- Remove unused Python packages
- Use UPX compression (enabled by default)
- Exclude unnecessary files

---

## 📝 Customization

### Change App Name

**1. Update package.json:**
```json
{
  "name": "your-bot-name",
  "productName": "Your Bot Name"
}
```

**2. Update build_windows.py:**
```python
PRODUCT_NAME = "Your Bot Name"
```

**3. Rebuild**

### Change Icon

Replace these files:
- `desktop/assets/icon.ico` (256x256)
- `desktop/assets/icon.png` (512x512)
- `desktop/assets/tray-icon.png` (32x32)

### Add Splash Screen

**1. Create splash.html** in `desktop/src/`

**2. Modify main.js**:
```javascript
// Show splash screen
const splash = new BrowserWindow({
    width: 400,
    height: 300,
    transparent: true,
    frame: false
});
splash.loadFile('src/splash.html');

// Load main window after 3 seconds
setTimeout(() => {
    splash.close();
    createWindow();
}, 3000);
```

---

## 🚢 Distribution

### Upload to GitHub Releases

```bash
# Tag version
git tag v1.0.0
git push origin v1.0.0

# Upload to GitHub Releases
- Go to repository → Releases → Create new release
- Upload: dist/GridBotChuck-Setup-1.0.0.exe
- Add release notes
```

### Create Download Page

**Simple HTML:**
```html
<a href="https://github.com/your-repo/releases/download/v1.0.0/GridBotChuck-Setup-1.0.0.exe">
    Download GridBot Chuck v1.0.0 for Windows
</a>
```

### Auto-Updates (Advanced)

Use `electron-updater`:
```javascript
const { autoUpdater } = require('electron-updater');

autoUpdater.checkForUpdatesAndNotify();
```

---

## 📊 Build Checklist

Before releasing:

- [ ] All tests pass
- [ ] Profit rotation engine working
- [ ] Setup wizard completes successfully
- [ ] Bot starts and connects to exchange
- [ ] Dashboard displays correctly
- [ ] System tray works
- [ ] Start/stop controls functional
- [ ] Logs are visible
- [ ] No console errors
- [ ] Tested on clean Windows machine
- [ ] Installer creates shortcuts
- [ ] Uninstaller works
- [ ] Version numbers updated
- [ ] CHANGELOG.md updated
- [ ] README.md updated
- [ ] LICENSE file included

---

## 🎉 You're Ready!

Your GridBot Chuck is now a **professional desktop application** that anyone can download and use!

**Next Steps:**
1. Test thoroughly
2. Create promotional materials (screenshots, video)
3. Write user documentation
4. Set up support channels (Discord, email)
5. Launch! 🚀

---

## 💡 Tips

**For Beta Testing:**
- Start with 5-10 trusted users
- Collect feedback on setup wizard
- Monitor for installation issues
- Iterate quickly

**For Marketing:**
- Create demo video (5min)
- Take high-quality screenshots
- Write compelling landing page
- Share in crypto trading communities

**For Support:**
- Set up Discord server
- Create FAQ document
- Monitor GitHub issues
- Provide quick responses

---

## 📞 Need Help?

- Check `TROUBLESHOOTING.md`
- Open GitHub issue
- Contact: support@gridbotchuck.com

Good luck with your launch! 🎊

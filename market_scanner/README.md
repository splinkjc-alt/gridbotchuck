# AI Market Scanner

A Python-based market scanner focused on **AI Stocks** and **AI Crypto Assets**.

## Features
- **AI Sector Focus**: Scans top AI stocks (NVDA, MSFT, PLTR, etc.) and AI tokens (FET, RNDR, TAO, etc.).
- **Location Aware**: Filters crypto pairs by currency (Default: USD).
- **4-Strategy Analysis**:
  1.  **Long-Term**: Trend following (200 SMA).
  2.  **Strategic**: Momentum (1-Month Return).
  3.  **Risk**: Safety (Inverse Volatility).
  4.  **Trading**: Dip Buying (RSI).

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the scanner (Terminal):
   ```bash
   python main.py
   ```
3. Run the Web App (GUI):
   ```bash
   streamlit run app.py
   ```

## VS Code Task & Hotkey
This project includes a VS Code Task named **"Run Market Scanner"**.

### Setting up a Hotkey (Ctrl+Shift+Alt+M)
To bind `Ctrl+Shift+Alt+M` to run this scanner:
1. Open Command Palette (`Ctrl+Shift+P`) and search for **"Preferences: Open Keyboard Shortcuts (JSON)"**.
2. Add the following to the list:
   ```json
   {
       "key": "ctrl+shift+alt+m",
       "command": "workbench.action.tasks.runTask",
       "args": "Run Market Scanner"
   }
   ```

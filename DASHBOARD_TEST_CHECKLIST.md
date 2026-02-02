# 🧪 Dashboard Button & Action Test Checklist

Use this checklist to verify all dashboard functionality before release.

---

## 📋 Pre-Test Setup

- [ ] Bot is running: `python main.py --config config/config.json --wait`
- [ ] Dashboard accessible at: `ttp:/h/localhost:8080`
- [ ] Browser console open (F12) to check for errors

---

## 🔧 Header Section

### Account Dropdown (⚙️ icon - top right)

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 1 | Click ⚙️ icon | Dropdown menu opens | | |
| 2 | Click outside dropdown | Dropdown closes | | |
| 3 | **Exchange Selector** | | | |
| 3a | Select "Kraken" | Shows notification, updates account name | | |
| 3b | Select "Coinbase" | Shows notification, updates account name | | |
| 3c | Select "Binance" | Shows notification, updates account name | | |
| 3d | Select "KuCoin" | Shows notification, updates account name | | |
| 3e | Select "Bybit" | Shows notification, updates account name | | |
| 4 | **Trading Mode Selector** | | | |
| 4a | Select "Live" | Shows notification confirming mode change | | |
| 4b | Select "Paper Trading" | Shows notification confirming mode change | | |
| 4c | Select "Backtest" | Shows notification confirming mode change | | |
| 5 | **API Settings** | Opens modal with API key inputs | | |
| 5a | Enter API Key + Secret, click Save | Modal closes, shows success notification | | |
| 5b | Click Cancel | Modal closes without saving | | |
| 5c | Click outside modal | Modal closes | | |
| 6 | **Notification Settings** | Opens modal with checkboxes | | |
| 6a | Toggle checkboxes, click Save | Modal closes, shows success notification | | |
| 6b | Click Cancel | Modal closes without saving | | |
| 7 | **Export Config** | Downloads JSON config file | | |
| 8 | **Reset Bot** | Shows confirmation, resets on confirm | | |

---

## 🤖 Bot Controls Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 9 | **Start Bot** (▶️) | Bot starts, status updates to "running" | | |
| 10 | **Pause Bot** (⏸️) | Bot pauses, status updates to "paused" | | |
| 11 | **Resume Bot** (▶️) | Bot resumes from pause | | |
| 12 | **Stop Bot** (⏹️) | Bot stops, status updates to "stopped" | | |

---

## 📊 Status Display

| # | Element | Expected Result | ✅/❌ | Notes |
|---|---------|-----------------|-------|-------|
| 13 | Connection indicator | Shows green "Connected" when API responds | | |
| 14 | Bot status badge | Updates based on bot state | | |
| 15 | Trading pair display | Shows current pair (e.g., HNT/USD) | | |
| 16 | Balance display | Shows available balance | | |
| 17 | Auto-refresh | Data updates every 2 seconds | | |

---

## 🧠 Chuck AI Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 18 | **Smart Scan** | Scans market, displays ranked pairs | | |
| 19 | **Start Auto-Portfolio** | Starts autonomous trading manager | | |
| 20 | **Stop Auto-Portfolio** | Stops portfolio manager | | |
| 21 | **View Portfolio** | Shows current portfolio positions | | |
| 22 | **Analyze Entry** | Shows entry signal analysis for current pair | | |

---

## 🔍 Market Scanner Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 23 | **Scan Markets** button | Triggers market scan | | |
| 24 | **Auto-Scan Toggle** | Enables/disables automatic scanning | | |
| 25 | Auto-scan interval dropdown | Changes scan frequency | | |
| 26 | Click on scanned coin row | Opens coin details modal | | |
| 27 | Coin details modal **X** button | Closes modal | | |
| 28 | **Select for Trading** button | Selects pair, closes modal | | |

---

## 📈 Multi-Pair Trading Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 29 | **Max Pairs** dropdown | Changes max concurrent pairs | | |
| 30 | **Capital per Pair** input | Updates allocation | | |
| 31 | **Add Pair** button | Opens pair selection | | |
| 32 | **Remove Pair** (🗑️) | Removes pair from list | | |
| 33 | **Configure Pair** (⚙️) | Opens pair configuration | | |
| 34 | **Start Multi-Pair** | Starts multi-pair trading | | |
| 35 | **Stop Multi-Pair** | Stops multi-pair trading | | |

---

## ⏱️ Multi-Timeframe Analysis Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 36 | **Run Analysis** | Analyzes across timeframes | | |
| 37 | Timeframe checkboxes | Toggles timeframes to analyze | | |
| 38 | Results display | Shows trend alignment across TFs | | |

---

## ⚙️ Grid Configuration Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 39 | Grid size input | Updates grid levels | | |
| 40 | Price range inputs | Sets upper/lower bounds | | |
| 41 | Spacing type dropdown | Arithmetic/Geometric selection | | |
| 42 | **Update Grid** button | Applies new grid configuration | | |
| 43 | Grid visualization | Shows grid levels visually | | |

---

## 📝 Orders Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 44 | Active orders display | Shows pending orders | | |
| 45 | **Cancel Order** button | Cancels selected order | | |
| 46 | **Cancel All** button | Cancels all orders | | |
| 47 | Order history tab | Shows completed orders | | |

---

## 📜 Activity Log Section

| # | Button/Action | Expected Result | ✅/❌ | Notes |
|---|---------------|-----------------|-------|-------|
| 48 | Log entries display | Shows timestamped events | | |
| 49 | Log auto-scroll | New entries scroll into view | | |
| 50 | **Clear Log** button | Clears all log entries | | |

---

## 🔔 Notifications (Toast Messages)

| # | Trigger | Expected Result | ✅/❌ | Notes |
|---|---------|-----------------|-------|-------|
| 51 | Success action | Green toast appears, fades after 3s | | |
| 52 | Error action | Red toast appears | | |
| 53 | Warning action | Yellow toast appears | | |
| 54 | Info action | Blue toast appears | | |

---

## 🌐 Browser Compatibility

| # | Browser | Works? | ✅/❌ | Notes |
|---|---------|--------|-------|-------|
| 55 | Chrome | | | |
| 56 | Firefox | | | |
| 57 | Edge | | | |
| 58 | Safari | | | |

---

## 📱 Responsive Design

| # | Screen Size | Works? | ✅/❌ | Notes |
|---|-------------|--------|-------|-------|
| 59 | Desktop (1920x1080) | | | |
| 60 | Laptop (1366x768) | | | |
| 61 | Tablet (768x1024) | | | |
| 62 | Mobile (375x667) | | | |

---

## 🐛 Error Handling

| # | Scenario | Expected Result | ✅/❌ | Notes |
|---|----------|-----------------|-------|-------|
| 63 | Bot not running | Shows "Disconnected" status | | |
| 64 | API timeout | Shows error notification | | |
| 65 | Invalid input | Shows validation error | | |
| 66 | Network error | Graceful error message | | |

---

## ✅ Test Summary

| Category | Passed | Failed | Total |
|----------|--------|--------|-------|
| Header/Account | /8 | | 8 |
| Bot Controls | /4 | | 4 |
| Status Display | /5 | | 5 |
| Chuck AI | /5 | | 5 |
| Market Scanner | /6 | | 6 |
| Multi-Pair | /7 | | 7 |
| Multi-Timeframe | /3 | | 3 |
| Grid Config | /5 | | 5 |
| Orders | /4 | | 4 |
| Activity Log | /3 | | 3 |
| Notifications | /4 | | 4 |
| Browser Compat | /4 | | 4 |
| Responsive | /4 | | 4 |
| Error Handling | /4 | | 4 |
| **TOTAL** | | | **66** |

---

## 📝 Tester Information

- **Tester Name:** ____________________
- **Date:** ____________________
- **Bot Version:** ____________________
- **Browser/OS:** ____________________

---

## 🔧 Issues Found

| Issue # | Description | Severity | Status |
|---------|-------------|----------|--------|
| | | | |
| | | | |
| | | | |

**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## ✍️ Sign-Off

- [ ] All critical functions tested
- [ ] No blocking issues found
- [ ] Ready for customer release

**Approved by:** ____________________
**Date:** ____________________

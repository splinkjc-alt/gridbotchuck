# GridBot Dashboard Source Code Export

This file contains the complete dashboard source code for reference by website building AI.

---

## 📊 File Overview

| File | Lines | Purpose |
|------|-------|---------|
| index.html | 947 | Main dashboard interface |
| styles.css | 3381 | Complete design system & styles |
| script.js | 2502 | Dashboard JavaScript logic |
| settings.html | 765 | Settings configuration page |
| settings.css | ~400 | Settings page styles |
| settings.js | 737 | Settings page logic |
| backtest.html | 247 | Backtest interface |
| backtest.css | 654 | Backtest page styles |
| backtest.js | 535 | Backtest logic |

---

## 🎨 Design System & CSS Variables

```css
:root {
  /* Primary/Brand Colors */
  --primary-color: #3b82f6;      /* Blue - main brand color */
  --primary-dark: #2563eb;       /* Darker blue */

  /* Semantic Colors */
  --success-color: #10b981;      /* Green - positive actions/values */
  --success-light: rgba(16, 185, 129, 0.1);
  --warning-color: #f59e0b;      /* Orange/amber - warnings */
  --danger-color: #ef4444;       /* Red - errors/negative */
  --info-color: #06b6d4;         /* Cyan - information */

  /* Background Colors (Slate palette) */
  --dark-bg: #0f172a;            /* Main dark background (slate-900) */
  --card-bg: #1e293b;            /* Card background (slate-800) */
  --card-hover: #334155;         /* Card hover state (slate-700) */
  --border-color: #334155;       /* Borders (slate-700) */

  /* Text Colors */
  --text-primary: #f1f5f9;       /* Main text (slate-100) */
  --text-secondary: #94a3b8;     /* Secondary text (slate-400) */

  /* Gradients */
  --gradient-primary: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);  /* Blue to purple */
  --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);  /* Green gradient */

  /* Shadows */
  --shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 40px rgba(0, 0, 0, 0.5);

  /* Transitions */
  --transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Typography

- **Primary Font**: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Google Fonts**: Inter (weights: 400, 500, 600, 700)
- **Monospace**: `'Courier New', monospace` (for logs)
- **Console Font**: `'Consolas', 'Monaco', monospace`

### Additional Colors

- **Risk Banner**: `#dc2626` to `#b91c1c` (red gradient)
- **Pro Badge**: `#fbbf24` to `#f59e0b` (gold/amber gradient)
- **Settings Background**: `linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)`

---

## 🖼️ Dashboard Screenshots Description

### Main Dashboard (index.html)

1. **Risk Warning Banner** - Red gradient bar at top with dismissible warning
2. **Header** - Blue-purple gradient with:
   - Brand logo: 📊 GridBot CHUCK (with gold "CHUCK" badge)
   - Live price display with change percentage
   - Account dropdown (exchange, mode, strategy selectors)
   - Connection status dot (green=connected, yellow=connecting, red=disconnected)

3. **Bot Control Section** - 4 action buttons:
   - ▶ Start Bot (green)
   - ⏸ Pause (yellow)
   - ⏩ Resume (cyan)
   - ⏹ Stop Bot (red)

4. **P&L Dashboard Cards** - 4 horizontal cards:
   - 💰 Total Portfolio ($XXX.XX)
   - 📈 Session P&L (+$XX.XX with %)
   - 🔄 Trades Today (count)
   - ⏱️ Bot Uptime (HH:MM:SS)

5. **Live Price Chart** - Chart.js line chart with:
   - Timeframe buttons: 1H | 4H | 1D
   - Grid levels overlay

6. **Market Scanner** - Filter controls + results table:
   - Filters: Min/Max Price, Timeframe, EMA Fast/Slow
   - Results: Rank, Pair, Price, 24h%, Score, Signal, EMA, CCI, MACD, Actions

7. **Multi-Pair Trading** - Configure multiple trading pairs

8. **Multi-Timeframe Analysis** - Trend cards for Daily/4H/1H

9. **Chuck AI Section** - 3 tabbed panels:
   - Smart Scan (analyze pair suitability)
   - Auto-Portfolio (autonomous trading)
   - Entry Signals (timing analysis)

10. **Status Section** - Bot status and balance info

11. **Orders Table** - Recent orders with columns: Time, Pair, Side, Price, Size, Status

12. **Logs Section** - Scrollable activity log with timestamps

---

## 🔧 Key UI Components

### Buttons

```html
<button class="btn btn-success">
  <span class="btn-icon">▶</span>
  <span class="btn-text">Start Bot</span>
</button>
```

Button classes: `.btn-success` (green), `.btn-warning` (yellow), `.btn-info` (cyan), `.btn-danger` (red), `.btn-primary` (blue gradient)

### Status Cards

```html
<div class="pnl-card profit">
  <div class="pnl-icon">📈</div>
  <div class="pnl-info">
    <span class="pnl-label">Session P&L</span>
    <span class="pnl-value positive">+$45.00</span>
    <span class="pnl-percent">(+2.3%)</span>
  </div>
</div>
```

### Scanner Table

```html
<table class="scanner-table">
  <thead>
    <tr>
      <th>Rank</th><th>Pair</th><th>Price</th><th>24h %</th>
      <th>Score</th><th>Signal</th><th>EMA</th><th>Actions</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td>BTC/USD</td>
      <td>$43,250.00</td>
      <td class="positive">+2.45%</td>
      <td><span class="score-badge high">85</span></td>
      <td><span class="signal-badge bullish">BULLISH</span></td>
      <td>Above</td>
      <td><button class="btn btn-small">Trade</button></td>
    </tr>
  </tbody>
</table>
```

### Connection Status

```html
<div class="connection-status">
  <span class="status-dot connected"></span>
  <span>Connected</span>
</div>
```

### Tooltips

```html
<button data-tooltip="Start the trading bot" data-tooltip-pos="bottom">
  Start Bot
</button>
```

---

## 📱 Responsive Breakpoints

```css
/* Tablet */
@media (max-width: 768px) {
  .main-content {
    padding: 1rem;
    gap: 1rem;
  }
  .control-buttons {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* Mobile */
@media (max-width: 480px) {
  .header-content {
    flex-direction: column;
    gap: 1rem;
  }
  .control-buttons {
    grid-template-columns: 1fr;
  }
}
```

---

## 🎯 Design Patterns Summary

1. **Dark Theme** - Slate color palette (900/800/700 backgrounds)
2. **Card-Based Layout** - Content in rounded cards with subtle borders
3. **Gradient Headers** - Blue-to-purple (#3b82f6 → #8b5cf6) brand gradient
4. **Color-Coded Actions** - Green=success, Red=danger, Yellow=warning, Blue=info
5. **Emoji Icons** - Consistent use of emoji for visual interest (📊 📈 💰 🔍 etc.)
6. **Custom Tooltips** - Data attribute-based tooltip system
7. **Responsive Grid** - CSS Grid with auto-fit and minmax
8. **Smooth Transitions** - 0.3s cubic-bezier easing
9. **Hover Effects** - Subtle lift (translateY) and shadow increase

---

## 📁 Source Files Location

All dashboard files are in: `/web/dashboard/`

```
web/
└── dashboard/
    ├── index.html      (Main dashboard)
    ├── styles.css      (Main styles)
    ├── script.js       (Main JS)
    ├── settings.html   (Settings page)
    ├── settings.css    (Settings styles)
    ├── settings.js     (Settings JS)
    ├── backtest.html   (Backtest page)
    ├── backtest.css    (Backtest styles)
    └── backtest.js     (Backtest JS)
```

---

## 🌐 Website Design Recommendations

Based on the dashboard design, the marketing website should:

1. **Match the Dark Theme** - Use same slate color palette
2. **Use Brand Gradient** - Blue-purple gradient for headers/CTAs
3. **Professional Typography** - Inter font family
4. **Card-Based Sections** - Feature cards with subtle borders
5. **Emoji Accents** - Use consistent emoji icons
6. **Color-Coded Benefits** - Green for gains, red for risks
7. **Live Demo Preview** - Screenshot or video of dashboard
8. **Mobile-First** - Responsive from mobile up

---

*Generated for website building AI reference*
*GridBot Chuck - Automated Grid Trading*

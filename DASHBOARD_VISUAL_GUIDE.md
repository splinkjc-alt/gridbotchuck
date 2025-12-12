# Dashboard Visual Guide

## Desktop Layout (1920x1080)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ 🤖 Grid Trading Bot Control        ● Connected                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  [▶ START BOT]  [⏸ PAUSE]  [⏩ RESUME]  [⏹ STOP BOT]                        │
│                                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │     BOT STATUS              │  │        BALANCE                       │  │
│  │                             │  │                                      │  │
│  │ Status: Running ✓           │  │ Fiat: $1,250.50                     │  │
│  │ Mode: BACKTEST              │  │ Crypto: 2.5 SOL                     │  │
│  │ Pair: SOL/usd              │  │ Total: $2,100.75                    │  │
│  │ Updated: 14:32:15           │  │                                      │  │
│  └─────────────────────────────┘  └──────────────────────────────────────┘  │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │          GRID CONFIGURATION                                          │   │
│  │                                                                      │   │
│  │ Central Price: $225.50        Total Grids: 8                       │   │
│  │ Buy Grids: 4                  Sell Grids: 4                        │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                    │
│  │  TOTAL   │  │   OPEN   │  │ FILLED   │  │  TOTAL   │                    │
│  │ ORDERS   │  │ ORDERS   │  │ ORDERS   │  │  FEES    │                    │
│  │    42    │  │    3     │  │   39     │  │ $12.50   │                    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘                    │
│                                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ RECENT ORDERS                                                                │
├─────┬──────┬──────────┬──────────┬──────────┬──────────────────────────────┤
│ ID  │ SIDE │  PRICE   │   QTY    │  STATUS  │ TIME                         │
├─────┼──────┼──────────┼──────────┼──────────┼──────────────────────────────┤
│ 42  │ SELL │ $230.50  │ 0.500    │ FILLED   │ 14:32:10                     │
│ 41  │ BUY  │ $218.75  │ 0.600    │ FILLED   │ 14:30:05                     │
│ 40  │ SELL │ $228.25  │ 0.400    │ FILLED   │ 14:28:50                     │
│ ... │  ... │   ...    │  ...     │   ...    │ ...                          │
├─────┴──────┴──────────┴──────────┴──────────┴──────────────────────────────┤
│                                                                               │
│ CONFIGURATION                          STATUS LOG                           │
│ Strategy: hedged_grid                  [14:32:15] Status updated      ✓    │
│ Spacing: geometric                     [14:30:10] Order filled        ✓    │
│ ☑ Take Profit: $3700                   [14:28:50] New order placed   ✓    │
│ ☑ Stop Loss: $2830                     [14:25:30] Bot started         ✓    │
│                                        [14:20:00] Connected            ✓    │
│                                                                               │
├──────────────────────────────────────────────────────────────────────────────┤
│ Grid Trading Bot • Auto-updates every 2 seconds • Last refresh: 14:32:15   │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Mobile Layout (iPhone 12, 390x844)

```
┌─────────────────────────────┐
│ 🤖 Grid Trading Bot Control │
│       ● Connected           │
├─────────────────────────────┤
│                             │
│    [▶ START BOT]            │
│    [⏸ PAUSE]               │
│    [⏩ RESUME]              │
│    [⏹ STOP BOT]            │
│                             │
├─────────────────────────────┤
│                             │
│    BOT STATUS               │
│ ──────────────────────────  │
│ Status: Running             │
│ Mode: BACKTEST              │
│ Pair: SOL/usd              │
│ Updated: 14:32:15           │
│                             │
│    BALANCE                  │
│ ──────────────────────────  │
│ Fiat: $1,250.50             │
│ Crypto: 2.5 SOL             │
│ Total: $2,100.75            │
│                             │
│    GRID CONFIG              │
│ ──────────────────────────  │
│ Central: $225.50            │
│ Total: 8  Buy: 4  Sell: 4   │
│                             │
├─────────────────────────────┤
│                             │
│  42    3    39    $12.50    │
│ ORDERS OPEN FILLED FEES     │
│                             │
├─────────────────────────────┤
│ RECENT ORDERS               │
│ ───────────────────────────│
│ 42  SELL $230.50 14:32:10  │
│ 41  BUY  $218.75 14:30:05  │
│ 40  SELL $228.25 14:28:50  │
│                             │
├─────────────────────────────┤
│ CONFIG                      │
│ ───────────────────────────│
│ ☑ Take Profit: $3700       │
│ ☑ Stop Loss: $2830         │
│                             │
├─────────────────────────────┤
│ STATUS LOG                  │
│ ───────────────────────────│
│ ✓ 14:32:15 Status updated  │
│ ✓ 14:30:10 Order filled    │
│ ✓ 14:28:50 New order       │
│ ✓ 14:25:30 Bot started     │
│                             │
├─────────────────────────────┤
│ Last refresh: 14:32:15      │
└─────────────────────────────┘
```

---

## Tablet Layout (iPad, 1024x768)

```
┌────────────────────────────────────────────────────────────────────────┐
│ 🤖 Grid Trading Bot Control          ● Connected                       │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [▶ START]  [⏸ PAUSE]  [⏩ RESUME]  [⏹ STOP]                         │
│                                                                        │
├────────────────────────────────┬───────────────────────────────────────┤
│                                │                                       │
│  BOT STATUS                    │  BALANCE                              │
│  ─────────────────────────────│───────────────────────────────────────│
│  Status: Running ✓             │  Fiat: $1,250.50                      │
│  Mode: BACKTEST                │  Crypto: 2.5 SOL                      │
│  Pair: SOL/usd                │  Total: $2,100.75                     │
│  Updated: 14:32:15             │                                       │
│                                │                                       │
├────────────────────────────────┴───────────────────────────────────────┤
│  GRID CONFIG                                                            │
│  Central: $225.50 | Total: 8 | Buy: 4 | Sell: 4                      │
├────────────────────────────────┬───────────────────────────────────────┤
│                                │                                       │
│  METRICS                       │  CONFIGURATION                        │
│  ─────────────────────────────│───────────────────────────────────────│
│  Total Orders:    42           │  Strategy: hedged_grid                │
│  Open Orders:     3            │  Spacing:  geometric                  │
│  Filled Orders:   39           │  ☑ TP: $3700                          │
│  Total Fees:      $12.50       │  ☑ SL: $2830                          │
│                                │                                       │
├────────────────────────────────────────────────────────────────────────┤
│ RECENT ORDERS                                                           │
│ ──────┬──────┬──────────┬──────────┬──────────┬──────────────────────  │
│ ID    │ SIDE │  PRICE   │   QTY    │  STATUS  │ TIME                  │
│ ──────┼──────┼──────────┼──────────┼──────────┼──────────────────────  │
│ 42    │ SELL │ $230.50  │ 0.500    │ FILLED   │ 14:32:10              │
│ 41    │ BUY  │ $218.75  │ 0.600    │ FILLED   │ 14:30:05              │
│ 40    │ SELL │ $228.25  │ 0.400    │ FILLED   │ 14:28:50              │
│                                                                        │
├────────────────────────────────────────────────────────────────────────┤
│ STATUS LOG                                                              │
│ [14:32:15] Status updated    ✓   [14:20:00] Connected          ✓     │
│ [14:30:10] Order filled      ✓   [14:15:00] Bot initialized    ✓     │
│ [14:28:50] New order placed  ✓   [14:10:00] Dashboard loaded   ✓     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Control Button States

### Default State (Ready)

```
┌─────────────────────┐
│ ▶ START BOT         │  Green, clickable
└─────────────────────┘
```

### Hover State

```
┌─────────────────────┐
│ ▶ START BOT         │  Slightly raised, darker
└─────────────────────┘  (translateY -2px)
```

### Active State

```
┌─────────────────────┐
│ ▶ START BOT         │  Pressed down
└─────────────────────┘
```

### Disabled State

```
┌─────────────────────┐
│ ▶ START BOT         │  Grayed out (50% opacity)
└─────────────────────┘
```

---

## Color Scheme

```
Primary Blue:     #2196F3  (Status, headers)
Success Green:    #4CAF50  (Start button, success logs)
Warning Yellow:   #FF9800  (Pause button, caution)
Info Cyan:        #00BCD4  (Resume button, info)
Danger Red:       #f44336  (Stop button, critical)
Dark Background:  #1a1a1a
Card Background:  #2d2d2d
Text Primary:     #ffffff
Text Secondary:   #b0b0b0
Border:           #404040
```

---

## Responsive Breakpoints

```
Desktop:   1920px+  (Full multi-column layout)
Tablet:   768px+   (2-column with wrapping)
Phone:    480px+   (Single column, full width)
Mobile:   <480px   (Extra compact)
```

---

## Interactive Elements

### Buttons

- Large touch targets (min 44x44px on mobile)
- Visual feedback on click
- Color-coded by function
- Clear text labels with icons

### Status Indicators

- Connection dot (animated pulse when disconnected)
- Running status color change
- Real-time metric updates

### Forms

- Checkbox toggles for TP/SL
- Text inputs for configuration
- Auto-submit on change

### Tables

- Scrollable on mobile
- Sticky header
- Responsive column sizing
- Hover effects on desktop

---

## Animation Effects

### Connection Status Pulse

```
0%:    opacity: 1.0
50%:   opacity: 0.5
100%:  opacity: 1.0
Repeats every 2 seconds (when disconnected)
```

### Button Hover

```
translateY: 0px → -2px
box-shadow: increases
Smooth transition: 0.3s
```

### Card Hover

```
border-color: gray → blue
box-shadow: increases
Subtle glow effect
```

---

## Accessibility Features

✅ High contrast colors (WCAG AA compliant)
✅ Semantic HTML structure
✅ Keyboard navigation support
✅ Clear button labels
✅ Status messages for screen readers
✅ Touch-friendly sizing
✅ Readable fonts (system stack)

---

This visual guide shows exactly what users see and how the dashboard responds to interaction!

"""
Indicator Combinations for Optimization
========================================

Defines all timeframe/indicator combinations to test during optimization.
"""

# Timeframes to test
TIMEFRAMES = ['5m', '15m', '30m', '1h']

# Strategy types
STRATEGIES = ['grid', 'mean_reversion', 'momentum']

# Indicator combinations to test
INDICATOR_COMBOS = {
    'rsi_only': {
        'name': 'RSI Only',
        'indicators': ['RSI(14)'],
        'params': {
            'rsi_period': 14,
            'rsi_buy': 30,
            'rsi_sell': 70
        }
    },
    'rsi_bb': {
        'name': 'RSI + Bollinger',
        'indicators': ['RSI(14)', 'Bollinger(20,2)'],
        'params': {
            'rsi_period': 14,
            'rsi_buy': 35,
            'rsi_sell': 65,
            'bb_period': 20,
            'bb_std': 2.0
        }
    },
    'rsi_ema': {
        'name': 'RSI + EMA Cross',
        'indicators': ['RSI(14)', 'EMA(20)', 'EMA(50)'],
        'params': {
            'rsi_period': 14,
            'rsi_buy': 35,
            'rsi_sell': 65,
            'ema_fast': 20,
            'ema_slow': 50
        }
    },
    'rsi_macd': {
        'name': 'RSI + MACD',
        'indicators': ['RSI(14)', 'MACD(12,26,9)'],
        'params': {
            'rsi_period': 14,
            'rsi_buy': 35,
            'rsi_sell': 65,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
    },
    'full': {
        'name': 'Full Suite',
        'indicators': ['RSI(14)', 'Bollinger(20,2)', 'EMA(20)', 'EMA(50)', 'MACD(12,26,9)'],
        'params': {
            'rsi_period': 14,
            'rsi_buy': 35,
            'rsi_sell': 65,
            'bb_period': 20,
            'bb_std': 2.0,
            'ema_fast': 20,
            'ema_slow': 50,
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9
        }
    }
}

# Default configuration when optimization hasn't run
DEFAULT_CONFIG = {
    'best_timeframe': '30m',
    'strategy': 'grid',
    'indicator_combo': 'rsi_bb',
    'indicators': ['RSI(14)', 'Bollinger(20,2)'],
    'params': INDICATOR_COMBOS['rsi_bb']['params'],
    'profit_pct': 0.0,
    'win_rate': 0.0,
    'last_optimized': None
}

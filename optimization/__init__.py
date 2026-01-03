"""
Optimization Module for Adaptive Trading
=========================================

Auto-discovers optimal settings per asset through backtesting.
"""

from .asset_optimizer import AssetOptimizer, optimize_asset, optimize_all
from .indicator_combos import INDICATOR_COMBOS, TIMEFRAMES, STRATEGIES

__all__ = [
    'AssetOptimizer',
    'optimize_asset',
    'optimize_all',
    'INDICATOR_COMBOS',
    'TIMEFRAMES',
    'STRATEGIES'
]

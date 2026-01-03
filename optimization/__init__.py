"""
Optimization Module for Adaptive Trading
=========================================

Auto-discovers optimal settings per asset through backtesting.
"""

from .asset_optimizer import AssetOptimizer, optimize_all, optimize_asset
from .indicator_combos import INDICATOR_COMBOS, STRATEGIES, TIMEFRAMES

__all__ = [
    "INDICATOR_COMBOS",
    "STRATEGIES",
    "TIMEFRAMES",
    "AssetOptimizer",
    "optimize_all",
    "optimize_asset"
]

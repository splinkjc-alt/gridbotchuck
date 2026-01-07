"""
Quick Start Chuck on Best Pair
==============================
Scans the market, finds the best pair, and starts Chuck immediately.
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

import ccxt
from market_scanner.pair_backtester import PairBacktester


async def find_best_pair():
    """Find the best trading pair."""
    print("\n" + "=" * 60)
    print("SCANNING FOR BEST PAIR...")
    print("=" * 60 + "\n")

    backtester = PairBacktester(exchange_id="kraken")

    # Quick scan of top candidates
    top_pairs = [
        "VET/USD", "PEPE/USD", "CRV/USD", "ADA/USD", "LINK/USD",
        "UNI/USD", "NEAR/USD", "SOL/USD", "DOGE/USD", "ETH/USD"
    ]

    results = await backtester.run_full_scan(pairs=top_pairs, timeframes=["1h"])

    if not results:
        print("No results found!")
        return None

    # Print top 5
    print("\n" + "=" * 60)
    print("TOP 5 PAIRS:")
    print("=" * 60)
    print(f"{'Rank':<5} {'Pair':<12} {'Score':<7} {'Return%':<9} {'Vol%':<7}")
    print("-" * 50)

    for i, r in enumerate(results[:5], 1):
        print(f"{i:<5} {r.pair:<12} {r.grid_score:<7.0f} {r.total_return_pct:<9.1f} {r.volatility:<7.1f}")

    best = results[0]
    return best


def get_current_price(pair: str) -> float:
    """Get current price from Kraken."""
    try:
        exchange = ccxt.kraken()
        ticker = exchange.fetch_ticker(pair)
        return ticker['last']
    except Exception as e:
        print(f"Error getting price: {e}")
        return None


def create_config(pair_info, capital: float = 100) -> str:
    """Create config file for the pair."""
    pair = pair_info.pair
    price = get_current_price(pair)

    if not price:
        print(f"Could not get price for {pair}")
        return None

    # Calculate range
    range_pct = pair_info.best_range_pct / 100
    price_low = price * (1 - range_pct / 2)
    price_high = price * (1 + range_pct / 2)

    # Determine decimal places based on price
    if price < 0.001:
        decimals = 8
    elif price < 0.1:
        decimals = 6
    elif price < 10:
        decimals = 4
    else:
        decimals = 2

    config = {
        "exchange": {
            "name": "kraken",
            "pair": pair,
            "api_key_env": "EXCHANGE_API_KEY",
            "secret_key_env": "EXCHANGE_SECRET_KEY"
        },
        "strategy": {
            "type": "SIMPLE_GRID",
            "grid_spacing": "GEOMETRIC",
            "grid_count": pair_info.recommended_grids,
            "price_range": {
                "low": round(price_low, decimals),
                "high": round(price_high, decimals)
            }
        },
        "risk_management": {
            "max_position_pct": 90,
            "stop_loss_pct": 15,
            "take_profit_pct": 20
        },
        "paper_trading": False,
        "auto_selected": {
            "score": pair_info.grid_score,
            "volatility": pair_info.volatility,
            "backtest_return": pair_info.total_return_pct,
            "selected_at": datetime.now().isoformat()
        }
    }

    # Save config
    pair_safe = pair.replace('/', '_')
    config_path = f"config/config_{pair_safe}_auto.json"

    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"\nConfig saved to: {config_path}")
    print(f"\nCONFIGURATION:")
    print(f"  Pair: {pair}")
    print(f"  Current Price: ${price:.6f}")
    print(f"  Grid Range: ${price_low:.6f} - ${price_high:.6f} ({pair_info.best_range_pct:.1f}%)")
    print(f"  Grid Count: {pair_info.recommended_grids}")
    print(f"  Grid Score: {pair_info.grid_score}/100")

    return config_path


async def main():
    """Main entry point."""
    # Find best pair
    best = await find_best_pair()

    if not best:
        print("No suitable pair found!")
        return

    print(f"\n*** RECOMMENDED: {best.pair} ***")
    print(f"    Score: {best.grid_score}/100")
    print(f"    Volatility: {best.volatility:.1f}%")
    print(f"    Backtest Return: {best.total_return_pct:.1f}%")

    # Create config
    config_path = create_config(best, capital=100)

    if config_path:
        print("\n" + "=" * 60)
        print("READY TO START!")
        print("=" * 60)
        print(f"\nTo start Chuck on {best.pair}, run:")
        print(f"\n  python main.py --config {config_path}")
        print("\nOr run Smart Chuck for auto-switching:")
        print("\n  python run_smart_chuck.py")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

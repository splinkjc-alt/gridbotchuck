#!/usr/bin/env python3
"""
Scan and Generate Configs - GridBot Chuck
==========================================

Standalone script to scan for best trading pairs and generate
optimized grid configurations.

Usage:
    python scan_and_generate_configs.py --exchange kraken --pairs 10
    python scan_and_generate_configs.py --exchange coinbase --quote USDT --min-volume 500000
"""

import argparse
import asyncio
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.pair_scanner import run_smart_scan


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Scan trading pairs and generate optimized grid configs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scan_and_generate_configs.py --exchange kraken --pairs 10
    python scan_and_generate_configs.py --exchange coinbase --quote USD --min-price 1 --max-price 50
    python scan_and_generate_configs.py --exchange binance --quote USDT --min-volume 1000000
        """,
    )

    parser.add_argument(
        "--exchange",
        "-e",
        type=str,
        default="kraken",
        choices=["kraken", "coinbase", "kucoin", "binance"],
        help="Exchange to scan (default: kraken)",
    )

    parser.add_argument("--pairs", "-p", type=int, default=10, help="Number of pairs to return (default: 10)")

    parser.add_argument("--quote", "-q", type=str, default="USD", help="Quote currency to filter by (default: USD)")

    parser.add_argument("--min-price", type=float, default=0.01, help="Minimum price filter (default: 0.01)")

    parser.add_argument("--max-price", type=float, default=100.0, help="Maximum price filter (default: 100.0)")

    parser.add_argument(
        "--min-volume", type=float, default=100000, help="Minimum 24h volume in quote currency (default: 100000)"
    )

    parser.add_argument(
        "--balance", type=float, default=100.0, help="Initial balance per pair in configs (default: 100.0)"
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="config/scanned_pairs",
        help="Output directory for configs (default: config/scanned_pairs)",
    )

    parser.add_argument("--no-save", action="store_true", help="Don't save config files, just print results")

    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Load environment variables
    load_dotenv()

    if not args.json:
        print(f"\n{'=' * 60}")
        print("  GridBot Chuck - Smart Pair Scanner")
        print(f"{'=' * 60}")
        print(f"  Exchange: {args.exchange.upper()}")
        print(f"  Quote Currency: {args.quote}")
        print(f"  Pairs to Find: {args.pairs}")
        print(f"  Price Range: ${args.min_price} - ${args.max_price}")
        print(f"  Min Volume: ${args.min_volume:,.0f}")
        print(f"{'=' * 60}\n")

    # Create temporary config for exchange service
    temp_config = {
        "exchange": {
            "name": args.exchange,
            "trading_fee": 0.0026,
            "trading_mode": "paper_trading",
        },
        "pair": {
            "base_currency": "BTC",
            "quote_currency": args.quote,
        },
        "trading_settings": {
            "timeframe": "15m",
            "period": {"start_date": "2024-01-01T00:00:00Z", "end_date": None},
            "initial_balance": args.balance,
        },
        "grid_strategy": {
            "type": "hedged_grid",
            "spacing": "geometric",
            "num_grids": 6,
            "range": {"top": 0, "bottom": 0},
        },
        "risk_management": {
            "take_profit": {"enabled": False, "threshold": None},
            "stop_loss": {"enabled": False, "threshold": None},
        },
        "logging": {"level": "WARNING", "log_to_file": False},
    }

    # Save temp config
    temp_config_path = Path("config/temp_scan_config.json")
    temp_config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(temp_config_path, "w") as f:
        json.dump(temp_config, f, indent=2)

    try:
        # Initialize
        config_manager = ConfigManager(str(temp_config_path), ConfigValidator())
        exchange_service = ExchangeServiceFactory.create_exchange_service(
            config_manager,
            TradingMode.PAPER_TRADING,
        )

        # Run scan
        results = await run_smart_scan(
            exchange_service=exchange_service,
            quote_currency=args.quote,
            num_pairs=args.pairs,
            min_price=args.min_price,
            max_price=args.max_price,
            min_volume=args.min_volume,
            save_configs=not args.no_save,
            exchange_name=args.exchange,
            balance_per_pair=args.balance,
        )

        if args.json:
            # Output as JSON
            output = {
                "exchange": args.exchange,
                "quote_currency": args.quote,
                "results": [r.to_dict() for r in results],
            }
            print(json.dumps(output, indent=2))
        else:
            if results:
                print(f"\n✓ Found {len(results)} suitable pairs!")
                if not args.no_save:
                    print(f"✓ Configs saved to {args.output_dir}/")
            else:
                print("\n✗ No suitable pairs found. Try adjusting filters.")

        # Cleanup
        await exchange_service.close_connection()

    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e)}))
        else:
            print(f"\n✗ Error: {e}")
        sys.exit(1)

    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Run Auto-Portfolio - GridBot Chuck
===================================

Standalone script to run the AI-powered auto-portfolio manager.

Usage:
    python run_auto_portfolio.py --exchange kraken --capital 500 --positions 5
    python run_auto_portfolio.py --exchange coinbase --capital 1000 --positions 10 --min-score 70
"""

import argparse
import asyncio
import json
from pathlib import Path
import signal
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.auto_portfolio_manager import AutoPortfolioManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the AI-powered auto-portfolio manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_auto_portfolio.py --exchange kraken --capital 500 --positions 5
    python run_auto_portfolio.py --exchange coinbase --capital 1000 --min-score 70
    python run_auto_portfolio.py --exchange binance --capital 5000 --positions 10 --duration 60
        """,
    )

    parser.add_argument(
        "--exchange",
        "-e",
        type=str,
        default="kraken",
        choices=["kraken", "coinbase", "kucoin", "binance"],
        help="Exchange to use (default: kraken)",
    )

    parser.add_argument(
        "--capital",
        "-c",
        type=float,
        default=500.0,
        help="Total capital to deploy (default: 500)",
    )

    parser.add_argument(
        "--positions",
        "-p",
        type=int,
        default=5,
        help="Maximum simultaneous positions (default: 5)",
    )

    parser.add_argument(
        "--pairs", type=int, default=10, help="Number of pairs to monitor (default: 10)"
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=65.0,
        help="Minimum entry signal score 0-100 (default: 65)",
    )

    parser.add_argument(
        "--scan-interval",
        type=int,
        default=300,
        help="Seconds between scan cycles (default: 300)",
    )

    parser.add_argument(
        "--quote", "-q", type=str, default="USD", help="Quote currency (default: USD)"
    )

    parser.add_argument(
        "--duration",
        "-d",
        type=int,
        default=None,
        help="Duration in minutes (default: indefinite)",
    )

    parser.add_argument(
        "--save-state",
        type=str,
        default=None,
        help="File to save portfolio state on exit",
    )

    parser.add_argument(
        "--json", action="store_true", help="Output final state as JSON"
    )

    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_args()

    # Load environment variables
    load_dotenv()

    if not args.json:
        pass

    # Create temporary config
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
            "initial_balance": args.capital,
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
        "logging": {"level": "INFO", "log_to_file": True},
    }

    temp_config_path = Path("config/temp_portfolio_config.json")
    temp_config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(temp_config_path, "w") as f:
        json.dump(temp_config, f, indent=2)

    manager = None
    exchange_service = None

    try:
        # Initialize
        config_manager = ConfigManager(str(temp_config_path), ConfigValidator())
        exchange_service = ExchangeServiceFactory.create_exchange_service(
            config_manager,
            TradingMode.PAPER_TRADING,
        )

        # Create manager
        manager = AutoPortfolioManager(
            exchange_service=exchange_service,
            total_capital=args.capital,
            max_positions=args.positions,
            min_entry_score=args.min_score,
            scan_interval=args.scan_interval,
        )

        # Handle graceful shutdown
        def signal_handler(sig, frame):
            if not args.json:
                pass
            asyncio.create_task(manager.stop())

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Run
        if args.duration:
            try:
                await asyncio.wait_for(
                    manager.start(
                        quote_currency=args.quote,
                        num_pairs=args.pairs,
                    ),
                    timeout=args.duration * 60,
                )
            except TimeoutError:
                await manager.stop()
        else:
            await manager.start(
                quote_currency=args.quote,
                num_pairs=args.pairs,
            )

        # Get final state
        manager.get_state()

        if args.save_state:
            manager.save_state(args.save_state)

        if args.json:
            pass
        else:
            pass

    except Exception:
        if args.json:
            pass
        else:
            pass
        sys.exit(1)

    finally:
        if exchange_service:
            await exchange_service.close_connection()
        if temp_config_path.exists():
            temp_config_path.unlink()


if __name__ == "__main__":
    asyncio.run(main())

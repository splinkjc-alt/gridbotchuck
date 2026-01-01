"""
GridBot Chuck - Interactive Launcher
=====================================

Interactive command-line launcher for GridBot Chuck with menu options:
1. Kraken Exchange
2. Coinbase Exchange
3. KuCoin Exchange
4. Binance Exchange
5. Smart Scan - Find Best Pairs
6. Auto-Portfolio - AI Autonomous Trading
7. Custom Config
8. Exit
"""

import asyncio
from datetime import UTC, datetime
import json
import os
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from config.trading_mode import TradingMode
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.auto_portfolio_manager import run_auto_portfolio
from strategies.pair_scanner import run_smart_scan


# ANSI color codes
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")  # noqa: S605


def print_header():
    """Print the GridBot Chuck header."""


def print_menu():
    """Print the main menu."""


def get_user_input(prompt: str, default: str = "") -> str:
    """Get user input with a default value."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_int_input(prompt: str, default: int, min_val: int = 1, max_val: int = 100) -> int:
    """Get integer input with validation."""
    while True:
        try:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
            value = int(user_input)
            if min_val <= value <= max_val:
                return value
        except ValueError:
            pass


def get_float_input(prompt: str, default: float, min_val: float = 0, max_val: float = float("inf")) -> float:
    """Get float input with validation."""
    while True:
        try:
            user_input = input(f"{prompt} [{default}]: ").strip()
            if not user_input:
                return default
            value = float(user_input)
            if min_val <= value <= max_val:
                return value
        except ValueError:
            pass


def create_exchange_config(exchange_name: str) -> dict:
    """Create a basic config for the specified exchange."""
    return {
        "exchange": {
            "name": exchange_name.lower(),
            "trading_fee": 0.0026,
            "trading_mode": "paper_trading",
        },
        "pair": {
            "base_currency": "BTC",
            "quote_currency": "USD",
        },
        "trading_settings": {
            "timeframe": "15m",
            "period": {
                "start_date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "end_date": None,
            },
            "initial_balance": 100,
        },
        "grid_strategy": {
            "type": "hedged_grid",
            "spacing": "geometric",
            "num_grids": 6,
            "range": {
                "top": 0,
                "bottom": 0,
            },
        },
        "risk_management": {
            "take_profit": {"enabled": False, "threshold": None},
            "stop_loss": {"enabled": False, "threshold": None},
        },
        "logging": {
            "level": "INFO",
            "log_to_file": True,
        },
    }


async def run_smart_scan_menu():
    """Interactive menu for Smart Scan feature."""

    # Get exchange selection

    exchange_choice = get_int_input("Exchange", 1, 1, 4)
    exchange_map = {1: "kraken", 2: "coinbase", 3: "kucoin", 4: "binance"}
    exchange_name = exchange_map[exchange_choice]

    # Get scan parameters
    num_pairs = get_int_input("Number of pairs to scan", 10, 5, 50)
    quote_currency = get_user_input("Quote currency", "USD")
    min_price = get_float_input("Minimum price ($)", 0.01, 0, 1000000)
    max_price = get_float_input("Maximum price ($)", 100.0, min_price, 1000000)
    min_volume = get_float_input("Minimum 24h volume ($)", 100000, 0, 1000000000)


    # Load environment variables
    load_dotenv()

    # Create a temporary config for the exchange service
    config = create_exchange_config(exchange_name)
    config["pair"]["quote_currency"] = quote_currency

    # Save temporary config
    temp_config_path = Path("config/temp_scan_config.json")
    with open(temp_config_path, "w") as f:
        json.dump(config, f, indent=2)

    try:
        # Initialize exchange service
        config_manager = ConfigManager(str(temp_config_path), ConfigValidator())
        exchange_service = ExchangeServiceFactory.create_exchange_service(
            config_manager,
            TradingMode.PAPER_TRADING,
        )

        # Run the scan
        results = await run_smart_scan(
            exchange_service=exchange_service,
            quote_currency=quote_currency,
            num_pairs=num_pairs,
            min_price=min_price,
            max_price=max_price,
            min_volume=min_volume,
            save_configs=True,
            exchange_name=exchange_name,
            balance_per_pair=100.0,
        )

        if results:

            # Ask if user wants to trade one

            choice = get_int_input("Choice", 0, 0, 3)

            if choice == 1 and results:
                pass
                # TODO: Launch bot with this config
            elif choice == 2:
                for _i, _r in enumerate(results, 1):
                    pass
                get_int_input("Select pair", 1, 1, len(results)) - 1
                # TODO: Launch bot with this config
            elif choice == 3:
                # Run auto-portfolio with scanned pairs
                await run_auto_portfolio_menu(
                    exchange_name=exchange_name,
                    pairs=[r.pair for r in results],
                )
        else:
            pass

        # Cleanup
        await exchange_service.close_connection()

    except Exception:  # noqa: S110
        pass  # Silent failure for try-finally
    finally:
        # Remove temp config
        if temp_config_path.exists():
            temp_config_path.unlink()


async def run_auto_portfolio_menu(
    exchange_name: str | None = None,
    pairs: list[str] | None = None,
):
    """Interactive menu for Auto-Portfolio feature."""

    # Get exchange if not provided
    if not exchange_name:

        exchange_choice = get_int_input("Exchange", 1, 1, 4)
        exchange_map = {1: "kraken", 2: "coinbase", 3: "kucoin", 4: "binance"}
        exchange_name = exchange_map[exchange_choice]

    # Get portfolio parameters
    total_capital = get_float_input("Total capital to deploy ($)", 500.0, 50, 1000000)
    max_positions = get_int_input("Maximum positions", 5, 1, 20)
    num_pairs = get_int_input("Number of pairs to monitor", 10, 5, 30)
    min_entry_score = get_float_input("Minimum entry score (0-100)", 65.0, 0, 100)
    scan_interval = get_int_input("Scan interval (seconds)", 300, 60, 3600)


    confirm = input(f"\n{Colors.GREEN}Start Auto-Portfolio? (y/n): {Colors.END}").strip().lower()
    if confirm != "y":
        return


    # Load environment variables
    load_dotenv()

    # Create config
    config = create_exchange_config(exchange_name)
    config["trading_settings"]["initial_balance"] = total_capital

    # Save temporary config
    temp_config_path = Path("config/temp_portfolio_config.json")
    with open(temp_config_path, "w") as f:
        json.dump(config, f, indent=2)

    try:
        # Initialize exchange service
        config_manager = ConfigManager(str(temp_config_path), ConfigValidator())
        exchange_service = ExchangeServiceFactory.create_exchange_service(
            config_manager,
            TradingMode.PAPER_TRADING,
        )

        # Run auto-portfolio
        await run_auto_portfolio(
            exchange_service=exchange_service,
            total_capital=total_capital,
            max_positions=max_positions,
            min_entry_score=min_entry_score,
            scan_interval=scan_interval,
            quote_currency="USD",
            num_pairs=num_pairs,
        )

        # Print final results

        # Cleanup
        await exchange_service.close_connection()

    except KeyboardInterrupt:
        pass
    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()


async def run_exchange_bot(exchange_name: str):
    """Run the grid trading bot for a specific exchange."""

    # For now, offer to run a smart scan for this exchange
    choice = input(f"\nRun Smart Scan for {exchange_name}? (y/n): ").strip().lower()
    if choice == "y":
        await run_smart_scan_menu()


async def main_menu():
    """Main menu loop."""
    while True:
        clear_screen()
        print_header()
        print_menu()

        choice = input(f"{Colors.CYAN}Select an option [1-8]: {Colors.END}").strip()

        if choice == "1":
            await run_exchange_bot("kraken")
        elif choice == "2":
            await run_exchange_bot("coinbase")
        elif choice == "3":
            await run_exchange_bot("kucoin")
        elif choice == "4":
            await run_exchange_bot("binance")
        elif choice == "5":
            await run_smart_scan_menu()
        elif choice == "6":
            await run_auto_portfolio_menu()
        elif choice == "7":
            get_user_input("Enter config file path", "config/config.json")
        elif choice == "8":
            break
        else:
            pass

        if choice not in ["8"]:
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")


def main():
    """Entry point."""
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        pass
    except Exception:
        sys.exit(1)


if __name__ == "__main__":
    main()

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
from datetime import datetime
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
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Print the GridBot Chuck header."""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   ██████╗ ██████╗ ██╗██████╗ ██████╗  ██████╗ ████████╗         ║
║  ██╔════╝ ██╔══██╗██║██╔══██╗██╔══██╗██╔═══██╗╚══██╔══╝         ║
║  ██║  ███╗██████╔╝██║██║  ██║██████╔╝██║   ██║   ██║            ║
║  ██║   ██║██╔══██╗██║██║  ██║██╔══██╗██║   ██║   ██║            ║
║  ╚██████╔╝██║  ██║██║██████╔╝██████╔╝╚██████╔╝   ██║            ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝╚═════╝ ╚═════╝  ╚═════╝    ╚═╝            ║
║                                                                  ║
║              {Colors.GREEN}CHUCK - AI-Powered Grid Trading{Colors.CYAN}                   ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Colors.END}
""")


def print_menu():
    """Print the main menu."""
    print(f"""
{Colors.YELLOW}═══════════════════════════════════════════════════════════════════
                         MAIN MENU
═══════════════════════════════════════════════════════════════════{Colors.END}

  {Colors.CYAN}[1]{Colors.END} 🌊 Kraken Exchange
  {Colors.CYAN}[2]{Colors.END} 🪙 Coinbase Exchange
  {Colors.CYAN}[3]{Colors.END} 🐲 KuCoin Exchange
  {Colors.CYAN}[4]{Colors.END} 🔶 Binance Exchange

  {Colors.GREEN}[5]{Colors.END} ⭐ Smart Scan - Find Best Pairs {Colors.GREEN}(NEW!){Colors.END}
  {Colors.GREEN}[6]{Colors.END} 🤖 Auto-Portfolio - AI Autonomous Trading {Colors.GREEN}(NEW!){Colors.END}

  {Colors.CYAN}[7]{Colors.END} ⚙️  Custom Config
  {Colors.RED}[8]{Colors.END} ❌ Exit

{Colors.YELLOW}═══════════════════════════════════════════════════════════════════{Colors.END}
""")


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
            print(f"{Colors.RED}Please enter a value between {min_val} and {max_val}{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.END}")


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
            print(f"{Colors.RED}Please enter a value between {min_val} and {max_val}{Colors.END}")
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.END}")


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
                "start_date": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
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
    print(f"""
{Colors.GREEN}═══════════════════════════════════════════════════════════════════
                    ⭐ SMART PAIR SCANNER
═══════════════════════════════════════════════════════════════════{Colors.END}

This feature scans available trading pairs and ranks them by:
  • Range-bound behavior (50% weight)
  • Volatility level (30% weight)
  • Trading volume (20% weight)

""")

    # Get exchange selection
    print("Select exchange to scan:")
    print(f"  {Colors.CYAN}[1]{Colors.END} Kraken")
    print(f"  {Colors.CYAN}[2]{Colors.END} Coinbase")
    print(f"  {Colors.CYAN}[3]{Colors.END} KuCoin")
    print(f"  {Colors.CYAN}[4]{Colors.END} Binance")
    print()

    exchange_choice = get_int_input("Exchange", 1, 1, 4)
    exchange_map = {1: "kraken", 2: "coinbase", 3: "kucoin", 4: "binance"}
    exchange_name = exchange_map[exchange_choice]

    # Get scan parameters
    print()
    num_pairs = get_int_input("Number of pairs to scan", 10, 5, 50)
    quote_currency = get_user_input("Quote currency", "USD")
    min_price = get_float_input("Minimum price ($)", 0.01, 0, 1000000)
    max_price = get_float_input("Maximum price ($)", 100.0, min_price, 1000000)
    min_volume = get_float_input("Minimum 24h volume ($)", 100000, 0, 1000000000)

    print(f"\n{Colors.YELLOW}Starting scan of {exchange_name.upper()} {quote_currency} pairs...{Colors.END}\n")

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
            print(f"\n{Colors.GREEN}✓ Scan complete! Found {len(results)} suitable pairs.{Colors.END}")
            print(f"{Colors.GREEN}✓ Configs saved to config/scanned_pairs/{Colors.END}")

            # Ask if user wants to trade one
            print(f"\n{Colors.YELLOW}What would you like to do?{Colors.END}")
            print(f"  {Colors.CYAN}[1]{Colors.END} Trade top ranked pair")
            print(f"  {Colors.CYAN}[2]{Colors.END} Select a pair to trade")
            print(f"  {Colors.CYAN}[3]{Colors.END} Run Auto-Portfolio with these pairs")
            print(f"  {Colors.CYAN}[0]{Colors.END} Return to main menu")

            choice = get_int_input("Choice", 0, 0, 3)

            if choice == 1 and results:
                print(f"\n{Colors.GREEN}Selected: {results[0].pair}{Colors.END}")
                print("Starting grid trading bot...")
                # TODO: Launch bot with this config
            elif choice == 2:
                print("\nAvailable pairs:")
                for i, r in enumerate(results, 1):
                    print(f"  [{i}] {r.pair} - Score: {r.total_score:.1f}")
                pair_idx = get_int_input("Select pair", 1, 1, len(results)) - 1
                print(f"\n{Colors.GREEN}Selected: {results[pair_idx].pair}{Colors.END}")
                # TODO: Launch bot with this config
            elif choice == 3:
                # Run auto-portfolio with scanned pairs
                await run_auto_portfolio_menu(
                    exchange_name=exchange_name,
                    pairs=[r.pair for r in results],
                )
        else:
            print(f"\n{Colors.RED}No suitable pairs found. Try adjusting filters.{Colors.END}")

        # Cleanup
        await exchange_service.close_connection()

    except Exception as e:
        print(f"\n{Colors.RED}Error during scan: {e}{Colors.END}")
    finally:
        # Remove temp config
        if temp_config_path.exists():
            temp_config_path.unlink()


async def run_auto_portfolio_menu(
    exchange_name: str | None = None,
    pairs: list[str] | None = None,
):
    """Interactive menu for Auto-Portfolio feature."""
    print(f"""
{Colors.GREEN}═══════════════════════════════════════════════════════════════════
                🤖 AUTO-PORTFOLIO MANAGER
═══════════════════════════════════════════════════════════════════{Colors.END}

This feature autonomously manages a portfolio of grid trading positions:
  • Monitors multiple pairs for optimal entry conditions
  • Uses RSI, price position, and volume analysis
  • Automatically enters when conditions are favorable
  • Allocates capital across best opportunities

""")

    # Get exchange if not provided
    if not exchange_name:
        print("Select exchange:")
        print(f"  {Colors.CYAN}[1]{Colors.END} Kraken")
        print(f"  {Colors.CYAN}[2]{Colors.END} Coinbase")
        print(f"  {Colors.CYAN}[3]{Colors.END} KuCoin")
        print(f"  {Colors.CYAN}[4]{Colors.END} Binance")
        print()

        exchange_choice = get_int_input("Exchange", 1, 1, 4)
        exchange_map = {1: "kraken", 2: "coinbase", 3: "kucoin", 4: "binance"}
        exchange_name = exchange_map[exchange_choice]

    # Get portfolio parameters
    print()
    total_capital = get_float_input("Total capital to deploy ($)", 500.0, 50, 1000000)
    max_positions = get_int_input("Maximum positions", 5, 1, 20)
    num_pairs = get_int_input("Number of pairs to monitor", 10, 5, 30)
    min_entry_score = get_float_input("Minimum entry score (0-100)", 65.0, 0, 100)
    scan_interval = get_int_input("Scan interval (seconds)", 300, 60, 3600)

    print(f"\n{Colors.YELLOW}Configuration:{Colors.END}")
    print(f"  Exchange: {exchange_name.upper()}")
    print(f"  Capital: ${total_capital:.2f}")
    print(f"  Max Positions: {max_positions}")
    print(f"  Capital per Position: ${total_capital / max_positions:.2f}")
    print(f"  Pairs to Monitor: {num_pairs}")
    print(f"  Min Entry Score: {min_entry_score}")
    print(f"  Scan Interval: {scan_interval}s")

    confirm = input(f"\n{Colors.GREEN}Start Auto-Portfolio? (y/n): {Colors.END}").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    print(f"\n{Colors.YELLOW}Starting Auto-Portfolio Manager...{Colors.END}")
    print(f"{Colors.YELLOW}Press Ctrl+C to stop{Colors.END}\n")

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
        final_state = await run_auto_portfolio(
            exchange_service=exchange_service,
            total_capital=total_capital,
            max_positions=max_positions,
            min_entry_score=min_entry_score,
            scan_interval=scan_interval,
            quote_currency="USD",
            num_pairs=num_pairs,
        )

        # Print final results
        print(f"\n{Colors.GREEN}═══════════════════════════════════════════════════════════════════")
        print("                    FINAL PORTFOLIO STATUS")
        print(f"═══════════════════════════════════════════════════════════════════{Colors.END}")
        print(f"  Total Capital: ${final_state.total_capital:.2f}")
        print(f"  Deployed: ${final_state.deployed_capital:.2f}")
        print(f"  Positions: {final_state.active_positions}")
        print(f"  Realized PnL: ${final_state.total_realized_pnl:+.2f}")
        print(f"  Unrealized PnL: ${final_state.total_unrealized_pnl:+.2f}")
        print(f"  Scan Cycles: {final_state.scan_cycle}")

        # Cleanup
        await exchange_service.close_connection()

    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Stopping Auto-Portfolio...{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
    finally:
        if temp_config_path.exists():
            temp_config_path.unlink()


async def run_exchange_bot(exchange_name: str):
    """Run the grid trading bot for a specific exchange."""
    print(f"\n{Colors.CYAN}Starting GridBot for {exchange_name.upper()}...{Colors.END}")
    print(f"{Colors.YELLOW}Note: For full trading, use 'python main.py --config config/config.json'{Colors.END}")

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
            config_path = get_user_input("Enter config file path", "config/config.json")
            print(f"\n{Colors.CYAN}To run with custom config:{Colors.END}")
            print(f"  python main.py --config {config_path}")
        elif choice == "8":
            print(f"\n{Colors.GREEN}Thanks for using GridBot Chuck! Happy trading! 🚀{Colors.END}\n")
            break
        else:
            print(f"{Colors.RED}Invalid option. Please try again.{Colors.END}")

        if choice not in ["8"]:
            input(f"\n{Colors.YELLOW}Press Enter to continue...{Colors.END}")


def main():
    """Entry point."""
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted. Goodbye!{Colors.END}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()

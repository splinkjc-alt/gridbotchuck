"""
Smart Chuck - Auto-Pair Selection Grid Bot
==========================================
Runs the grid bot on the best performing pair based on backtest analysis.
Periodically rescans and can switch pairs if a better opportunity emerges.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

import requests
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from market_scanner.pair_backtester import PairBacktester  # noqa: E402
from shared_pair_tracker import get_tracker  # noqa: E402


def send_telegram(message: str):
    """Send notification via Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token:
        return

    # If no chat_id, try to get it from recent messages
    if not chat_id:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=5)
            data = resp.json()
            if data.get("result"):
                chat_id = str(data["result"][-1]["message"]["chat"]["id"])
        except Exception:
            return

    if not chat_id:
        return

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }, timeout=10)
    except Exception as e:
        logging.warning(f"Telegram notification failed: {e}")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/smart_chuck.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmartChuck")


class SmartChuck:
    """
    Smart grid bot launcher that automatically selects the best trading pair.
    """

    # Pairs to consider (Kraken supported)
    CANDIDATE_PAIRS = [
        "VET/USD", "PEPE/USD", "CRV/USD", "ADA/USD", "LINK/USD",
        "UNI/USD", "NEAR/USD", "ICP/USD", "SOL/USD", "DOGE/USD",
        "XRP/USD", "DOT/USD", "ALGO/USD", "XLM/USD", "HBAR/USD",
        "ETH/USD", "BTC/USD"
    ]

    def __init__(self,
                 min_score: float = 65,
                 rescan_hours: float = 4,
                 capital_usd: float = 100,
                 scan_offset_seconds: int = 0,
                 check_interval_seconds: int = 60):
        """
        Initialize Smart Chuck.

        Args:
            min_score: Minimum grid score to consider a pair (0-100)
            rescan_hours: How often to rescan for better pairs
            capital_usd: Trading capital in USD
            scan_offset_seconds: Offset to stagger scans with other bots
            check_interval_seconds: How often to check bot health
        """
        self.min_score = min_score
        self.rescan_hours = rescan_hours
        self.capital_usd = capital_usd
        self.scan_offset_seconds = scan_offset_seconds
        self.check_interval_seconds = check_interval_seconds

        self.current_pair = None
        self.current_score = 0
        self.bot_process = None
        self.last_scan = None

        self.backtester = PairBacktester(exchange_id="kraken")
        self.results_file = Path("data/backtest_results.json")

        # Shared pair tracker to avoid conflicts with other bots
        self.pair_tracker = get_tracker()

    async def scan_pairs(self) -> dict:
        """
        Scan all candidate pairs and return the best one.
        Avoids pairs that other bots are currently trading.

        Returns:
            Dict with best pair info or None
        """
        logger.info("=" * 60)
        logger.info("CHUCK SCANNING FOR BEST TRADING PAIR")
        logger.info("=" * 60)

        # Get pairs to avoid (other bots' current pairs)
        avoid_pairs = self.pair_tracker.get_other_pairs("chuck")
        if avoid_pairs:
            logger.info(f"Avoiding pairs traded by other bots: {avoid_pairs}")

        results = await self.backtester.run_full_scan(
            pairs=self.CANDIDATE_PAIRS,
            timeframes=["1h"]
        )

        if not results:
            logger.warning("No pairs found in scan")
            return None

        # Save results
        self.backtester.save_results(str(self.results_file))

        # Get best pair meeting minimum score AND not traded by others
        for r in results:
            # Skip pairs being traded by other bots
            if r.pair in avoid_pairs:
                logger.info(f"Skipping {r.pair} - being traded by another bot")
                continue

            if r.grid_score >= self.min_score:
                best = {
                    'pair': r.pair,
                    'score': r.grid_score,
                    'return_pct': r.total_return_pct,
                    'volatility': r.volatility,
                    'range_pct': r.best_range_pct,
                    'grids': r.recommended_grids,
                    'indicators': r.indicators
                }
                logger.info(f"\nBEST PAIR FOR CHUCK: {best['pair']} (Score: {best['score']:.0f})")
                logger.info(f"  Volatility: {best['volatility']:.1f}%")
                logger.info(f"  Backtest Return: {best['return_pct']:.1f}%")
                logger.info(f"  Optimal Range: {best['range_pct']:.1f}%")
                return best

        logger.warning(f"No pairs met minimum score of {self.min_score}")
        return None

    def generate_config(self, pair_info: dict) -> dict:
        """Generate grid bot config for the selected pair."""
        pair = pair_info['pair']
        base, quote = pair.split('/')

        # Get current price
        try:
            import ccxt
            exchange = ccxt.kraken()
            ticker = exchange.fetch_ticker(pair)
            current_price = ticker['last']
        except Exception:
            current_price = 1.0

        # Calculate grid range
        range_pct = pair_info['range_pct'] / 100
        price_low = current_price * (1 - range_pct / 2)
        price_high = current_price * (1 + range_pct / 2)

        # Proper config format for main.py
        config = {
            "exchange": {
                "name": "kraken",
                "trading_fee": 0.0026,
                "trading_mode": "live"
            },
            "pair": {
                "base_currency": base,
                "quote_currency": quote
            },
            "trading_settings": {
                "timeframe": "1h",
                "period": {
                    "start_date": "2026-01-01T00:00:00Z",
                    "end_date": "2026-12-31T23:59:59Z"
                },
                "initial_balance": self.capital_usd
            },
            "grid_strategy": {
                "type": "simple_grid",
                "spacing": "geometric",
                "num_grids": pair_info['grids'],
                "range": {
                    "top": round(price_high, 8),
                    "bottom": round(price_low, 8)
                }
            },
            "risk_management": {
                "take_profit": {"enabled": False, "threshold": price_high * 1.5},
                "stop_loss": {"enabled": False, "threshold": price_low * 0.5}
            },
            "logging": {
                "log_level": "INFO",
                "log_to_file": True
            },
            "api": {
                "enabled": True,
                "port": 8080
            }
        }

        return config

    def save_config(self, config: dict) -> str:
        """Save config to file and return path."""
        base = config['pair']['base_currency']
        quote = config['pair']['quote_currency']
        pair_safe = f"{base}_{quote}"
        config_path = f"config/config_smart_{pair_safe}.json"

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Config saved to {config_path}")
        return config_path

    async def start_bot(self, config_path: str):
        """Start the grid bot with the given config."""
        if self.bot_process:
            logger.info("Stopping existing bot...")
            self.bot_process.terminate()
            await asyncio.sleep(2)

        logger.info(f"Starting grid bot with config: {config_path}")

        # Start the bot
        self.bot_process = subprocess.Popen(
            [sys.executable, "main.py", "--config", config_path],
            cwd=str(Path(__file__).parent)
        )

        logger.info(f"Bot started with PID: {self.bot_process.pid}")

    async def should_switch_pair(self, new_best: dict) -> bool:
        """
        Determine if we should switch to a new pair.

        Only switch if:
        - New pair scores significantly higher (>10 points)
        - Current pair has dropped significantly
        """
        if not self.current_pair:
            return True

        if new_best['pair'] == self.current_pair:
            return False

        score_diff = new_best['score'] - self.current_score

        if score_diff > 10:
            logger.info(f"New pair {new_best['pair']} scores {score_diff:.0f} points higher")
            return True

        if self.current_score < self.min_score:
            logger.info(f"Current pair {self.current_pair} dropped below minimum score")
            return True

        return False

    async def run(self):
        """Main loop - scan, select, and manage the bot."""
        logger.info("=" * 60)
        logger.info("SMART CHUCK - AUTO-PAIR GRID BOT")
        logger.info("=" * 60)
        logger.info(f"Capital: ${self.capital_usd}")
        logger.info(f"Min Score: {self.min_score}")
        logger.info(f"Rescan Interval: {self.rescan_hours} hours")
        logger.info(f"Scan Offset: {self.scan_offset_seconds}s (stagger with other bots)")
        logger.info(f"Health Check: every {self.check_interval_seconds}s")
        logger.info("=" * 60)

        # Apply initial offset to stagger startup with other bots
        if self.scan_offset_seconds > 0:
            logger.info(f"Waiting {self.scan_offset_seconds}s offset before first scan...")
            await asyncio.sleep(self.scan_offset_seconds)

        while True:
            try:
                # Check if it's time to scan
                should_scan = (
                    self.last_scan is None or
                    datetime.now() - self.last_scan > timedelta(hours=self.rescan_hours)
                )

                if should_scan:
                    # Scan for best pair
                    best = await self.scan_pairs()
                    self.last_scan = datetime.now()

                    if best and await self.should_switch_pair(best):
                        # Generate and save config
                        config = self.generate_config(best)
                        config_path = self.save_config(config)

                        # Update tracking
                        self.current_pair = best['pair']
                        self.current_score = best['score']

                        # Claim this pair so other bots avoid it
                        self.pair_tracker.claim_pair("chuck", self.current_pair)

                        # Start bot
                        await self.start_bot(config_path)

                        logger.info(f"\n*** CHUCK NOW TRADING: {self.current_pair} ***\n")

                        # Send notification
                        send_telegram(
                            f"🤖 *CHUCK* switched to *{self.current_pair}*\n"
                            f"Score: {best['score']}/100\n"
                            f"Volatility: {best['volatility']:.1f}%\n"
                            f"Backtest Return: {best['return_pct']:.1f}%"
                        )

                # Check bot health
                if self.bot_process:
                    if self.bot_process.poll() is not None:
                        logger.warning("Bot process died, will restart on next scan")
                        self.bot_process = None

                # Wait before next check (staggered interval)
                await asyncio.sleep(self.check_interval_seconds)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                if self.bot_process:
                    self.bot_process.terminate()
                break

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(self.check_interval_seconds)


async def main():
    """Entry point."""
    from dotenv import load_dotenv
    load_dotenv()

    # Chuck scans first (no offset), then other bots follow
    # Stagger check intervals to avoid simultaneous API calls
    chuck = SmartChuck(
        min_score=60,              # Minimum score to consider a pair
        rescan_hours=2,            # Rescan every 2 hours
        capital_usd=100,           # Trading capital
        scan_offset_seconds=0,     # Chuck goes first
        check_interval_seconds=90  # Check every 90 seconds
    )

    await chuck.run()


if __name__ == "__main__":
    asyncio.run(main())

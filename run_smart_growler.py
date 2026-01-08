"""
Smart Growler - Auto-Pair Selection Grid Bot #2
================================================
Second grid bot that scans and picks the best pair.
Avoids the pair Chuck is already trading.
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

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from market_scanner.pair_backtester import PairBacktester
from shared_pair_tracker import get_tracker


def send_telegram(message: str):
    """Send notification via Telegram."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

    if not token:
        return

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
        logging.FileHandler("logs/smart_growler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("SmartGrowler")


class SmartGrowler:
    """
    Second smart grid bot that picks the best pair Chuck isn't trading.
    """

    CANDIDATE_PAIRS = [
        "VET/USD", "PEPE/USD", "CRV/USD", "ADA/USD", "LINK/USD",
        "UNI/USD", "NEAR/USD", "ICP/USD", "SOL/USD", "DOGE/USD",
        "XRP/USD", "DOT/USD", "ALGO/USD", "XLM/USD", "HBAR/USD",
        "ETH/USD", "BTC/USD"
    ]

    def __init__(self,
                 min_score: float = 60,
                 rescan_hours: float = 2,
                 capital_usd: float = 100,
                 avoid_pairs: list = None,
                 scan_offset_seconds: int = 0,
                 check_interval_seconds: int = 60):
        """
        Initialize Smart Growler.

        Args:
            min_score: Minimum grid score to consider a pair
            rescan_hours: How often to rescan for better pairs
            capital_usd: Trading capital in USD
            avoid_pairs: Pairs to avoid (e.g., Chuck's pair)
            scan_offset_seconds: Offset to stagger scans with other bots
            check_interval_seconds: How often to check bot health
        """
        self.min_score = min_score
        self.rescan_hours = rescan_hours
        self.capital_usd = capital_usd
        self.avoid_pairs = avoid_pairs or []
        self.scan_offset_seconds = scan_offset_seconds
        self.check_interval_seconds = check_interval_seconds

        self.current_pair = None
        self.current_score = 0
        self.bot_process = None
        self.last_scan = None

        self.backtester = PairBacktester(exchange_id="kraken")
        self.results_file = Path("data/backtest_results_growler.json")

        # Shared pair tracker to coordinate with other bots
        self.pair_tracker = get_tracker()

    def get_pairs_to_avoid(self) -> list:
        """Get pairs being traded by other bots."""
        return self.pair_tracker.get_other_pairs("growler")

    async def scan_pairs(self) -> dict:
        """Scan pairs, avoiding pairs being traded by other bots."""
        logger.info("=" * 60)
        logger.info("GROWLER SCANNING FOR BEST PAIR")
        logger.info("=" * 60)

        # Get pairs to avoid (from shared tracker)
        avoid_pairs = self.get_pairs_to_avoid()
        if avoid_pairs:
            logger.info(f"Avoiding pairs traded by other bots: {avoid_pairs}")

        results = await self.backtester.run_full_scan(
            pairs=self.CANDIDATE_PAIRS,
            timeframes=["1h"]
        )

        if not results:
            return None

        self.backtester.save_results(str(self.results_file))

        # Get best pair not being traded by other bots
        for r in results:
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
                logger.info(f"\nBEST PAIR FOR GROWLER: {best['pair']} (Score: {best['score']:.0f})")
                logger.info(f"  Volatility: {best['volatility']:.1f}%")
                logger.info(f"  Backtest Return: {best['return_pct']:.1f}%")
                return best

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
                "port": 8081
            }
        }

        return config

    def save_config(self, config: dict) -> str:
        """Save config to file."""
        pair = config['pair']['base_currency'] + '_' + config['pair']['quote_currency']
        config_path = f"config/config_smart_growler_{pair}.json"

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"Config saved to {config_path}")
        return config_path

    async def start_bot(self, config_path: str):
        """Start the grid bot."""
        if self.bot_process:
            logger.info("Stopping existing Growler bot...")
            self.bot_process.terminate()
            await asyncio.sleep(2)

        logger.info(f"Starting Growler with config: {config_path}")

        self.bot_process = subprocess.Popen(
            [sys.executable, "main.py", "--config", config_path],
            cwd=str(Path(__file__).parent)
        )

        logger.info(f"Growler started with PID: {self.bot_process.pid}")

    async def should_switch_pair(self, new_best: dict) -> bool:
        """Check if we should switch pairs."""
        if not self.current_pair:
            return True

        if new_best['pair'] == self.current_pair:
            return False

        score_diff = new_best['score'] - self.current_score

        if score_diff > 10:
            logger.info(f"New pair {new_best['pair']} scores {score_diff:.0f} points higher")
            return True

        return False

    async def run(self):
        """Main loop."""
        logger.info("=" * 60)
        logger.info("SMART GROWLER - AUTO-PAIR GRID BOT #2")
        logger.info("=" * 60)
        logger.info(f"Capital: ${self.capital_usd}")
        logger.info(f"Rescan Interval: {self.rescan_hours} hours")
        logger.info(f"Scan Offset: {self.scan_offset_seconds}s (stagger with Chuck)")
        logger.info(f"Health Check: every {self.check_interval_seconds}s")
        logger.info("=" * 60)

        # Apply initial offset to stagger startup with Chuck
        if self.scan_offset_seconds > 0:
            logger.info(f"Waiting {self.scan_offset_seconds}s offset before first scan...")
            await asyncio.sleep(self.scan_offset_seconds)

        while True:
            try:
                should_scan = (
                    self.last_scan is None or
                    datetime.now() - self.last_scan > timedelta(hours=self.rescan_hours)
                )

                if should_scan:
                    best = await self.scan_pairs()
                    self.last_scan = datetime.now()

                    if best and await self.should_switch_pair(best):
                        config = self.generate_config(best)
                        config_path = self.save_config(config)

                        self.current_pair = best['pair']
                        self.current_score = best['score']

                        # Claim this pair so other bots avoid it
                        self.pair_tracker.claim_pair("growler", self.current_pair)

                        await self.start_bot(config_path)

                        logger.info(f"\n*** GROWLER NOW TRADING: {self.current_pair} ***\n")

                        # Send notification
                        send_telegram(
                            f"🐕 *GROWLER* switched to *{self.current_pair}*\n"
                            f"Score: {best['score']}/100\n"
                            f"Volatility: {best['volatility']:.1f}%\n"
                            f"Backtest Return: {best['return_pct']:.1f}%"
                        )

                if self.bot_process and self.bot_process.poll() is not None:
                    logger.warning("Growler process died, will restart on next scan")
                    self.bot_process = None

                await asyncio.sleep(self.check_interval_seconds)

            except KeyboardInterrupt:
                logger.info("Shutting down Growler...")
                if self.bot_process:
                    self.bot_process.terminate()
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                await asyncio.sleep(self.check_interval_seconds)


async def main():
    from dotenv import load_dotenv
    load_dotenv()

    # Growler scans 45 seconds after Chuck to avoid API conflicts
    # Uses different check interval to prevent overlap
    growler = SmartGrowler(
        min_score=60,
        rescan_hours=2,
        capital_usd=100,
        scan_offset_seconds=45,    # Wait 45s after startup (Chuck goes first)
        check_interval_seconds=75  # Different from Chuck's 90s to avoid overlap
    )

    await growler.run()


if __name__ == "__main__":
    asyncio.run(main())

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

from market_scanner.pair_backtester import PairBacktester


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
                 capital_usd: float = 100):
        """
        Initialize Smart Chuck.

        Args:
            min_score: Minimum grid score to consider a pair (0-100)
            rescan_hours: How often to rescan for better pairs
            capital_usd: Trading capital in USD
        """
        self.min_score = min_score
        self.rescan_hours = rescan_hours
        self.capital_usd = capital_usd

        self.current_pair = None
        self.current_score = 0
        self.bot_process = None
        self.last_scan = None

        self.backtester = PairBacktester(exchange_id="kraken")
        self.results_file = Path("data/backtest_results.json")

    async def scan_pairs(self) -> dict:
        """
        Scan all candidate pairs and return the best one.

        Returns:
            Dict with best pair info or None
        """
        logger.info("=" * 60)
        logger.info("SCANNING FOR BEST TRADING PAIR")
        logger.info("=" * 60)

        results = await self.backtester.run_full_scan(
            pairs=self.CANDIDATE_PAIRS,
            timeframes=["1h"]
        )

        if not results:
            logger.warning("No pairs found in scan")
            return None

        # Save results
        self.backtester.save_results(str(self.results_file))

        # Get best pair meeting minimum score
        for r in results:
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
                logger.info(f"\nBEST PAIR: {best['pair']} (Score: {best['score']:.0f})")
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

        # Get current price (approximate from backtest data)
        # In production, fetch live price
        try:
            import ccxt
            exchange = ccxt.kraken()
            ticker = exchange.fetch_ticker(pair)
            current_price = ticker['last']
        except Exception:
            current_price = 1.0  # Fallback

        # Calculate grid range
        range_pct = pair_info['range_pct'] / 100
        price_low = current_price * (1 - range_pct / 2)
        price_high = current_price * (1 + range_pct / 2)

        config = {
            "exchange": "kraken",
            "pair": pair,
            "strategy": "SIMPLE_GRID",
            "grid_spacing": "GEOMETRIC",
            "grid_count": pair_info['grids'],
            "price_range": {
                "low": round(price_low, 6),
                "high": round(price_high, 6)
            },
            "order_size_usd": self.capital_usd / pair_info['grids'],
            "live_mode": True,
            "auto_selected": True,
            "selection_score": pair_info['score'],
            "selection_time": datetime.now().isoformat()
        }

        return config

    def save_config(self, config: dict) -> str:
        """Save config to file and return path."""
        pair_safe = config['pair'].replace('/', '_')
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
            cwd=str(Path(__file__).parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
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
        logger.info("=" * 60)

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

                        # Start bot
                        await self.start_bot(config_path)

                        logger.info(f"\n*** NOW TRADING: {self.current_pair} ***\n")

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

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                if self.bot_process:
                    self.bot_process.terminate()
                break

            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)


async def main():
    """Entry point."""
    from dotenv import load_dotenv
    load_dotenv()

    chuck = SmartChuck(
        min_score=60,       # Minimum score to consider a pair
        rescan_hours=2,     # Rescan every 2 hours
        capital_usd=100     # Trading capital
    )

    await chuck.run()


if __name__ == "__main__":
    asyncio.run(main())

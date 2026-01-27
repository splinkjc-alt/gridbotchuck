"""
CrossKiller - EMA 9/20 Crossover Strategy Runner

Uses Coinbase exchange with safety protections:
- Stop-loss: Auto-sell if position drops 7%
- Take-profit: Auto-sell if position gains 5%
- Time-stop: Auto-sell after 6 hours max hold
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv

load_dotenv()

from config.config_manager import ConfigManager
from config.config_validator import ConfigValidator
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.ema_crossover_strategy import EMACrossoverStrategy


async def main():
    # Setup logging with absolute path
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "crosskiller_error.log"),
        ],
    )
    logger = logging.getLogger("EMABot")

    # Load CrossKiller config (Coinbase)
    config_path = Path(__file__).parent / "config" / "config_crosskiller.json"
    config_manager = ConfigManager(str(config_path), ConfigValidator())

    logger.info("=" * 60)
    logger.info("EMA 9/20 CROSSOVER BOT STARTED")
    logger.info("=" * 60)
    logger.info("Strategy: Buy when EMA 9 > EMA 20 with widening gap")

    # Get position sizing from config
    position_config = config_manager.config.get("position_sizing", {})
    max_positions = position_config.get("max_positions", 3)
    buy_percent = position_config.get("position_size_percent", 20.0)
    min_reserve = position_config.get("min_reserve_percent", 10.0)

    logger.info(f"Position Size: {buy_percent}% | Reserve: {min_reserve}%")
    logger.info(f"Max Positions: {max_positions}")

    # Safety parameters
    stop_loss = 7.0  # Exit if down 7%
    take_profit = 5.0  # Exit if up 5%
    max_hold = 6.0  # Exit after 6 hours max

    logger.info("=" * 60)
    logger.info("SAFETY FEATURES ENABLED:")
    logger.info(f"  Stop-Loss: -{stop_loss}%")
    logger.info(f"  Take-Profit: +{take_profit}%")
    logger.info(f"  Max Hold Time: {max_hold} hours")
    logger.info("=" * 60)

    # Create exchange service
    trading_mode = config_manager.get_trading_mode()
    exchange_service = ExchangeServiceFactory.create_exchange_service(
        config_manager, trading_mode
    )

    try:
        # Fetch and display starting balance
        try:
            balance = await exchange_service.get_balance()
            usd = balance.get("total", {}).get("USD", 0)
            logger.info("Current balances:")
            logger.info(f"  USD: ${usd:.2f}")

            # Show active positions
            active = 0
            for currency, amount in balance.get("total", {}).items():
                if amount > 0 and currency not in ["USD", "USDT", "USDC"]:
                    active += 1
            logger.info(f"Active positions: {active}")
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")

        # Create strategy with safety features
        strategy = EMACrossoverStrategy(
            config_manager=config_manager,
            exchange_service=exchange_service,
            ema_fast=9,
            ema_slow=20,
            max_positions=max_positions,
            position_size_percent=buy_percent,
            min_reserve_percent=min_reserve,
            # Safety parameters
            stop_loss_pct=stop_loss,
            take_profit_pct=take_profit,
            max_hold_hours=max_hold,
        )

        # Run strategy
        await strategy.start()

    except KeyboardInterrupt:
        logger.info("Shutting down CrossKiller...")
    finally:
        if hasattr(exchange_service, "close"):
            await exchange_service.close()


if __name__ == "__main__":
    asyncio.run(main())

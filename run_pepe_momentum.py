"""
PEPE Momentum Bot - Optimized Settings
=======================================

Best combo from backtest:
- Timeframe: 30m
- Indicators: RSI + EMA
- Strategy: Momentum
- Result: +36.41% over 30 days (54% win rate, 173 trades)
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
from strategies.momentum_strategy import MomentumStrategy


async def main():
    # Setup logging
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "pepe_momentum.log"),
        ],
    )
    logger = logging.getLogger("PEPE-Momentum")

    # Load config
    config_path = Path(__file__).parent / "config" / "config_pepe_momentum.json"
    config_manager = ConfigManager(str(config_path), ConfigValidator())

    logger.info("=" * 60)
    logger.info("PEPE MOMENTUM BOT - OPTIMIZED")
    logger.info("=" * 60)
    logger.info("Backtest Result: +36.41% (30 days, 54% win rate)")
    logger.info("Settings: 30m | RSI + EMA | Momentum")
    logger.info("=" * 60)

    # Create exchange service (Kraken)
    trading_mode = config_manager.get_trading_mode()
    exchange_service = ExchangeServiceFactory.create_exchange_service(
        config_manager, trading_mode
    )

    try:
        # Show starting balance
        try:
            balance = await exchange_service.get_balance()
            usd = balance.get("USD", {}).get("free", 0)
            pepe = balance.get("PEPE", {}).get("free", 0)
            logger.info(f"Starting USD: ${usd:.2f}")
            logger.info(f"Starting PEPE: {pepe:.0f}")
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")

        # Create strategy with optimized settings
        strategy = MomentumStrategy(
            config_manager=config_manager,
            exchange_service=exchange_service,
            symbol="PEPE/USD",
            timeframe="30m",
            # Indicators: RSI + EMA (best for PEPE)
            use_rsi=True,
            use_bb=False,
            use_ema=True,
            # RSI params
            rsi_period=14,
            rsi_oversold=30,
            rsi_overbought=85,  # Raised from 70 - let winners run
            # EMA params
            ema_fast=9,
            ema_slow=20,
            # Position sizing
            position_size_usd=200.0,  # $200 per trade
            # Risk management (momentum settings)
            take_profit_pct=5.0,
            stop_loss_pct=3.5,
            max_hold_hours=24.0,
        )

        # Run strategy
        await strategy.start()

    except KeyboardInterrupt:
        logger.info("Shutting down PEPE Momentum Bot...")
    finally:
        if hasattr(exchange_service, "close"):
            await exchange_service.close()


if __name__ == "__main__":
    asyncio.run(main())

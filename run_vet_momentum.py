"""
VET Momentum Bot - Optimized Settings
======================================

Best combo from backtest:
- Timeframe: 15m
- Indicators: RSI + Bollinger Bands
- Strategy: Momentum
- Result: +23.56% over 30 days (83% win rate)
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
            logging.FileHandler(log_dir / "vet_momentum.log"),
        ],
    )
    logger = logging.getLogger("VET-Momentum")

    # Load config
    config_path = Path(__file__).parent / "config" / "config_vet_momentum.json"
    config_manager = ConfigManager(str(config_path), ConfigValidator())

    logger.info("=" * 60)
    logger.info("VET MOMENTUM BOT - OPTIMIZED")
    logger.info("=" * 60)
    logger.info("Backtest Result: +23.56% (30 days, 83% win rate)")
    logger.info("Settings: 15m | RSI + Bollinger Bands | Momentum")
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
            vet = balance.get("VET", {}).get("free", 0)
            logger.info(f"Starting USD: ${usd:.2f}")
            logger.info(f"Starting VET: {vet:.2f}")
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")

        # Create strategy with optimized settings
        strategy = MomentumStrategy(
            config_manager=config_manager,
            exchange_service=exchange_service,
            symbol="VET/USD",
            timeframe="15m",
            # Indicators: RSI + BB (best for VET)
            use_rsi=True,
            use_bb=True,
            use_ema=False,
            # RSI params
            rsi_period=14,
            rsi_oversold=30,
            rsi_overbought=70,
            # BB params
            bb_period=20,
            bb_std=2.0,
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
        logger.info("Shutting down VET Momentum Bot...")
    finally:
        if hasattr(exchange_service, "close"):
            await exchange_service.close()


if __name__ == "__main__":
    asyncio.run(main())

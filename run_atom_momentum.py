"""
ATOM Momentum Bot - EMA Crossover Strategy
===========================================

Settings from backtest:
- Timeframe: 15m
- Indicators: RSI(14) + EMA(6/25)
- Strategy: Buy on EMA cross up
- Result: +3.20% over 30 days (75% win rate)
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
            logging.FileHandler(log_dir / "atom_momentum.log"),
        ],
    )
    logger = logging.getLogger("ATOM-Momentum")

    # Load config
    config_path = Path(__file__).parent / "config" / "config_atom_momentum.json"
    config_manager = ConfigManager(str(config_path), ConfigValidator())

    logger.info("=" * 60)
    logger.info("ATOM MOMENTUM BOT - EMA CROSSOVER")
    logger.info("=" * 60)
    logger.info("Backtest Result: +3.20% (30 days, 75% win rate)")
    logger.info("Settings: 15m | RSI(14) + EMA(6/25) | Momentum")
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
            atom = balance.get("ATOM", {}).get("free", 0)
            logger.info(f"Starting USD: ${usd:.2f}")
            logger.info(f"Starting ATOM: {atom:.4f}")
        except Exception as e:
            logger.warning(f"Could not fetch balance: {e}")

        # Create strategy with EMA crossover settings
        strategy = MomentumStrategy(
            config_manager=config_manager,
            exchange_service=exchange_service,
            symbol="ATOM/USD",
            timeframe="15m",
            # Indicators: RSI + EMA (optimized for ATOM)
            use_rsi=True,
            use_bb=False,
            use_ema=True,
            # RSI params
            rsi_period=14,
            rsi_oversold=30,
            rsi_overbought=70,
            # EMA params (6/25 crossover)
            ema_fast=6,
            ema_slow=25,
            # Position sizing
            position_size_usd=200.0,  # $200 per trade
            # Risk management
            take_profit_pct=5.0,
            stop_loss_pct=3.5,
            max_hold_hours=24.0,
        )

        # Run strategy
        await strategy.start()

    except KeyboardInterrupt:
        logger.info("Shutting down ATOM Momentum Bot...")
    finally:
        if hasattr(exchange_service, "close"):
            await exchange_service.close()


if __name__ == "__main__":
    asyncio.run(main())

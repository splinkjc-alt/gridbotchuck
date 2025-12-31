"""
EMA Crossover Strategy Runner

Scans market for top 10 coins, monitors EMA 9/20 crossovers:
- Buy when EMA 9 crosses ABOVE EMA 20
- Sell when EMA 9 crosses BELOW EMA 20
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from config.config_manager import ConfigManager
from core.services.exchange_service_factory import ExchangeServiceFactory
from strategies.ema_crossover_strategy import EMACrossoverStrategy


async def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger("EMACrossover")
    
    # Load config
    config_path = Path(__file__).parent / "config" / "config.json"
    config_manager = ConfigManager(str(config_path))
    
    logger.info("=" * 60)
    logger.info("EMA 9/20 CROSSOVER STRATEGY")
    logger.info("=" * 60)
    logger.info("Strategy Rules:")
    logger.info("  - Scan market for top 10 coins by momentum")
    logger.info("  - BUY when EMA 9 crosses ABOVE EMA 20")
    logger.info("  - SELL when EMA 9 crosses BELOW EMA 20")
    logger.info("=" * 60)
    
    # Create exchange service
    exchange_factory = ExchangeServiceFactory(config_manager)
    exchange_service = await exchange_factory.create()
    
    try:
        # Get position sizing from config
        risk_config = config_manager.get_risk_management_config()
        position_config = risk_config.get("position_sizing", {})
        buy_percent = position_config.get("buy_percent_of_total", 20.0)
        min_reserve = position_config.get("min_reserve_percent", 10.0)
        
        # Create strategy
        strategy = EMACrossoverStrategy(
            config_manager=config_manager,
            exchange_service=exchange_service,
            ema_fast=9,
            ema_slow=20,
            max_positions=3,
            position_size_percent=buy_percent,
            min_reserve_percent=min_reserve,
        )
        
        # Run strategy
        await strategy.start()
        
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if hasattr(exchange_service, "close"):
            await exchange_service.close()


if __name__ == "__main__":
    asyncio.run(main())

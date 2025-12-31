"""Quick smoke test to verify imports and config loading."""

from __future__ import annotations

import logging
import sys

# ...existing code...

LOGGER = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    LOGGER.info("Checking imports...")

    try:
        from config.config_manager import ConfigManager
        from core.bot_management.event_bus import EventBus

        LOGGER.info("  Core imports OK")
    except ImportError:
        LOGGER.exception("  Import failed")
        return 1

    LOGGER.info("Checking config...")
    try:
        config = ConfigManager("config/config.json")
        mode = config.get_trading_mode()
        LOGGER.info("  Config loaded. Trading mode: %s", mode)
    except Exception:
        LOGGER.exception("  Config error")
        return 1

    LOGGER.info("Checking event bus...")
    try:
        _ = EventBus()
        LOGGER.info("  EventBus created")
    except Exception:
        LOGGER.exception("  EventBus error")
        return 1

    LOGGER.info("")
    LOGGER.info("All smoke tests passed!")
    return 0


if __name__ == "__main__":
    result = main()
    input("Press Enter to exit...")
    sys.exit(result)

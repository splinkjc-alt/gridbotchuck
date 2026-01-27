"""
Integration module to add API control to the existing GridTradingBot.
This module is called from main.py to enable web/mobile control.
"""

import logging

from core.bot_management.bot_api_server import BotAPIServer


class BotAPIIntegration:
    """Integrates REST API control into the trading bot."""

    def __init__(self, bot, event_bus, config_manager, port: int = 8080):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bot = bot
        self.event_bus = event_bus
        self.config_manager = config_manager
        self.port = port
        self.api_server: BotAPIServer | None = None

    async def start(self):
        """Start the API server."""
        try:
            self.api_server = BotAPIServer(
                self.bot,
                self.event_bus,
                self.config_manager,
                self.port,
            )
            await self.api_server.start()
            self.logger.info(f"Bot API server started on port {self.port}")
            self.logger.info(f"Access dashboard at: http://localhost:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start API server: {e}")
            raise

    async def stop(self):
        """Stop the API server."""
        if self.api_server:
            await self.api_server.stop()
            self.logger.info("Bot API server stopped")

    def is_running(self) -> bool:
        """Check if API server is running."""
        return (
            self.api_server is not None
            and hasattr(self.api_server, "runner")
            and self.api_server.runner is not None
        )

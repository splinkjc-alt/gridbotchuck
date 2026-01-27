"""
Decision Journal Integration for Grid Bots
==========================================

Provides easy integration of the decision journal into existing bots.
Monitors and records trading decisions without modifying core bot code.

Usage:
    from decision_journal_integration import JournalizedBot

    # Wrap your bot
    bot = JournalizedBot("chuck", exchange_service, config_manager)

    # Log decisions as they happen
    bot.log_buy_decision(pair, price, reason, **conditions)
    bot.log_sell_decision(pair, price, reason, **conditions)
    bot.log_skip_decision(pair, price, reason, **conditions)

    # Get summary
    bot.print_journal_summary()
"""

import logging
from datetime import datetime
from typing import Any

from decision_journal import Decision, DecisionJournal


logger = logging.getLogger(__name__)


class JournalizedBot:
    """
    Wrapper that adds decision journaling to any bot.

    Can be used standalone or as a mixin for existing bot classes.
    """

    def __init__(
        self,
        bot_name: str,
        exchange_service: Any = None,
        config_manager: Any = None,
        db_path: str = "data/decision_journal.db",
    ):
        """
        Initialize the journalized bot wrapper.

        Args:
            bot_name: Name of the bot (e.g., "chuck", "growler")
            exchange_service: Optional exchange service for fetching market data
            config_manager: Optional config manager for getting settings
            db_path: Path to the SQLite database
        """
        self.bot_name = bot_name
        self.exchange_service = exchange_service
        self.config_manager = config_manager
        self.journal = DecisionJournal(bot_name, db_path)
        self._decision_counter = 0

        logger.info(f"Decision journal initialized for {bot_name}")

    def _get_market_conditions(self, pair: str) -> dict:
        """Fetch current market conditions if exchange service available."""
        conditions = {}

        if self.exchange_service is None:
            return conditions

        try:
            # Try to get ticker data
            ticker = (
                self.exchange_service.fetch_ticker_sync(pair)
                if hasattr(self.exchange_service, "fetch_ticker_sync")
                else None
            )

            if ticker:
                conditions["price"] = ticker.get("last", 0)
                conditions["bid"] = ticker.get("bid", 0)
                conditions["ask"] = ticker.get("ask", 0)
                conditions["volume"] = ticker.get("baseVolume", 0)
        except Exception as e:
            logger.debug(f"Could not fetch market conditions: {e}")

        return conditions

    def log_decision(
        self,
        action: str,
        pair: str,
        price: float,
        reasoning: str,
        rsi: float = None,
        trend: str = None,
        grid_position: str = None,
        grid_level: int = None,
        open_buys: int = 0,
        open_sells: int = 0,
        fiat_balance: float = 0,
        crypto_balance: float = 0,
        exchange_status: str = "ok",
        signals: list = None,
        websocket_connected: bool = True,
        ema_9: float = None,
        ema_30: float = None,
        volatility_pct: float = None,
    ) -> int:
        """
        Log a trading decision to the journal.

        Args:
            action: BUY, SELL, HOLD, SKIP, or ERROR
            pair: Trading pair (e.g., "ADA/USD")
            price: Current price
            reasoning: Why this decision was made
            ... other conditions

        Returns:
            Decision ID for tracking outcomes
        """
        decision = Decision(
            timestamp=datetime.now().isoformat(),
            bot_name=self.bot_name,
            action=action.upper(),
            pair=pair,
            price=price,
            rsi=rsi,
            ema_9=ema_9,
            ema_30=ema_30,
            volatility_pct=volatility_pct,
            trend=trend,
            grid_level=grid_level,
            grid_position=grid_position,
            open_buy_orders=open_buys,
            open_sell_orders=open_sells,
            fiat_balance=fiat_balance,
            crypto_balance=crypto_balance,
            reasoning=reasoning,
            signals=signals,
            exchange_status=exchange_status,
            websocket_connected=websocket_connected,
        )

        decision_id = self.journal.log_decision(decision)
        self._decision_counter += 1

        logger.info(
            f"[JOURNAL] {self.bot_name} #{decision_id}: {action} {pair} @ ${price:.4f} - {reasoning[:50]}"
        )

        return decision_id

    def log_buy_decision(
        self, pair: str, price: float, reasoning: str, **kwargs
    ) -> int:
        """Log a BUY decision."""
        return self.log_decision("BUY", pair, price, reasoning, **kwargs)

    def log_sell_decision(
        self, pair: str, price: float, reasoning: str, **kwargs
    ) -> int:
        """Log a SELL decision."""
        return self.log_decision("SELL", pair, price, reasoning, **kwargs)

    def log_hold_decision(
        self, pair: str, price: float, reasoning: str, **kwargs
    ) -> int:
        """Log a HOLD decision (waiting for conditions)."""
        return self.log_decision("HOLD", pair, price, reasoning, **kwargs)

    def log_skip_decision(
        self, pair: str, price: float, reasoning: str, **kwargs
    ) -> int:
        """Log a SKIP decision (conditions not met)."""
        return self.log_decision("SKIP", pair, price, reasoning, **kwargs)

    def log_error_decision(
        self,
        pair: str,
        price: float,
        reasoning: str,
        exchange_status: str = "error",
        **kwargs,
    ) -> int:
        """Log an ERROR (failed to execute)."""
        return self.log_decision(
            "ERROR", pair, price, reasoning, exchange_status=exchange_status, **kwargs
        )

    def update_outcome(
        self,
        decision_id: int,
        outcome: str,
        outcome_price: float = None,
        pnl: float = None,
    ):
        """
        Update the outcome of a previous decision.

        Args:
            decision_id: ID returned from log_decision
            outcome: filled, cancelled, pending, failed
            outcome_price: Price at which order was filled
            pnl: Profit/loss from this trade
        """
        self.journal.update_outcome(decision_id, outcome, outcome_price, pnl)
        logger.info(
            f"[JOURNAL] Updated #{decision_id}: {outcome}, P/L: ${pnl:.2f}"
            if pnl
            else f"[JOURNAL] Updated #{decision_id}: {outcome}"
        )

    def print_journal_summary(self):
        """Print a summary of all decisions."""
        self.journal.print_summary()

    def get_stats(self) -> dict:
        """Get decision statistics."""
        return self.journal.get_stats()

    def get_patterns(self) -> dict:
        """Analyze decision patterns."""
        return self.journal.analyze_patterns()

    def export_journal(self, filepath: str = None) -> str:
        """Export journal to JSON file."""
        return self.journal.export_to_json(filepath)

    def get_recent_decisions(self, limit: int = 20) -> list:
        """Get recent decisions."""
        return self.journal.get_recent_decisions(limit)


def add_journal_to_bot(bot_instance: Any, bot_name: str) -> JournalizedBot:
    """
    Add decision journaling capability to an existing bot instance.

    Args:
        bot_instance: The bot to enhance
        bot_name: Name for the journal

    Returns:
        JournalizedBot wrapper with journal methods
    """
    journal_wrapper = JournalizedBot(
        bot_name=bot_name,
        exchange_service=getattr(bot_instance, "exchange_service", None),
        config_manager=getattr(bot_instance, "config_manager", None),
    )

    # Attach journal methods to the bot
    bot_instance.journal = journal_wrapper.journal
    bot_instance.log_decision = journal_wrapper.log_decision
    bot_instance.log_buy_decision = journal_wrapper.log_buy_decision
    bot_instance.log_sell_decision = journal_wrapper.log_sell_decision
    bot_instance.log_skip_decision = journal_wrapper.log_skip_decision
    bot_instance.log_error_decision = journal_wrapper.log_error_decision
    bot_instance.update_outcome = journal_wrapper.update_outcome
    bot_instance.print_journal_summary = journal_wrapper.print_journal_summary

    logger.info(f"Attached decision journal to {bot_name}")

    return journal_wrapper


# Example integration with GridTradingBot
async def monitor_grid_decisions(
    bot: Any,
    journal: JournalizedBot,
    pair: str,
    price: float,
    action: str,
    grid_level: int = None,
    reasoning: str = "",
):
    """
    Helper to log grid bot decisions with full context.

    Call this from your bot's decision points.
    """
    # Get balances if available
    fiat = (
        getattr(bot.balance_tracker, "balance", 0)
        if hasattr(bot, "balance_tracker")
        else 0
    )
    crypto = (
        getattr(bot.balance_tracker, "crypto_balance", 0)
        if hasattr(bot, "balance_tracker")
        else 0
    )

    # Get grid info
    grid_manager = getattr(bot, "grid_manager", None)
    open_buys = 0
    open_sells = 0

    if grid_manager:
        grid_levels = getattr(grid_manager, "grid_levels", {})
        for level in grid_levels.values():
            if hasattr(level, "active_order"):
                order = level.active_order
                if order:
                    if hasattr(order, "side"):
                        if str(order.side).upper() == "BUY":
                            open_buys += 1
                        else:
                            open_sells += 1

    # Determine grid position
    grid_position = "in_range"
    if grid_manager:
        grids = getattr(grid_manager, "price_grids", [])
        if grids:
            if price > max(grids):
                grid_position = "above"
            elif price < min(grids):
                grid_position = "below"

    return journal.log_decision(
        action=action,
        pair=pair,
        price=price,
        reasoning=reasoning,
        grid_level=grid_level,
        grid_position=grid_position,
        open_buys=open_buys,
        open_sells=open_sells,
        fiat_balance=fiat,
        crypto_balance=crypto,
    )


if __name__ == "__main__":
    # Demo
    print("Decision Journal Integration Demo")
    print("-" * 40)

    # Create a journalized bot
    bot = JournalizedBot("chuck_demo")

    # Log some decisions
    d1 = bot.log_buy_decision(
        pair="ADA/USD",
        price=0.39,
        reasoning="RSI oversold at 28, grid level 3 triggered",
        rsi=28,
        grid_level=3,
        grid_position="in_range",
        open_buys=2,
        open_sells=1,
        fiat_balance=500,
        crypto_balance=100,
        signals=["rsi_oversold", "grid_hit"],
    )
    print(f"Logged BUY decision #{d1}")

    d2 = bot.log_skip_decision(
        pair="ADA/USD",
        price=0.395,
        reasoning="No grid level triggered, price between levels",
        grid_position="in_range",
        fiat_balance=450,
        crypto_balance=150,
    )
    print(f"Logged SKIP decision #{d2}")

    d3 = bot.log_error_decision(
        pair="ADA/USD",
        price=0.39,
        reasoning="Kraken API timeout after 3 retries",
        exchange_status="timeout",
    )
    print(f"Logged ERROR decision #{d3}")

    # Update outcome
    bot.update_outcome(d1, "filled", outcome_price=0.388, pnl=0.52)

    # Print summary
    print("\n")
    bot.print_journal_summary()

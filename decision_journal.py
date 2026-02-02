"""
Decision Journal - Tracks bot trading decisions in detail
=========================================================

Records every decision a bot makes so we can analyze:
- What it saw (market conditions)
- What it decided (buy/sell/hold)
- Why it decided that (signals, indicators)
- What happened after (outcome)

Usage:
    journal = DecisionJournal("chuck")
    journal.log_decision(
        action="BUY",
        pair="ADA/USD",
        price=0.39,
        conditions={...},
        reasoning="RSI oversold, price at grid level"
    )
    journal.print_summary()
"""

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Decision:
    """A single trading decision."""

    timestamp: str
    bot_name: str
    action: str  # BUY, SELL, HOLD, SKIP, ERROR
    pair: str
    price: float

    # Market conditions
    rsi: float | None = None
    ema_9: float | None = None
    ema_30: float | None = None
    volatility_pct: float | None = None
    trend: str | None = None  # bullish, bearish, neutral

    # Grid state
    grid_level: int | None = None
    grid_position: str | None = None  # above, below, in_range
    open_buy_orders: int = 0
    open_sell_orders: int = 0

    # Balances
    fiat_balance: float = 0
    crypto_balance: float = 0

    # Decision reasoning
    reasoning: str = ""
    signals: list = None

    # Connection/health
    exchange_status: str = "ok"
    websocket_connected: bool = True

    # Outcome (filled in later)
    outcome: str | None = None  # filled, cancelled, pending, failed
    outcome_price: float | None = None
    pnl: float | None = None


class DecisionJournal:
    """
    Records and analyzes bot trading decisions.

    Stores decisions in SQLite for persistence and analysis.
    """

    def __init__(self, bot_name: str, db_path: str = "data/decision_journal.db"):
        self.bot_name = bot_name
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                bot_name TEXT NOT NULL,
                action TEXT NOT NULL,
                pair TEXT NOT NULL,
                price REAL NOT NULL,
                rsi REAL,
                ema_9 REAL,
                ema_30 REAL,
                volatility_pct REAL,
                trend TEXT,
                grid_level INTEGER,
                grid_position TEXT,
                open_buy_orders INTEGER,
                open_sell_orders INTEGER,
                fiat_balance REAL,
                crypto_balance REAL,
                reasoning TEXT,
                signals TEXT,
                exchange_status TEXT,
                websocket_connected INTEGER,
                outcome TEXT,
                outcome_price REAL,
                pnl REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Summary stats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                bot_name TEXT NOT NULL,
                total_decisions INTEGER,
                buy_decisions INTEGER,
                sell_decisions INTEGER,
                hold_decisions INTEGER,
                skip_decisions INTEGER,
                error_decisions INTEGER,
                filled_orders INTEGER,
                failed_orders INTEGER,
                total_pnl REAL,
                exchange_errors INTEGER,
                UNIQUE(date, bot_name)
            )
        """)

        conn.commit()
        conn.close()

    def log_decision(self, decision: Decision) -> int:
        """Log a decision to the journal."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        signals_json = json.dumps(decision.signals) if decision.signals else None

        cursor.execute(
            """
            INSERT INTO decisions (
                timestamp, bot_name, action, pair, price,
                rsi, ema_9, ema_30, volatility_pct, trend,
                grid_level, grid_position, open_buy_orders, open_sell_orders,
                fiat_balance, crypto_balance, reasoning, signals,
                exchange_status, websocket_connected, outcome, outcome_price, pnl
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                decision.timestamp,
                decision.bot_name,
                decision.action,
                decision.pair,
                decision.price,
                decision.rsi,
                decision.ema_9,
                decision.ema_30,
                decision.volatility_pct,
                decision.trend,
                decision.grid_level,
                decision.grid_position,
                decision.open_buy_orders,
                decision.open_sell_orders,
                decision.fiat_balance,
                decision.crypto_balance,
                decision.reasoning,
                signals_json,
                decision.exchange_status,
                1 if decision.websocket_connected else 0,
                decision.outcome,
                decision.outcome_price,
                decision.pnl,
            ),
        )

        decision_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return decision_id

    def update_outcome(
        self,
        decision_id: int,
        outcome: str,
        outcome_price: float = None,
        pnl: float = None,
    ):
        """Update the outcome of a decision."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE decisions
            SET outcome = ?, outcome_price = ?, pnl = ?
            WHERE id = ?
        """,
            (outcome, outcome_price, pnl, decision_id),
        )

        conn.commit()
        conn.close()

    def get_recent_decisions(self, limit: int = 50) -> list[dict]:
        """Get recent decisions."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM decisions
            WHERE bot_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """,
            (self.bot_name, limit),
        )

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_stats(self) -> dict:
        """Get decision statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Action counts
        cursor.execute(
            """
            SELECT action, COUNT(*) as count
            FROM decisions
            WHERE bot_name = ?
            GROUP BY action
        """,
            (self.bot_name,),
        )
        actions = dict(cursor.fetchall())

        # Outcome counts
        cursor.execute(
            """
            SELECT outcome, COUNT(*) as count
            FROM decisions
            WHERE bot_name = ? AND outcome IS NOT NULL
            GROUP BY outcome
        """,
            (self.bot_name,),
        )
        outcomes = dict(cursor.fetchall())

        # Exchange errors
        cursor.execute(
            """
            SELECT COUNT(*) FROM decisions
            WHERE bot_name = ? AND exchange_status != 'ok'
        """,
            (self.bot_name,),
        )
        exchange_errors = cursor.fetchone()[0]

        # Total PnL
        cursor.execute(
            """
            SELECT SUM(pnl) FROM decisions
            WHERE bot_name = ? AND pnl IS NOT NULL
        """,
            (self.bot_name,),
        )
        total_pnl = cursor.fetchone()[0] or 0

        # Decision frequency
        cursor.execute(
            """
            SELECT COUNT(*) FROM decisions WHERE bot_name = ?
        """,
            (self.bot_name,),
        )
        total = cursor.fetchone()[0]

        conn.close()

        return {
            "total_decisions": total,
            "actions": actions,
            "outcomes": outcomes,
            "exchange_errors": exchange_errors,
            "total_pnl": total_pnl,
        }

    def analyze_patterns(self) -> dict:
        """Analyze decision patterns to find issues."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        patterns = {}

        # When does the bot SKIP?
        cursor.execute(
            """
            SELECT reasoning, COUNT(*) as count
            FROM decisions
            WHERE bot_name = ? AND action = 'SKIP'
            GROUP BY reasoning
            ORDER BY count DESC
            LIMIT 5
        """,
            (self.bot_name,),
        )
        patterns["skip_reasons"] = [dict(row) for row in cursor.fetchall()]

        # When does the bot ERROR?
        cursor.execute(
            """
            SELECT exchange_status, COUNT(*) as count
            FROM decisions
            WHERE bot_name = ? AND action = 'ERROR'
            GROUP BY exchange_status
            ORDER BY count DESC
        """,
            (self.bot_name,),
        )
        patterns["error_causes"] = [dict(row) for row in cursor.fetchall()]

        # What RSI levels trigger buys?
        cursor.execute(
            """
            SELECT
                CASE
                    WHEN rsi < 30 THEN 'oversold (<30)'
                    WHEN rsi < 50 THEN 'low (30-50)'
                    WHEN rsi < 70 THEN 'mid (50-70)'
                    ELSE 'overbought (>70)'
                END as rsi_zone,
                action,
                COUNT(*) as count
            FROM decisions
            WHERE bot_name = ? AND rsi IS NOT NULL
            GROUP BY rsi_zone, action
        """,
            (self.bot_name,),
        )
        patterns["rsi_actions"] = [dict(row) for row in cursor.fetchall()]

        # Grid position analysis
        cursor.execute(
            """
            SELECT grid_position, action, COUNT(*) as count
            FROM decisions
            WHERE bot_name = ? AND grid_position IS NOT NULL
            GROUP BY grid_position, action
        """,
            (self.bot_name,),
        )
        patterns["grid_actions"] = [dict(row) for row in cursor.fetchall()]

        conn.close()
        return patterns

    def print_summary(self):
        """Print a summary of decisions."""
        stats = self.get_stats()
        patterns = self.analyze_patterns()

        print(f"\n{'='*60}")
        print(f"DECISION JOURNAL: {self.bot_name.upper()}")
        print(f"{'='*60}")

        print(f"\nTotal Decisions: {stats['total_decisions']}")
        print("\nActions:")
        for action, count in stats["actions"].items():
            pct = (
                (count / stats["total_decisions"] * 100)
                if stats["total_decisions"] > 0
                else 0
            )
            print(f"  {action:10} {count:5} ({pct:.1f}%)")

        if stats["outcomes"]:
            print("\nOutcomes:")
            for outcome, count in stats["outcomes"].items():
                print(f"  {outcome:10} {count:5}")

        print(f"\nExchange Errors: {stats['exchange_errors']}")
        print(f"Total P/L: ${stats['total_pnl']:.2f}")

        if patterns["skip_reasons"]:
            print("\nTop Skip Reasons:")
            for p in patterns["skip_reasons"][:3]:
                print(f"  - {p['reasoning'][:50]}... ({p['count']}x)")

        if patterns["error_causes"]:
            print("\nError Causes:")
            for p in patterns["error_causes"]:
                print(f"  - {p['exchange_status']}: {p['count']}x")

        print(f"{'='*60}\n")

    def export_to_json(self, filepath: str = None) -> str:
        """Export all decisions to JSON."""
        if filepath is None:
            filepath = f"data/{self.bot_name}_decisions_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

        decisions = self.get_recent_decisions(limit=10000)
        stats = self.get_stats()
        patterns = self.analyze_patterns()

        export = {
            "bot_name": self.bot_name,
            "exported_at": datetime.now().isoformat(),
            "stats": stats,
            "patterns": patterns,
            "decisions": decisions,
        }

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(export, f, indent=2, default=str)

        return filepath


# Helper function to create a decision from bot state
def create_decision_from_state(
    bot_name: str,
    action: str,
    pair: str,
    price: float,
    reasoning: str,
    rsi: float = None,
    trend: str = None,
    grid_position: str = None,
    open_buys: int = 0,
    open_sells: int = 0,
    fiat: float = 0,
    crypto: float = 0,
    exchange_status: str = "ok",
    signals: list = None,
) -> Decision:
    """Helper to create a decision object."""
    return Decision(
        timestamp=datetime.now().isoformat(),
        bot_name=bot_name,
        action=action,
        pair=pair,
        price=price,
        rsi=rsi,
        trend=trend,
        grid_position=grid_position,
        open_buy_orders=open_buys,
        open_sell_orders=open_sells,
        fiat_balance=fiat,
        crypto_balance=crypto,
        reasoning=reasoning,
        signals=signals,
        exchange_status=exchange_status,
    )


if __name__ == "__main__":
    # Demo
    print("Decision Journal Demo")
    print("-" * 40)

    journal = DecisionJournal("chuck_test")

    # Log some test decisions
    d1 = create_decision_from_state(
        bot_name="chuck_test",
        action="BUY",
        pair="ADA/USD",
        price=0.39,
        reasoning="RSI oversold at 28, price at grid level 3",
        rsi=28,
        trend="bearish",
        grid_position="in_range",
        open_buys=2,
        open_sells=1,
        fiat=500,
        crypto=100,
        signals=["rsi_oversold", "grid_level_hit"],
    )
    journal.log_decision(d1)

    d2 = create_decision_from_state(
        bot_name="chuck_test",
        action="SKIP",
        pair="ADA/USD",
        price=0.395,
        reasoning="No grid level hit, waiting",
        rsi=35,
        trend="bearish",
        grid_position="in_range",
        open_buys=2,
        open_sells=1,
        fiat=450,
        crypto=150,
    )
    journal.log_decision(d2)

    d3 = create_decision_from_state(
        bot_name="chuck_test",
        action="ERROR",
        pair="ADA/USD",
        price=0.39,
        reasoning="Kraken connection timeout",
        exchange_status="error",
    )
    journal.log_decision(d3)

    journal.print_summary()

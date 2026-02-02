"""
Order Repository - SQLite persistence for order history.
"""

from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

import aiosqlite

from core.order_handling.order import Order


class OrderRepository:
    """
    Persists orders to SQLite database.
    Enables order history across bot restarts and provides audit trail.
    """

    def __init__(self, db_path: str = "data/gridbotchuck.db"):
        """
        Initialize order repository.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Create database tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    pair TEXT NOT NULL,
                    side TEXT NOT NULL,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    filled REAL NOT NULL DEFAULT 0,
                    average REAL,
                    fee REAL DEFAULT 0,
                    grid_level REAL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    filled_at TEXT,
                    metadata TEXT
                )
            """
            )

            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT NOT NULL,
                    pair TEXT NOT NULL,
                    side TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    fee REAL NOT NULL,
                    profit REAL,
                    balance_after REAL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (order_id) REFERENCES orders (id)
                )
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_orders_pair ON orders(pair)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trades_pair ON trade_history(pair)
            """
            )

            await db.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trade_history(timestamp)
            """
            )

            await db.commit()

        self.logger.info(f"Order repository initialized at {self.db_path}")

    async def save_order(
        self,
        order: Order,
        grid_level: float | None = None,
        metadata: dict | None = None,
    ):
        """
        Save or update an order in the database.

        Args:
            order: Order instance to save
            grid_level: Grid level price (optional)
            metadata: Additional metadata as dict (optional)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO orders (
                        id, pair, side, type, status, price, quantity, filled,
                        average, fee, grid_level, created_at, updated_at, filled_at, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order.id,
                        order.pair,
                        order.side.value,
                        order.type.value,
                        order.status.value,
                        order.price,
                        order.quantity,
                        order.filled,
                        order.average,
                        order.fee,
                        grid_level,
                        order.created_at.isoformat()
                        if order.created_at
                        else datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        order.filled_at.isoformat() if order.filled_at else None,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                await db.commit()

        except Exception as e:
            self.logger.error(f"Error saving order {order.id}: {e}")

    async def save_trade(
        self,
        order: Order,
        profit: float | None = None,
        balance_after: float | None = None,
    ):
        """
        Record a completed trade in history.

        Args:
            order: Filled order
            profit: Profit from this trade (optional)
            balance_after: Account balance after trade (optional)
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT INTO trade_history (
                        order_id, pair, side, price, quantity, fee, profit,
                        balance_after, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        order.id,
                        order.pair,
                        order.side.value,
                        order.average or order.price,
                        order.filled,
                        order.fee,
                        profit,
                        balance_after,
                        datetime.now().isoformat(),
                    ),
                )
                await db.commit()

            self.logger.info(f"Recorded trade for order {order.id}")

        except Exception as e:
            self.logger.error(f"Error saving trade {order.id}: {e}")

    async def get_order(self, order_id: str) -> dict | None:
        """
        Retrieve an order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order data as dict, or None if not found
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT * FROM orders WHERE id = ?", (order_id,)
                ) as cursor:
                    row = await cursor.fetchone()

                    if row:
                        return dict(row)

        except Exception as e:
            self.logger.error(f"Error retrieving order {order_id}: {e}")

        return None

    async def get_open_orders(self, pair: str | None = None) -> list[dict]:
        """
        Get all open orders, optionally filtered by pair.

        Args:
            pair: Trading pair filter (optional)

        Returns:
            List of open orders
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                if pair:
                    query = "SELECT * FROM orders WHERE status = 'open' AND pair = ? ORDER BY created_at DESC"
                    params = (pair,)
                else:
                    query = "SELECT * FROM orders WHERE status = 'open' ORDER BY created_at DESC"
                    params = ()

                async with db.execute(query, params) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error retrieving open orders: {e}")
            return []

    async def get_order_history(
        self,
        pair: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get order history with optional filters.

        Args:
            pair: Trading pair filter
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of orders to return

        Returns:
            List of historical orders
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                query = "SELECT * FROM orders WHERE 1=1"
                params = []

                if pair:
                    query += " AND pair = ?"
                    params.append(pair)

                if start_date:
                    query += " AND created_at >= ?"
                    params.append(start_date.isoformat())

                if end_date:
                    query += " AND created_at <= ?"
                    params.append(end_date.isoformat())

                query += " ORDER BY created_at DESC LIMIT ?"
                params.append(limit)

                async with db.execute(query, tuple(params)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error retrieving order history: {e}")
            return []

    async def get_trade_history(
        self,
        pair: str | None = None,
        start_date: datetime | None = None,
        limit: int = 100,
    ) -> list[dict]:
        """
        Get trade history.

        Args:
            pair: Trading pair filter
            start_date: Start date filter
            limit: Maximum number of trades to return

        Returns:
            List of trades
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                query = "SELECT * FROM trade_history WHERE 1=1"
                params = []

                if pair:
                    query += " AND pair = ?"
                    params.append(pair)

                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())

                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)

                async with db.execute(query, tuple(params)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(row) for row in rows]

        except Exception as e:
            self.logger.error(f"Error retrieving trade history: {e}")
            return []

    async def get_statistics(self, pair: str | None = None) -> dict:
        """
        Get trading statistics.

        Args:
            pair: Trading pair filter (optional)

        Returns:
            Statistics dictionary
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row

                pair_filter = f"AND pair = '{pair}'" if pair else ""

                # Total orders
                async with db.execute(
                    f"SELECT COUNT(*) as count FROM orders WHERE 1=1 {pair_filter}"
                ) as cursor:
                    total_orders = (await cursor.fetchone())["count"]

                # Filled orders
                async with db.execute(
                    f"SELECT COUNT(*) as count FROM orders WHERE status = 'closed' {pair_filter}"
                ) as cursor:
                    filled_orders = (await cursor.fetchone())["count"]

                # Total trades
                async with db.execute(
                    f"SELECT COUNT(*) as count FROM trade_history WHERE 1=1 {pair_filter}"
                ) as cursor:
                    total_trades = (await cursor.fetchone())["count"]

                # Total fees
                async with db.execute(
                    f"SELECT SUM(fee) as total FROM trade_history WHERE 1=1 {pair_filter}"
                ) as cursor:
                    total_fees = (await cursor.fetchone())["total"] or 0.0

                # Total profit
                async with db.execute(
                    f"SELECT SUM(profit) as total FROM trade_history WHERE profit IS NOT NULL {pair_filter}"
                ) as cursor:
                    total_profit = (await cursor.fetchone())["total"] or 0.0

                return {
                    "total_orders": total_orders,
                    "filled_orders": filled_orders,
                    "total_trades": total_trades,
                    "total_fees": total_fees,
                    "total_profit": total_profit,
                    "fill_rate": (filled_orders / total_orders * 100)
                    if total_orders > 0
                    else 0,
                }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

    async def cleanup_old_orders(self, days: int = 90):
        """
        Remove old completed orders from database.

        Args:
            days: Keep orders from last N days
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    DELETE FROM orders
                    WHERE status IN ('closed', 'canceled', 'expired')
                    AND updated_at < ?
                """,
                    (cutoff_date.isoformat(),),
                )

                deleted = db.total_changes
                await db.commit()

            self.logger.info(
                f"Cleaned up {deleted} old orders (older than {days} days)"
            )

        except Exception as e:
            self.logger.error(f"Error cleaning up old orders: {e}")

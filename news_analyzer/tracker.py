"""
News Prediction Tracker
=======================
Tracks news sentiment predictions vs actual price outcomes.
Uses SQLite for persistence.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    """A sentiment prediction."""

    id: int
    symbol: str
    headline: str
    source: str
    api_source: str
    sentiment_score: float
    sentiment_label: str
    confidence: float
    price_at_news: float
    predicted_direction: str  # "up", "down", "neutral"
    created_at: datetime


@dataclass
class Outcome:
    """The actual outcome of a prediction."""

    prediction_id: int
    price_after_1h: Optional[float]
    price_after_4h: Optional[float]
    price_after_24h: Optional[float]
    actual_direction_1h: Optional[str]
    actual_direction_4h: Optional[str]
    actual_direction_24h: Optional[str]
    correct_1h: Optional[bool]
    correct_4h: Optional[bool]
    correct_24h: Optional[bool]


@dataclass
class SourceStats:
    """Statistics for a news source."""

    source: str
    total_predictions: int
    correct_1h: int
    correct_4h: int
    correct_24h: int
    accuracy_1h: float
    accuracy_4h: float
    accuracy_24h: float
    avg_confidence: float
    bullish_accuracy: float
    bearish_accuracy: float


class NewsTracker:
    """
    Tracks news predictions and outcomes in SQLite.

    Allows backtesting to determine which news sources are most accurate.
    """

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "news_tracker.db"

        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True)

        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Predictions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                headline TEXT NOT NULL,
                summary TEXT,
                source TEXT NOT NULL,
                api_source TEXT NOT NULL,
                url TEXT,
                sentiment_score REAL NOT NULL,
                sentiment_label TEXT NOT NULL,
                confidence REAL NOT NULL,
                price_at_news REAL,
                predicted_direction TEXT NOT NULL,
                news_published_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, headline, source)
            )
        """)

        # Outcomes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS outcomes (
                prediction_id INTEGER PRIMARY KEY,
                price_after_1h REAL,
                price_after_4h REAL,
                price_after_24h REAL,
                pct_change_1h REAL,
                pct_change_4h REAL,
                pct_change_24h REAL,
                actual_direction_1h TEXT,
                actual_direction_4h TEXT,
                actual_direction_24h TEXT,
                correct_1h INTEGER,
                correct_4h INTEGER,
                correct_24h INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (prediction_id) REFERENCES predictions(id)
            )
        """)

        # Source stats cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS source_stats (
                source TEXT PRIMARY KEY,
                api_source TEXT,
                total_predictions INTEGER DEFAULT 0,
                correct_1h INTEGER DEFAULT 0,
                correct_4h INTEGER DEFAULT 0,
                correct_24h INTEGER DEFAULT 0,
                total_bullish INTEGER DEFAULT 0,
                correct_bullish INTEGER DEFAULT 0,
                total_bearish INTEGER DEFAULT 0,
                correct_bearish INTEGER DEFAULT 0,
                avg_confidence REAL DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Indexes
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_symbol ON predictions(symbol)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_source ON predictions(source)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_predictions_created ON predictions(created_at)"
        )

        conn.commit()
        conn.close()

    def add_prediction(
        self,
        symbol: str,
        headline: str,
        summary: str,
        source: str,
        api_source: str,
        url: str,
        sentiment_score: float,
        sentiment_label: str,
        confidence: float,
        price_at_news: float,
        news_published_at: datetime = None,
    ) -> int:
        """
        Add a new prediction to track.

        Returns prediction ID.
        """
        # Determine predicted direction
        if sentiment_score > 0.15:
            predicted_direction = "up"
        elif sentiment_score < -0.15:
            predicted_direction = "down"
        else:
            predicted_direction = "neutral"

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO predictions
                (symbol, headline, summary, source, api_source, url,
                 sentiment_score, sentiment_label, confidence, price_at_news,
                 predicted_direction, news_published_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    symbol,
                    headline,
                    summary,
                    source,
                    api_source,
                    url,
                    sentiment_score,
                    sentiment_label,
                    confidence,
                    price_at_news,
                    predicted_direction,
                    news_published_at,
                ),
            )

            conn.commit()
            return cursor.lastrowid

        finally:
            conn.close()

    def update_outcome(
        self, prediction_id: int, price_after: float, hours_elapsed: int
    ):
        """
        Update outcome for a prediction.

        Args:
            prediction_id: ID of the prediction
            price_after: Price after elapsed time
            hours_elapsed: 1, 4, or 24 hours
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Get prediction info
            cursor.execute(
                """
                SELECT price_at_news, predicted_direction, sentiment_label
                FROM predictions WHERE id = ?
            """,
                (prediction_id,),
            )
            row = cursor.fetchone()
            if not row:
                return

            price_at_news, predicted_direction, sentiment_label = row

            # Calculate change
            if price_at_news and price_at_news > 0:
                pct_change = ((price_after - price_at_news) / price_at_news) * 100
            else:
                pct_change = 0

            # Determine actual direction
            if pct_change > 0.5:
                actual_direction = "up"
            elif pct_change < -0.5:
                actual_direction = "down"
            else:
                actual_direction = "neutral"

            # Was prediction correct?
            correct = (predicted_direction == actual_direction) or (
                predicted_direction == "neutral" and abs(pct_change) < 1
            )

            # Ensure outcome row exists
            cursor.execute(
                """
                INSERT OR IGNORE INTO outcomes (prediction_id)
                VALUES (?)
            """,
                (prediction_id,),
            )

            # Update appropriate columns
            if hours_elapsed == 1:
                cursor.execute(
                    """
                    UPDATE outcomes SET
                        price_after_1h = ?,
                        pct_change_1h = ?,
                        actual_direction_1h = ?,
                        correct_1h = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE prediction_id = ?
                """,
                    (
                        price_after,
                        pct_change,
                        actual_direction,
                        int(correct),
                        prediction_id,
                    ),
                )

            elif hours_elapsed == 4:
                cursor.execute(
                    """
                    UPDATE outcomes SET
                        price_after_4h = ?,
                        pct_change_4h = ?,
                        actual_direction_4h = ?,
                        correct_4h = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE prediction_id = ?
                """,
                    (
                        price_after,
                        pct_change,
                        actual_direction,
                        int(correct),
                        prediction_id,
                    ),
                )

            elif hours_elapsed == 24:
                cursor.execute(
                    """
                    UPDATE outcomes SET
                        price_after_24h = ?,
                        pct_change_24h = ?,
                        actual_direction_24h = ?,
                        correct_24h = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE prediction_id = ?
                """,
                    (
                        price_after,
                        pct_change,
                        actual_direction,
                        int(correct),
                        prediction_id,
                    ),
                )

            conn.commit()

        finally:
            conn.close()

    def get_source_stats(self, min_predictions: int = 10) -> list[SourceStats]:
        """
        Get accuracy statistics for each news source.

        Args:
            min_predictions: Minimum predictions to include source

        Returns:
            List of SourceStats sorted by 24h accuracy
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT
                    p.source,
                    COUNT(*) as total,
                    SUM(CASE WHEN o.correct_1h = 1 THEN 1 ELSE 0 END) as correct_1h,
                    SUM(CASE WHEN o.correct_4h = 1 THEN 1 ELSE 0 END) as correct_4h,
                    SUM(CASE WHEN o.correct_24h = 1 THEN 1 ELSE 0 END) as correct_24h,
                    AVG(p.confidence) as avg_conf,
                    SUM(CASE WHEN p.predicted_direction = 'up' THEN 1 ELSE 0 END) as total_bullish,
                    SUM(CASE WHEN p.predicted_direction = 'up' AND o.correct_24h = 1 THEN 1 ELSE 0 END) as correct_bullish,
                    SUM(CASE WHEN p.predicted_direction = 'down' THEN 1 ELSE 0 END) as total_bearish,
                    SUM(CASE WHEN p.predicted_direction = 'down' AND o.correct_24h = 1 THEN 1 ELSE 0 END) as correct_bearish
                FROM predictions p
                LEFT JOIN outcomes o ON p.id = o.prediction_id
                WHERE o.correct_24h IS NOT NULL
                GROUP BY p.source
                HAVING COUNT(*) >= ?
                ORDER BY (SUM(CASE WHEN o.correct_24h = 1 THEN 1.0 ELSE 0 END) / COUNT(*)) DESC
            """,
                (min_predictions,),
            )

            stats = []
            for row in cursor.fetchall():
                (
                    source,
                    total,
                    c1h,
                    c4h,
                    c24h,
                    avg_conf,
                    total_bull,
                    correct_bull,
                    total_bear,
                    correct_bear,
                ) = row

                stats.append(
                    SourceStats(
                        source=source,
                        total_predictions=total,
                        correct_1h=c1h or 0,
                        correct_4h=c4h or 0,
                        correct_24h=c24h or 0,
                        accuracy_1h=(c1h / total * 100) if total > 0 else 0,
                        accuracy_4h=(c4h / total * 100) if total > 0 else 0,
                        accuracy_24h=(c24h / total * 100) if total > 0 else 0,
                        avg_confidence=avg_conf or 0,
                        bullish_accuracy=(correct_bull / total_bull * 100)
                        if total_bull > 0
                        else 0,
                        bearish_accuracy=(correct_bear / total_bear * 100)
                        if total_bear > 0
                        else 0,
                    )
                )

            return stats

        finally:
            conn.close()

    def get_pending_outcomes(self, hours: int = 1) -> list[tuple]:
        """
        Get predictions that need outcome updates.

        Returns list of (prediction_id, symbol, created_at)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cutoff = datetime.now() - timedelta(hours=hours)
            column = f"price_after_{hours}h"

            cursor.execute(
                f"""
                SELECT p.id, p.symbol, p.created_at
                FROM predictions p
                LEFT JOIN outcomes o ON p.id = o.prediction_id
                WHERE p.created_at < ?
                AND (o.{column} IS NULL OR o.prediction_id IS NULL)
            """,
                (cutoff,),
            )

            return cursor.fetchall()

        finally:
            conn.close()

    def get_recent_predictions(self, symbol: str = None, limit: int = 50) -> list[dict]:
        """Get recent predictions with outcomes."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            if symbol:
                cursor.execute(
                    """
                    SELECT p.*, o.pct_change_1h, o.pct_change_24h,
                           o.correct_1h, o.correct_24h
                    FROM predictions p
                    LEFT JOIN outcomes o ON p.id = o.prediction_id
                    WHERE p.symbol = ?
                    ORDER BY p.created_at DESC
                    LIMIT ?
                """,
                    (symbol, limit),
                )
            else:
                cursor.execute(
                    """
                    SELECT p.*, o.pct_change_1h, o.pct_change_24h,
                           o.correct_1h, o.correct_24h
                    FROM predictions p
                    LEFT JOIN outcomes o ON p.id = o.prediction_id
                    ORDER BY p.created_at DESC
                    LIMIT ?
                """,
                    (limit,),
                )

            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def generate_report(self) -> str:
        """Generate a text report of source accuracy."""
        stats = self.get_source_stats(min_predictions=5)

        if not stats:
            return "No data available yet. Need more predictions with outcomes."

        report = "News Source Accuracy Report\n"
        report += "=" * 60 + "\n\n"

        report += f"{'Source':<25} {'Total':>6} {'1h':>8} {'4h':>8} {'24h':>8}\n"
        report += "-" * 60 + "\n"

        for s in stats:
            report += f"{s.source[:24]:<25} {s.total_predictions:>6} "
            report += f"{s.accuracy_1h:>7.1f}% {s.accuracy_4h:>7.1f}% {s.accuracy_24h:>7.1f}%\n"

        report += "\n"

        # Best and worst
        if len(stats) >= 2:
            best = stats[0]
            worst = stats[-1]
            report += f"Best Source (24h): {best.source} ({best.accuracy_24h:.1f}%)\n"
            report += (
                f"Worst Source (24h): {worst.source} ({worst.accuracy_24h:.1f}%)\n"
            )

        return report

"""
Signal Logger
=============

Tracks scanner signals and validates them against actual price movements.
Helps calculate prediction accuracy over time.

Usage:
    python signal_logger.py --summary          # Show accuracy stats
    python signal_logger.py --validate         # Update outcomes for past signals
    python signal_logger.py --recent 20        # Show recent signals
"""

import argparse
import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import ccxt

DB_PATH = Path(__file__).parent / "data" / "signals.db"


def init_db():
    """Initialize the signals database."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal TEXT NOT NULL,
            strength INTEGER,
            price REAL NOT NULL,
            rsi REAL,
            indicators TEXT,
            timeframe TEXT,
            strategy TEXT,
            -- Outcome tracking
            outcome_checked INTEGER DEFAULT 0,
            price_1h REAL,
            price_4h REAL,
            price_24h REAL,
            outcome TEXT,
            profit_pct REAL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON signals(timestamp)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_symbol ON signals(symbol)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_signal ON signals(signal)")
    conn.commit()
    conn.close()


def log_signal(
    symbol: str,
    signal: str,
    strength: int,
    price: float,
    rsi: float | None = None,
    indicators: dict | None = None,
    timeframe: str | None = None,
    strategy: str | None = None,
):
    """Log a new signal to the database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO signals (timestamp, symbol, signal, strength, price, rsi, indicators, timeframe, strategy)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(tz=UTC).isoformat(),
            symbol,
            signal,
            strength,
            price,
            rsi,
            json.dumps(indicators) if indicators else None,
            timeframe,
            strategy,
        ),
    )
    conn.commit()
    conn.close()


def validate_signals(exchange: ccxt.Exchange | None = None):
    """Check outcomes for signals that are old enough."""
    if exchange is None:
        exchange = ccxt.kraken()

    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get signals older than 24h that haven't been validated
    cutoff = (datetime.now(tz=UTC) - timedelta(hours=24)).isoformat()
    signals = conn.execute(
        """
        SELECT * FROM signals
        WHERE outcome_checked = 0 AND timestamp < ?
        AND signal IN ('BUY', 'SELL')
        """,
        (cutoff,),
    ).fetchall()

    print(f"Validating {len(signals)} signals...")
    validated = 0

    for sig in signals:
        symbol = sig["symbol"]
        signal_type = sig["signal"]
        entry_price = sig["price"]
        signal_time = datetime.fromisoformat(sig["timestamp"])

        try:
            # Fetch current price
            ticker = exchange.fetch_ticker(symbol)
            current_price = ticker["last"]

            # Calculate price change
            price_change_pct = ((current_price - entry_price) / entry_price) * 100

            # Determine if signal was correct
            if signal_type == "BUY":
                # BUY is correct if price went UP
                outcome = "CORRECT" if price_change_pct > 0 else "WRONG"
            else:  # SELL
                # SELL is correct if price went DOWN
                outcome = "CORRECT" if price_change_pct < 0 else "WRONG"

            # Update the record
            conn.execute(
                """
                UPDATE signals
                SET outcome_checked = 1, price_24h = ?, outcome = ?, profit_pct = ?
                WHERE id = ?
                """,
                (current_price, outcome, price_change_pct, sig["id"]),
            )
            validated += 1
            print(f"  {symbol} {signal_type} @ ${entry_price:.4f} -> ${current_price:.4f} ({price_change_pct:+.2f}%) = {outcome}")

        except Exception as e:
            print(f"  {symbol}: Error - {e}")

    conn.commit()
    conn.close()
    print(f"\nValidated {validated} signals")


def get_accuracy_stats() -> dict:
    """Calculate accuracy statistics."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    stats = {
        "total_signals": 0,
        "validated": 0,
        "correct": 0,
        "wrong": 0,
        "accuracy_pct": 0.0,
        "by_signal": {},
        "by_symbol": {},
    }

    # Overall stats
    row = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE signal IN ('BUY', 'SELL')").fetchone()
    stats["total_signals"] = row["cnt"]

    row = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE outcome_checked = 1").fetchone()
    stats["validated"] = row["cnt"]

    row = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE outcome = 'CORRECT'").fetchone()
    stats["correct"] = row["cnt"]

    row = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE outcome = 'WRONG'").fetchone()
    stats["wrong"] = row["cnt"]

    if stats["validated"] > 0:
        stats["accuracy_pct"] = (stats["correct"] / stats["validated"]) * 100

    # By signal type
    for signal_type in ["BUY", "SELL"]:
        rows = conn.execute(
            """
            SELECT outcome, COUNT(*) as cnt
            FROM signals
            WHERE signal = ? AND outcome_checked = 1
            GROUP BY outcome
            """,
            (signal_type,),
        ).fetchall()
        correct = sum(r["cnt"] for r in rows if r["outcome"] == "CORRECT")
        total = sum(r["cnt"] for r in rows)
        stats["by_signal"][signal_type] = {
            "total": total,
            "correct": correct,
            "accuracy_pct": (correct / total * 100) if total > 0 else 0,
        }

    # By symbol (top 10)
    rows = conn.execute(
        """
        SELECT symbol,
               SUM(CASE WHEN outcome = 'CORRECT' THEN 1 ELSE 0 END) as correct,
               COUNT(*) as total
        FROM signals
        WHERE outcome_checked = 1
        GROUP BY symbol
        ORDER BY total DESC
        LIMIT 10
        """
    ).fetchall()
    for r in rows:
        stats["by_symbol"][r["symbol"]] = {
            "total": r["total"],
            "correct": r["correct"],
            "accuracy_pct": (r["correct"] / r["total"] * 100) if r["total"] > 0 else 0,
        }

    conn.close()
    return stats


def get_recent_signals(limit: int = 20) -> list[dict]:
    """Get recent signals."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """
        SELECT * FROM signals
        WHERE signal IN ('BUY', 'SELL')
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    signals = [dict(r) for r in rows]
    conn.close()
    return signals


def print_summary():
    """Print accuracy summary."""
    stats = get_accuracy_stats()

    print("\n" + "=" * 60)
    print("SIGNAL ACCURACY REPORT")
    print("=" * 60)

    print(f"\nTotal Signals: {stats['total_signals']}")
    print(f"Validated:     {stats['validated']}")
    print(f"Pending:       {stats['total_signals'] - stats['validated']}")

    if stats["validated"] > 0:
        print(f"\nOverall Accuracy: {stats['accuracy_pct']:.1f}%")
        print(f"  Correct: {stats['correct']}")
        print(f"  Wrong:   {stats['wrong']}")

        print("\nBy Signal Type:")
        print("-" * 40)
        for sig_type, data in stats["by_signal"].items():
            print(f"  {sig_type:6} | {data['correct']:3}/{data['total']:3} = {data['accuracy_pct']:5.1f}%")

        if stats["by_symbol"]:
            print("\nBy Symbol (Top 10):")
            print("-" * 40)
            for symbol, data in stats["by_symbol"].items():
                print(f"  {symbol:12} | {data['correct']:3}/{data['total']:3} = {data['accuracy_pct']:5.1f}%")
    else:
        print("\nNo validated signals yet. Run --validate after 24h.")

    print("=" * 60)


def print_recent(limit: int = 20):
    """Print recent signals."""
    signals = get_recent_signals(limit)

    print("\n" + "=" * 70)
    print(f"RECENT SIGNALS (Last {limit})")
    print("=" * 70)
    print(f"{'Time':20} | {'Symbol':12} | {'Signal':6} | {'Price':>10} | {'RSI':>5} | {'Outcome':8}")
    print("-" * 70)

    for sig in signals:
        ts = sig["timestamp"][:19].replace("T", " ")
        outcome = sig["outcome"] or "pending"
        rsi = f"{sig['rsi']:.1f}" if sig["rsi"] else "-"
        print(f"{ts:20} | {sig['symbol']:12} | {sig['signal']:6} | ${sig['price']:>9.4f} | {rsi:>5} | {outcome:8}")

    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Signal Logger")
    parser.add_argument("--summary", action="store_true", help="Show accuracy stats")
    parser.add_argument("--validate", action="store_true", help="Validate old signals")
    parser.add_argument("--recent", type=int, metavar="N", help="Show recent N signals")

    args = parser.parse_args()

    if args.validate:
        validate_signals()
    elif args.recent:
        print_recent(args.recent)
    elif args.summary:
        print_summary()
    else:
        print_summary()

"""
Discord Poster
==============

Posts trading signals and updates to Discord via webhook.

Setup:
1. In Discord: Server Settings > Integrations > Webhooks > New Webhook
2. Copy the webhook URL
3. Add to .env: DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

Usage:
    python discord_poster.py --signal          # Post latest signals
    python discord_poster.py --promo           # Post promo/ad
    python discord_poster.py --stats           # Post signal accuracy stats
"""

import argparse
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DB_PATH = Path(__file__).parent / "data" / "signals.db"


def post_to_discord(content: str = None, embed: dict = None):
    """Send a message to Discord webhook."""
    if not WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL not set in .env")
        print("Get it from: Discord Server Settings > Integrations > Webhooks")
        return False

    payload = {"thread_name": "GridBot Chuck Signals"}
    if content:
        payload["content"] = content
    if embed:
        payload["embeds"] = [embed]

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 204:
            print("Posted to Discord successfully!")
            return True
        else:
            print(f"Discord error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Error posting to Discord: {e}")
        return False


def post_signals():
    """Post latest trading signals to Discord."""
    if not DB_PATH.exists():
        print("No signals database found. Run the scanner first.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get latest signals (last scan)
    signals = conn.execute("""
        SELECT * FROM signals
        WHERE signal IN ('BUY', 'SELL')
        ORDER BY timestamp DESC
        LIMIT 15
    """).fetchall()
    conn.close()

    if not signals:
        print("No signals to post.")
        return

    # Build embed
    buy_signals = [s for s in signals if s["signal"] == "BUY"]
    sell_signals = [s for s in signals if s["signal"] == "SELL"]

    fields = []

    if buy_signals:
        buy_text = "\n".join([
            f"**{s['symbol']}** @ ${s['price']:.4f} (RSI: {s['rsi']:.1f})"
            for s in buy_signals[:5]
        ])
        fields.append({
            "name": "🟢 BUY Signals",
            "value": buy_text or "None",
            "inline": True
        })

    if sell_signals:
        sell_text = "\n".join([
            f"**{s['symbol']}** @ ${s['price']:.4f} (RSI: {s['rsi']:.1f})"
            for s in sell_signals[:5]
        ])
        fields.append({
            "name": "🔴 SELL Signals",
            "value": sell_text or "None",
            "inline": True
        })

    embed = {
        "title": "📊 GridBot Chuck - Live Signals",
        "description": "Scanning 15 crypto + 5 stocks with per-asset optimized settings",
        "color": 0x00ff00 if buy_signals else 0xff0000,
        "fields": fields,
        "footer": {
            "text": "github.com/splinkjc-alt/gridbotchuck"
        },
        "timestamp": datetime.now(tz=UTC).isoformat()
    }

    post_to_discord(embed=embed)


def post_promo():
    """Post promotional message to Discord."""
    embed = {
        "title": "🤖 GridBot Chuck - Open Source Trading Bot",
        "description": (
            "A trading bot that optimizes itself for **each coin**.\n\n"
            "No more one-size-fits-all settings. BTC gets different indicators than DOGE.\n\n"
            "**Features:**\n"
            "• Tests 60+ combinations per asset\n"
            "• Finds optimal timeframe & indicators via backtesting\n"
            "• Scans 20 assets with individual configs\n"
            "• Tracks signal accuracy\n\n"
            "**Recent Backtest Results:**\n"
            "• APT: +22.9% (1h, RSI+EMA)\n"
            "• LINK: +17.9% (1h, RSI+BB)\n"
            "• SOL: +15.9% (1h, RSI+BB)\n\n"
            "Open source. Python. Free."
        ),
        "color": 0x5865F2,
        "fields": [
            {
                "name": "🔗 GitHub",
                "value": "[splinkjc-alt/gridbotchuck](https://github.com/splinkjc-alt/gridbotchuck)",
                "inline": True
            }
        ],
        "footer": {
            "text": "⚠️ Not financial advice. Paper trading. DYOR."
        }
    }

    post_to_discord(embed=embed)


def post_stats():
    """Post signal accuracy stats to Discord."""
    if not DB_PATH.exists():
        print("No signals database found.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    total = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE signal IN ('BUY', 'SELL')").fetchone()["cnt"]
    validated = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE outcome_checked = 1").fetchone()["cnt"]
    correct = conn.execute("SELECT COUNT(*) as cnt FROM signals WHERE outcome = 'CORRECT'").fetchone()["cnt"]

    conn.close()

    accuracy = (correct / validated * 100) if validated > 0 else 0

    embed = {
        "title": "📈 GridBot Chuck - Signal Accuracy",
        "color": 0x00ff00 if accuracy >= 60 else 0xffaa00 if accuracy >= 50 else 0xff0000,
        "fields": [
            {"name": "Total Signals", "value": str(total), "inline": True},
            {"name": "Validated", "value": str(validated), "inline": True},
            {"name": "Accuracy", "value": f"{accuracy:.1f}%", "inline": True},
            {"name": "Correct", "value": str(correct), "inline": True},
            {"name": "Wrong", "value": str(validated - correct), "inline": True},
            {"name": "Pending", "value": str(total - validated), "inline": True},
        ],
        "footer": {
            "text": "github.com/splinkjc-alt/gridbotchuck"
        },
        "timestamp": datetime.now(tz=UTC).isoformat()
    }

    post_to_discord(embed=embed)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Discord Poster")
    parser.add_argument("--signal", action="store_true", help="Post latest signals")
    parser.add_argument("--promo", action="store_true", help="Post promotional message")
    parser.add_argument("--stats", action="store_true", help="Post accuracy stats")
    parser.add_argument("--test", action="store_true", help="Test webhook connection")

    args = parser.parse_args()

    if args.test:
        post_to_discord(content="🤖 GridBot Chuck webhook test - connection successful!")
    elif args.signal:
        post_signals()
    elif args.promo:
        post_promo()
    elif args.stats:
        post_stats()
    else:
        print("Usage:")
        print("  python discord_poster.py --signal   # Post latest signals")
        print("  python discord_poster.py --promo    # Post promo/ad")
        print("  python discord_poster.py --stats    # Post accuracy stats")
        print("  python discord_poster.py --test     # Test webhook")

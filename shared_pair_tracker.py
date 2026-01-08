"""
Shared Pair Tracker
===================

Allows multiple bots to coordinate and avoid trading the same pairs.
Uses a JSON file to track which bot is trading which pair.

Usage:
    tracker = SharedPairTracker()

    # Bot claims a pair
    tracker.claim_pair("chuck", "ADA/USD")

    # Another bot checks what to avoid
    avoid = tracker.get_other_pairs("growler")  # Returns ["ADA/USD"]

    # Bot releases pair
    tracker.release_pair("chuck")
"""

import json
import logging
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SharedPairTracker:
    """
    Tracks which pairs each bot is trading to prevent conflicts.
    """

    def __init__(self, tracker_file: str = "data/active_pairs.json"):
        self.tracker_file = Path(tracker_file)
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create tracker file if it doesn't exist."""
        if not self.tracker_file.exists():
            self._save({})

    def _load(self) -> dict:
        """Load current tracking data."""
        try:
            with open(self.tracker_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save(self, data: dict):
        """Save tracking data."""
        with open(self.tracker_file, 'w') as f:
            json.dump(data, f, indent=2)

    def claim_pair(self, bot_name: str, pair: str):
        """
        Claim a pair for a bot.

        Args:
            bot_name: Name of the bot claiming the pair
            pair: Trading pair (e.g., "ADA/USD")
        """
        data = self._load()
        data[bot_name] = {
            "pair": pair,
            "claimed_at": time.time(),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._save(data)
        logger.info(f"[TRACKER] {bot_name} claimed {pair}")

    def release_pair(self, bot_name: str):
        """
        Release a bot's pair claim.

        Args:
            bot_name: Name of the bot releasing its pair
        """
        data = self._load()
        if bot_name in data:
            old_pair = data[bot_name].get("pair", "unknown")
            del data[bot_name]
            self._save(data)
            logger.info(f"[TRACKER] {bot_name} released {old_pair}")

    def get_pair(self, bot_name: str) -> Optional[str]:
        """
        Get the pair a specific bot is trading.

        Args:
            bot_name: Name of the bot

        Returns:
            The pair being traded, or None
        """
        data = self._load()
        bot_data = data.get(bot_name, {})
        return bot_data.get("pair")

    def get_other_pairs(self, bot_name: str, stale_hours: float = 6) -> list:
        """
        Get pairs being traded by OTHER bots (to avoid).

        Args:
            bot_name: The calling bot's name (will be excluded)
            stale_hours: Ignore claims older than this (bot might have crashed)

        Returns:
            List of pairs to avoid
        """
        data = self._load()
        avoid_pairs = []
        current_time = time.time()
        stale_seconds = stale_hours * 3600

        for other_bot, bot_data in data.items():
            if other_bot == bot_name:
                continue

            pair = bot_data.get("pair")
            claimed_at = bot_data.get("claimed_at", 0)

            # Skip stale claims
            if current_time - claimed_at > stale_seconds:
                logger.debug(f"[TRACKER] Ignoring stale claim: {other_bot} -> {pair}")
                continue

            if pair:
                avoid_pairs.append(pair)
                logger.info(f"[TRACKER] {bot_name} should avoid {pair} (claimed by {other_bot})")

        return avoid_pairs

    def get_all_active(self) -> dict:
        """
        Get all active pair claims.

        Returns:
            Dict of bot_name -> pair info
        """
        return self._load()

    def is_pair_available(self, pair: str, requester: str = None, stale_hours: float = 6) -> bool:
        """
        Check if a pair is available to trade.

        Args:
            pair: The pair to check
            requester: The bot asking (will ignore its own claim)
            stale_hours: Ignore claims older than this

        Returns:
            True if pair is available
        """
        data = self._load()
        current_time = time.time()
        stale_seconds = stale_hours * 3600

        for bot_name, bot_data in data.items():
            if bot_name == requester:
                continue

            claimed_pair = bot_data.get("pair")
            claimed_at = bot_data.get("claimed_at", 0)

            if claimed_pair == pair and (current_time - claimed_at) < stale_seconds:
                return False

        return True


# Global instance for easy access
_tracker = None


def get_tracker() -> SharedPairTracker:
    """Get the global tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = SharedPairTracker()
    return _tracker


if __name__ == "__main__":
    # Demo
    print("Shared Pair Tracker Demo")
    print("-" * 40)

    tracker = SharedPairTracker("data/test_pairs.json")

    # Chuck claims ADA
    tracker.claim_pair("chuck", "ADA/USD")

    # Growler claims PEPE
    tracker.claim_pair("growler", "PEPE/USD")

    # Check active pairs
    print("\nActive pairs:", tracker.get_all_active())

    # Chuck checks what to avoid
    avoid = tracker.get_other_pairs("chuck")
    print(f"\nChuck should avoid: {avoid}")

    # Growler checks what to avoid
    avoid = tracker.get_other_pairs("growler")
    print(f"Growler should avoid: {avoid}")

    # Is VET available?
    print(f"\nVET/USD available: {tracker.is_pair_available('VET/USD')}")
    print(f"ADA/USD available: {tracker.is_pair_available('ADA/USD')}")

    # Chuck releases
    tracker.release_pair("chuck")
    print(f"\nAfter Chuck releases: ADA/USD available: {tracker.is_pair_available('ADA/USD')}")

"""
Bot Watchdog - Auto-restart frozen bots
=======================================
Monitors bot processes and restarts them if they freeze or crash.
Saves state so bots resume with same pairs.
"""

import json
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/watchdog.log"), logging.StreamHandler()],
)
logger = logging.getLogger("Watchdog")

# State file to track bot status
STATE_FILE = Path("data/watchdog_state.json")

# Bot configurations
BOTS = {
    "crosskiller": {
        "script": "run_crosskiller_daytrader.py",
        "log_file": "logs/crosskiller_paper.log",
        "args": ["--paper"],  # Paper mode for testing
        "enabled": True,
        "max_stale_minutes": 5,  # Restart if no log activity for 5 min
    },
    "vet_momentum": {
        "script": "run_vet_momentum.py",
        "log_file": "logs/vet_momentum.log",
        "args": [],
        "enabled": False,  # Disabled - Kraken API issues
        "max_stale_minutes": 10,
    },
    "pepe_momentum": {
        "script": "run_pepe_momentum.py",
        "log_file": "logs/pepe_momentum.log",
        "args": [],
        "enabled": False,  # Disabled - Kraken API issues
        "max_stale_minutes": 10,
    },
}


def load_state() -> dict:
    """Load watchdog state from file."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"bots": {}, "last_check": None}


def save_state(state: dict):
    """Save watchdog state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def get_log_age_minutes(log_file: str) -> float:
    """Get how many minutes since log file was last modified."""
    log_path = Path(log_file)
    if not log_path.exists():
        return float("inf")

    mtime = datetime.fromtimestamp(log_path.stat().st_mtime)
    age = datetime.now() - mtime
    return age.total_seconds() / 60


def is_bot_frozen(bot_name: str, config: dict) -> bool:
    """Check if bot appears frozen (no recent log activity)."""
    log_age = get_log_age_minutes(config["log_file"])
    max_stale = config.get("max_stale_minutes", 5)

    if log_age > max_stale:
        logger.warning(
            f"{bot_name}: Log stale for {log_age:.1f} min (max: {max_stale})"
        )
        return True
    return False


def check_log_for_errors(log_file: str, lines: int = 20) -> bool:
    """Check recent log lines for repeated errors."""
    log_path = Path(log_file)
    if not log_path.exists():
        return False

    try:
        with open(log_path, "r") as f:
            # Read last N lines
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) >= lines else all_lines

            # Count error lines
            error_count = sum(1 for line in recent if "ERROR" in line)

            # If more than 80% are errors, bot is probably stuck
            if error_count > lines * 0.8:
                return True
    except Exception:
        pass
    return False


def start_bot(bot_name: str, config: dict) -> bool:
    """Start a bot process."""
    script = config["script"]
    args = config.get("args", [])

    if not Path(script).exists():
        logger.error(f"{bot_name}: Script not found: {script}")
        return False

    try:
        cmd = [sys.executable, script] + args
        log_file = config["log_file"]

        # Start process with output to log file
        with open(log_file, "a") as log:
            log.write(f"\n{'='*60}\n")
            log.write(f"WATCHDOG RESTART: {datetime.now()}\n")
            log.write(f"{'='*60}\n")

        process = subprocess.Popen(
            cmd,
            stdout=open(log_file, "a"),
            stderr=subprocess.STDOUT,
            cwd=str(Path(__file__).parent),
        )

        logger.info(f"{bot_name}: Started (PID: {process.pid})")
        return True

    except Exception as e:
        logger.error(f"{bot_name}: Failed to start: {e}")
        return False


def restart_bot(bot_name: str, config: dict, state: dict) -> bool:
    """Restart a frozen bot."""
    logger.info(f"{bot_name}: Restarting...")

    # Record restart in state
    if bot_name not in state["bots"]:
        state["bots"][bot_name] = {"restarts": 0, "last_restart": None}

    state["bots"][bot_name]["restarts"] += 1
    state["bots"][bot_name]["last_restart"] = datetime.now().isoformat()
    save_state(state)

    return start_bot(bot_name, config)


def run_watchdog(check_interval: int = 60):
    """Main watchdog loop."""
    logger.info("=" * 60)
    logger.info("BOT WATCHDOG STARTED")
    logger.info("=" * 60)
    logger.info(f"Monitoring: {[b for b, c in BOTS.items() if c['enabled']]}")
    logger.info(f"Check interval: {check_interval}s")
    logger.info("=" * 60)

    state = load_state()

    while True:
        try:
            for bot_name, config in BOTS.items():
                if not config.get("enabled", True):
                    continue

                # Check if bot is frozen
                if is_bot_frozen(bot_name, config):
                    # Double-check with error analysis
                    if check_log_for_errors(config["log_file"]):
                        logger.warning(f"{bot_name}: Stuck in error loop")

                    # Restart the bot
                    restart_bot(bot_name, config, state)

                    # Wait a bit after restart
                    time.sleep(10)
                else:
                    log_age = get_log_age_minutes(config["log_file"])
                    logger.debug(f"{bot_name}: OK (log age: {log_age:.1f}m)")

            state["last_check"] = datetime.now().isoformat()
            save_state(state)

        except Exception as e:
            logger.error(f"Watchdog error: {e}")

        time.sleep(check_interval)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Bot Watchdog")
    parser.add_argument(
        "--interval", type=int, default=60, help="Check interval in seconds"
    )
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    args = parser.parse_args()

    if args.once:
        # Single check mode
        state = load_state()
        for bot_name, config in BOTS.items():
            if config.get("enabled", True):
                if is_bot_frozen(bot_name, config):
                    restart_bot(bot_name, config, state)
                else:
                    print(f"{bot_name}: OK")
    else:
        run_watchdog(args.interval)

"""Bot Watchdog - Background Launcher

Runs the bot watchdog as a background process (no console window).
Uses .pyw extension to run without console on Windows.
"""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPT_DIR / ".venv" / "Scripts" / "pythonw.exe"
SYSTEM_PYTHON = "pythonw"
WATCHDOG_SCRIPT = SCRIPT_DIR / "bot_watchdog.py"

# Use venv python if available, otherwise system
python_exe = str(VENV_PYTHON) if VENV_PYTHON.exists() else SYSTEM_PYTHON

subprocess.Popen(
    [python_exe, str(WATCHDOG_SCRIPT)],
    cwd=str(SCRIPT_DIR),
    creationflags=subprocess.CREATE_NO_WINDOW
)

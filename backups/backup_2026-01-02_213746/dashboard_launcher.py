from __future__ import annotations

import argparse
import logging
from pathlib import Path
import subprocess
import sys
import threading
import time
from typing import TYPE_CHECKING
import webbrowser

import requests
from requests import RequestException

LOGGER = logging.getLogger(__name__)

try:
    from PIL import Image, ImageDraw
except ImportError:
    Image = ImageDraw = None  # type: ignore[assignment]
    LOGGER.warning("Note: Pillow is not installed; tray icon graphics are unavailable.")

if TYPE_CHECKING:  # pragma: no cover - imported for type checkers only
    from PIL.Image import Image as PILImage

HAS_PYSTRAY = False

try:  # Optional dependency used for the system tray icon
    from pystray import Icon, Menu, MenuItem

    HAS_PYSTRAY = True
except ImportError:
    LOGGER.warning("Note: For system tray icon, install: pip install pystray pillow")


class DashboardLauncher:
    """Manage bot lifecycle and launch the dashboard UI."""

    def __init__(self, port: int, config_path: str) -> None:
        self.port = port
        self.config_path = config_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self.dashboard_url = f"http://localhost:{port}"
        self.bot_process: subprocess.Popen[str] | None = None
        self._opener_thread: threading.Thread | None = None

    def _build_bot_command(self) -> list[str] | None:
        """Construct a sanitized command to launch the bot process."""
        try:
            main_script_path = Path("main.py").resolve(strict=True)
        except FileNotFoundError:
            self.logger.error("main.py not found in the current working directory.")
            return None

        try:
            config_path = Path(self.config_path).resolve(strict=True)
        except FileNotFoundError:
            self.logger.error("Config file not found at %s", self.config_path)
            return None

        unsafe_tokens = ("\n", "\r", "\x00")
        if any(token in str(config_path) for token in unsafe_tokens):
            self.logger.error("Config file path contains unsafe characters and cannot be used.")
            return None

        return [sys.executable, str(main_script_path), "--config", str(config_path), "--wait-for-start"]

    def _validate_command(self, command: list[str]) -> bool:
        """Ensure the launch command cannot execute untrusted input."""
        if not command:
            self.logger.error("Launch command is empty.")
            return False

        expected_executable = Path(sys.executable).resolve()
        actual_executable = Path(command[0]).resolve()
        if expected_executable != actual_executable:
            self.logger.error("Executable mismatch detected when preparing bot command.")
            return False

        unsafe_tokens = ("\n", "\r", "\x00", "&", "|", ";", ">", "<", "`")
        for arg in command[1:]:
            if any(token in arg for token in unsafe_tokens):
                self.logger.error("Unsafe token detected in command argument: %s", arg)
                return False
        return True

    def start_bot(self) -> None:
        """Start the trading bot in a background process."""
        if self.bot_process and self.bot_process.poll() is None:
            self.logger.info("Bot process already running (PID: %s)", self.bot_process.pid)
            return

        if self.check_api_running():
            self.logger.info("Bot API is already running. Skipping bot startup.")
            return

        command = self._build_bot_command()
        if command is None or not self._validate_command(command):
            return

        try:
            self.bot_process = subprocess.Popen(  # noqa: S603
                command,
                cwd=str(Path(command[1]).resolve().parent),
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.logger.info("Bot process started (PID: %s)", self.bot_process.pid)
        except Exception:
            self.logger.exception("Failed to start bot process.")
            self.bot_process = None

    def stop_bot(self) -> None:
        """Terminate the trading bot process if it is running."""
        if not self.bot_process:
            return

        if self.bot_process.poll() is not None:
            self.bot_process = None
            return

        self.logger.info("Stopping bot process...")
        self.bot_process.terminate()
        try:
            self.bot_process.wait(timeout=10)
            self.logger.info("Bot process terminated cleanly.")
        except subprocess.TimeoutExpired:
            self.logger.warning("Bot process did not terminate; killing now.")
            self.bot_process.kill()
        finally:
            self.bot_process = None

    def create_icon_image(self) -> PILImage:
        """Create a simple robot icon for the system tray."""
        if Image is None or ImageDraw is None:
            raise RuntimeError("Cannot create tray icon because Pillow is not installed.")

        size = 64
        img = Image.new("RGB", (size, size), color="black")
        draw = ImageDraw.Draw(img)

        draw.rectangle([10, 15, 54, 45], outline="lime", width=2)
        draw.ellipse([20, 22, 28, 30], fill="lime")
        draw.ellipse([36, 22, 44, 30], fill="lime")
        draw.arc([20, 30, 44, 40], 0, 180, fill="lime", width=2)
        draw.line([32, 15, 32, 5], fill="lime", width=2)
        draw.ellipse([28, 0, 36, 8], outline="lime", width=2)

        return img

    def check_api_running(self) -> bool:
        """Return True if the dashboard API responds to a health check."""
        try:
            response = requests.get(f"{self.dashboard_url}/api/health", timeout=2)
            return response.ok
        except RequestException as exc:
            self.logger.debug("Bot API health check failed: %s", exc)
            return False

    def wait_for_api(self, timeout: int = 30) -> bool:
        """Poll until the API is available or the timeout is reached."""
        self.logger.info("Waiting for bot API server to start on port %s...", self.port)
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.check_api_running():
                self.logger.info("Bot API server is running.")
                return True
            time.sleep(1)

        self.logger.error("Timeout waiting for API server after %s seconds.", timeout)
        return False

    def open_dashboard(self) -> None:
        """Open the dashboard UI in the user's default browser."""
        self.logger.info("Opening dashboard at %s", self.dashboard_url)
        webbrowser.open(self.dashboard_url, new=2, autoraise=True)

    def on_quit(self, icon, item) -> None:  # type: ignore[override]
        """Handle the system tray quit action."""
        self.logger.info("Closing dashboard launcher...")
        self.stop_bot()
        icon.stop()

    def on_open_dashboard(self, icon, item) -> None:  # type: ignore[override]
        """Handle the system tray open dashboard action."""
        self.open_dashboard()

    def on_status(self, icon, item) -> None:  # type: ignore[override]
        """Log current dashboard availability from the tray menu."""
        message = "Dashboard is running." if self.check_api_running() else "Dashboard is not responding."
        if hasattr(icon, "notify"):
            icon.notify(message)
        self.logger.info(message)

    def run_with_tray(self) -> None:
        """Run the launcher with a system tray icon."""
        if not HAS_PYSTRAY:
            self.logger.info("pystray not installed. Falling back to console mode.")
            self.run_simple()
            return

        if Image is None or ImageDraw is None:
            self.logger.warning("Pillow not installed. Falling back to console mode.")
            self.run_simple()
            return

        icon_image = self.create_icon_image()
        menu = Menu(
            MenuItem("Open Dashboard", self.on_open_dashboard),
            MenuItem("Check Status", self.on_status),
            MenuItem("Quit", self.on_quit),
        )

        icon = Icon("GridTradingBot", icon_image, menu=menu)
        self.logger.info("System tray icon created. Starting system tray...")

        self.start_bot()
        if self.bot_process:
            self._start_opener_thread()

        try:
            icon.run()
        finally:
            self.stop_bot()

    def run_simple(self) -> None:
        """Run the launcher without the optional tray icon."""
        self.logger.info("Grid Trading Bot Dashboard Launcher starting...")
        self.start_bot()
        if not self.bot_process:
            return

        if self.wait_for_api():
            self.open_dashboard()
            self.logger.info("Dashboard opened in your browser. Press Ctrl+C to exit.")
        else:
            self.logger.error("Could not connect to bot API server.")
            self.logger.warning("Ensure the bot is running: python main.py --config config/config.json")

        try:
            while self.bot_process and self.bot_process.poll() is None:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Launcher closed by user.")
        finally:
            self.stop_bot()

    def wait_and_open(self) -> None:
        """Wait for the API to be ready and open the dashboard once."""
        if self.wait_for_api():
            self.open_dashboard()

    def _start_opener_thread(self) -> None:
        """Start a background thread that waits for the API and opens the dashboard."""
        if self._opener_thread and self._opener_thread.is_alive():
            return
        self._opener_thread = threading.Thread(target=self.wait_and_open, name="dashboard-opener", daemon=True)
        self._opener_thread.start()


def main() -> None:
    """Command-line entry point for the launcher."""
    parser = argparse.ArgumentParser(description="Grid Trading Bot Dashboard Launcher")
    parser.add_argument("--port", type=int, default=8080, help="Bot API port (default: 8080)")
    parser.add_argument("--config", type=str, default="config/config.json", help="Path to config file")
    parser.add_argument("--no-tray", action="store_true", help="Run without system tray")
    parser.add_argument("--log-level", default="INFO", help="Logging level (default: INFO)")
    args = parser.parse_args()

    log_level_name = args.log_level.upper()
    if not hasattr(logging, log_level_name):
        parser.error(f"Invalid log level: {args.log_level}")

    logging.basicConfig(
        level=getattr(logging, log_level_name),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    launcher = DashboardLauncher(port=args.port, config_path=args.config)

    if args.no_tray or not HAS_PYSTRAY:
        launcher.run_simple()
    else:
        launcher.run_with_tray()


if __name__ == "__main__":
    main()

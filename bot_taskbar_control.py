"""
Grid Trading Bot - Taskbar Control Application
Provides system tray icon for easy on/off control of the bot
"""

import contextlib
from pathlib import Path
import sys
from threading import Event, Thread
import time
import webbrowser

from PIL import Image, ImageDraw
import pystray
import requests


class BotTaskbarControl:
    def __init__(self, host="localhost", port=8080):
        self.host = host
        self.port = port
        self.api_url = f"http://{self.host}:{self.port}"
        self.bot_process = None
        self.is_running = False
        self.stop_event = Event()
        self.icon = None

        # Get the bot directory
        self.bot_dir = Path(__file__).parent
        self.config_path = self.bot_dir / "config" / "config.json"

    def create_icon_image(self, status="idle"):
        """Create an icon image for the system tray"""
        # Create a simple colored square icon
        size = 64
        image = Image.new("RGB", (size, size), color="white")
        draw = ImageDraw.Draw(image)

        # Color based on status
        if status == "running":
            color = "green"
            text = "✓"
        elif status == "stopped":
            color = "red"
            text = "✗"
        else:  # paused or idle
            color = "orange"
            text = "⏸"

        # Draw background circle
        margin = 8
        draw.ellipse([margin, margin, size - margin, size - margin], fill=color, outline="black", width=2)

        # Draw text
        with contextlib.suppress(Exception):  # Font loading might fail on some systems
            draw.text((size // 2 - 6, size // 2 - 8), text, fill="white")

        return image

    def check_api_running(self):
        """Check if bot API is running"""
        try:
            response = requests.get(f"{self.api_url}/api/bot/status", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    def get_bot_status(self):
        """Get current bot status"""
        with contextlib.suppress(Exception):
            response = requests.get(f"{self.api_url}/api/bot/status", timeout=2)
            if response.status_code == 200:
                data = response.json()
                return data.get("status", "unknown")
        return "unknown"

    def start_bot(self):
        """Start the bot"""
        try:
            response = requests.post(f"{self.api_url}/api/bot/start", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def stop_bot(self):
        """Stop the bot"""
        try:
            response = requests.post(f"{self.api_url}/api/bot/stop", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def pause_bot(self):
        """Pause the bot"""
        try:
            response = requests.post(f"{self.api_url}/api/bot/pause", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def resume_bot(self):
        """Resume the bot"""
        try:
            response = requests.post(f"{self.api_url}/api/bot/resume", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def open_dashboard(self):
        """Open dashboard in browser"""
        webbrowser.open(self.api_url)

    def on_start_clicked(self, icon, item):
        """Handle start button click"""
        if self.start_bot():
            pass
        else:
            pass
        self.update_icon()

    def on_stop_clicked(self, icon, item):
        """Handle stop button click"""
        if self.stop_bot():
            pass
        else:
            pass
        self.update_icon()

    def on_pause_clicked(self, icon, item):
        """Handle pause button click"""
        if self.pause_bot():
            pass
        else:
            pass
        self.update_icon()

    def on_resume_clicked(self, icon, item):
        """Handle resume button click"""
        if self.resume_bot():
            pass
        else:
            pass
        self.update_icon()

    def on_dashboard_clicked(self, icon, item):
        """Handle dashboard button click"""
        self.open_dashboard()

    def on_quit_clicked(self, icon, item):
        """Handle quit button click"""
        self.stop_event.set()
        icon.stop()

    def update_icon(self):
        """Update the icon based on bot status"""
        status = self.get_bot_status()
        new_icon = self.create_icon_image(status)
        if self.icon:
            self.icon.icon = new_icon

    def update_status_thread(self):
        """Periodically update status"""
        while not self.stop_event.is_set():
            self.update_icon()
            time.sleep(2)

    def run(self):
        """Run the system tray application"""

        # Check if API is running
        if not self.check_api_running():

            for _i in range(30):
                if self.check_api_running():
                    break
                time.sleep(1)
            else:
                return


        # Create the menu
        menu = pystray.Menu(
            pystray.MenuItem("Dashboard", self.on_dashboard_clicked),
            pystray.MenuItem("-", None),
            pystray.MenuItem("▶ Start", self.on_start_clicked),
            pystray.MenuItem("⏸ Pause", self.on_pause_clicked),
            pystray.MenuItem("▶ Resume", self.on_resume_clicked),
            pystray.MenuItem("⏹ Stop", self.on_stop_clicked),
            pystray.MenuItem("-", None),
            pystray.MenuItem("Quit", self.on_quit_clicked),
        )

        # Create initial icon
        initial_icon = self.create_icon_image("idle")

        # Create the tray icon
        self.icon = pystray.Icon(
            "Grid Trading Bot", initial_icon, title="Grid Trading Bot - Click to control", menu=menu
        )

        # Start the status update thread
        update_thread = Thread(target=self.update_status_thread, daemon=True)
        update_thread.start()


        # Run the icon
        self.icon.run()


def main():
    """Main entry point"""
    try:
        # Check if pystray and pillow are installed
        from PIL import Image
        import pystray
    except ImportError:
        return 1

    # Create and run the control app
    controller = BotTaskbarControl()
    controller.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

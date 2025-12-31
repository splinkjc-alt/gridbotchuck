#!/usr/bin/env python3
"""
GridBot Pro - Beta Program Manager

Simple tool to manage beta signups and generate beta license keys.
Run this script to:
  1. Generate beta keys for email addresses
  2. View all beta signups
  3. Export beta testers list

Usage:
    python beta_manager.py generate user@example.com
    python beta_manager.py list
    python beta_manager.py export
"""

import argparse
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.licensing.license_manager import LicenseManager, LicenseType


class BetaManager:
    """Manages beta program signups and license generation."""

    SIGNUPS_FILE = Path(__file__).parent / "beta_signups.json"

    def __init__(self):
        self.license_manager = LicenseManager()
        self.signups = self._load_signups()

    def _load_signups(self) -> dict:
        """Load existing signups from file."""
        if self.SIGNUPS_FILE.exists():
            with open(self.SIGNUPS_FILE) as f:
                return json.load(f)
        return {"signups": [], "generated_keys": {}}

    def _save_signups(self):
        """Save signups to file."""
        with open(self.SIGNUPS_FILE, "w") as f:
            json.dump(self.signups, f, indent=2, default=str)

    def add_signup(self, email: str) -> bool:
        """Add a new beta signup."""
        email = email.lower().strip()

        if email in [s["email"] for s in self.signups["signups"]]:
            return False

        self.signups["signups"].append(
            {
                "email": email,
                "signup_date": datetime.now().isoformat(),
                "key_generated": False,
            }
        )
        self._save_signups()
        return True

    def generate_beta_key(self, email: str, machine_id: str | None = None) -> str:
        """Generate a beta license key for an email."""
        email = email.lower().strip()

        # Generate the key
        key = self.license_manager.generate_license_key(
            license_type=LicenseType.BETA,
            customer_email=email,
            machine_id=machine_id,  # None = not hardware-locked for beta
            expiry_days=14,
        )

        # Record the key generation
        self.signups["generated_keys"][email] = {
            "key": key,
            "generated_date": datetime.now().isoformat(),
            "expires": (datetime.now() + timedelta(days=14)).isoformat(),
        }

        # Update signup record
        for signup in self.signups["signups"]:
            if signup["email"] == email:
                signup["key_generated"] = True
                break
        else:
            # Add to signups if not already there
            self.add_signup(email)

        self._save_signups()
        return key

    def list_signups(self):
        """List all beta signups."""
        if not self.signups["signups"]:
            return


        for _i, signup in enumerate(self.signups["signups"], 1):
            "🔑 Key Generated" if signup["key_generated"] else "⏳ Awaiting Key"
            datetime.fromisoformat(signup["signup_date"]).strftime("%Y-%m-%d %H:%M")


    def export_signups(self, filename: str = "beta_testers.csv"):
        """Export signups to CSV."""
        filepath = Path(__file__).parent / filename

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Signup Date", "Key Generated", "Expires"])

            for signup in self.signups["signups"]:
                key_info = self.signups["generated_keys"].get(signup["email"], {})
                expires = key_info.get("expires", "N/A")
                writer.writerow(
                    [
                        signup["email"],
                        signup["signup_date"],
                        signup["key_generated"],
                        expires,
                    ]
                )



def main():
    parser = argparse.ArgumentParser(
        description="GridBot Pro Beta Program Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python beta_manager.py generate user@example.com    Generate beta key for user
  python beta_manager.py add user@example.com         Add user to waitlist (no key yet)
  python beta_manager.py list                         Show all signups
  python beta_manager.py export                       Export to CSV

The generated keys should be sent to users along with download instructions.
Beta keys are valid for 14 days from generation.
        """,
    )

    parser.add_argument("command", choices=["generate", "add", "list", "export"], help="Command to run")
    parser.add_argument("email", nargs="?", help="Email address (required for generate/add commands)")
    parser.add_argument("--machine-id", help="Optional machine ID to lock the key to specific hardware")

    args = parser.parse_args()
    manager = BetaManager()

    if args.command == "generate":
        if not args.email:
            sys.exit(1)

        manager.generate_beta_key(args.email, args.machine_id)

    elif args.command == "add":
        if not args.email:
            sys.exit(1)
        manager.add_signup(args.email)

    elif args.command == "list":
        manager.list_signups()

    elif args.command == "export":
        manager.export_signups()


if __name__ == "__main__":
    main()

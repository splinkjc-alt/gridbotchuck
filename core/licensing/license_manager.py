"""
GridBot Pro - License Manager
Validates and manages software licenses for commercial distribution.
"""

from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import platform

logger = logging.getLogger(__name__)


class LicenseType:
    """License tier definitions."""

    TRIAL = "trial"
    BETA = "beta"  # Free beta access for early testers
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseManager:
    """
    Manages license validation for GridBot Pro.

    Features:
    - Hardware-bound license keys
    - Expiration date validation
    - Feature gating by license tier
    - Offline validation (no server required for basic checks)
    """

    # Secret key for HMAC signing (in production, use environment variable)
    _SECRET_KEY = os.environ.get("GRIDBOT_LICENSE_SECRET", "your-secret-key-here")

    # License file location
    LICENSE_FILE = Path(__file__).parent.parent.parent / "license.key"

    # Feature limits by license type
    FEATURE_LIMITS = {
        LicenseType.TRIAL: {
            "max_pairs": 1,
            "max_grids": 5,
            "market_scanner": False,
            "multi_pair": False,
            "notifications": False,
            "expiry_days": 14,
        },
        LicenseType.BETA: {
            "max_pairs": 3,
            "max_grids": 15,
            "market_scanner": True,
            "multi_pair": True,
            "notifications": True,
            "expiry_days": 14,  # 2 weeks beta access
            "is_beta": True,
        },
        LicenseType.BASIC: {
            "max_pairs": 2,
            "max_grids": 10,
            "market_scanner": True,
            "multi_pair": False,
            "notifications": True,
            "expiry_days": 365,
        },
        LicenseType.PRO: {
            "max_pairs": 5,
            "max_grids": 20,
            "market_scanner": True,
            "multi_pair": True,
            "notifications": True,
            "expiry_days": 365,
        },
        LicenseType.ENTERPRISE: {
            "max_pairs": -1,  # Unlimited
            "max_grids": -1,  # Unlimited
            "market_scanner": True,
            "multi_pair": True,
            "notifications": True,
            "expiry_days": 365,
        },
    }

    def __init__(self):
        self.license_data: dict | None = None
        self.is_valid = False
        self.license_type = LicenseType.TRIAL
        self._load_license()

    def _get_machine_id(self) -> str:
        """Generate a unique machine identifier for hardware binding."""
        # Combine multiple system identifiers
        identifiers = [
            platform.node(),  # Hostname
            platform.machine(),  # Machine type
            platform.processor(),  # Processor info
        ]

        # Try to get more hardware-specific info
        try:
            import uuid

            identifiers.append(str(uuid.getnode()))  # MAC address
        except Exception as e:
            logger.debug(f"Could not get MAC address for machine ID: {e}")

        combined = "|".join(identifiers)
        return hashlib.sha256(combined.encode()).hexdigest()[:32]

    def _generate_signature(self, data: dict) -> str:
        """Generate HMAC signature for license data."""
        # Create a consistent string representation
        data_str = json.dumps(data, sort_keys=True)
        signature = hmac.new(self._SECRET_KEY.encode(), data_str.encode(), hashlib.sha256).hexdigest()
        return signature

    def _verify_signature(self, data: dict, signature: str) -> bool:
        """Verify the HMAC signature of license data."""
        expected = self._generate_signature(data)
        return hmac.compare_digest(expected, signature)

    def generate_license_key(
        self, license_type: str, customer_email: str, machine_id: str | None = None, expiry_days: int | None = None
    ) -> str:
        """
        Generate a new license key.

        This would typically be called from your sales/admin system.
        """
        if machine_id is None:
            machine_id = self._get_machine_id()

        if expiry_days is None:
            expiry_days = self.FEATURE_LIMITS.get(license_type, {}).get("expiry_days", 365)

        expiry_date = datetime.now() + timedelta(days=expiry_days)

        license_data = {
            "type": license_type,
            "email": customer_email,
            "machine_id": machine_id,
            "issued": datetime.now().isoformat(),
            "expires": expiry_date.isoformat(),
            "version": "2.0",
        }

        signature = self._generate_signature(license_data)

        # Combine data and signature
        full_license = {
            "data": license_data,
            "signature": signature,
        }

        # Encode as base64-ish format for distribution
        license_json = json.dumps(full_license)
        encoded = hashlib.sha256(license_json.encode()).hexdigest()[:8].upper()

        # Create a readable license key format
        license_key = f"GRID-{encoded}-{license_json}"

        return license_key

    def _load_license(self):
        """Load and validate license from file."""
        if not self.LICENSE_FILE.exists():
            logger.info("No license file found. Running in trial mode.")
            self._set_trial_mode()
            return

        try:
            with open(self.LICENSE_FILE) as f:
                content = f.read().strip()

            # Parse license key
            if content.startswith("GRID-"):
                # Extract JSON part
                parts = content.split("-", 2)
                if len(parts) >= 3:
                    license_json = parts[2]
                    full_license = json.loads(license_json)

                    data = full_license.get("data", {})
                    signature = full_license.get("signature", "")

                    # Verify signature
                    if not self._verify_signature(data, signature):
                        logger.warning("License signature invalid!")
                        self._set_trial_mode()
                        return

                    # Check machine ID
                    if data.get("machine_id") != self._get_machine_id():
                        logger.warning("License not valid for this machine!")
                        self._set_trial_mode()
                        return

                    # Check expiration
                    expires = datetime.fromisoformat(data.get("expires", "2000-01-01"))
                    if expires < datetime.now():
                        logger.warning("License has expired!")
                        self._set_trial_mode()
                        return

                    # License is valid!
                    self.license_data = data
                    self.license_type = data.get("type", LicenseType.TRIAL)
                    self.is_valid = True
                    logger.info(f"License validated: {self.license_type.upper()}")
                    return

        except Exception as e:
            logger.error(f"Error loading license: {e}")

        self._set_trial_mode()

    def _set_trial_mode(self):
        """Set the license to trial mode."""
        self.license_data = None
        self.license_type = LicenseType.TRIAL
        self.is_valid = False
        logger.info("Running in TRIAL mode with limited features.")

    def get_feature_limit(self, feature: str):
        """Get the limit for a specific feature based on license type."""
        limits = self.FEATURE_LIMITS.get(self.license_type, self.FEATURE_LIMITS[LicenseType.TRIAL])
        return limits.get(feature)

    def check_feature(self, feature: str) -> bool:
        """Check if a feature is enabled for the current license."""
        limit = self.get_feature_limit(feature)
        if isinstance(limit, bool):
            return limit
        return limit != 0

    def get_license_info(self) -> dict:
        """Get current license information."""
        limits = self.FEATURE_LIMITS.get(self.license_type, self.FEATURE_LIMITS[LicenseType.TRIAL])

        info = {
            "type": self.license_type.upper(),
            "is_valid": self.is_valid,
            "features": limits,
            "machine_id": self._get_machine_id(),
        }

        if self.license_data:
            info["email"] = self.license_data.get("email", "")
            info["expires"] = self.license_data.get("expires", "")
            info["issued"] = self.license_data.get("issued", "")

        return info

    def validate_operation(self, operation: str, current_count: int = 0) -> tuple[bool, str]:
        """
        Validate if an operation is allowed under the current license.

        Returns: (allowed: bool, message: str)
        """
        limits = self.FEATURE_LIMITS.get(self.license_type, self.FEATURE_LIMITS[LicenseType.TRIAL])

        if operation == "add_pair":
            max_pairs = limits.get("max_pairs", 1)
            if max_pairs != -1 and current_count >= max_pairs:
                return (
                    False,
                    f"License limit reached: Maximum {max_pairs} trading pairs allowed. Upgrade to unlock more.",
                )

        elif operation == "add_grid":
            max_grids = limits.get("max_grids", 5)
            if max_grids != -1 and current_count >= max_grids:
                return False, f"License limit reached: Maximum {max_grids} grid levels allowed. Upgrade to unlock more."

        elif operation == "market_scanner":
            if not limits.get("market_scanner", False):
                return False, "Market Scanner is a PRO feature. Upgrade to unlock."

        elif operation == "multi_pair":
            if not limits.get("multi_pair", False):
                return False, "Multi-pair trading is a PRO feature. Upgrade to unlock."

        return True, "OK"


# Global license manager instance
_license_manager: LicenseManager | None = None


def get_license_manager() -> LicenseManager:
    """Get or create the global license manager instance."""
    global _license_manager
    if _license_manager is None:
        _license_manager = LicenseManager()
    return _license_manager


def check_license(feature: str | None = None) -> bool:
    """Quick check if license is valid (and optionally if a feature is enabled)."""
    manager = get_license_manager()
    if feature:
        return manager.check_feature(feature)
    return manager.is_valid


# CLI for generating licenses (for admin use)
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GridBot Pro License Generator")
    parser.add_argument("--type", choices=["trial", "basic", "pro", "enterprise"], default="basic")
    parser.add_argument("--email", required=True, help="Customer email")
    parser.add_argument("--days", type=int, help="License validity in days")
    parser.add_argument("--machine-id", help="Target machine ID (leave empty for current machine)")

    args = parser.parse_args()

    manager = LicenseManager()

    if args.machine_id is None:
        pass

    license_key = manager.generate_license_key(
        license_type=args.type, customer_email=args.email, machine_id=args.machine_id, expiry_days=args.days
    )


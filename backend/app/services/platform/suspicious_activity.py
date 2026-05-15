"""Suspicious activity detection service for login monitoring.

Reference: Phase 11 — Suspicious Activity Detection
"""

import os
from typing import Any, Optional

from geoip2.database import Reader
from geoip2.errors import AddressNotFoundError

from app.core.config import settings


class SuspiciousActivityService:
    """Service for detecting suspicious login activity."""

    def __init__(self):
        self.geoip_reader = None
        if os.path.exists(settings.geoip_database_path):
            try:
                self.geoip_reader = Reader(settings.geoip_database_path)
            except Exception as e:
                print(f"Failed to load GeoIP database: {e}")

    def get_ip_location(self, ip_address: str) -> dict[str, Any]:
        """Get location information for an IP address."""
        if not self.geoip_reader:
            return {"country_code": None, "city": None, "region": None}

        try:
            response = self.geoip_reader.city(ip_address)
            return {
                "country_code": response.country.iso_code,
                "city": response.city.name,
                "region": response.subdivisions.most_specific.name
                if response.subdivisions
                else None,
            }
        except AddressNotFoundError:
            return {"country_code": None, "city": None, "region": None}
        except Exception as e:
            print(f"GeoIP lookup failed: {e}")
            return {"country_code": None, "city": None, "region": None}

    def is_new_location(
        self,
        known_locations: list,
        current_country_code: str,
        current_city: Optional[str],
    ) -> bool:
        """Check if current location is new compared to known locations."""
        if not known_locations:
            return True

        for location in known_locations:
            if (
                location.country_code == current_country_code
                and location.city == current_city
            ):
                return False

        return True

    def is_new_device(
        self,
        known_devices: list,
        current_device_fingerprint: str,
    ) -> bool:
        """Check if current device is new compared to known devices."""
        if not known_devices:
            return True

        for device in known_devices:
            if device.device_fingerprint == current_device_fingerprint:
                return False

        return True

"""
geolocator.py — Address to lat/lon via Nominatim (OpenStreetMap, free, no API key)
"""
import requests
import time
import sys
from dataclasses import dataclass
from typing import Optional

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "custody-calendar-generator/1.0 (educational use)"


@dataclass
class GeoLocation:
    lat: float
    lon: float
    display_name: str


def geocode(address: str) -> Optional[GeoLocation]:
    """Convert a free-form address string to lat/lon via Nominatim."""
    params = {
        "q": address,
        "format": "json",
        "limit": "1",
        "addressdetails": "1",
    }
    headers = {"User-Agent": USER_AGENT}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        r = results[0]
        return GeoLocation(
            lat=float(r["lat"]),
            lon=float(r["lon"]),
            display_name=r.get("display_name", address),
        )
    except Exception as e:
        print(f"[geolocator] Error geocoding '{address}': {e}", file=sys.stderr)
        return None


def haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Haversine distance between two lat/lon points, returned in miles.
    """
    import math
    R_MILES = 3958.8
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R_MILES * c


if __name__ == "__main__":
    # Quick test
    addr = sys.argv[1] if len(sys.argv) > 1 else "Glass Mountain Trl, Austin, TX"
    loc = geocode(addr)
    if loc:
        print(f"Address: {addr}")
        print(f"Lat/Lon: {loc.lat}, {loc.lon}")
        print(f"Display: {loc.display_name}")
    else:
        print("Geocoding failed")

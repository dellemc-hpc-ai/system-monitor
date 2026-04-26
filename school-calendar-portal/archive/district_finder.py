"""
district_finder.py — Find school district from lat/lon using NCES CCD data.
Fetches state-filtered data from Census Bureau CCD LEA API, caches per state.
"""
import json
import os
import sys
import time
import requests
from dataclasses import dataclass
from typing import Optional
from math import radians, sin, cos, sqrt, atan2, degrees, asin

# Use the geolocator's haversine
sys.path.insert(0, os.path.dirname(__file__))
from geolocator import haversine_miles

NCES_CCD_URL = "https://api.census.gov/data/2023/ccd/lau/lea"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")
os.makedirs(CACHE_DIR, exist_ok=True)

STATE_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08",
    "CT": "09", "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16",
    "IL": "17", "IN": "18", "IA": "19", "KS": "20", "KY": "21", "LA": "22",
    "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39", "OK": "40",
    "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
    "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56",
}

STATE_ABBREV_FROM_FIPS = {v: k for k, v in STATE_FIPS.items()}


@dataclass
class DistrictInfo:
    nces_id: str      # 7-digit LEAID
    name: str
    state: str        # 2-letter abbreviation
    lat: float
    lon: float
    distance_miles: float


def _bearing(lat1, lon1, lat2, lon2):
    """Compute initial bearing from point 1 to point 2 in degrees."""
    phi1, phi2 = radians(lat1), radians(lat2)
    dlon = radians(lon2 - lon1)
    x = sin(dlon) * cos(phi2)
    y = cos(phi1) * sin(phi2) - sin(phi1) * cos(phi2) * cos(dlon)
    initial_bearing = degrees(atan2(x, y))
    return (initial_bearing + 360) % 360


def _point_from_bearing(lat, lon, bearing_deg, distance_km):
    """Given start point, bearing, and distance, return destination lat/lon."""
    R = 6371.0  # km
    d = distance_km / R
    phi1 = radians(lat)
    brng = radians(bearing_deg)
    phi2 = asin(sin(phi1) * cos(d) + cos(phi1) * sin(d) * cos(brng))
    lon2 = radians(lon) + atan2(sin(brng) * sin(d) * cos(phi1),
                               cos(d) - sin(phi1) * sin(phi2))
    return degrees(phi2), degrees(lon2)


def _bounding_box(lat, lon, radius_miles):
    """Compute approximate bounding box for a radius in miles."""
    radius_km = radius_miles * 1.60934
    # Cardinal directions
    n = _point_from_bearing(lat, lon, 0, radius_km)
    s = _point_from_bearing(lat, lon, 180, radius_km)
    e = _point_from_bearing(lat, lon, 90, radius_km)
    w = _point_from_bearing(lat, lon, 270, radius_km)
    return {
        "north": max(n[0], s[0]),
        "south": min(n[0], s[0]),
        "east": max(e[1], w[1]),
        "west": min(e[1], w[1]),
    }


def _fetch_nces_for_state(state_abbrev: str, force: bool = False) -> Optional[list]:
    """Fetch all operating school districts (LEAID) for a state via CCD LEA API."""
    cache_file = os.path.join(CACHE_DIR, f"nces_{state_abbrev.lower()}.json")
    if not force and os.path.exists(cache_file):
        age_days = (time.time() - os.path.getmtime(cache_file)) / 86400
        if age_days < 180:  # < 6 months old
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)

    fips = STATE_FIPS.get(state_abbrev.upper())
    if not fips:
        print(f"[district_finder] Unknown state: {state_abbrev}", file=sys.stderr)
        return None

    params = {
        "get": "LEAID,LEANM,LSTATE,LATCOD,LONCOD",
        "for": f"state:{fips}",
        "district_type": "1",  # Operating districts only
    }
    try:
        resp = requests.get(NCES_CCD_URL, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[district_finder] NCES API error: {e}", file=sys.stderr)
        # Try cached version regardless of age
        if os.path.exists(cache_file):
            with open(cache_file, encoding="utf-8") as f:
                return json.load(f)
        return None

    if not data or len(data) < 2:
        return None

    headers = data[0]
    rows = data[1:]
    districts = []
    for row in rows:
        d = dict(zip(headers, row))
        lat = d.get("LATCOD")
        lon = d.get("LONCOD")
        if lat and lon and lat != "None" and lon != "None":
            try:
                districts.append({
                    "nces_id": d["LEAID"],
                    "name": d["LEANM"],
                    "state": d["LSTATE"],
                    "lat": float(lat),
                    "lon": float(lon),
                })
            except (ValueError, TypeError):
                pass

    # Cache
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(districts, f)
    print(f"[district_finder] Cached {len(districts)} districts for {state_abbrev}")
    return districts


def find_districts_for_address(lat: float, lon: float, state_abbrev: str, limit: int = 5):
    """
    Find the N closest school districts to a given lat/lon in a given state.
    Returns list of DistrictInfo sorted by distance.
    """
    districts = _fetch_nces_for_state(state_abbrev)
    if not districts:
        return []

    results = []
    for d in districts:
        dist = haversine_miles(lat, lon, d["lat"], d["lon"])
        results.append(DistrictInfo(
            nces_id=d["nces_id"],
            name=d["name"],
            state=d["state"],
            lat=d["lat"],
            lon=d["lon"],
            distance_miles=round(dist, 1),
        ))

    results.sort(key=lambda x: x.distance_miles)
    return results[:limit]


if __name__ == "__main__":
    # Quick test with Frank's address
    sys.path.insert(0, os.path.dirname(__file__))
    from geolocator import geocode

    addr = sys.argv[1] if len(sys.argv) > 1 else "Glass Mountain Trl, Austin TX"
    loc = geocode(addr)
    if not loc:
        print("Geocoding failed")
        sys.exit(1)
    print(f"Lat/Lon: {loc.lat}, {loc.lon}")

    # Determine state from address
    state = "TX"
    districts = find_districts_for_address(loc.lat, loc.lon, state, limit=5)
    print(f"\nTop {len(districts)} districts near {addr}:")
    for i, d in enumerate(districts, 1):
        print(f"  {i}. {d.name} (NCES: {d.nces_id}) — {d.distance_miles} mi away")

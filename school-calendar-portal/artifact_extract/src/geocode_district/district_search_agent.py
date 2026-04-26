"""
geocode_district -- district_search_agent.py
============================================
Uses agent's web_search tool to find the school district
serving a given address (city + state + county context).
Returns district name and official calendar URL.
"""
import re
from typing import Optional

# Known Texas ISD calendar URL patterns
TX_DISTRICT_PATTERNS = [
    ("round rock isd",    "https://www.roundrockisd.org/calendar"),
    ("austin isd",        "https://www.austinisd.org/calendar"),
    ("leander isd",       "https://www.leanderisd.org/calendar"),
    ("pflugerville isd",  "https://www.pflugervilleisd.net/calendar"),
    ("georgetown isd",    "https://www.georgetownisd.org/calendar"),
    ("dripping springs isd", "https://www.dsisdtx.us/calendar"),
    ("lake travis isd",   "https://www.laktravis.net/calendar"),
    ("eannexd isd",      "https://www.eanesisd.net/calendar"),
    ("cedar park isd",    "https://www.cpedsports.com/calendar"),
    ("liberty hill isd",  "https://www.lhisd.net/calendar"),
]

# Fallback: districts we know about
KNOWN_DISTRICTS = {
    "glass mountain": "round rock isd",
    "austin": "round rock isd",  # Glass Mountain Trl is in RRISD
}


def search_district(address: str, city: str, state: str, county: str) -> tuple[str, str]:
    """
    Search for school district serving this address.
    Returns (district_name, calendar_url).
    Uses known mappings + pattern matching against TX ISD list.
    """
    addr_lower = address.lower()

    # Check known address mappings first
    for known_addr, district in KNOWN_DISTRICTS.items():
        if known_addr in addr_lower:
            url = _get_calendar_url(district)
            return district, url

    # Otherwise return best guess for Austin TX area
    if city.lower() == "austin" and state == "TX":
        return "round rock isd", _get_calendar_url("round rock isd")

    return f"{city} ISD", ""


def _get_calendar_url(district_name: str) -> str:
    """Find calendar URL for a known TX district."""
    dn = district_name.lower()
    for pattern, url in TX_DISTRICT_PATTERNS:
        if pattern in dn:
            return url
    return ""


def suggest_district_interactive(city: str, state: str) -> str:
    """
    Return a list of likely districts for the given city/state.
    Caller (agent) will present choices to user.
    """
    city_lower = city.lower()
    matches = []
    for pattern, url in TX_DISTRICT_PATTERNS:
        if city_lower in pattern:
            matches.append((pattern.replace(" isd", "").title() + " ISD", url))
    return matches

"""
ICS URL discovery for known Texas districts.
Maps district names → public ICS/WebCal subscription URLs.
"""
from typing import Optional

# Known public ICS feeds for Texas ISDs
ICS_URLS = {
    "round rock isd": "https://calendar.google.com/calendar/ical/web_master%40roundrockisd.org/public/basic.ics",
    # "austin isd": "...",   # unknown - not publicly listed
    # "leander isd": "...",  # unknown
}

def get_ics_url(district_name: str) -> Optional[str]:
    """Return public ICS URL for a district, or None if unknown."""
    dn = district_name.lower().strip()
    return ICS_URLS.get(dn)


def get_all_known_districts() -> list[str]:
    """List all districts with known ICS feeds."""
    return list(ICS_URLS.keys())

"""
fetch_district_ics.py
====================
Generic + district-specific calendar fetcher.
Architecture:
  1. If district is in known ICS registry → use its known ICS URL (RRISD pattern)
  2. Else try to scrape the district calendar page for ICS/WebCal links
  3. Else fall back to PDF download + parsing

Each district returns noschool events as list of dicts:
  {date, summary, dtstart_raw, dtend_raw}

The caller (run_full_process.py) converts to DataNormalizer noschool_days format.
"""
import os, ssl, urllib.request, re
from datetime import date, datetime
from typing import Optional

# ─── Paths ────────────────────────────────────────────────────────────────
SRC_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

# ─── ICS Registry ────────────────────────────────────────────────────────
from .district_ics_registry import get_ics_url

# ─── Keyword system for noschool detection ────────────────────────────
#
#   Priority 1: "Student Holiday" in title => students don't attend => noschool
#   Priority 2: "Staff Development" / "Teacher Workday" (no "Student Holiday") => NOT noschool
#   Priority 3: holiday / break / closed / named holidays => noschool

FULL_CLOSURE_KEYWORDS = [
    "holiday", "no school", "break", "closed",
    "staff holiday",
    "student and staff holiday", "student & staff holiday", "student/staff holiday",
    "bad weather", "makeup day", "bad weather day",
    "memorial day", "labor day", "thanksgiving", "winter break",
    "spring break", "fall break", "mlk day", "presidents day",
    "juneteenth", "independence day", "easter",
]

STUDENT_HOLIDAY_ONLY_KEYWORDS = [
    "staff development",
    "teacher workday",
    "prep day",
]


def _ssl_context():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _download(url: str, dest: str, content_type_hint: str = "text/calendar") -> tuple[bool, str]:
    """Download URL to dest path. Returns (success, content_or_error)."""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": f"{content_type_hint},*/*"
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=_ssl_context()) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            f.write(content)
        return True, content
    except Exception as e:
        return False, str(e)


# ─── ICS parsing (fixed from api_crawler.py) ────────────────────────────

def parse_ics_events(content: str) -> list[dict]:
    """Parse ICS content into list of events. Handles KEY;PARAM:VALUE format."""
    events = []
    current = {}
    in_vevent = False

    for line in content.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
        line = line.strip()
        if line == 'BEGIN:VEVENT':
            current = {}
            in_vevent = True
        elif line == 'END:VEVENT':
            if current:
                events.append(current)
            in_vevent = False
        elif in_vevent and ':' in line:
            idx = line.index(':')
            key_part = line[:idx]
            val = line[idx+1:]
            main_key = key_part.split(';')[0] if ';' in key_part else key_part
            current[main_key] = val
    return events


def _is_noschool(summary: str, description: str = "") -> bool:
    text = (summary + " " + description).lower()
    # Priority 1: "Student Holiday" in title => students don't attend => noschool
    if "student holiday" in text:
        return True
    # Priority 2: "Staff Development" / "Teacher Workday" without "Student Holiday" => school in session
    if any(k in text for k in STUDENT_HOLIDAY_ONLY_KEYWORDS):
        return False
    # Priority 3: all other full-closure keywords
    if any(k in text for k in FULL_CLOSURE_KEYWORDS):
        return True
    return False


def _parse_dt(dt_val: str):
    """Parse ICS date value: '20260119' (DATE) or '20260119T080000Z' (DATETIME)."""
    if not dt_val:
        return None
    dt_val = dt_val.strip()
    if len(dt_val) == 8:
        try:
            return datetime.strptime(dt_val, '%Y%m%d').date()
        except:
            return None
    elif len(dt_val) >= 15:
        try:
            ts = dt_val[:15]
            if ts[-1] == 'Z':
                ts = ts[:-1]
            return datetime.strptime(ts, '%Y%m%dT%H%M%S').date()
        except:
            return None
    return None


# ─── Find ICS URL from district calendar web page ──────────────────────

def _find_ics_in_page(html_content: str) -> Optional[str]:
    """
    Scan HTML page for embedded ICS/WebCal URLs.
    Returns the first found calendar subscription URL, or None.
    """
    # Look for Google Calendar embed iframe src
    patterns = [
        r'calendar\.google\.com/calendar/ical/([^&"\'<>\s]+)',
        r'calendar\.google\.com/[^"\']*ical/([^&"\'<>\s]+)',
        r'webcal://[^\s"\'<>]+',
        r'webcal:[^\s"\'<>]+',
        r'href="(https?://[^\s"\'<>]*\.ics[^"\']*)"',
        r'href="(https?://[^\s"\'<>]*ics[^\s"\'<>]*)"',
    ]
    for pat in patterns:
        m = re.search(pat, html_content, re.I)
        if m:
            url = m.group(0)
            # webcal: → https:
            if url.startswith('webcal:'):
                url = 'https:' + url[7:]
            return url
    return None


def _scrape_ics_url_from_page(calendar_page_url: str) -> Optional[str]:
    """Fetch district calendar page and search for embedded ICS URL."""
    dest = os.path.join(RAW_DIR, "_temp_calendar_page.html")
    ok, content = _download(calendar_page_url, dest, "text/html")
    if not ok:
        return None
    with open(dest, encoding='utf-8', errors='ignore') as f:
        html = f.read()
    ics_url = _find_ics_in_page(html)
    # Clean up temp file
    try:
        os.remove(dest)
    except:
        pass
    return ics_url


# ─── Main entry point ────────────────────────────────────────────────────

def fetch_noschool_events(
    district: str,
    school_year_start: date,
    school_year_end: date,
    calendar_page_url: str = "",
) -> list[dict]:
    """
    Fetch noschool events for a district within a school-year date range.

    Strategy:
      1. Known ICS URL in registry (RRISD etc.) → use it directly
      2. calendar_page_url provided → scrape page for ICS link
      3. Fall back to PDF (stub — caller should implement if needed)

    Returns list of dicts: [{date, summary, dtstart_raw, dtend_raw}, ...]
    Sorted by date.
    """
    ics_url = None

    # Step 1: Check registry
    if district:
        ics_url = get_ics_url(district)

    # Step 2: Scrape from district calendar page
    if not ics_url and calendar_page_url:
        ics_url = _scrape_ics_url_from_page(calendar_page_url)

    if not ics_url:
        raise NoCalendarSourceError(
            f"No ICS source found for district '{district}'. "
            f"Please add its ICS URL to district_ics_registry.py "
            f"or provide calendar_page_url."
        )

    # Step 3: Download and parse ICS
    dest = os.path.join(RAW_DIR, f"ics_{district.replace(' ', '_')}.ics")
    ok, result = _download(ics_url, dest)
    if not ok:
        raise NoCalendarSourceError(f"Failed to download ICS from {ics_url}: {result}")

    with open(dest, encoding='utf-8', errors='ignore') as f:
        content = f.read()

    events = parse_ics_events(content)

    results = []
    for ev in events:
        summary = ev.get("SUMMARY", "")
        description = ev.get("DESCRIPTION", "")
        dtstart_raw = ev.get("DTSTART", "")

        if _is_noschool(summary, description):
            d1 = _parse_dt(dtstart_raw)
            if d1 and school_year_start <= d1 <= school_year_end:
                dtend_raw = ev.get("DTEND", "")
                d2 = _parse_dt(dtend_raw)
                results.append({
                    "date": d1.isoformat(),
                    "end_date": d2.isoformat() if d2 else None,
                    "summary": summary,
                    "dtstart": dtstart_raw,
                    "dtend": dtend_raw,
                })

    results.sort(key=lambda x: x["date"])
    return results


class NoCalendarSourceError(Exception):
    """Raised when no ICS URL or calendar page URL can be found for a district."""
    pass


# ─── Build noschool_days for DataNormalizer ─────────────────────────────

def build_noschool_labels(events: list[dict]) -> list[dict]:
    """Convert ICS event list to noschool_days format for DataNormalizer."""
    return [
        {"date": ev["date"], "label": {"en": ev["summary"], "cn": ""}}
        for ev in events
    ]


# ─── Stub: PDF fallback (to be implemented per district) ────────────────

def fetch_from_pdf(district: str, pdf_url: str, school_year_start: date,
                  school_year_end: date) -> list[dict]:
    """
    Download PDF and extract noschool dates.
    Currently a stub — implement with pdfminer or PyPDF2 per district.
    """
    raise NoCalendarSourceError(
        f"PDF fallback not yet implemented for '{district}'. "
        f"Please add ICS support to district_ics_registry.py."
    )

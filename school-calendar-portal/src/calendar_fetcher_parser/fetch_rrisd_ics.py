"""
fetch_rrisd_ics.py
=================
Fetches RRISD noschool days from the official Google Calendar ICS feed.
Updates data/raw/rrisd_google_calendar.ics and returns parsed events.

Source: web_master@roundrockisd.org Google Calendar
URL: https://calendar.google.com/calendar/ical/web_master%40roundrockisd.org/public/basic.ics
"""
import os, ssl, urllib.request, json
from datetime import datetime, date

SRC_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(SRC_DIR)
RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
ICS_URL = "https://calendar.google.com/calendar/ical/web_master@roundrockisd.org/public/basic.ics"
ICS_DEST = os.path.join(RAW_DIR, "rrisd_google_calendar.ics")

# Two-tier keyword system for RRISD ICS parsing:
#
#   FULL CLOSURE   — school is closed, everyone is off
#   STUDENT HOLIDAY — students don't attend, but staff may report
#
# The is_noschool() function returns True only for FULL CLOSURE events.
# Student-holiday-only events (Staff Dev, Teacher Workday, etc.) are NOT
# treated as school closures because the school remains "in session" for
# staff — relevant for custody calculations where school in session matters.

FULL_CLOSURE_KEYWORDS = [
    "holiday", "no school", "break", "closed",
    "bad weather", "makeup day", "bad weather day",
    "memorial day", "labor day", "thanksgiving", "winter break",
    "spring break", "fall break", "mlk day", "presidents day",
    "juneteenth", "independence day",
    # These phrases explicitly include "staff" or "student & staff" → full closure
    "staff holiday",
    "student and staff holiday",
    "student & staff holiday",
]

# Student-holiday-only keywords — school open for staff, students off.
# These are NOT full closures and do NOT trigger noschool status.
STUDENT_HOLIDAY_ONLY_KEYWORDS = [
    "staff development",
    "teacher workday",
    "prep day",
    # "student holiday" alone means students off, but does NOT mean school closed.
    # However, when paired with an explicit holiday name (e.g. "Columbus Day Student Holiday")
    # it IS a full closure — handled by the "holiday" check above.
]

def fetch_ics(url: str, dest_path: str) -> bool:
    """Download ICS file from URL to dest_path."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/calendar,*/*"
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[ICS] Downloaded {len(content)} chars -> {dest_path}")
        return True
    except Exception as e:
        print(f"[ICS] Fetch failed: {e}")
        return False


def parse_ics_events(content: str) -> list[dict]:
    """Parse ICS content into list of events."""
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


def is_noschool(summary: str, description: str = "") -> bool:
    """
    Returns True for any day students do NOT attend school.

    Priority matching:
      1. "Student Holiday" in title (with or without staff) => noschool
         e.g. "Student Holiday/Staff Development", "Columbus Day Student Holiday"
      2. "Staff Development" / "Teacher Workday" / "Prep Day" (no "Student Holiday") => NOT noschool
      3. Named holiday / break / closed keywords => noschool
    """
    text = (summary + " " + description).lower()

    # Priority 1: "Student Holiday" in title => students don't attend => noschool
    if "student holiday" in text:
        return True

    # Priority 2: staff-development / teacher-workday WITHOUT "Student Holiday" => school in session
    if any(k in text for k in STUDENT_HOLIDAY_ONLY_KEYWORDS):
        return False

    # Priority 3: all other full-closure keywords
    if any(k in text for k in FULL_CLOSURE_KEYWORDS):
        return True

    return False


def parse_dt(dt_val: str):
    """Parse ICS DTSTART/DTEND value like '20260119' or '20260119T080000Z'."""
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


def fetch_noschool_events(school_year_start: date, school_year_end: date) -> list[dict]:
    """
    Fetch RRISD ICS and return noschool events within the given school year date range.
    Each returned dict: {date, summary, dtstart, dtend}
    """
    # Download fresh ICS
    ok = fetch_ics(ICS_URL, ICS_DEST)
    if not ok:
        # Fall back to cached file
        if os.path.exists(ICS_DEST):
            print("[ICS] Using cached ICS file")
            with open(ICS_DEST, encoding='utf-8', errors='ignore') as f:
                content = f.read()
        else:
            raise RuntimeError("ICS fetch failed and no cached file available")
    else:
        with open(ICS_DEST, encoding='utf-8', errors='ignore') as f:
            content = f.read()

    events = parse_ics_events(content)
    print(f"[ICS] Parsed {len(events)} total events from ICS")

    results = []
    for ev in events:
        summary = ev.get("SUMMARY", "")
        description = ev.get("DESCRIPTION", "")
        dtstart_raw = ev.get("DTSTART", "")

        if is_noschool(summary, description):
            d1 = parse_dt(dtstart_raw)
            if d1 and school_year_start <= d1 <= school_year_end:
                dtend_raw = ev.get("DTEND", "")
                d2 = parse_dt(dtend_raw)
                results.append({
                    "date": d1.isoformat(),
                    "end_date": d2.isoformat() if d2 else None,
                    "summary": summary,
                    "dtstart": dtstart_raw,
                    "dtend": dtend_raw,
                })

    results.sort(key=lambda x: x["date"])
    return results


def build_noschool_labels(events: list[dict]) -> list[dict]:
    """Convert ICS event list to noschool_days format for DataNormalizer."""
    return [
        {"date": ev["date"], "label": {"en": ev["summary"], "cn": ""}}
        for ev in events
    ]


if __name__ == "__main__":
    # Quick test
    print("Fetching RRISD ICS...")
    from datetime import date as date_cls
    sy_start = date_cls(2025, 8, 1)
    sy_end = date_cls(2026, 8, 31)
    events = fetch_noschool_events(sy_start, sy_end)
    print(f"\n=== RRISD Noschool Days 2025-2026 ({len(events)} total) ===")
    for ev in events:
        d = date_cls.fromisoformat(ev["date"])
        print(f"  {ev['date']} ({d.strftime('%a')}): {ev['summary']}")

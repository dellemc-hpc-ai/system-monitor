"""
calendar_fetcher_parser -- api_crawler.py
=========================================
Fetches calendar data from public APIs (ICS feeds, Google Calendar, etc.)
"""
import json
import urllib.request
import re
import os
from datetime import datetime

RAW_DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "raw"
)

def fetch_ics(url: str, dest_path: str) -> bool:
    """Download an ICS file from URL."""
    import ssl
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
        return True
    except Exception as e:
        print(f"ICS fetch failed: {e}")
        return False


def parse_ics_events(content: str) -> list[dict]:
    """
    Parse ICS content into list of events.
    Handles ICS KEY;PARAM:VALUE format correctly (e.g. DTSTART;VALUE=DATE:20260119).
    """
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
            # Handle KEY;PARAM:VALUE format - strip params to get main key name
            main_key = key_part.split(';')[0] if ';' in key_part else key_part
            current[main_key] = val
    return events


def fetch_web_page(url: str, dest_path: str) -> bool:
    """Fetch a web page and save raw HTML."""
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Web fetch failed: {e}")
        return False


def save_source_meta(source_url: str, source_type: str, file_path: str,
                      success: bool, error: str = "") -> None:
    """Save metadata about the fetched source."""
    meta_file = os.path.join(RAW_DATA_DIR, "source_meta.json")
    meta = []
    if os.path.exists(meta_file):
        with open(meta_file, "r", encoding="utf-8") as f:
            meta = json.load(f)

    entry = {
        "url": source_url,
        "type": source_type,
        "saved_path": file_path,
        "success": success,
        "error": error,
        "collected_at": datetime.now().isoformat(),
        "version": "1.0"
    }
    meta.append(entry)

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

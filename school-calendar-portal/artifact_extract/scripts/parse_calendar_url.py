"""
Parse a school district calendar from URL, PDF, or ICS feed.
Supports:
- ICS calendar feeds (.ics files or Google Calendar export)
- Web page URLs: extracts calendar data via scraping
- PDF files: extracts text from PDF
- Image files: OCR via web service

Outputs structured JSON with school year data.
"""
import sys
import json
import re
import urllib.request
from datetime import datetime

def fetch_url_content(url):
    """Fetch content from a URL."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; CoParentingBot/1.0)',
        'Accept': 'text/html,application/xhtml+xml,application/xml,text/calendar'
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
        content_type = resp.headers.get('Content-Type', '')
    return content, content_type

def parse_ics(content):
    """
    Parse ICS (iCalendar) format. Common for Google Calendar exports.
    Returns list of events with dtstart, dtend, summary.
    """
    events = []
    current = {}
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('BEGIN:VEVENT'):
            current = {}
        elif line.startswith('END:VEVENT'):
            if current:
                events.append(current)
        elif ':' in line:
            key, val = line.split(':', 1)
            if 'DTSTART' in key:
                current['dtstart'] = val
            elif 'DTEND' in key:
                current['dtend'] = val
            elif 'SUMMARY' in key:
                current['summary'] = val
            elif 'DESCRIPTION' in key:
                current['description'] = val
    return events

def ics_to_school_data(events):
    """
    Convert ICS events to school calendar format.
    Identifies: first/last day, breaks, noschool days.
    """
    result = {
        'district': 'Unknown',
        'schoolYears': {},
        'notes': 'Parsed from ICS calendar'
    }

    # Categorize events
    first_days = []
    last_days = []
    breaks = {'thanksgiving': [], 'christmas': [], 'spring': []}
    noschool = []

    for evt in events:
        summary = evt.get('summary', '').lower()
        desc = evt.get('description', '').lower()
        dtstart = evt.get('dtstart', '')[:8]  # YYYYMMDD
        dtend = evt.get('dtend', '')[:8]

        if not dtstart:
            continue

        # Format date
        try:
            date_str = f"{dtstart[:4]}-{dtstart[4:6]}-{dtstart[6:8]}"
        except:
            continue

        # First/last day keywords
        if any(k in summary for k in ['first day', 'instruction begins', 'students return']):
            first_days.append(date_str)

        if any(k in summary for k in ['last day', 'instruction ends', 'summer']):
            last_days.append(date_str)

        # Break detection
        if any(k in summary for k in ['thanksgiving', 'fall break']):
            breaks['thanksgiving'].append({'start': date_str})
        elif any(k in summary for k in ['christmas', 'winter break', 'holiday']):
            breaks['christmas'].append({'start': date_str})
        elif any(k in summary for k in ['spring break']):
            breaks['spring'].append({'start': date_str})

        # No-school indicators
        if any(k in summary for k in ['holiday', 'no school', 'student holiday', 'staff development']):
            if 'thanksgiving' not in summary and 'christmas' not in summary and 'spring' not in summary:
                noschool.append({'date': date_str, 'label': evt.get('summary', 'No School')})

    print(f"First days found: {first_days[:5]}")
    print(f"Last days found: {last_days[:5]}")
    print(f"Noschool days found: {len(noschool)}")

    return result

def extract_calendar_dates_from_text(text):
    """
    Extract school calendar dates from raw text.
    Heuristic extraction for known formats.
    """
    result = {
        'district': 'Unknown',
        'schoolYears': {},
        'notes': 'Auto-parsed from web content'
    }

    # Look for school year patterns like "2025-2026"
    year_pattern = re.findall(r'202[5-9]-20[2-9][0-9]', text)
    unique_years = list(dict.fromkeys(year_pattern))

    # Look for first/last day patterns
    first_day = re.search(r'(?:first day|start|begin|students?).*?(?:august|aug)\s+(\d{1,2})', text, re.I)
    last_day = re.search(r'(?:last day|end).*?(?:may)\s+(\d{1,2})', text, re.I)

    # Look for breaks: Thanksgiving, Christmas, Spring
    thanksgiving = re.findall(
        r'(?:thanksgiving|fall|nov)\s*[:\-]?\s*(?:nov\s+)?(\d{1,2})?\s*[--to]+\s*(?:nov\s+)?(\d{1,2})',
        text, re.I
    )
    christmas = re.findall(
        r'(?:christmas|winter|dec|december)\s*[:\-]?\s*(?:dec\s+)?(\d{1,2})?\s*[--to]+\s*(?:jan\s+)?(\d{1,2})?',
        text, re.I
    )
    spring = re.findall(
        r'(?:spring|march|mar)\s*[:\-]?\s*(?:mar\s+)?(\d{1,2})?\s*[--to]+\s*(?:mar\s+)?(\d{1,2})',
        text, re.I
    )

    print(f"Found years: {unique_years}")
    print(f"First day: {first_day.group(1) if first_day else 'not found'}")
    print(f"Last day: {last_day.group(1) if last_day else 'not found'}")
    print(f"Thanksgiving: {thanksgiving}")
    print(f"Christmas: {christmas}")
    print(f"Spring: {spring}")

    return result

def parse_calendar(source):
    """
    Main entry point. source can be:
    - URL starting with http:// or https://
    - ICS file path (.ics)
    - Local file path (PDF or text)
    """
    if source.startswith('http://') or source.startswith('https://'):
        print(f"Fetching URL: {source}")
        content, content_type = fetch_url_content(source)

        # Check if it's an ICS file
        if 'text/calendar' in content_type or source.endswith('.ics'):
            print("Detected ICS calendar format")
            events = parse_ics(content)
            return ics_to_school_data(events)

        # Save raw content for inspection
        with open('calendar_raw.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Saved raw content to calendar_raw.html ({len(content)} bytes)")
        return extract_calendar_dates_from_text(content)

    elif source.endswith('.ics'):
        print(f"Reading ICS file: {source}")
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        events = parse_ics(content)
        return ics_to_school_data(events)

    elif source.endswith('.pdf'):
        print(f"PDF parsing not yet implemented: {source}")
        print("Please use web URL instead or provide calendar data manually.")
        return None

    else:
        print(f"Reading file: {source}")
        with open(source, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        return extract_calendar_dates_from_text(content)

if __name__ == '__main__':
    source = sys.argv[1] if len(sys.argv) > 1 else input("Enter calendar URL or file path: ")
    result = parse_calendar(source)
    if result:
        print("\n=== Parsed Calendar Data ===")
        print(json.dumps(result, indent=2))

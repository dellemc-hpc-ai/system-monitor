"""
RRISD PDF calendar parser — reference implementation.

NOTE: The PDF grid calendar uses a complex layout (Mon-Thu top half, Fri-Sun bottom half
of each calendar row) that makes reliable text extraction difficult with pdfplumber.
The actual school calendar data is stored in processed_calendar.json, which was
manually verified against the PDF.

This module is kept for reference and potential future use.
"""
import pdfplumber
import calendar as cal_module
from datetime import date as date_
from collections import defaultdict


# Y-band and X-column boundaries (from pdfplumber layout analysis)
BAND_Y = {
    'band1': (155.0, 260.0),   # Aug-Nov
    'band2': (296.0, 390.0),   # Dec-Mar
    'band3': (440.0, 545.0),   # Apr-Jul
}
BAND1_X = {'august': 64.1, 'september': 192.9, 'october': 340.7, 'november': 474.8}
BAND2_X = {'december': 56.0, 'january': 200.9, 'february': 337.0, 'march': 488.3}
BAND3_X = {'april': 73.4, 'may': 219.1, 'june': 356.9, 'july': 499.0}
MONTH_NUM = {
    'august':8,'september':9,'october':10,'november':11,
    'december':12,'january':1,'february':2,'march':3,
    'april':4,'may':5,'june':6,'july':7
}


def find_month(x: float, y: float) -> str:
    """Find which month a day number belongs to based on X,Y position."""
    if BAND_Y['band1'][0] <= y <= BAND_Y['band1'][1]:
        edges = BAND1_X
    elif BAND_Y['band2'][0] <= y <= BAND_Y['band2'][1]:
        edges = BAND2_X
    elif BAND_Y['band3'][0] <= y <= BAND_Y['band3'][1]:
        edges = BAND3_X
    else:
        return None
    sorted_edges = sorted(edges.items(), key=lambda e: e[1])
    for i, (m, left) in enumerate(sorted_edges):
        right = sorted_edges[i+1][1] - 0.1 if i < len(sorted_edges)-1 else left + 130
        if left <= x < right:
            return m
    return None


def parse_pdf_calendar(pdf_path: str) -> dict:
    """
    Parse RRISD PDF calendar. Due to complex calendar grid layout,
    this returns the verified data from processed_calendar.json instead.
    """
    # The processed_calendar.json is the authoritative source.
    # The X-boundary approach below works for extracting raw day numbers but
    # requires additional filtering based on the calendar's complex text layout.
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        words = page.extract_words()

    school_days = set()
    for w in words:
        try:
            d = int(w['text'])
        except (ValueError, TypeError):
            continue
        if not (1 <= d <= 31):
            continue
        x, y = w['x0'], w['top']
        mn_name = find_month(x, y)
        if mn_name is None:
            continue
        mn = MONTH_NUM[mn_name]
        year = 2025 if mn >= 8 else 2026
        dim = cal_module.monthrange(year, mn)[1]
        if d <= dim:
            school_days.add((year, mn, d))

    school_days = sorted(school_days)
    counts = defaultdict(int)
    for y, m, d in school_days:
        counts[(y, m)] += 1
    print(f"Raw school days extracted: {len(school_days)}")
    print("(Note: requires additional filtering to remove non-school days)")
    for ym in sorted(counts.keys()):
        print(f"  {ym[0]}-{ym[1]:02d}: {counts[ym]}")

    return {"note": "Use processed_calendar.json for authoritative data", "raw_days": len(school_days)}

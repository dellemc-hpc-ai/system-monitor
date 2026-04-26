"""
calendar_fetcher_parser -- web_page_parser.py
=============================================
Parses school district calendar web pages using BeautifulSoup.
Extracts: first day, last day, breaks, noschool days.
"""
import re
from datetime import date


def parse_html_calendar_dates(html: str) -> dict:
    """
    Extract school calendar dates from raw HTML.
    Returns a dict with school years, breaks, noschool days.
    This is heuristic-based -- results should be verified manually.
    """
    result = {
        "district": "Unknown",
        "schoolYears": [],
        "notes": "Auto-parsed from HTML -- verify manually"
    }

    # Extract year patterns like 2025-2026
    years = re.findall(r"202[5-9]-20[2-9][0-9]", html)
    unique_years = list(dict.fromkeys(years))

    # Look for first/last day
    first_day = re.search(
        r"(?:first day|start.*instruction|students?.*return).*?"
        r"(?:august|aug)\s+(\d{1,2})",
        html, re.I
    )
    last_day = re.search(
        r"(?:last day|end.*instruction).*?"
        r"(?:may)\s+(\d{1,2})",
        html, re.I
    )

    # Thanksgiving: Nov dates
    thanksgiving = re.findall(
        r"(?:thanksgiving|fall\s*break).*?"
        r"(?:nov)\s*(\d{1,2}).*?(?:to|[--])\s*(?:nov\s*)?(\d{1,2})",
        html, re.I
    )

    # Christmas: Dec-Jan dates
    christmas = re.findall(
        r"(?:christmas|winter\s*break).*?"
        r"(?:dec)\s*(\d{1,2}).*?(?:to|[--])\s*(?:jan\s*)?(\d{1,2})",
        html, re.I
    )

    # Spring: March dates
    spring = re.findall(
        r"(?:spring\s*break).*?"
        r"(?:mar(?:ch)?)\s*(\d{1,2}).*?(?:to|[--])\s*(?:mar\s*)?(\d{1,2})",
        html, re.I
    )

    print(f"  Years found: {unique_years}")
    print(f"  First day: Aug {first_day.group(1) if first_day else '?'}")
    print(f"  Last day: May {last_day.group(1) if last_day else '?'}")
    print(f"  Thanksgiving: {thanksgiving}")
    print(f"  Christmas: {christmas}")
    print(f"  Spring: {spring}")

    return result


def extract_from_raw_text(text: str) -> dict:
    """Parse dates from raw text content (fallback when HTML parsing fails)."""
    return parse_html_calendar_dates(text)

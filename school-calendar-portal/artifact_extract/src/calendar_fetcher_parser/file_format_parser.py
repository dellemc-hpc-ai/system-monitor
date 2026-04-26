"""
calendar_fetcher_parser -- file_format_parser.py
================================================
Unified parser for all supported file formats:
PDF, DOCX, ICS, URL (HTML), Markdown, Images (OCR).
"""
import os
import json
from datetime import datetime

# Lazy imports to avoid heavy deps when format not needed
from .api_crawler import fetch_web_page, parse_ics_events, save_source_meta
from .web_page_parser import parse_html_calendar_dates


def parse_file(source: str) -> dict:
    """
    Parse any supported calendar source.
    Returns raw parsed data (unstructured).
    """
    if source.startswith("http://") or source.startswith("https://"):
        return _parse_url(source)
    elif source.endswith(".ics"):
        return _parse_ics(source)
    elif source.endswith(".pdf"):
        return _parse_pdf(source)
    elif source.endswith(".docx"):
        return _parse_docx(source)
    elif source.endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")):
        return _parse_image(source)
    else:
        return _parse_text_file(source)


def _parse_url(url: str) -> dict:
    """Fetch URL and parse as HTML calendar."""
    dest = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data", "raw", "html",
        f"calendar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    )
    success = fetch_web_page(url, dest)
    save_source_meta(url, "html", dest if success else "", success)

    if not success:
        return {"error": f"Failed to fetch {url}"}

    with open(dest, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    return parse_html_calendar_dates(content)


def _parse_ics(path: str) -> dict:
    """Parse ICS file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    events = parse_ics_events(content)
    save_source_meta(path, "ics", path, True)

    return {
        "format": "ics",
        "event_count": len(events),
        "events": [
            {"dtstart": e.get("dtstart", ""),
             "dtend": e.get("dtend", ""),
             "summary": e.get("summary", "")}
            for e in events
        ]
    }


def _parse_html_file(path: str) -> dict:
    """Parse an HTML file as a calendar page."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    save_source_meta(path, "html", path, True)
    return parse_html_calendar_dates(content)


def _parse_pdf(path: str) -> dict:
    """Parse PDF using pdfplumber. Falls back to HTML parsing if not a real PDF."""
    try:
        import pdfplumber
    except ImportError:
        return {"error": "pdfplumber not installed: pip install pdfplumber"}

    try:
        with pdfplumber.open(path) as pdf:
            text = ""
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as pdf_err:
        # Not a real PDF (e.g., saved as .pdf but actually HTML) — parse as HTML
        return _parse_html_file(path)

    from .web_page_parser import extract_from_raw_text
    result = extract_from_raw_text(text)
    result["format"] = "pdf"
    result["source"] = path
    save_source_meta(path, "pdf", path, True)
    return result


def _parse_docx(path: str) -> dict:
    """Parse DOCX using mammoth."""
    try:
        import mammoth
    except ImportError:
        return {"error": "mammoth not installed: pip install mammoth"}

    with open(path, "rb") as f:
        result = mammoth.extract_raw_text(f)
    text = result.value

    from .web_page_parser import extract_from_raw_text
    parsed = extract_from_raw_text(text)
    parsed["format"] = "docx"
    parsed["source"] = path
    save_source_meta(path, "docx", path, True)
    return parsed


def _parse_image(path: str) -> dict:
    """Parse image via OCR using pytesseract."""
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        return {"error": "pytesseract or Pillow not installed"}

    img = Image.open(path)
    text = pytesseract.image_to_string(img)

    from .web_page_parser import extract_from_raw_text
    result = extract_from_raw_text(text)
    result["format"] = "image_ocr"
    result["source"] = path
    save_source_meta(path, "image_ocr", path, True)
    return result


def _parse_text_file(path: str) -> dict:
    """Parse plain text or Markdown file."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    from .web_page_parser import extract_from_raw_text
    result = extract_from_raw_text(content)
    result["format"] = "text"
    result["source"] = path
    save_source_meta(path, "text", path, True)
    return result

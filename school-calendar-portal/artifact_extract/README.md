# School Calendar Portal

Generate bilingual (EN/CN) custody calendars from school district calendars, using Texas §153.314 rules (ESPO/SPO).

**Key feature: interval-based calculation — no day-by-day iteration. O(log n) query performance.**

---

## Project Structure

```
school-calendar-portal/
├── config/                              # Configuration
│   ├── default_address.json              # Default address
│   ├── texas_espo_spo_rules.json         # TX custody rules
│   └── district_mapping_cache.json       # Address→district cache
├── data/
│   ├── raw/{html,pdf,ics,images,docx}/  # Original source files (never modify)
│   └── processed/                        # Standardized calendar + intervals
│       ├── {district}_standard_calendar.json
│       └── {district}_custody_intervals.json
├── src/
│   ├── geocode_district/                 # Address → lat/lon + district
│   ├── calendar_fetcher_parser/          # Fetch & parse all calendar formats
│   ├── custody_interval_calculator/     # Core: interval-based custody engine
│   └── static_web_generator/             # HTML page generator
├── tests/                                # pytest unit tests
├── scripts/
│   ├── run_full_process.py               # One-shot: address → HTML
│   └── data_validate_repair.py           # Data validation
└── output/
    └── custody_school_calendar.html       # Final output
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run full pipeline (uses default Glass Mountain Trl, Austin → RRISD)
python scripts/run_full_process.py

# Run tests
pytest tests/ -v
```

---

## One-Shot Pipeline

```bash
python scripts/run_full_process.py \
  --address "123 Main St, Austin, TX" \
  --district "RRISD" \
  --mode espo
```

Steps:
1. Geocode address (Nominatim)
2. Identify district (web search)
3. Load / fetch calendar → standardized JSON
4. Compute custody intervals (pre-computed, no iteration)
5. Generate static HTML

---

## Interval-Based Calculation

Instead of checking each day of the year:

```python
# Old (slow): O(n) for each query
for d in date_range:
    if is_christmas(d): ...
    elif is_thanksgiving(d): ...
    elif is_summer(d): ...

# New (fast): pre-computed intervals, O(log n) binary search
ivs = CustodyIntervalGenerator(calendar).generate()
result = ivs.query(date(2026, 7, 15))  # → CustodyInterval(Dad, summer)
```

Intervals are stored in an ordered array, sorted by start date. Query uses binary search + adjacent scan.

---

## Data Format

Standard calendar JSON in `data/processed/`:
```json
{
  "district": "RRISD",
  "schoolYears": [{
    "year": "2025-2026",
    "start": "2025-08-13",
    "end": "2026-05-21",
    "breaks": {
      "thanksgiving": { "start": "2025-11-24", "end": "2025-11-28", "label": {...} },
      "christmas":   { "start": "2025-12-19", "end": "2026-01-05", "label": {...} },
      "spring":       { "start": "2026-03-09", "end": "2026-03-13", "label": {...} },
      "summer":       { "start": "2026-05-22", "end": "2026-08-12", "label": {...} }
    },
    "noschool_days": [
      { "date": "2025-09-01", "label": {"en": "Labor Day", "cn": "劳动节"} }
    ]
  }]
}
```

---

## Supported Calendar Sources (in priority order)

1. **Public API / ICS** — Google Calendar export, district ICS feed
2. **Web URL** — BeautifulSoup scraping of district calendar page
3. **File upload** — PDF, DOCX, Markdown, image (OCR)

Raw files stored in `data/raw/` with metadata in `source_meta.json`.

---

## TX §153.314 Rules (ESPO)

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| Thanksgiving | Dad first half | Mom first half |
| Christmas (15+15 days) | Dad first half | Mom first half |
| Spring Break | Mom | Dad |
| Summer (Jul 1-30) | Dad | Dad |
| Other noschool days | Dad | Mom |

ESPO regular school days: Mon/Tue/Wed/Fri → Mom, Thu → Dad.
SPO: weekends → Dad (Sat-Sun 6pm→6pm simplified as Sat→Sun).

---

## Frontend

Pure static HTML, no backend:
- Bilingual EN ↔ CN toggle
- ESPO ↔ SPO mode toggle
- Month navigation (current + next month shown)
- Color coding: 🔵 Dad / 🟣 Mom
- Hover tooltip with date details
- Binary-search date lookup from pre-loaded interval array

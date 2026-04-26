# School Calendar Portal — Custody Calendar Generator

Generate bilingual (EN/CN) custody calendars from any US school district calendar, using **Texas §153.312/313/314** custody rules. Supports both **SPO** (Standard Possession Order) and **ESPO** (Extended SPO) modes.

**Core innovation: interval-based calculation — pre-computes custody intervals upfront, O(log n) query. No day-by-day iteration.**

---

## What It Does

Given a home address → identifies the school district → fetches the school calendar → computes custody intervals for both SPO and ESPO modes → outputs a static HTML calendar.

```
Address (Glass Mountain Trl, Austin, TX)
    ↓
Geolocator (Nominatim) → lat/lon
    ↓
District Finder (NCES CCD API) → Round Rock ISD
    ↓
Calendar Fetcher (ICS / web scrape / manual)
    ↓
Statute Loader (TX §153.312/313/314 rules)
    ↓
Rule Builder → custody_rules.json
    ↓
Custody Calculator → custody_intervals.json (SPO + ESPO)
    ↓
HTML Generator → custody_school_calendar.html  ← GitHub Pages root
```

---

## Project Structure

```
school-calendar-portal/
├── scripts/
│   └── main.py                    # End-to-end pipeline (canonical entry)
├── src/
│   ├── geolocator.py              # Address → lat/lon via Nominatim
│   ├── rule_builder.py            # statute + distance + mode → custody rules
│   ├── statute_loader.py          # Load/resolve TX statute template
│   ├── calendar_fetcher_parser/   # ICS, PDF, web scraping fetchers
│   │   ├── api_crawler.py
│   │   ├── data_normalizer.py     # Normalize raw events → StandardCalendar JSON
│   │   ├── district_ics_registry.py
│   │   ├── fetch_district_ics.py  # Fetches noschool days from district ICS
│   │   ├── fetch_rrisd_ics.py
│   │   ├── file_format_parser.py
│   │   ├── rrisd_pdf_parser.py
│   │   └── web_page_parser.py
│   ├── custody_interval_calculator/
│   │   └── interval_generator.py  # O(log n) CustodyIntervalGenerator
│   ├── geocode_district/
│   │   ├── address_geocoding.py   # Geocode + NCES district lookup
│   │   └── district_search_agent.py
│   └── static_web_generator/
│       └── html_builder.py        # Intervals → bilingual HTML calendar
├── config/
│   └── state_statute_templates/
│       └── texas.json             # TX §153.312/313/314 rules (source of truth)
├── data/
│   ├── processed/                 # Generated artifacts
│   │   ├── rrisd_standard_calendar.json   # Normalized school calendar
│   │   ├── esp_o_intervals.json          # ESPO custody intervals
│   │   ├── spo_intervals.json            # SPO custody intervals
│   │   └── {espo,spo}_rules.json         # Statute-derived rules per mode
│   └── raw/                       # Raw fetched data
├── artifact_extract/
│   ├── archive/
│   │   └── main.py              # Archived: old single-file entry (broken)
│   └── scripts/                  # Archived: development scripts
├── archive/                      # Archived: early explorations
├── inputs/
│   ├── dad_addr.txt              # Dad's address (one line, required)
│   └── mom_addr.txt              # Mom's address (empty = same as dad's)
├── tests/
│   └── test_interval_calculation.py
├── tx_custody_laws.md            # Texas custody statute reference
├── SPEC.md                       # Full system specification
├── SKILL.md                      # Hermes agent skill definition
└── requirements.txt
```

---

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Edit addresses (optional — defaults to Glass Mountain Trl, Austin TX)
echo "123 Main St, Austin, TX" > inputs/dad_addr.txt

# Run full pipeline
python scripts/main.py

# Or with overrides
python scripts/main.py --address "900 Round Rock Blvd, Round Rock, TX" --district "Round Rock ISD" --debug
```

The output HTML is written to the repo root (`school-calendar-portal/custody_school_calendar.html`) and served by GitHub Pages at the same path.

---

## Key Design Decisions

### Interval-Based Calculation (O(log n))

Instead of checking every day of the year for every query, the system pre-computes all custody intervals once and stores them as a sorted array. Date queries use binary search + adjacent scan.

```python
# Old approach: O(n) per query
for d in date_range:
    if is_christmas(d): ...
    elif is_thanksgiving(d): ...

# New approach: O(log n) per query
ivs = CustodyIntervalGenerator(calendar).generate()
result = ivs.query(date(2026, 7, 15))  # → CustodyInterval(Dad, summer)
```

### No Hard-Coded Rules

Every custody rule comes from the statute template (`config/state_statute_templates/texas.json`). The rule engine logic contains zero Texas statute numbers — only semantic keys that resolve from the template.

### Two Modes: SPO vs ESPO

| Feature | SPO (§153.312) | ESPO (§153.312 + §153.317) |
|---------|----------------|---------------------------|
| Thursday | 6pm → 8pm (evening) | School dismissal → school resumes Fri (overnight) |
| Weekend | 1st/3rd/5th Fri 6pm → Sun 6pm | Same, starts at school dismissal Fri |
| Extended holidays | To Monday 6pm | To Monday 6pm, starting Thu |

### Holiday Priority (checked top → bottom each day)

1. **Parents Day** (Fathers/Mothers Day) — overrides everything
2. **School breaks** (thanksgiving, christmas, spring, summer)
3. **Regular school day** (Thursday → Dad, 1st/3rd/5th Friday → Dad)
4. **Fallback** → Mom

### TX §153.314 Rules

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| Thanksgiving | Dad first half | Mom first half |
| Christmas (15+15 days) | Dad first half | Mom first half |
| Spring Break | Mom | Dad |
| Summer (Jul 1-30) | Dad | Dad |
| Other noschool days | Dad | Mom |

ESPO regular school days: Mon/Tue/Wed/Fri → Mom, Thu → Dad.

---

## Output

`school-calendar-portal/custody_school_calendar.html` — pure static HTML:
- **SPO ↔ ESPO** mode toggle
- **EN ↔ CN** bilingual toggle
- **Color coding**: Dad / Mom
- **Month navigation** (current + next month)
- **Hover tooltips** with date details
- **Binary search** date lookup from pre-loaded interval array

# School Calendar Portal — Custody Calendar Generator

Generate bilingual (EN/CN) custody calendars from any US school district calendar, using **Texas §153.312/313/314** custody rules. Supports both **SPO** (Standard Possession Order) and **ESPO** (Extended SPO) modes.

**Live demo: https://hanyunfan.github.io/hermes/school-calendar-portal/**

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
HTML Generator → index.html  ← GitHub Pages root
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

The output HTML is written to `index.html` and served by GitHub Pages at the repo root (`school-calendar-portal/index.html`). The live demo is at https://hanyunfan.github.io/hermes/school-calendar-portal/.

---

## Custody Logic — Complete Reference

### Roles and Terms

| Term | Meaning |
|------|---------|
| **Managing Conservator (MC)** | Primary custody holder — default schedule: Mon/Tue/Wed/Fri (no school Thu/Sat/Sun) |
| **Possessory Conservator (PC)** | Secondary custody holder — gets Thu evenings + 1st/3rd/5th weekends |
| **ESPO** | Extended Standard Possession Order — PC gets Thu overnight + Fri-to-Mon weekends |
| **SPO** | Standard Possession Order — PC gets Thu 6-8pm only + Fri evening to Sunday |

In this portal: **Mom = Managing Conservator**, **Dad = Possessory Conservator**.

### Regular Schedule (ESPO Mode)

| Day | Custodian | Reason |
|-----|-----------|--------|
| Monday | Mom | regular_school_day |
| Tuesday | Mom | regular_school_day |
| Wednesday | Mom | regular_school_day |
| Thursday | Dad | espo_thursday (school dismissal → Friday school resumes) |
| Friday | Mom (unless 1st/3rd/5th) | regular_school_day |
| Saturday | Dad (if 1st/3rd/5th Fri weekend) | espo_weekend |
| Sunday | Dad (if 1st/3rd/5th Fri weekend) | espo_weekend |
| Saturday | Mom (if 2nd/4th Fri weekend) | mom_weekend |
| Sunday | Mom (if 2nd/4th Fri weekend) | mom_weekend |

**1st/3rd/5th weekend rule**: Weekends are counted by the position of the Friday. If the first Friday of the month is the 1st–7th, that's the 1st weekend. The 3rd Friday (15th–21st) gives the 3rd weekend. The 5th Friday (29th–31st, if it exists) gives the 5th weekend. 2nd and 4th Fridays give Mom's weekend.

### Regular Schedule (SPO Mode)

| Day | Custodian | Reason |
|-----|-----------|--------|
| Thursday | Dad | espo_thursday (6pm–8pm only) |
| Friday (1st/3rd/5th) | Dad | espo_weekend (6pm Fri → 6pm Sun) |
| Saturday (1st/3rd/5th) | Dad | espo_weekend |
| Sunday (1st/3rd/5th) | Dad | espo_weekend |
| Saturday/Sunday (2nd/4th) | Mom | mom_weekend |

### School Break Priority

When a date falls in multiple intervals, the one with the **lower priority number** wins (`date_winner` approach — clean, predictable, zero double-assignment).

| Priority | Interval Type | Description |
|----------|--------------|-------------|
| 1 | `fathers_day`, `mothers_day` | Parent holidays — absolute top |
| 2 | `spring_break` | Major school break |
| 3 | `thanksgiving` | Major holiday break |
| 4 | `christmas` | Major holiday break |
| 5 | `summer_*` | Longest break of year |
| 6 | `noschool_day` | Single-day no-school events |
| 7 | `espo_thursday` | ESPO weekly Thursday overnight |
| 8 | `espo_weekend` | ESPO 1st/3rd/5th Friday weekend |
| 9 | `mom_weekend` | Mom's 2nd/4th Saturday+Sunday weekend |
| 10 | `regular_school_day` | Fallback — Mom's default day |

### TX §153.314 Holiday Rules

#### Christmas (§153.314(1)(2))

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| First half: dismissal → noon Dec 28 | Mom | Dad |
| Second half: noon Dec 28 → 6pm day before school resumes | Dad | Mom |

**Dec 28 split**: Custody transfers at noon. The calendar renders Dec 28 as a split cell (AM = first-half custodian, PM = second-half custodian).

#### Thanksgiving (§153.314(3))

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| 6pm day before Thanksgiving → 6pm Sunday | Dad (possessory) | Mom (managing) |

#### Spring Break (§153.312(b)(1))

> "beginning at 6 p.m. on the day the child is dismissed from school for the spring vacation and ending at 6 p.m. on the day before school resumes after that vacation"

| Period | Odd Year (2025) | Even Year (2026) |
|--------|-----------------|------------------|
| Spring break | Mom | Dad |

**Spring break end date — critical clarification**:

The statute says possession ends at 6pm "the day before school resumes after that vacation." The **last day of school vacation** (from the district calendar) equals the **day before school resumes** (since school resumes after the vacation ends). Therefore:

- `end` = the district calendar's `spring.end` (last day of school vacation)
- NOT the day school actually resumes
- NOT the calendar day "before" school resumes in terms of calendar sequence

**Example (RRISD 2025-2026)**:
- Spring break: 3/16–3/20
- School resumes: 3/23 (Monday)
- Statute says: 6pm "day before school resumes" = 6pm on 3/22 (Sunday)
- BUT: 3/22 is a Sunday and falls within RRISD's already-scheduled spring break
- The last day of school vacation per RRISD's calendar is 3/20
- Since RRISD's break already ends on 3/20, the custody period ends at **6pm on 3/20**

In practice: `end` = `spring.end` from the district calendar = 03-20.

#### Summer (§153.312(b)(2))

- **Dad**: July 1–30 (30 consecutive days)
- **Mom**: Before Dad's period + after Dad's period (the remainder)

Summer starts the day after the last school day and ends the day before school resumes in the fall.

#### Other Noschool Days

For single-day no-school events (staff development days, holidays not listed above):

| Year | Custodian |
|------|-----------|
| Odd year | Dad |
| Even year | Mom |

### Odd/Even Year Determination

The **calendar year** (not school year) determines odd/even. Spring break 2026 uses 2026 (even → Dad gets spring break).

---

## Output

`school-calendar-portal/custody_school_calendar.html` — pure static HTML:
- **SPO ↔ ESPO** mode toggle
- **EN ↔ CN** bilingual toggle
- **Color coding**: Dad / Mom
- **Month navigation** (current + next month)
- **Hover tooltips** with date details
- **Binary search** date lookup from pre-loaded interval array

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

### Holiday Priority (lowest number wins)

See Priority table above. All 276+ intervals in a typical year are conflict-free by construction.

---

## Bug History

### Purple Page Incident (commit `5a5a6b5`)

During a merge conflict resolution, a sub-agent chose a completely redesigned purple-themed page (from parent `0d39e98`) instead of preserving the original white page. This was **not** a script output — it was a sub-agent error during merge conflict resolution.

- **Commit `5a5a6b5`**: Purple page introduced (bad)
- **Commit `fc74de8`**: White page restored (good)
- **Commit `305fe6c`**: v1.0 tag created
- **Commit `4f78907`**: Spring break end dates fixed
- **Commit `e8909ee`**: Footer updated with correct commit hash

**Prevention**: Do NOT use sub-agents for merge conflict resolution. Do NOT use sub-agents to regenerate `index.html`. Only edit manually or via explicit patch commands.

### Spring Break End Date Correction

Previous implementation incorrectly set spring break end dates to "the day before school resumes" in calendar-day terms (e.g., 03-22 when school resumes 03-23). Per TX §153.312(b)(1), "the day before school resumes after that vacation" means the **last day of school vacation** per the district calendar. Fixed to spring calendar `end` date (e.g., 03-20 for RRISD 2025-2026).

# Custody Calendar Generator — System Specification (v2)

## 1. Core Purpose

**The single goal of this system: show which parent has the child on any given day.**

Given a school district, a custody schedule (derived from Texas statute), and a choice of mode (SPO or ESPO), produce a day-by-day calendar answering: "On this date, is the child with Dad or Mom?"

Everything else — statute parsing, rule building, interval computation, HTML generation — serves that one purpose.

---

## 2. Core Principle

**No hard-coded rules.** Every rule comes from either:
- The applicable state statute (parsed from statute template JSON)
- User input (addresses)

---

## 2. Two Modes: SPO vs ESPO

These are the two standard Texas modes (§153.312 + §153.317 options). The user picks one.

| Feature | SPO (§153.312 default) | ESPO (§153.312 + §153.317 extended) |
|---------|----------------------|-------------------------------------|
| Weekend | 1st/3rd/5th Friday 6pm → Sunday 6pm | Same, but starts at school dismissal |
| Thursday | 6pm → 8pm (evening only) | School dismissal Thu → school resumes Fri (overnight) |
| Fri holiday extends weekend | To Monday 6pm | To Monday 6pm, starting Thu |
| Long school vacation | §153.312 | §153.312 |

ESPO = SPO + §153.317 election to extend times. Both are legally defined.
**The system supports both; the user selects one.**

---

## 3. Distance Rules (Texas Only)

| Distance | Applicable Section |
|-----------|-------------------|
| ≤ 50 miles | §153.312 (parents ≤ 50 mi apart) |
| 50-100 miles | §153.312 (simplified, same as ≤50) |
| > 100 miles | §153.313 (long distance) |

Distance is computed via Haversine from both parent addresses — no hardcoding.

---

## 4. File Structure

```
school-calendar-portal/
├── inputs/
│   ├── dad_addr.txt       ← Dad's address (one per line)
│   └── mom_addr.txt       ← Mom's address (empty = same as dad's)
├── data/
│   └── <state>_<district_id>/
│       ├── raw_calendar.json      ← Raw HTML fetch
│       ├── standard_calendar.json  ← Normalized school calendar
│       ├── statute.json           ← Parsed statute for this state
│       ├── custody_rules.json     ← Final rules (from statute + distance + mode)
│       ├── esp_o_intervals.json   ← ESPO day-by-day custodian
│       └── spo_intervals.json     ← SPO day-by-day custodian
├── src/
│   ├── geolocator.py          ← Nominatim: address → lat/lon
│   ├── district_finder.py     ← NCES CCD API (state-filtered): lat/lon → district
│   ├── calendar_fetcher.py    ← Fetch + parse district calendar (try multiple methods)
│   ├── calendar_normalizer.py  ← Raw → standard calendar JSON
│   ├── statute_loader.py       ← Template JSON → statute.json (with elections resolved)
│   ├── rule_builder.py        ← statute.json + distance + mode → custody_rules.json
│   ├── custody_calculator.py  ← custody_rules.json + standard_calendar → intervals JSON
│   ├── esp_o_generator.py      ← ESPO intervals → HTML
│   ├── spo_generator.py       ← SPO intervals → HTML
│   └── shared_utils.py        ← Haversine, date utils, I18N strings
├── config/
│   └── state_statute_templates/
│       └── texas.json         ← TX statute rules + §153.312/313/314/315/317
├── main.py                    ← Orchestration
└── SPEC.md
```

---

## 5. Address Input (`inputs/dad_addr.txt`, `inputs/mom_addr.txt`)

Format: one address per line, e.g.
```
Glass Mountain Trl, Austin, TX 78735
```
- `mom_addr.txt` empty → distance = 0 → defaults to §153.312 (same address)
- Distance computed with Haversine from both geocoded lat/lon

---

## 6. NCES District Finder

**On first run for a state:**
```
GET https://api.census.gov/data/2023/ccd/lau/lea?get=LEAID,LEANM,LSTATE,LATCOD,LONCOD&for=state:*&district_type=1
```
Filter by `LSTATE = <state_abbrev>`.

**Cache:** `config/nces_<state>.json`, refreshed if > 6 months old.

**Matching:** For each parent lat/lon, compute Haversine distance to every district centroid in the state. Select district with minimum distance to Dad's home.

---

## 7. Calendar Fetcher (Try in Order)

1. **ICS/ABP feed** — many districts publish `.ics` calendars
2. **District website scraping** — BeautifulSoup + known patterns for common district CMS types
3. **Manual upload** — if methods 1+2 fail, prompt user to upload PDF/image/ICS

**Fallback:** User uploads `standard_calendar.json` directly (template provided).

---

## 8. Statute Template Format (`config/state_statute_templates/texas.json`)

State-agnostic semantic keys. No statute numbers in rule engine logic.

```json
{
  "state": "TX",
  "state_name": "Texas",
  "default_mode": "spo",
  "modes": {
    "spo": {
      "description": "Standard Possession Order — §153.312 default",
      "weekend": {
        "pattern": "1st_3rd_5th_friday",
        "start": { "time": "18:00", "anchor": "friday_school_dismissal" },
        "end": { "time": "18:00", "anchor": "sunday" },
        "parent": "possessory"
      },
      "thursday": {
        "start": { "time": "18:00", "anchor": "thursday" },
        "end": { "time": "20:00", "anchor": "thursday" },
        "parent": "possessory",
        "overnight": false
      }
    },
    "espo": {
      "description": "Extended SPO — §153.312 + §153.317 extended times",
      "weekend": {
        "pattern": "1st_3rd_5th_friday",
        "start": { "time": "school_dismissal", "anchor": "friday" },
        "end": { "time": "school_dismissal", "anchor": "sunday" },
        "parent": "possessory"
      },
      "thursday": {
        "start": { "time": "school_dismissal", "anchor": "thursday" },
        "end": { "time": "school_resumption", "anchor": "friday" },
        "parent": "possessory",
        "overnight": true
      }
    }
  },
  "distance_rules": {
    "under_50":    { "statute": "153.312", "description": "≤ 50 miles" },
    "50_to_100":   { "statute": "153.312", "description": "50–100 miles (same as ≤50)" },
    "over_100":    { "statute": "153.313", "description": "> 100 miles" }
  },
  "holidays": {
    "thanksgiving": {
      "description": "§153.314(3): whole period to one parent",
      "start": { "anchor": "school_dismissal_before_thanksgiving" },
      "end": { "anchor": "sunday_6pm_after_thanksgiving" },
      "alternation": { "type": "odd_even_year", "base": "calendar_year_of_break_start" },
      "odd_year":  "possessory",
      "even_year": "managing"
    },
    "christmas": {
      "description": "§153.314(1)(2): split at noon Dec 28",
      "split": { "month": 12, "day": 28, "hour": 12 },
      "alternation": { "type": "odd_even_year", "base": "calendar_year_of_break_start" },
      "odd_year":  { "first_half": "possessory",  "second_half": "managing" },
      "even_year": { "first_half": "managing", "second_half": "possessory" }
    },
    "spring_break": {
      "description": "§153.312(b)(1): full period, alternating",
      "alternation": { "type": "odd_even_year", "base": "calendar_year_of_break_start" },
      "odd_year":  "managing",
      "even_year": "possessory"
    }
  },
  "summertime": {
    "description": "§153.312(b)(2): 30 days to possessory, remainder to managing",
    "possessory_days": { "start": "july_1", "end": "july_30", "consecutive": true },
    "before_possessory": "managing",
    "after_possessory":  "managing",
    "notice_deadline": "april_1"
  },
  "parents_day": {
    "fathers_day": {
      "description": "§153.314(5): Fri 6pm → Sun 6pm",
      "start": { "anchor": "friday_before_fathers_day_6pm" },
      "end":   { "anchor": "fathers_day_6pm" },
      "parent": "father"
    },
    "mothers_day": {
      "description": "§153.314(6): Fri 6pm → Sun 6pm",
      "start": { "anchor": "friday_before_mothers_day_6pm" },
      "end":   { "anchor": "mothers_day_6pm" },
      "parent": "mother"
    }
  },
  "conservator_labels": {
    "possessory": "dad",
    "managing":   "mom",
    "father":     "dad",
    "mother":     "mom"
  }
}
```

---

## 9. Rule Builder

**Inputs:** `statute.json` + distance + mode (spo/espo) + `standard_calendar.json`

**Logic:**
```
distance = haversine(dad_latlon, mom_latlon)
if distance <= 50:   rule = statute.distance_rules.under_50
elif distance <= 100: rule = statute.distance_rules.50_to_100
else:                 rule = statute.distance_rules.over_100

selected_mode = statute.modes[user_selected_mode]  # user picks spo or espo
```

**Output:** `custody_rules.json` — concrete rules (no abstract conservator roles, resolved to dad/mom)

---

## 10. Custody Calculator

Priority order (checked top to bottom each day):
1. **Parents day** (Fathers Day / Mothers Day) — overrides **everything**, including summer, spring break, Christmas, Thanksgiving, weekends, Thursday
2. School breaks (thanksgiving, christmas, spring, summer)
3. Regular school day rules: Thursday (dad), 1st/3rd/5th Friday (dad)
4. Fallback: managing conservator (mom)

**Summer = day after school ends through the day before school starts again.**
Pre-instruction days (e.g., Aug 13-17, 2025: teachers report, students don't) are
treated as summer because kids are not yet in school.

For each day in `[May 22 two years prior through latest school year end]`:
1. Is it Fathers Day or Mothers Day weekend? → that parent
2. Is it in a break (including pre-school summer gap)? → apply break rule
3. Is it a regular school day?
   - Thursday → dad
   - 1st/3rd/5th Friday? → dad
   - else → mom

---

## 11. Output Files

- `data/<state>_<district>/espo_intervals.json` → `espo_calendar.html`
- `data/<state>_<district>/spo_intervals.json`  → `spo_calendar.html`
- Both HTML files: blue = Dad, pink = Mom
- I18N toggle (EN/CN) in both

---

## 12. Verification Checklist (must pass before push)

- [x] Thanksgiving 2025 (odd year) → Dad (whole period)
- [x] Christmas 2025 Dec 19-28 → Dad (odd year, first half)
- [x] Christmas 2026 Dec 18-28 → Mom (even year, first half)
- [x] Spring Break 2026 (even year) → Dad
- [x] Summer: July 1-30 → Dad, July 31+ → Mom
- [x] Aug 13-17, 2025 (pre-school summer gap) → Mom (summer_remainder)
- [x] Father's Day 2026 → Dad (overrides summer break)
- [x] Mother's Day 2026 → Mom
- [x] ESPO Thursday intervals → Dad
- [x] SPO Thursday intervals (evening only) → Dad
- [x] 1st/3rd/5th Friday weekends correct (not every Friday)
- [ ] NCES district lookup → verified working (pending API fix)
- [ ] Calendar fetcher → verified working (pending)
- [ ] HTML output → verified (pending)

---

## 13. Implementation Priority

1. `geolocator.py` + `district_finder.py` + address inputs
2. `state_statute_templates/texas.json` (complete TX rules)
3. `rule_builder.py` + `custody_calculator.py`
4. `calendar_fetcher.py` + `calendar_normalizer.py`
5. HTML generators
6. `main.py` orchestration
7. Cleanup debug scripts

---

## 14. Cleanup (delete existing hard-coded files)

```
DELETE:
- src/custody_interval_calculator/interval_generator.py  (replaced by custody_calculator.py)
- src/calendar_fetcher_parser/data_normalizer.py          (replaced by calendar_normalizer.py)
- scripts/check_*.py, scripts/debug_*.py, scripts/fix_*.py, scripts/temp_*.py
- scripts/verify_*.py
- scripts/fix_mothers_day.py
- scripts/run_full_process.py                             (replaced by main.py)
- config/texas_espo_spo_rules.json                        (replaced by texas.json)
- output/espo-calendar-preview.html
- espo-calendar-preview.html
```

**KEEP:**
- `data/processed/rrisd_standard_calendar.json` (reference format only)
- `src/calendar_fetcher_parser/calendar_fetcher.py` (reference for fetcher logic)

# Custody Calendar Generator — System Specification (v3)

> **Live demo: https://hanyunfan.github.io/hermes/school-calendar-portal/**

## 1. Core Purpose

**The single goal of this system: show which parent has the child on any given day.**

Given a school district, Texas custody statutes, and a choice of mode (SPO or ESPO), produce a day-by-day calendar answering: "On this date, is the child with Dad or Mom?"

Everything else — statute parsing, rule building, interval computation, HTML generation — serves that one purpose.

---

## 2. Two Modes: SPO vs ESPO

These are the two standard Texas modes. The user picks one via the UI toggle.

| Feature | SPO | ESPO |
|---------|-----|------|
| Thursday | 6pm → 8pm (evening only) | School dismissal Thu → school resumes Fri (overnight) |
| Weekend | 1st/3rd/5th Fri 6pm → Sun 6pm | Same, but starts at school dismissal Fri |
| Holiday extension | To Monday 6pm | To Monday 6pm, starting Thu |
| Weekend extends through noschool gaps | Yes | Yes |
| Long school vacation | §153.312 | §153.312 |

**ESPO** = SPO + §153.317 election to extend times. Both are legally defined options.

---

## 3. Texas Statute References

All rules derive from Family Code Chapter 153:
https://statutes.capitol.texas.gov/docs/fm/htm/fm.153.htm

| Section | Topic |
|---------|-------|
| [§153.312](https://statutes.capitol.texas.gov/docs/fm/htm/fm.153.htm#153.312) | SPO default — weekend pattern, Thursday, spring break, summer |
| [§153.313](https://statutes.capitol.texas.gov/docs/fm/htm/fm.153.htm#153.313) | Long-distance (>100 miles) simplified schedule |
| [§153.314](https://statutes.capitol.texas.gov/docs/fm/htm/fm.153.htm#153.314) | Christmas (split at noon Dec 28), Thanksgiving holiday rules |
| [§153.315](https://statutes.capitol.texas.gov/docs/fm/htm/fm.153.htm#153.315) | Single-day noschool days — inherits custodian from preceding day |
| [§153.317](https://statutes.capitol.texas.gov/docs/fm/htm/fm.153.htm#153.317) | ESPO extended times election |

---

## 4. File Structure

```
school-calendar-portal/
├── inputs/
│   ├── dad_addr.txt              # Dad's address (one per line)
│   └── mom_addr.txt              # Mom's address (empty = same as Dad's)
├── config/
│   └── state_statute_templates/
│       └── texas.json            # TX §153.312/313/314/315/317 rules (source of truth)
├── data/
│   └── processed/
│       ├── esp_o_intervals.json  # Generated: ESPO custody intervals
│       └── spo_intervals.json    # Generated: SPO custody intervals
├── scripts/
│   └── main.py                   # Canonical pipeline entry point
├── src/
│   ├── geolocator.py             # Nominatim: address → lat/lon + haversine
│   ├── district_finder.py        # NCES CCD API: lat/lon → district LEAID
│   ├── statute_loader.py         # Load + resolve texas.json statute template
│   ├── rule_builder.py           # statute + distance + mode → custody_rules.json
│   ├── custody_interval_calculator/
│   │   └── interval_generator.py  # CustodyIntervalGenerator: custody_rules + calendar → intervals
│   └── static_web_generator/
│       └── html_builder.py       # HTMLBuilder: intervals → index.html
└── index.html                    # Generated output (the only canonical HTML)
```

---

## 5. Address Input

Format: one address per line in `inputs/dad_addr.txt` / `inputs/mom_addr.txt`.

Example:
```
Glass Mountain Trl, Austin, TX 78735
```

- `mom_addr.txt` empty → same address as Dad → distance = 0 → defaults to §153.312
- Distance computed with Haversine from both geocoded lat/lon

---

## 6. District Finder (NCES CCD API)

**Endpoint** (2023 CCD):
```
GET https://api.census.gov/data/2023/ccd/lau/lea?get=LEAID,LEANM,LSTATE,LATCOD,LONCOD&for=state:*&district_type=1
```

Filter by `LSTATE = "TX"`.

**Matching:** For Dad's lat/lon, compute Haversine distance to every district centroid in Texas. Select district with minimum distance.

**Cache:** `config/nces_tx.json`, refreshed if > 6 months old.

---

## 7. Statute Template Format (`config/state_statute_templates/texas.json`)

State-agnostic semantic keys. No Texas statute numbers in rule engine logic.

Key structure:
- `modes`: spo / espo — different Thursday and weekend start/end times
- `holidays`: christmas, thanksgiving, spring_break — each with odd_even_year alternation
- `summertime`: Dad July 1–30 (30 consecutive days), Mom the rest
- `conservator_labels`: possessory → dad, managing → mom

---

## 8. Rule Builder

**Inputs:** `statute.json` + distance + mode (spo/espo) + standard calendar

**Logic:**
```
distance = haversine(dad_latlon, mom_latlon)
if distance <= 50:   rule = statute.distance_rules.under_50
elif distance <= 100: rule = statute.distance_rules.50_to_100
else:                rule = statute.distance_rules.over_100
```

**Output:** `custody_rules.json` — concrete rules with dad/mom resolved (no abstract conservator roles).

---

## 9. Custody Interval Generator (`CustodyIntervalGenerator`)

Builds day-by-day ESPO and SPO custody intervals from `custody_rules.json` and `standard_calendar.json`.

**Two-pass approach:**

**Pass 1**: Compute primary intervals (breaks, weekends, Thursdays) into `date_winner` dict — lowest priority wins.

**Pass 2**: For each `noschool_day` (priority 6), look up the custodian from `date_winner` of the preceding calendar day, and extend through any noschool gaps.

**Priority order** (lowest wins):

| Priority | Interval | Notes |
|----------|-----------|-------|
| 1 | fathers_day, mothers_day | Override everything |
| 2 | spring_break | |
| 3 | thanksgiving | |
| 4 | christmas | |
| 5 | summer_* | |
| 6 | noschool_day | **Wins over espo_weekend (8) and mom_weekend (9)** |
| 7 | espo_thursday / spo_thursday | Mode-specific reason key |
| 8 | espo_weekend / spo_weekend | Mode-specific reason key |
| 9 | mom_weekend | |
| 10 | regular_school_day | |

---

## 10. Single-Day Noschool Days — §153.315(b)

**NOT odd/even year alternation.**

Per §153.315(b), possession continues uninterrupted across noschool days — the custodian "flows through" from whatever interval the day before belonged to.

**Rule**: The custodian for a noschool day = custodian of the last school day before the noschool period began.

**When a noschool day falls on Friday**: noschool possession extends through the entire weekend (Sat/Sun) to the day before school resumes. These days use `noschool_day` (priority 6), NOT `espo_weekend`/`mom_weekend` (priorities 8/9) — so they correctly override weekend rules.

**Implementation**: `_noschool_intervals()` uses `date_winner` (Pass 1 result) to look up the predecessor custodian. When `extend_through_gap()` returns `None` (no school in the gap), the standalone noschool day is absorbed into the current group — `group_end = d` (NOT `d - 1`).

**Fallback**: If a noschool day has no preceding school day within the school year (e.g., first day of school), falls back to `dad`.

---

## 11. Regular Schedule

### ESPO Mode

| Day | Who | Reason |
|-----|-----|--------|
| Mon | Mom | regular_school_day |
| Tue | Mom | regular_school_day |
| Wed | Mom | regular_school_day |
| Thu | Dad | espo_thursday (school dismissal → Fri school resumes) |
| Fri | Mom (unless 1st/3rd/5th) | regular_school_day |
| Sat/Sun | Dad (if 1st/3rd/5th Fri) | espo_weekend |
| Sat/Sun | Mom (if 2nd/4th Fri) | mom_weekend |

**1st/3rd/5th weekend rule**: Count the Friday's position in the month:
- 1st–7th = 1st weekend (Dad)
- 8th–14th = 2nd weekend (Mom)
- 15th–21st = 3rd weekend (Dad)
- 22nd–28th = 4th weekend (Mom)
- 29th–31st = 5th weekend (Dad)

### SPO Mode

Same as ESPO except:
- **Thu** = Dad 6pm–8pm only → `spo_thursday`
- **Weekend** = Friday 6pm to Sunday 6pm → `spo_weekend`

**The `reason` label in interval data MUST differ by mode.** `_weekend_thursday_intervals()` must use `spo_thursday`/`spo_weekend` for SPO and `espo_thursday`/`espo_weekend` for ESPO. If both modes use the same labels, SPO and ESPO display identically — a critical bug.

---

## 12. Holiday Rules

### Christmas §153.314(1)(2)

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| First half: school dismissal → noon Dec 28 | Mom | Dad |
| Second half: noon Dec 28 → 6pm day before school resumes | Dad | Mom |

**Start date** = last school day before district's `christmas.start` (walk backward).

**Dec 28 split**: Custody transfers at **NOON**. Render as split cell (AM = first-half custodian, PM = second-half custodian).

### Thanksgiving §153.314(3)

| Year | Who gets whole Thanksgiving period |
|------|-------------------------------------|
| Odd | Dad (possessory) |
| Even | Mom (managing) |

**Start date** = last school day before district's Thanksgiving break start. Walk backward from `(district_start - 1 day)` until hitting a Mon–Fri school day.

### Spring Break §153.312(b)(1)

| Year | Who gets spring break |
|------|----------------------|
| Odd | Mom |
| Even | Dad |

**Start**: 6pm on the last school day before spring break begins.
**End**: 6pm on the **day before school resumes** (NOT the district's `spring.end`).

### Summer §153.312(b)(2)

- **Dad**: July 1–30 (30 consecutive days)
- **Mom**: Before Dad + after Dad

---

## 13. Odd/Even Year Determination

Uses **calendar year** (not school year). Spring break 2026 = even year = Dad.

---

## 14. Output Files

```
data/processed/espo_intervals.json  → embedded in index.html as ESPO_INTERVALS
data/processed/spo_intervals.json   → embedded in index.html as SPO_INTERVALS
index.html                          → the single canonical output (served by GitHub Pages)
```

Both ESPO and SPO intervals are embedded in the same `index.html`. The UI toggles between them client-side.

---

## 15. HTML Output

Pure static HTML (`index.html`) — no server required:
- **SPO ↔ ESPO** mode toggle
- **EN ↔ CN** bilingual toggle
- **Color coding**: Dad (blue) / Mom (pink)
- **Month navigation** (current + next month)
- **Hover tooltips** with date + custodian details
- **Christmas Dec 28 split cell** (AM/PM different colors)
- **Footer**: TX statute links (§153.312/313/314/315/317) + district + git commit hash + generation timestamp

---

## 16. Verification Checklist

- [x] Christmas 2025 Dec 19–28 → Mom (odd year, first half)
- [x] Christmas 2025 Dec 29–Jan 5 → Dad (odd year, second half)
- [x] Christmas 2026 Dec 18–28 → Dad (even year, first half)
- [x] Christmas 2026 Dec 29–Jan 5 → Mom (even year, second half)
- [x] Christmas Dec 28 split cell (AM/PM different colors)
- [x] Thanksgiving 2025 (odd year) → Dad
- [x] Thanksgiving 2026 (even year) → Mom
- [x] Spring Break 2026 (even year) → Dad
- [x] Summer: July 1–30 → Dad, July 31+ → Mom
- [x] Father's Day 2026 → Dad (overrides summer)
- [x] Mother's Day 2026 → Mom (overrides summer)
- [x] ESPO Thursday → Dad (overnight, school dismissal → Fri resume)
- [x] SPO Thursday → Dad (evening only 6pm–8pm)
- [x] 1st/3rd/5th Friday weekends correct (not every Friday)
- [x] Single-day noschool days → inherits custodian from preceding day (NOT odd/even alternating)
- [x] Footer statute links are real `<a>` tags (not Markdown links rendered as text)

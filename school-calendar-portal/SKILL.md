---
name: school-calendar-portal
description: "Create a co-parenting custody calendar portal for a US school district. Use when: (1) user provides a school district calendar URL, PDF, or image, (2) user wants to generate a custody calendar for their address, (3) user asks to build a co-parenting portal for their school district. Workflow: geocode address → identify school district → fetch Texas custody laws → parse calendar data → generate 2-year ESPO and SPO calendar HTML. Triggers on phrases like create custody calendar, build co-parenting portal, generate school calendar, espo spo calendar, 学区calendar生成, 抚养权日历."
---

# School Calendar Portal Skill

Generate a 2-year co-parenting custody calendar (SPO + ESPO) for a US school district, with Texas Family Code custody rules.

**Live demo: https://hanyunfan.github.io/hermes/school-calendar-portal/**

## Canonical Entry Point

```
scripts/main.py
```

All other scripts in `scripts/` are standalone dev utilities — not part of the pipeline.

## Step 1 — Ask for Inputs

Ask the user for:
1. **Dad's address** → written to `inputs/dad_addr.txt`
2. **Mom's address** → written to `inputs/mom_addr.txt` (empty = same as Dad's)
3. **District name** or address to geolocate (system auto-detects via NCES API)

## Step 2 — Run the Pipeline

```bash
cd ~/hermes/school-calendar-portal
python scripts/main.py
```

The pipeline:
```
scripts/main.py
  ├── geolocator (Nominatim) → lat/lon for dad/mom
  ├── district_finder (NCES API) → auto-detect district
  ├── statute_loader → config/state_statute_templates/texas.json
  ├── rule_builder → custody_rules.json
  ├── CustodyIntervalGenerator → espo_intervals.json + spo_intervals.json
  └── HTMLBuilder → index.html
```

**Cache note**: `main.py` loads cached `data/processed/espo_intervals.json` and `spo_intervals.json` if they exist. To force full regeneration after logic fixes:
```bash
rm -f data/processed/espo_intervals.json data/processed/spo_intervals.json
python scripts/main.py
```

## Step 3 — Verify Output

Open `index.html` in browser. Check:
1. Today's date is highlighted with outline
2. Christmas Dec 28 renders as split cell (AM/PM different colors)
3. Thanksgiving shows correct custodian per odd/even year
4. SPO/ESPO toggle works (SPO button may be hidden — see Pitfall #5)
5. EN/CN language toggle works

## Step 4 — Push to GitHub

```bash
cd ~/hermes/school-calendar-portal
git add -A
git commit -m "Update custody calendar"
git push origin main
```

GitHub Pages serves from: `https://hanyunfan.github.io/hermes/school-calendar-portal/index.html`

**Important**: Pushing a new commit does NOT update `index.html`'s footer commit hash — the hash is baked in at generation time by `main.py`. After any logic fix, you MUST regenerate and push:
```
rm -f data/processed/espo_intervals.json data/processed/spo_intervals.json
python scripts/main.py
git add -A && git commit -m "..." && git push
```

---

# Custody Logic Reference

## Roles

| Term | Role | Default schedule |
|------|------|-----------------|
| **Managing Conservator (MC)** | Primary custodian | Mon/Tue/Wed/Fri |
| **Possessory Conservator (PC)** | Secondary custodian | Thu evenings + 1st/3rd/5th weekends |

In this system: **Mom = MC (managing)**, **Dad = PC (possessory)**.

## Regular Schedule

### ESPO Mode

| Day | Who | Reason key |
|-----|-----|-----------|
| Mon | Mom | regular_school_day |
| Tue | Mom | regular_school_day |
| Wed | Mom | regular_school_day |
| Thu | Dad | espo_thursday (school dismissal → school resumes Fri overnight) |
| Fri | Mom (unless 1st/3rd/5th weekend) | regular_school_day |
| Sat/Sun | Dad (if 1st/3rd/5th Fri) | espo_weekend |
| Sat/Sun | Mom (if 2nd/4th Fri) | mom_weekend |

**1st/3rd/5th weekend rule**: Count the Friday's position in the month:
- Friday on 1st–7th = 1st weekend (Dad)
- Friday on 8th–14th = 2nd weekend (Mom)
- Friday on 15th–21st = 3rd weekend (Dad)
- Friday on 22nd–28th = 4th weekend (Mom)
- Friday on 29th–31st = 5th weekend (Dad)

### SPO Mode

Same as ESPO except:
- **Thu** = Dad 6pm–8pm only (evening only, not overnight) → `spo_thursday`
- **Weekend** = Friday 6pm to Sunday 6pm (not school dismissal to Monday) → `spo_weekend`

**Critical**: The `reason` label in interval data MUST differ by mode. In `interval_generator.py` `_weekend_thursday_intervals()`:
```python
reason = "espo_thursday" if self.mode == "espo" else "spo_thursday"
reason = "espo_weekend" if self.mode == "espo" else "spo_weekend"
```
If both modes use `espo_thursday`/`espo_weekend` labels, SPO and ESPO display identically in the UI — a critical bug.

## Holiday Rules

### Thanksgiving ([§153.314(3)](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153))

Possession: 6pm on the day school is dismissed BEFORE Thanksgiving → 6pm following Sunday.

| Year | Who gets whole Thanksgiving period |
|------|-------------------------------------|
| Odd | Dad (possessory) |
| Even | Mom (managing) |

**Start date** = the last school day BEFORE the district's Thanksgiving break (NOT the district's `thanksgiving.start` which is the first noschool day). Walk backward from `(district_start - 1 day)` until hitting a Mon–Fri school day within the school year.

Example: RRISD 2025 — district break starts 11-24 (Mon, Thanksgiving week), but last school day = 11-21 (Fri). Possession starts 6pm 11-21 (Fri).

### Christmas ([§153.314(1)(2)](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153))

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| First half: school dismissal → noon Dec 28 | Mom | Dad |
| Second half: noon Dec 28 → 6pm day before school resumes | Dad | Mom |

**Start date** = last school day before district's `christmas.start` (walk backward, same as Thanksgiving).

**Dec 28 split**: Custody transfers at **NOON**. Render as split cell (AM = first-half custodian, PM = second-half custodian).

**Christmas labels in UI**: Do NOT hardcode "Dad" or "Mom" in the label — the custodian alternates by year. Labels should be "Christmas 1st half" / "Christmas 2nd half" (custodian shown via cell color).

### Spring Break ([§153.312(b)(1)](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153))

Possession: 6pm on the day child is dismissed for spring vacation → 6pm on the day BEFORE school resumes.

| Year | Who gets spring break |
|------|----------------------|
| Odd | Mom |
| Even | Dad |

**End date** = the day before school resumes (NOT the district's `spring.end`). Per RRISD: break 3/16–3/20, school resumes 3/23 (Mon), so custody ends 6pm 3/22 (Sunday).

### Summer ([§153.312(b)(2)](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153))

- **Dad**: July 1–30 (30 consecutive days)
- **Mom**: All other summer days (before Dad + after Dad)

### Single-Day Noschool Days ([§153.315(b)](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153))

**NOT odd/even year alternation.**

Per §153.315(b), possession continues uninterrupted across noschool days — the custodian "flows through" from whatever interval the day before belonged to.

- The custodian for a noschool day = custodian of the last school day before the noschool period began
- When a noschool day falls on Friday, and the following weekend has no school with resumption Monday: the noschool possession **extends through the entire weekend** (Sat/Sun) to the day before school resumes. These days use `noschool_day` (priority 6), NOT `espo_weekend`/`mom_weekend` (priorities 8/9) — so they correctly override weekend rules.
- If a standalone noschool day has no preceding school day (e.g., first day of school year), falls back to `dad`

**Implementation detail**: `_noschool_intervals()` uses `date_winner` (Pass 1 result) to look up the predecessor custodian. When no school was in session during the gap (`extend_through_gap` returns `None`), the standalone day is absorbed into the current group — `group_end = d` (NOT `d - 1`). An earlier bug had `group_end = d - 1` which left the standalone day as a separate interval with a different custodian.

## Priority System

When multiple intervals cover the same date, lowest priority number wins:

| Priority | Interval | Notes |
|----------|-----------|-------|
| 1 | fathers_day, mothers_day | Override everything |
| 2 | spring_break | |
| 3 | thanksgiving | |
| 4 | christmas | |
| 5 | summer_* | |
| 6 | **noschool_day** | **Wins over espo_weekend (8) and mom_weekend (9)** |
| 7 | espo_thursday / spo_thursday | Both use priority 7; reason key differs by mode |
| 8 | espo_weekend / spo_weekend | Both use priority 8; reason key differs by mode |
| 9 | mom_weekend | Overwritten by noschool_day (p=6) |
| 10 | regular_school_day | |

## Odd/Even Year Determination

Uses **calendar year** (not school year). Spring break 2026 = even year = Dad.

---

# Texas Statute References

All TX custody rules: https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153

| Section | Topic |
|---------|-------|
| [§153.312](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153) | SPO default — weekend, Thursday, spring break, summer |
| [§153.313](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153) | Long-distance (>100 miles) simplified schedule |
| [§153.314](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153) | Christmas, Thanksgiving holiday rules |
| [§153.315](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153) | Single-day noschool days — inherits from preceding day (§153.315(b)) |
| [§153.317](https://statutes.capitol.texas.gov/?tab=1&code=FA&chapter=FA.153) | ESPO extended times election |

---

# Pitfalls

1. **Spring break end date**: Per §153.312(b)(1), custody ends at 6pm on the day BEFORE school resumes. The district's `spring.end` is the last day of the school's spring break calendar — NOT the statute's reference. Fix: use `day_before_school_resumes`, not `br.end`.

2. **Thanksgiving start date**: Per §153.314(3), possession starts at 6pm on the day school is dismissed BEFORE Thanksgiving. District's `thanksgiving.start` is the first noschool day — custody starts on the LAST school day before that. Walk backward from `(district_start - 1 day)`.

3. **Christmas Dec 28 split**: Render as split cell with AM = first-half custodian, PM = second-half custodian. Custody transfers at **NOON** (not 6pm or midnight).

4. **Christmas labels**: Do NOT hardcode "Dad" or "Mom" in `christmas_first_half` / `christmas_second_half` labels — custodian alternates by odd/even year. Use "Christmas 1st half" / "Christmas 2nd half" (custodian shown via cell color).

5. **SPO button hidden**: After fixing SPO mode (`_weekend_thursday_intervals` now generates `spo_thursday`/`spo_weekend` labels), the SPO button was hidden with `style="display:none"` as a temporary measure. To re-enable: remove the `display:none` in `html_builder.py` `espoBtn`/`spoBtn` section.

6. **Stale cache**: `main.py` loads cached `espo_intervals.json` / `spo_intervals.json` if they exist. If cache is stale, the page shows wrong data even after pushing. Always force regeneration after logic fixes.

7. **Footer timestamp uses git commit time, not generation time**: Fixed — footer now uses `datetime.now()` at generation time. `get_git_timestamp()` (which used `git log origin/main`) was replaced with `datetime.now().strftime('%Y-%m-%d %H:%M:%S')`.

8. **Only `index.html` is canonical**: A separate `custody_school_calendar.html` may exist from manual creation. Only `index.html` is generated by the pipeline and served by GitHub Pages.

9. **GitHub Pages URL**: `https://hanyunfan.github.io/hermes/school-calendar-portal/index.html` (served from `hermes` repo's `school-calendar-portal/` subdirectory, NOT from the `school-calendar-portal` repo root).

10. **Must regenerate HTML after each code fix**: After any code change, you MUST:
    ```
    rm -f data/processed/espo_intervals.json data/processed/spo_intervals.json
    python scripts/main.py
    git add -A && git commit -m "..." && git push
    ```
    Skipping regeneration leaves `index.html` with the old commit hash and old logic.

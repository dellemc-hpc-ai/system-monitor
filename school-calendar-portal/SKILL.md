---
name: school-calendar-portal
description: "Create a co-parenting custody calendar portal for a US school district. Use when: (1) user provides a school district calendar URL, PDF, or image, (2) user wants to generate a custody calendar for their address, (3) user asks to build a co-parenting portal for their school district. Workflow: geocode address → identify school district → fetch Texas custody laws → parse calendar data → generate 2-year ESPO and SPO calendar HTML. Triggers on phrases like create custody calendar, build co-parenting portal, generate school calendar, espo spo calendar, 学区calendar生成, 抚养权日历."
---

# School Calendar Portal Skill

Generate a 2-year co-parenting custody calendar (SPO + ESPO) for a US school district, with Texas §153.312/313/314 custody rules.

## Step 1 — Ask for Inputs

Ask the user for:
1. **District name** (e.g., "Round Rock ISD") or address to geolocate
2. **Calendar data** — key dates needed:
   - First day of school (fall)
   - Last day of school (spring)
   - Thanksgiving break dates
   - Christmas break (start = last instruction day, end = day before school resumes)
   - Spring break dates (start = first day of break, end = last day of school vacation)
   - Any single-day noschool days

If the user provides a URL or ICS feed, use `src/calendar_fetcher_parser/fetch_district_ics.py` to download.

## Step 2 — Create Standard Calendar JSON

Create `data/processed/{district}_standard_calendar.json`:

```json
{
  "district": "Round Rock ISD",
  "schoolYears": [
    {
      "year": "2025-2026",
      "start": "2025-08-13",
      "end": "2026-05-21",
      "breaks": {
        "thanksgiving": { "start": "2025-11-24", "end": "2025-11-30", "label": { "en": "Thanksgiving Break", "cn": "感恩节假期" } },
        "christmas": { "start": "2025-12-19", "end": "2026-01-05", "label": { "en": "Christmas Break", "cn": "圣诞假期" } },
        "spring": { "start": "2026-03-16", "end": "2026-03-20", "label": { "en": "Spring Break", "cn": "春假" } },
        "summer": { "start": "2026-05-22", "end": "2026-08-12", "label": { "en": "Summer Break", "cn": "暑假" } }
      },
      "noschool_days": [
        { "date": "2025-09-01", "label": { "en": "Student & Staff Holiday", "cn": "" } }
      ]
    }
  ]
}
```

**CRITICAL — Spring break end date**: Per TX §153.312(b)(1), spring break possession ends at 6pm on the day before school resumes after that vacation. This is the calendar day BEFORE school resumes (e.g., 03-22 when school resumes 03-23 Monday) — NOT the district calendar's `spring.end` (which is the last day of the school's scheduled spring break, e.g., 03-20). The statute is a calendar reference, not a district calendar field. Example: RRISD spring break 3/16-3/20, school resumes 3/23 (Monday) — custody ends 6pm 3/22 (Sunday).

## Step 3 — Run the Pipeline

```bash
cd ~/Desktop/hermes/school-calendar-portal
python scripts/main.py
```

Or with overrides:
```bash
python scripts/main.py --address "900 Round Rock Blvd, Round Rock, TX" --district "Round Rock ISD" --debug
```

This generates `index.html` with `ESPO_INTERVALS` and `SPO_INTERVALS` arrays.

## Step 4 — Verify Output

Open `index.html` in browser. Check:
1. Today's date is highlighted with outline
2. Spring break days show correct custodian
3. Christmas Dec 28 renders as split cell (AM/PM different colors)
4. Thanksgiving shows correct custodian per odd/even year
5. SPO/ESPO toggle works
6. EN/CN language toggle works

## Step 5 — Push to GitHub

```bash
cd ~/Desktop/hermes
git add school-calendar-portal/index.html
git commit -m "Update custody calendar"
git push origin main
```

Then update the footer in `index.html` to show the new commit hash:
```html
<div class="footer">TX Sec.153.314 -- {district} -- commit:{new_hash}</div>
```
Commit and push again.

---

# Custody Logic Reference

## Roles

| Term | Role | Default schedule |
|------|------|-----------------|
| **Managing Conservator (MC)** | Primary custodian | Mon/Tue/Wed/Fri (no Thu/Sat/Sun) |
| **Possessory Conservator (PC)** | Secondary custodian | Thu evenings + 1st/3rd/5th weekends |

In this system: **Mom = MC**, **Dad = PC**.

## Regular Schedule

### ESPO Mode

| Day | Who | Reason key |
|-----|-----|-----------|
| Mon | Mom | regular_school_day |
| Tue | Mom | regular_school_day |
| Wed | Mom | regular_school_day |
| Thu | Dad | espo_thursday (school dismissal to Friday school resumes) |
| Fri | Mom (unless 1st/3rd/5th weekend) | regular_school_day |
| Sat/Sun | Dad (if 1st/3rd/5th Fri) | espo_weekend |
| Sat/Sun | Mom (if 2nd/4th Fri) | mom_weekend |

**1st/3rd/5th weekend rule**: Count the position of the Friday in the month:
- Friday on 1st-7th = 1st weekend (Dad)
- Friday on 8th-14th = 2nd weekend (Mom)
- Friday on 15th-21st = 3rd weekend (Dad)
- Friday on 22nd-28th = 4th weekend (Mom)
- Friday on 29th-31st = 5th weekend (Dad, if a Friday exists)

### SPO Mode

Same as ESPO except:
- Thu = Dad 6pm-8pm only (not overnight)
- Weekend = Friday 6pm to Sunday 6pm (not school dismissal to Monday)

## Holiday Rules

### Thanksgiving (§153.314(3))

| Year | Who gets Thanksgiving |
|------|----------------------|
| Odd | Dad (possessory) |
| Even | Mom (managing) |

Possession: 6pm day before Thanksgiving to 6pm following Sunday.

### Christmas (§153.314(1)(2))

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| First half: school dismissal to noon Dec 28 | Mom | Dad |
| Second half: noon Dec 28 to 6pm day before school resumes | Dad | Mom |

Dec 28 is a split day: custody transfers at NOON. Render as split cell (AM/PM with separator).

### Spring Break (§153.312(b)(1))

Possession: 6pm on the day child is dismissed for spring vacation to 6pm on the day before school resumes.

| Year | Who gets spring break |
|------|----------------------|
| Odd | Mom |
| Even | Dad |

**End date = the day before school resumes** (NOT the district's spring.end). Per RRISD: break 3/16-3/20, school resumes 3/23 (Mon), so custody ends 6pm 3/22 (Sun).

### Summer (§153.312(b)(2))

- **Dad**: July 1-30 (30 consecutive days)
- **Mom**: All other summer days (before Dad + after Dad)

### Single-Day Noschool Days

| Year | Who |
|------|-----|
| Odd | Dad |
| Even | Mom |

## Priority System (date_winner)

When multiple intervals cover the same date, lowest priority wins:

| Priority | Interval |
|----------|-----------|
| 1 | fathers_day, mothers_day |
| 2 | spring_break |
| 3 | thanksgiving |
| 4 | christmas |
| 5 | summer_* |
| 6 | noschool_day |
| 7 | espo_thursday |
| 8 | espo_weekend |
| 9 | mom_weekend |
| 10 | regular_school_day |

## Odd/Even Year Determination

Uses **calendar year** (not school year). Spring break 2026 = even year = Dad.

---

# Pitfalls

1. **Spring break end date**: Per §153.312(b)(1), custody ends 6pm on "the day before school resumes." For RRISD: break ends 03-20, school resumes 03-23, so custody ends 6pm **03-22** (Sunday). This is a calendar date — the day before school resumes — NOT the district's `spring.end`. The statute's language is the authoritative source, not the district calendar field.

2. **Christmas Dec 28 split**: Render as split cell with AM = first-half custodian, PM = second-half custodian. Custody transfers at NOON (not 6pm or midnight).

3. **1st/3rd/5th weekend counting**: Count from the Friday's position in the month, not the calendar date. A Friday on the 7th = 1st weekend. A Friday on the 21st = 3rd weekend.

4. **ESPO Thursday end**: Thursday possession ends when school resumes on Friday (not 6pm Thursday). This is an overnight possession.

5. **Do NOT use sub-agents to regenerate index.html**: Any regeneration risks introducing purple page or other styling changes. Edit only with explicit patch commands.

6. **Summer dad period**: Must be exactly 30 consecutive days. If Dad starts July 1, he gets July 1-30.

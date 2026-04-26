---
name: school-calendar-portal
description: Create a co-parenting custody calendar portal for a US school district. Use when: (1) user provides a school district calendar URL, PDF, or image, (2) user wants to generate a custody calendar for their address, (3) user asks to build a co-parenting portal for their school district. Workflow: geocode address → identify school district → fetch Texas custody laws → parse calendar data → generate 2-year ESPO and SPO calendar HTML. Triggers on phrases like "create custody calendar", "build co-parenting portal", "generate school calendar", "espo spo calendar", "学区calendar生成".
---

# School Calendar Portal Skill

Generate a 2-year co-parenting custody calendar (SPO + ESPO) for a US school district, with Texas §153.314 custody rules.

## Workflow

### Step 1 — Gather Inputs

Ask the user for:
1. **Calendar source**: URL link, PDF file path, or image file path of the school district calendar
2. **Address** (optional, default: `Glass Mountain Trl, Austin, TX`)

If the user provides a district name directly (e.g., "Round Rock ISD"), use that without geocoding.

### Step 2 — Identify School District

**Step 2a — Geocode the address**:
```bash
python scripts/geocode_address.py "Glass Mountain Trl, Austin, TX"
```
Returns city, state, county for context.

**Step 2b — Find district via web search**:
Use the `web_search` tool to find which school district serves that address:
```
Search: "school district Glass Mountain Trail Austin TX calendar 2025-2026"
```
Or search for known districts in that city + county.

**Step 2c — Confirm calendar URL**:
Once district is identified, search for its official calendar URL.

**If district is found**: Confirm with user and use the calendar URL.
**If district is not found**: Ask the user to specify the district name or provide a calendar URL directly.

### Step 3 — Fetch Texas Custody Laws

Fetch and save Texas §153.314 and related statutes:
```bash
python scripts/fetch_tx_laws.py tx_custody_laws.md
```
This saves `tx_custody_laws.md` to the workspace. Read relevant sections to inform custody logic.

### Step 4 — Get Calendar Data

**Step 4a — Try public API**:
Search for a public calendar API for the district. Many districts publish:
- Google Calendar feeds (ICS)
- District open data portals
- Texas Education Agency data (for TX districts)

Use web_search:
```
Search: "[District Name] calendar API ICS feed 2025-2026"
```
If an ICS/calendar feed is found, download it and parse into JSON.

**Step 4b — Scrape from URL**:
```bash
python scripts/parse_calendar_url.py "https://example.com/calendar"
```
This saves `calendar_raw.html` for inspection and tries to extract dates.

**Step 4c — User provides data**:
If no API or URL works, ask the user to:
- Upload the calendar PDF/image
- Or manually enter key dates (first day, last day, Thanksgiving/Christmas/Spring break dates)

**For known districts** (e.g., RRISD): If the district is already known and data is confirmed, use the existing format and skip scraping.

Create a `calendar_data.json` file following the schema in `references/texas-districts.md`:

```json
{
  "district": "District Name",
  "state": "TX",
  "schoolYears": {
    "YYYY-YYYY": {
      "yearLabel": "YYYY-YYYY",
      "firstDay": "YYYY-MM-DD",
      "lastDay": "YYYY-MM-DD",
      "schoolResumes": "YYYY-MM-DD",
      "breaks": {
        "thanksgiving": { "start": "...", "end": "...", "schoolResumes": "..." },
        "christmas": { "lastInstructionDay": "...", "breakStart": "...", "schoolResumes": "...", "custodyEnd": "..." },
        "spring": { "start": "...", "end": "...", "schoolResumes": "..." }
      },
      "noschool": [
        { "date": "YYYY-MM-DD", "label": "Holiday Name" }
      ]
    }
  }
}
```

Key rules:
- `christmas.custodyEnd` = day before `schoolResumes` (per §153.314: possession ends 6pm day before school resumes)
- `christmas.lastInstructionDay` = last day students attend before break
- Summer break: `start` = day after `lastDay`, `end` = day before `schoolResumes`

### Step 6 — Generate HTML Portal

```bash
python scripts/generate_portal.py calendar_data.json output_index.html
```

This generates a standalone HTML file with:
- **SPO tab**: Standard Possession Order (every Thursday Dad 6-8pm, 1st/3rd/5th Fri-Sat-Sun)
- **ESPO tab**: Expanded Standard Possession Order (alternating schedule per §153.314)
- **Language toggle**: EN / 中文
- School breaks, noschool days, holidays color-coded by parent

### Step 7 — Deliver

Save all output files to the workspace. Key files:
- `calendar_data.json` — structured calendar data
- `index.html` (or custom name) — the portal HTML
- `tx_custody_laws.md` — saved Texas custody statutes

## Custody Logic Summary

From `references/tx-custody-laws.md`:

| Period | Odd Year | Even Year |
|--------|----------|-----------|
| Christmas first half | Mom | Dad |
| Christmas second half | Dad | Mom |
| Thanksgiving first half | Dad | Mom |
| Spring entire | Dad | Mom |
| Other holidays | Dad | Mom |

- **Summer**: Dad gets July 1-30; Mom gets rest of summer
- **Thursday**: Always Dad (6-8pm) outside summer break
- **Odd/even**: Calendar year (not school year)

## Key Scripts

- `scripts/geocode_address.py` — Convert address to lat/lon (Nominatim, no API key)
- `scripts/fetch_tx_laws.py` — Fetch Texas §153.314 etc. from web, save to .md
- `scripts/parse_calendar_url.py` — Scrape calendar URL, extract dates to JSON
- `scripts/generate_portal.py` — Generate the HTML custody calendar portal

## Reference Files

- `references/tx-custody-laws.md` — Texas Family Code custody statutes summary
- `references/texas-districts.md` — Known Texas districts, calendar schema, custody rules

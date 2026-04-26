# Texas School Districts — Known Calendars

## Austin Metro Area

### Round Rock ISD (RRISD)
- Website: https://roundrockisd.org/o/rrisd/page/calendars
- 2025-2026: First day Aug 12, Last day May 21
- 2026-2027: First day Aug 18, Last day May 27
- Calendar: Student holidays, Thanksgiving, Christmas, Spring Break

### Austin ISD
- Website: https://www.austinisd.org/calendar
- Similar structure to RRISD

### Eanes ISD (West Austin)
- Often starts earlier, ends earlier than surrounding districts

### Leander ISD (Cedar Park/NW Austin)
- Website: https://www.leanderisd.org/calendar

## How to Identify a School District

1. **From address**: Use geocoding (Nominatim/OpenStreetMap) to get lat/lon
2. **From URL**: If user provides district calendar URL, extract district name
3. **From PDF/image**: OCR or text extraction, then search for district name

## Calendar Data Schema

```json
{
  "district": "Round Rock ISD",
  "state": "Texas",
  "schoolYears": {
    "2025-2026": {
      "yearLabel": "2025-2026",
      "firstDay": "2025-08-12",
      "lastDay": "2026-05-21",
      "schoolResumes": "2026-08-13",
      "breaks": {
        "thanksgiving": {
          "start": "2025-11-24",
          "end": "2025-11-28",
          "schoolResumes": "2025-12-01"
        },
        "christmas": {
          "lastInstructionDay": "2025-12-19",
          "breakStart": "2025-12-20",
          "schoolResumes": "2026-01-06",
          "custodyEnd": "2026-01-05"
        },
        "spring": {
          "start": "2026-03-16",
          "end": "2026-03-20",
          "schoolResumes": "2026-03-23"
        }
      },
      "noschool": [
        { "date": "2025-09-01", "label": "Labor Day" },
        { "date": "2025-09-22", "label": "Student Holiday (Rosh Hashanah)" }
      ]
    }
  }
}
```

## Calendar Data Fields

| Field | Description |
|-------|-------------|
| `firstDay` | First day students attend school |
| `lastDay` | Last day students attend school |
| `schoolResumes` | First day students return after summer break |
| `breaks.thanksgiving.start/end` | Thanksgiving break dates |
| `breaks.christmas.lastInstructionDay` | Last day students attend before Christmas |
| `breaks.christmas.custodyEnd` | Last day of Christmas custody possession |
| `breaks.spring.start/end` | Spring break dates |
| `noschool[].date` | Individual no-school days (holidays, teacher days) |
| `noschool[].label` | Name/description of the no-school day |

## Custody Calculation Rules

- **Christmas**: Split at Dec 28 (noon per statute, midnight used for simplicity)
  - Even year (2026): Dad first half, Mom second half
  - Odd year (2025): Mom first half, Dad second half
- **Thanksgiving**: Split at midpoint of break
  - Even year: Mom Mon-Wed, Dad Thu-Fri
  - Odd year: Dad Mon-Wed, Mom Thu-Fri
- **Spring Break**: Entire break to one parent
  - Even year: Mom
  - Odd year: Dad
- **Summer**: Dad gets July 1-30, Mom gets remainder
- **Other holidays**: Odd year = Dad, Even year = Mom

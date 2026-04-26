"""
calendar_fetcher_parser -- data_normalizer.py
=============================================
Converts raw parsed data into the StandardCalendar JSON structure.
Validates using Pydantic models.
"""
import json
import os
from datetime import datetime, timedelta
from typing import Optional

# Add parent src to path for pydantic import
try:
    from pydantic import BaseModel, Field, field_validator
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object

PROCESSED_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "processed"
)


# ─── Pydantic Models ─────────────────────────────────────────────────────────

if HAS_PYDANTIC:

    class BreakLabel(BaseModel):
        en: str
        cn: str = ""

    class SchoolBreakModel(BaseModel):
        start: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
        end: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
        label: BreakLabel

    class NoSchoolDayModel(BaseModel):
        date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
        label: BreakLabel

    class SchoolYearModel(BaseModel):
        year: str = Field(..., pattern=r"^\d{4}-\d{4}$")
        start: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
        end: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
        breaks: dict[str, SchoolBreakModel] = Field(default_factory=dict)
        noschool_days: list[NoSchoolDayModel] = Field(default_factory=list)

        @field_validator("breaks")
        @classmethod
        def check_break_keys(cls, v):
            allowed = {"thanksgiving", "christmas", "spring", "summer"}
            for k in v.keys():
                if k not in allowed:
                    raise ValueError(f"Unknown break type: {k}")
            return v

    class StandardCalendarModel(BaseModel):
        district: str
        schoolYears: list[SchoolYearModel]
        source: str = ""
        collected_at: str = ""

else:
    # Minimal fallback without pydantic
    class StandardCalendarModel:
        pass


# ─── Normalizer ───────────────────────────────────────────────────────────────

class DataNormalizer:
    """
    Converts raw parsed calendar data -> StandardCalendar JSON.
    Applies manual corrections for known学区 (e.g. RRISD).
    """

    KNOWN_DISTRICTS = {
        "round rock isd": "RRISD",
        "rrisd": "RRISD",
        "austin isd": "AISD",
        "leander isd": "LISD",
    }

    def __init__(self, district_name: str):
        self.district = self._normalize_district_name(district_name)
        self._data = {
            "district": self.district,
            "schoolYears": [],
            "source": "",
            "collected_at": datetime.now().isoformat()
        }

    def _normalize_district_name(self, name: str) -> str:
        name_lower = name.lower().strip()
        return self.KNOWN_DISTRICTS.get(name_lower, name)

    def add_school_year(
        self,
        year: str,
        start: str,
        end: str,
        breaks: dict[str, dict],
        noschool_days: list[dict]
    ) -> None:
        """
        Add a school year with its breaks and noschool days.
        breaks: { "thanksgiving": {start, end, label}, ... }
        noschool_days: [{date, label}, ...]
        """
        sy = {
            "year": year,
            "start": start,
            "end": end,
            "breaks": breaks,
            "noschool_days": noschool_days
        }

        if HAS_PYDANTIC:
            try:
                sy = SchoolYearModel(**sy).model_dump()
            except Exception as e:
                print(f"  Warning: school year validation error: {e}")

        self._data["schoolYears"].append(sy)

    def set_source(self, source: str) -> None:
        self._data["source"] = source

    def validate(self) -> list[str]:
        """Run validation checks. Returns list of error messages."""
        errors = []
        for sy in self._data.get("schoolYears", []):
            # Check year range is valid
            sy_start = sy["start"]
            sy_end = sy["end"]
            if sy_start >= sy_end:
                errors.append(f"Invalid year {sy['year']}: start >= end")
            # Check break dates are within school year
            for br_name, br in sy.get("breaks", {}).items():
                # Summer break starts the day AFTER school ends - always outside school year
                if br_name == "summer":
                    continue
                if not (sy_start <= br["start"] <= sy_end):
                    errors.append(f"Break {br_name} start {br['start']} outside school year")
                if not (sy_start <= br["end"] <= sy_end):
                    errors.append(f"Break {br_name} end {br['end']} outside school year")
        return errors

    def _adjust_school_start(self) -> None:
        """
        Adjust school year start dates so the first day is the first Monday
        on or after Aug 1 (when RRISD traditionally starts). This ensures
        teacher work days (Aug 13-17 for 2025-2026) are treated as summer,
        not regular school days, since students don't attend yet.
        For custody purposes: before actual instruction begins = summer.
        """
        from datetime import date as date_cls, timedelta
        school_years = self._data.get("schoolYears", [])
        for sy in school_years:
            sy_start = date_cls.fromisoformat(sy["start"])
            # Find first Monday >= Aug 1 of that year
            aug1 = date_cls(sy_start.year, 8, 1)
            days_until_monday = (7 - aug1.weekday()) % 7  # 0 if Aug 1 is Monday
            first_monday = aug1 + timedelta(days=days_until_monday)
            # Only adjust if current start is before the first Monday
            # (i.e., teacher work days before students arrive)
            if sy_start < first_monday:
                sy["start"] = first_monday.isoformat()

    def _adjust_summer_breaks(self) -> None:
        """
        Ensure summer break covers all days between the end of one school year
        and the start of the next (including Aug 13-17 teacher work days).
        For each school year:
          - summer.start = day after previous school year ended (or May 22 default)
          - summer.end = day before THIS school year starts (so Aug 13-17 = summer)
        """
        from datetime import date as date_cls, timedelta
        school_years = self._data.get("schoolYears", [])
        for i, sy in enumerate(school_years):
            if "summer" not in sy.get("breaks", {}):
                continue

            sy_start = date_cls.fromisoformat(sy["start"])

            # Find previous school year to know when last one ended
            prev_sy_end = None
            for j in range(i - 1, -1, -1):
                prev_sy_end = date_cls.fromisoformat(school_years[j]["end"])
                break

            if prev_sy_end:
                # Summer starts the day after the previous school year ended
                new_summer_start = prev_sy_end + timedelta(days=1)
            else:
                # First school year: default to May 22
                new_summer_start = date_cls(sy_start.year - 1, 5, 22)

            # Summer ends the day before THIS school year starts
            # (so Aug 13-17 teacher days are treated as summer)
            last_summer_day = sy_start - timedelta(days=1)

            sy["breaks"]["summer"]["start"] = new_summer_start.isoformat()
            sy["breaks"]["summer"]["end"] = last_summer_day.isoformat()

    def save(self, filename: Optional[str] = None) -> str:
        """Save to processed/ directory. Returns saved path."""
        self._adjust_school_start()
        self._adjust_summer_breaks()
        os.makedirs(PROCESSED_DIR, exist_ok=True)
        if filename is None:
            filename = f"{self.district.lower()}_standard_calendar.json"
        path = os.path.join(PROCESSED_DIR, filename)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

        print(f"Saved standard calendar: {path}")
        return path

    def get_data(self) -> dict:
        return self._data

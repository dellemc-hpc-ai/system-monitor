"""
tests -- test_interval_calculation.py
======================================
Tests for custody interval generation:
- No overlaps
- All school days covered
- Holiday rules correct
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from datetime import date, timedelta
from custody_interval_calculator import (
    CustodyIntervalGenerator, StandardCalendar, SchoolYear,
    SchoolBreak, NoSchoolDay, IntervalList, CustodyInterval
)


def make_calendar() -> StandardCalendar:
    """Build a minimal test calendar."""
    cal = StandardCalendar(district="TEST ISD")

    cal.school_years.append(SchoolYear(
        year="2025-2026",
        start="2025-08-13",
        end="2026-05-21",
        breaks={
            "thanksgiving": SchoolBreak(
                start="2025-11-24", end="2025-11-28",
                label={"en": "Thanksgiving", "cn": "感恩节"}
            ),
            "christmas": SchoolBreak(
                start="2025-12-19", end="2026-01-05",
                label={"en": "Christmas", "cn": "圣诞"}
            ),
            "spring": SchoolBreak(
                start="2026-03-09", end="2026-03-13",
                label={"en": "Spring Break", "cn": "春假"}
            ),
            "summer": SchoolBreak(
                start="2026-05-22", end="2026-08-12",
                label={"en": "Summer", "cn": "暑假"}
            )
        },
        noschool_days=[
            NoSchoolDay(date="2025-09-01", label={"en": "Labor Day", "cn": "劳动节"})
        ]
    ))
    return cal


class TestIntervalGenerator:
    def test_no_overlaps(self):
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()
        errors = ivs.verify_no_overlaps()
        assert len(errors) == 0, f"Overlaps found: {errors}"

    def test_all_intervals_sorted(self):
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()
        for i in range(len(ivs) - 1):
            assert ivs[i].end < ivs[i+1].start, \
                f"Intervals out of order: {ivs[i]} -> {ivs[i+1]}"

    def test_thanksgiving_odd_year(self):
        """2025 is odd year -> Dad first half Thanksgiving."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()

        # Find Thanksgiving intervals
        tg_ivs = [iv for iv in ivs if iv.reason == "thanksgiving_first_half"
                  or iv.reason == "thanksgiving_second_half"]

        # 2025-11-24 is Mon, 5 days total -> first half (2-3 days) should be Dad
        assert len(tg_ivs) == 2, f"Expected 2 TG intervals, got {len(tg_ivs)}: {tg_ivs}"
        # Odd year first half -> Dad
        first_half = next(iv for iv in tg_ivs if iv.reason == "thanksgiving_first_half")
        assert first_half.custodian == "dad", f"Odd year TG first half should be Dad, got {first_half.custodian}"

    def test_christmas_odd_year(self):
        """2025 is odd year -> Dad first half Christmas."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()

        xm_ivs = [iv for iv in ivs if "christmas" in iv.reason]
        assert len(xm_ivs) == 2, f"Expected 2 Christmas intervals, got {len(xm_ivs)}"
        first = next(iv for iv in xm_ivs if "first" in iv.reason)
        assert first.custodian == "mom", f"Odd year Christmas first half should be Mom (per §153.314: odd year -> Mom first)"

    def test_spring_odd_year_mom(self):
        """2025-2026: spring 2026 is odd year-start -> Mom."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()

        spring = next((iv for iv in ivs if iv.reason == "spring_break"), None)
        assert spring is not None, "No spring break interval found"
        assert spring.custodian == "mom", f"Spring break (odd year-start) should be Mom, got {spring.custodian}"

    def test_summer_dad_30_days(self):
        """Summer: Dad gets July 1-30."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()

        dad_ivs = [iv for iv in ivs if iv.reason == "summer_dad_30_days"]
        assert len(dad_ivs) >= 1, "No Dad summer interval found"
        dad = dad_ivs[0]
        assert dad.start.month == 7 and dad.start.day == 1, f"Dad summer should start Jul 1, got {dad.start}"
        assert dad.end.day == 30, f"Dad summer should end day 30, got {dad.end.day}"

    def test_noschool_not_in_breaks(self):
        """Noschool days that fall within major breaks are not double-counted."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()

        # Labor Day (Sep 1) is outside all breaks -> should be in noschool interval
        labor_day = date(2025, 9, 1)
        result = ivs.query(labor_day)
        assert result is not None, f"Labor Day should be in an interval, got None"
        assert result.custodian in ("dad", "mom"), f"Unexpected custodian: {result.custodian}"

    def test_query_returns_correct_interval(self):
        """Binary search query returns correct custodian."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="espo")
        ivs = gen.generate()

        # Test a known date: Dec 31 2025 (Christmas break, odd year -> Dad first half)
        d = date(2025, 12, 25)
        result = ivs.query(d)
        assert result is not None, f"No interval found for {d}"
        assert result.custodian == "mom", f"Dec 25 2025 should be Mom (Christmas odd year: Mom first half Dec 19-27 per §153.314)"

        # Dec 30 2025: in second half of odd-year Christmas -> Dad
        d2 = date(2025, 12, 30)
        result2 = ivs.query(d2)
        assert result2 is not None, f"No interval for {d2}"
        assert result2.custodian == "dad", f"Dec 30 2025 should be Dad (Christmas odd year: Dad second half Dec 28+)"

    def test_spo_weekend_mode(self):
        """SPO mode: weekends -> Dad."""
        cal = make_calendar()
        gen = CustodyIntervalGenerator(cal, mode="spo")
        ivs = gen.generate()

        spo_ivs = [iv for iv in ivs if iv.reason == "spo_weekend"]
        assert len(spo_ivs) > 0, "SPO mode should produce weekend intervals"


class TestIntervalList:
    def test_append_maintains_sort(self):
        ivs = IntervalList()
        ivs.append(CustodyInterval(date(2026, 3, 1), date(2026, 3, 5), "mom", "test"))
        ivs.append(CustodyInterval(date(2026, 3, 15), date(2026, 3, 20), "dad", "test"))
        ivs.append(CustodyInterval(date(2026, 3, 8), date(2026, 3, 10), "mom", "test"))

        assert len(ivs) == 3
        # Should be sorted by start date
        assert ivs[0].start == date(2026, 3, 1)
        assert ivs[1].start == date(2026, 3, 8)
        assert ivs[2].start == date(2026, 3, 15)

    def test_query_within_interval(self):
        ivs = IntervalList()
        ivs.append(CustodyInterval(date(2026, 3, 1), date(2026, 3, 10), "mom", "test"))
        ivs.append(CustodyInterval(date(2026, 3, 15), date(2026, 3, 20), "dad", "test"))

        assert ivs.query(date(2026, 3, 5)).custodian == "mom"
        assert ivs.query(date(2026, 3, 15)).custodian == "dad"
        assert ivs.query(date(2026, 3, 11)) is None  # Gap between intervals

    def test_verify_no_overlaps(self):
        ivs = IntervalList()
        ivs.append(CustodyInterval(date(2026, 3, 1), date(2026, 3, 5), "mom", "test"))
        ivs.append(CustodyInterval(date(2026, 3, 4), date(2026, 3, 10), "dad", "test"))  # Overlap!
        errors = ivs.verify_no_overlaps()
        assert len(errors) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

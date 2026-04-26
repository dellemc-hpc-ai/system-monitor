"""Test Thanksgiving + Christmas custody after fix."""
import json, sys, os
proj = r"C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal"
sys.path.insert(0, proj)
os.chdir(proj)

from datetime import date
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator

# Load calendar
with open(os.path.join(proj, "data", "processed", "rrisd_standard_calendar.json"), encoding="utf-8") as f:
    cal = json.load(f)

# Build rules properly (as main.py does)
with open(os.path.join(proj, "config", "state_statute_templates", "texas.json"), encoding="utf-8") as f:
    statute = json.load(f)

# Run for both modes
for mode in ["espo", "spo"]:
    rules = build_custody_rules(statute, 0.0, mode, 30.4425, -97.8134, 30.4425, -97.8134)
    calc = CustodyCalculator(rules, cal)

    print("=" * 60)
    print("Mode: {}  (2026 = even year -> Dad Thanksgiving, Dad Xmas first half)".format(mode.upper()))
    print("=" * 60)

    test_dates = [
        ("2026-11-19", "Thu before Thanksgiving (regular)"),
        ("2026-11-20", "Last school day before Thanksgiving -> Dad"),
        ("2026-11-21", "Thanksgiving Thu"),
        ("2026-11-22", "Thanksgiving Fri"),
        ("2026-11-23", "Thanksgiving Sat"),
        ("2026-11-24", "Thanksgiving Sun"),
        ("2026-11-25", "Mon after Thanksgiving"),
        ("2026-11-26", "Tue after Thanksgiving"),
        ("2026-11-27", "Wed after Thanksgiving"),
        ("2026-11-28", "Thu after (not in period)"),
        ("2026-11-29", "Sun after Thanksgiving -> end of period"),
        ("2026-11-30", "Mon after period"),
        # Christmas
        ("2026-12-17", "Thu before Christmas break"),
        ("2026-12-18", "Christmas break start - Dad first half"),
        ("2026-12-27", "Last first-half day (Dec 27)"),
        ("2026-12-28", "Second half (Dec 28+) - Mom"),
        ("2026-12-31", "New Year's Eve"),
        ("2027-01-01", "New Year's Day"),
        ("2027-01-04", "Last day before school resumes"),
    ]

    print("\nThanksgiving period debug:")
    for d_str, _ in test_dates[:12]:
        d = date.fromisoformat(d_str)
        tg_start, tg_end = calc._thanksgiving_period(d)
        print("  {}: tg_start={}, tg_end={}".format(d_str, tg_start, tg_end))

    print()
    for d_str, note in test_dates:
        d = date.fromisoformat(d_str)
        cust, reason = calc._get_custodian(d)
        print("  {} ({}): {} | {:30s}  ; {}".format(
            d_str, d.strftime("%a"), cust, reason, note))
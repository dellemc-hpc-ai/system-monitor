"""Debug Thanksgiving detection for Nov 20."""
import json, sys, os
proj = r"C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal"
sys.path.insert(0, proj)
os.chdir(proj)

from datetime import date
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator

with open(os.path.join(proj, "data", "processed", "rrisd_standard_calendar.json"), encoding="utf-8") as f:
    cal = json.load(f)

with open(os.path.join(proj, "config", "state_statute_templates", "texas.json"), encoding="utf-8") as f:
    statute = json.load(f)

rules = build_custody_rules(statute, 0.0, "espo", 30.4425, -97.8134, 30.4425, -97.8134)
calc = CustodyCalculator(rules, cal)

# Debug: print school_years and their breaks
print("School years in calendar:")
for sy in calc.school_years:
    print("  Year:", sy.get("year"))
    print("    start:", sy.get("start"), "end:", sy.get("end"))
    print("    breaks:", list(sy.get("breaks", {}).keys()))
    print("    noschool_days count:", len(sy.get("noschool_days", [])))

# Check Nov 20 specifically
d = date(2026, 11, 20)
print("\nNov 20 2026 debug:")
print("  weekday:", d.weekday(), "(4=Fri)")
print("  _is_noschool_day:", calc._is_noschool_day(d))
br_name, br_data = calc._in_which_break(d)
print("  _in_which_break:", br_name, br_data)

# Check all noschool_days in Nov 2026
print("\nNov 2026 noschool days:")
for sy in calc.school_years:
    sy_start = date.fromisoformat(sy["start"])
    sy_end = date.fromisoformat(sy["end"])
    if not (sy_start <= d <= sy_end):
        continue
    for nsd in sy.get("noschool_days", []):
        nsd_date = date.fromisoformat(nsd["date"])
        if nsd_date.year == 2026 and nsd_date.month == 11:
            label = nsd.get("label", {})
            if isinstance(label, dict):
                label = label.get("en", "?")
            print("  ", nsd_date, label)

# Check what _thanksgiving_period returns for Nov 20
tg_start, tg_end = calc._thanksgiving_period(d)
print("\n_thanksgiving_period for Nov 20:", tg_start, tg_end)

# Check last school day before Christmas
print("\nLast school day before Christmas (2026-2027):")
for sy in calc.school_years:
    if sy.get("year") == "2026-2027":
        last_sd = calc._last_school_day_before_break("christmas", sy)
        print(" ", last_sd)
        break

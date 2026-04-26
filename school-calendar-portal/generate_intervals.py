"""Generate custody intervals without geocoding dependency."""
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

with open(os.path.join(proj, "config", "state_statute_templates", "texas.json"), encoding="utf-8") as f:
    statute = json.load(f)

for mode in ["espo", "spo"]:
    rules = build_custody_rules(statute, 0.0, mode, 30.4425, -97.8134, 30.4425, -97.8134)
    calc = CustodyCalculator(rules, cal)
    intervals = calc.compute_intervals()

    out_path = os.path.join(proj, "data", "processed", "{}_intervals.json".format(mode))
    calc.save_intervals(intervals, out_path)
    print("[{}] {} intervals -> {}".format(mode.upper(), len(intervals), out_path))

# Verify key dates
print("\n=== Verification ===")
rules = build_custody_rules(statute, 0.0, "espo", 30.4425, -97.8134, 30.4425, -97.8134)
calc = CustodyCalculator(rules, cal)

test = [
    ("2026-11-20", "Last school day before Thanksgiving (2026 even -> Mom)"),
    ("2026-11-21", "Thanksgiving Sat (2026 even -> Mom)"),
    ("2026-11-29", "Sun after Thanksgiving (2026 even -> Mom)"),
    ("2026-12-18", "Christmas break start (2026 even -> Dad first half)"),
    ("2026-12-27", "Last first-half day (2026 even -> Dad)"),
    ("2026-12-28", "Second half (2026 even -> Mom)"),
    ("2027-01-04", "Last day before school resumes (Mom second half)"),
]
for d_str, note in test:
    d = date.fromisoformat(d_str)
    cust, reason = calc._get_custodian(d)
    print("  {} ({}): {} | {}  <- {}".format(d_str, d.strftime("%a"), cust, reason, note))

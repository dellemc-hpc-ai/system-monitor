"""Force-reload and verify custody intervals."""
import json, sys, os
proj = r"C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal"
sys.path.insert(0, proj)
os.chdir(proj)

# Force reload
import importlib
import src.custody_calculator
importlib.reload(src.custody_calculator)
import src.rule_builder
importlib.reload(src.rule_builder)

from datetime import date
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator

with open(os.path.join(proj, "data", "processed", "rrisd_standard_calendar.json"), encoding="utf-8") as f:
    cal = json.load(f)

with open(os.path.join(proj, "config", "state_statute_templates", "texas.json"), encoding="utf-8") as f:
    statute = json.load(f)

rules = build_custody_rules(statute, 0.0, "espo", 30.4425, -97.8134, 30.4425, -97.8134)
calc = CustodyCalculator(rules, cal)

print("=== Debug: _thanksgiving_period for Nov 20-30 ===")
for day in range(20, 30):
    d = date(2026, 11, day)
    tg_start, tg_end = calc._thanksgiving_period(d)
    print("  Nov {}: tg_start={}, tg_end={}".format(day, tg_start, tg_end))

print("\n=== Debug: _get_custodian for Nov 28-30 ===")
for day in range(28, 31):
    d = date(2026, 11, day)
    cust, reason = calc._get_custodian(d)
    print("  Nov {}: {} | {}".format(day, cust, reason))

print("\n=== Debug: Christmas Jan 1-5 ===")
for day in range(1, 6):
    d = date(2027, 1, day)
    br_name, br_data = calc._in_which_break(d)
    tg_start, tg_end = calc._thanksgiving_period(d)
    is_first_half = d.month == 12 and d.day < 28
    print("  Jan {}: in_break={}, is_first_half={}".format(day, br_name, is_first_half))
    cust, reason = calc._get_custodian(d)
    print("    -> {} | {}".format(cust, reason))

print("\n=== Final intervals ===")
intervals = calc.compute_intervals()
for iv in intervals:
    if str(iv.start) >= "2026-11-20" and str(iv.start) <= "2027-01-07":
        print("  {} - {} : {} | {}".format(iv.start, iv.end, iv.custodian, iv.reason))

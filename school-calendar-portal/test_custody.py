"""
test_custody.py — Automated custody rule checker.
Run after any change to custody_calculator.py.

Checks every day covered by the calendar data and reports only if problems found.
No output = all clean.
"""
import sys, os, json
from datetime import date, timedelta

PROJ = r"C:\Users\frank\.openclaw\workspace\projects\TASK-001-allergy-report\school-calendar-portal"
sys.path.insert(0, PROJ)
os.chdir(PROJ)

from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator, load_standard_calendar

with open("config/state_statute_templates/texas.json", encoding="utf-8") as f:
    statute = json.load(f)
rules = build_custody_rules(statute, 0.0, "espo", 30.4425, -97.8134, 30.4425, -97.8134)
cal = load_standard_calendar("data/processed/rrisd_standard_calendar.json")
calc = CustodyCalculator(rules, cal)

# ─── Collect all relevant dates ───────────────────────────────────────────────

all_nsd = {}
for sy in cal["schoolYears"]:
    for n in sy.get("noschool_days", []):
        d = date.fromisoformat(n["date"])
        all_nsd[d] = n["label"]["en"]

all_sy_ranges = []
for sy in cal["schoolYears"]:
    all_sy_ranges.append((date.fromisoformat(sy["start"]), date.fromisoformat(sy["end"]), sy["year"]))

def in_school_year(d):
    return any(sy_start <= d <= sy_end for sy_start, sy_end, _ in all_sy_ranges)

def summer_window(d):
    return (d.month == 5 and d.day >= 22) or d.month in (6, 7) or (d.month == 8 and d.day <= 17)

def prev_school_day(d):
    prev = d - timedelta(days=1)
    for _ in range(90):
        if prev not in all_nsd:
            return prev
        prev -= timedelta(days=1)
    return None

def get_custodian(d):
    return calc._get_custodian(d)

def get_break(d):
    return calc._in_which_break(d)

# ─── Test cases ──────────────────────────────────────────────────────────────

errors = []
warnings = []

def fail(msg):
    errors.append(msg)

def warn(msg):
    warnings.append(msg)

# ── Rule 1: School days must NOT be labeled summer ────────────────────────
for sy_start, sy_end, sy_name in all_sy_ranges:
    d = sy_start
    while d <= sy_end:
        if d not in all_nsd:
            _, reason = get_custodian(d)
            if reason in ("summer_remainder", "summer_possessory"):
                fail(f"school_day_summer: {d} ({d.strftime('%a')}) in {sy_name} is a school day but got reason={reason}")
        d += timedelta(days=1)

# ── Rule 2: Aug 13 2025 must be a school day (first day of SY 2025-2026) ──
d = date(2025, 8, 13)
_, reason = get_custodian(d)
if reason in ("summer_remainder", "summer_possessory"):
    fail(f"aug13_not_school: {d} got reason={reason}")

# ── Rule 3: No-school days inside a break must get break reason (not no_school_day) ──
for d, label in sorted(all_nsd.items()):
    brk, _ = get_break(d)
    _, reason = get_custodian(d)
    if brk and reason == "no_school_day":
        fail(f"noschool_inside_break: {d} ({d.strftime('%a')}) '{label}' is inside break '{brk}' but got reason=no_school_day")

# ── Rule 4: No-school days OUTSIDE breaks must get no_school_day reason ──
for d, label in sorted(all_nsd.items()):
    brk, _ = get_break(d)
    if not brk:
        _, reason = get_custodian(d)
        if reason != "no_school_day":
            fail(f"noschool_missing: {d} ({d.strftime('%a')}) '{label}' is standalone noschool but got reason={reason}")

# ── Rule 5: No-school day rollover: custodian must match preceding school day ──
# (skip if the day is a holiday that overrides rollover, e.g. Thanksgiving/Christmas)
for d in sorted(all_nsd):
    brk, _ = get_break(d)
    if brk:
        continue  # Skip: break reason takes precedence over rollover
    prev = prev_school_day(d)
    if prev is None:
        warn(f"noschool_chain_too_long: {d}")
        continue
    prev_cust, _ = get_custodian(prev)
    cust, reason = get_custodian(d)
    if cust != prev_cust:
        fail(f"noschool_rollover_wrong: {d} ({d.strftime('%a')}) '{all_nsd[d]}' -> {cust}/{reason} but prev school day {prev} ({prev.strftime('%a')}) -> {prev_cust}")

# ── Rule 6: Summer window dates outside all school years must be summer ──
for year in [2026, 2027]:
    for month in [5, 6, 7, 8]:
        days = range(22, 32) if month == 5 else range(1, 32) if month != 8 else range(1, 18)
        for day in days:
            try:
                d = date(year, month, day)
            except:
                continue
            if not in_school_year(d) and d not in all_nsd:
                _, reason = get_custodian(d)
                if reason not in ("summer_remainder", "summer_possessory", "fathers_day"):
                    fail(f"summer_missing: {d} ({d.strftime('%a')}) not in school year, not noschool, not fathers_day, but got reason={reason}")

# ── Rule 7: Christmas 2026 (even year) — Dad first half Dec 18-27, Mom second half Dec 28-Jan 5 ──
# Per §153.314: possession begins when school is dismissed. 2026 Christmas break starts Dec 19 (no-school day).
# The last school day before break is Dec 18 (Thu, staff development day for students → not in session).
# So Christmas possession starts Dec 19 (break day 1) for 2026.
xmas_tests = [
    # (date, expected_custodian, expected_reason, note)
    (date(2026, 12, 18), "dad",    "christmas_first_half",  "Dec 18 2026: Fri before break, but is a no-school staff day → break day 1 is Dec 19"),
    (date(2026, 12, 19), "dad",    "christmas_first_half",  "Dec 19: Christmas break day 1, even year → Dad"),
    (date(2026, 12, 27), "dad",    "christmas_first_half",  "Dec 27: last day before noon Dec 28 split"),
    (date(2026, 12, 28), "mom",    "christmas_second_half", "Dec 28 noon: second half begins, even year → Mom"),
    (date(2027, 1, 4),   "mom",    "christmas_second_half", "Jan 4: last day before school resumes Jan 5"),
    # Odd year 2025: Mom first half, Dad second half
    # Dec 18 2025 is a no-school day (staff development), Christmas break starts Dec 19
    (date(2025, 12, 19), "mom",    "christmas_first_half",  "Dec 19: Christmas break day 1, odd year → Mom"),
    (date(2025, 12, 27), "mom",    "christmas_first_half",  "Dec 27: last day before split"),
    (date(2025, 12, 28), "dad",    "christmas_second_half", "Dec 28 noon: odd year → Dad"),
    (date(2026, 1, 5),   "mom",    "christmas_second_half", "Jan 5 2026: last day of Christmas break (school resumes Jan 6)"),
]
for d, exp_cust, exp_reason, note in xmas_tests:
    cust, reason = get_custodian(d)
    if cust != exp_cust or reason != exp_reason:
        fail(f"christmas_wrong: {d} ({d.strftime('%a')}) -> {cust}/{reason}, expected {exp_cust}/{exp_reason}  [{note}]")

# ── Rule 8: Thanksgiving 2026 (even year) — Mom, period = last school day before → Sunday after ──
# 2026 Thanksgiving break: Nov 23-27 (Mon-Fri). Thanksgiving Thu = Nov 26.
# Last school day before break = Nov 20 (Fri). Period: Nov 20 → Nov 30 (Sun after Thanksgiving).
# Nov 30 is NOT in the period → mom/default_custody.
tg_tests = [
    (date(2026, 11, 20), "mom",        "thanksgiving", "Last school day before Thanksgiving, even year → Mom"),
    (date(2026, 11, 21), "mom",        "thanksgiving", "Sat in Thanksgiving period"),
    (date(2026, 11, 26), "mom",        "thanksgiving", "Thanksgiving Thu, even year → Mom"),
    (date(2026, 11, 29), "mom",        "thanksgiving", "Sun after Thanksgiving, period end"),
    (date(2026, 11, 30), "mom",        "default_custody", "Mon after Thanksgiving Sunday: NOT in period → default"),
    # 2025 odd year: Dad
    (date(2025, 11, 20), "dad",        "thanksgiving", "Last school day before Thanksgiving, odd year → Dad"),
    (date(2025, 11, 27), "dad",        "thanksgiving", "Thu Thanksgiving 2025, odd year → Dad"),
    (date(2025, 11, 30), "dad",        "thanksgiving", "Sun after Thanksgiving 2025, period end"),
]
for d, exp_cust, exp_reason, note in tg_tests:
    cust, reason = get_custodian(d)
    if cust != exp_cust or reason != exp_reason:
        fail(f"thanksgiving_wrong: {d} ({d.strftime('%a')}) -> {cust}/{reason}, expected {exp_cust}/{exp_reason}  [{note}]")

# ── Rule 9: Father's Day 2025 (Jun 15), 2026 (Jun 21), 2027 (Jun 20) ──
fd_tests = [
    # 2025: Father's Day Sun Jun 15. Possession: Fri 6pm → Sun 6pm.
    (date(2025, 6, 13), "dad", "fathers_day", "Fri before Father's Day 2025 (Jun 15 Sun)"),
    (date(2025, 6, 14), "dad", "fathers_day", "Sat in Father's Day weekend"),
    (date(2025, 6, 15), "dad", "fathers_day", "Father's Day 2025"),
    (date(2025, 6, 16), "mom", "default_custody", "Mon after Father's Day 2025: no statutory extension to Mon"),
    # 2026: Father's Day Sun Jun 21. Possession: Fri Jun 18 6pm → Sun Jun 21 6pm.
    (date(2026, 6, 18), "dad", "fathers_day", "Thu before Father's Day 2026 (Dad gets Thu night)"),
    (date(2026, 6, 19), "dad", "fathers_day", "Fri of Father's Day weekend 2026"),
    (date(2026, 6, 20), "dad", "fathers_day", "Sat in Father's Day weekend 2026"),
    (date(2026, 6, 21), "dad", "fathers_day", "Father's Day 2026 (Sun)"),
    # 2027: Father's Day Sun Jun 20. Possession: Fri Jun 18 6pm → Sun Jun 20 6pm.
    (date(2027, 6, 18), "dad", "fathers_day", "Fri of Father's Day weekend 2027"),
    (date(2027, 6, 19), "dad", "fathers_day", "Sat in Father's Day weekend 2027"),
    (date(2027, 6, 20), "dad", "fathers_day", "Father's Day 2027 (Sun)"),
    (date(2027, 6, 21), "mom", "default_custody", "Mon after Father's Day 2027: no school, but no statutory Mon extension"),
]
for d, exp_cust, exp_reason, note in fd_tests:
    cust, reason = get_custodian(d)
    if cust != exp_cust or reason != exp_reason:
        fail(f"fathers_day_wrong: {d} ({d.strftime('%a')}) -> {cust}/{reason}, expected {exp_cust}/{exp_reason}  [{note}]")

# ── Rule 10: Summer 2027 (post-last-SY): Dad Jul 1-30, Mom rest ──
summer_2027_tests = [
    (date(2027, 5, 28), "mom", "summer_remainder",   "May 28: last school day, summer remainder before Dad's 30 days"),
    (date(2027, 6, 17), "mom", "summer_remainder",   "Jun 17: last day before Dad's possessory period"),
    (date(2027, 6, 18), "dad", "fathers_day",         "Jun 18: Father's Day Fri (Dad's weekend starts)"),
    (date(2027, 6, 21), "mom", "summer_remainder",   "Jun 21: Mon after Father's Day, summer remainder resumes"),
    (date(2027, 6, 30), "mom", "summer_remainder",   "Jun 30: last day before Dad's 30 days"),
    (date(2027, 7, 1),  "dad", "summer_possessory",  "Jul 1: Dad's 30 days begin"),
    (date(2027, 7, 15), "dad", "summer_possessory",  "Jul 15: middle of Dad's 30 days"),
    (date(2027, 7, 30), "dad", "summer_possessory",  "Jul 30: last day of Dad's 30 days"),
    (date(2027, 8, 1),  "mom", "summer_remainder",   "Aug 1: back to Mom's remainder"),
    (date(2027, 8, 17), "mom", "summer_remainder",   "Aug 17: last day of summer window"),
]
for d, exp_cust, exp_reason, note in summer_2027_tests:
    cust, reason = get_custodian(d)
    if cust != exp_cust or reason != exp_reason:
        fail(f"summer_2027_wrong: {d} ({d.strftime('%a')}) -> {cust}/{reason}, expected {exp_cust}/{exp_reason}  [{note}]")

# ── Rule 11: Spring Break 2027 (odd year) — Mom ──
spring_2027_tests = [
    (date(2027, 3, 13), "mom", "spring_break_pre", "Fri: last school day before spring break"),
    (date(2027, 3, 14), "mom", "spring_break_pre", "Sat before break"),
    (date(2027, 3, 15), "mom", "spring_break",     "Spring break day 1 (Sun)"),
    (date(2027, 3, 19), "mom", "spring_break",     "Spring break day 5 (Thu)"),
    (date(2027, 3, 20), "mom", "spring_break_post", "Fri: day after break"),
    (date(2027, 3, 21), "mom", "spring_break_post", "Sat after break"),
    (date(2027, 3, 22), "mom", "default_custody",  "Mon: school resumes"),
]
for d, exp_cust, exp_reason, note in spring_2027_tests:
    cust, reason = get_custodian(d)
    if cust != exp_cust or reason != exp_reason:
        fail(f"spring_break_wrong: {d} ({d.strftime('%a')}) -> {cust}/{reason}, expected {exp_cust}/{exp_reason}  [{note}]")

# ─── Report ─────────────────────────────────────────────────────────────────

if errors:
    print(f"ERRORS ({len(errors)}):")
    for e in errors:
        print(f"  FAIL: {e}")
else:
    print("All checks passed.")

if warnings:
    print(f"\nWARNINGS ({len(warnings)}):")
    for w in warnings:
        print(f"  WARN: {w}")

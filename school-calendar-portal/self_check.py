"""
self_check.py — Run after every change to custody_calculator.py
Reports ONLY if problems found. No output = all clean.
All expected values derived from real calendar data + statute rules.
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

# ─── Helpers ─────────────────────────────────────────────────────────────────

def cust(d):
    return calc._get_custodian(d)

def noschool(d):
    return calc._is_noschool_day(d)

def in_break(d):
    return calc._in_which_break(d)

def is_school_year(d):
    for sy in cal["schoolYears"]:
        s = date.fromisoformat(sy["start"])
        e = date.fromisoformat(sy["end"])
        if s <= d <= e:
            return True
    return False

def prev_school_day(d):
    prev = d - timedelta(days=1)
    for _ in range(90):
        if not noschool(prev):
            return prev
        prev -= timedelta(days=1)
    return None

ERRORS = []

def check(name, d, exp_c, exp_r):
    c, r = cust(d)
    if c != exp_c or r != exp_r:
        ERRORS.append(f"[{name}] {d} ({d.strftime('%a')}): got {c}/{r}  expected {exp_c}/{exp_r}")

# ─────────────────────────────────────────────────────────────────────────────
# T1: Aug 13 2025 must be a school day
# Note: May 21 2026 = LAST school day = summer day 1 (legitimate summer_remainder)
# ─────────────────────────────────────────────────────────────────────────────

check("T1 aug13", date(2025, 8, 13), "mom", "default_custody")

# ─────────────────────────────────────────────────────────────────────────────
# T2: no-school inside break → break reason (not no_school_day)
# T3: standalone no-school → no_school_day
# ─────────────────────────────────────────────────────────────────────────────

for sy in cal["schoolYears"]:
    for nsd in sy.get("noschool_days", []):
        d = date.fromisoformat(nsd["date"])
        brk, _ = in_break(d)
        c, r = cust(d)
        if brk and r == "no_school_day":
            ERRORS.append(f"[T2 noschool_in_break] {d} ({d.strftime('%a')}) inside break '{brk}' but got reason=no_school_day")
        if not brk and r != "no_school_day":
            ERRORS.append(f"[T3 standalone_noschool] {d} ({d.strftime('%a')}) not in break but got reason={r}")

# ─────────────────────────────────────────────────────────────────────────────
# T4: no-school rollover custodian matches preceding school day
# ─────────────────────────────────────────────────────────────────────────────

for sy in cal["schoolYears"]:
    for nsd in sy.get("noschool_days", []):
        d = date.fromisoformat(nsd["date"])
        brk, _ = in_break(d)
        if brk:
            continue
        prev = prev_school_day(d)
        if prev is None:
            continue
        prev_c, _ = cust(prev)
        c, r = cust(d)
        if c != prev_c:
            ERRORS.append(f"[T4 noschool_rollover] {d} ({d.strftime('%a')}) -> {c}/{r} but prev school day {prev} ({prev.strftime('%a')}) -> {prev_c}")

# ─────────────────────────────────────────────────────────────────────────────
# T5: Summer window outside school years → summer reason
# ─────────────────────────────────────────────────────────────────────────────

for y in [2026, 2027]:
    for m, (m_start, m_end) in {5: (22, 31), 6: (1, 30), 7: (1, 31), 8: (1, 17)}.items():
        for day in range(m_start, m_end + 1):
            try:
                d = date(y, m, day)
            except:
                continue
            if not is_school_year(d) and not noschool(d):
                c, r = cust(d)
                if r not in ("summer_remainder", "summer_possessory", "fathers_day",
                              "spring_break_pre", "spring_break_post"):
                    ERRORS.append(f"[T5 summer_window] {d} ({d.strftime('%a')}) not in school year, not noschool, but got reason={r}")

# ─────────────────────────────────────────────────────────────────────────────
# T6: Christmas — statute §153.314
# Alternation base: br_start.year (calendar year Christmas vacation BEGINS)
#   odd year br_start → odd_year_first=mom, odd_year_second=dad
#   even year br_start → even_year_first=dad, even_year_second=mom
# Split at noon Dec 28:
#   First half = Dec 18-28 (morning, up to and including Dec 28 before noon)
#   Second half = Dec 28 noon onward + all Jan dates
# 2025-2026 (br_start=Dec19,2025 odd): mom first half, dad second half
# 2026-2027 (br_start=Dec18,2026 even): dad first half, mom second half
# ─────────────────────────────────────────────────────────────────────────────

for d, exp_c, exp_r in [
    (date(2025, 12, 19), "mom", "christmas_first_half"),
    (date(2025, 12, 27), "mom", "christmas_first_half"),
    (date(2025, 12, 28), "mom", "christmas_first_half"),
    (date(2025, 12, 29), "dad", "christmas_second_half"),
    (date(2026,  1,  5), "dad", "christmas_second_half"),
    (date(2026,  1,  6), "mom", "default_custody"),
    (date(2026, 12, 18), "dad", "christmas_first_half"),
    (date(2026, 12, 27), "dad", "christmas_first_half"),
    (date(2026, 12, 28), "dad", "christmas_first_half"),
    (date(2026, 12, 29), "mom", "christmas_second_half"),
    (date(2027,  1,  4), "mom", "christmas_second_half"),
    (date(2027,  1,  5), "mom", "christmas_second_half"),
    (date(2027,  1,  6), "mom", "default_custody"),
]:
    check("T6 christmas", d, exp_c, exp_r)

# ─────────────────────────────────────────────────────────────────────────────
# T7: Thanksgiving — statute §153.314(3)
# odd year → Dad; even year → Mom
# 2025-2026 (odd): period Nov21→Nov30 (Sun). Dad.
# 2026-2027 (even): period Nov20→Nov29 (Sun). Mom.
# ─────────────────────────────────────────────────────────────────────────────

for d, exp_c, exp_r in [
    (date(2025, 11, 21), "dad", "thanksgiving"),
    (date(2025, 11, 28), "dad", "thanksgiving"),
    (date(2025, 11, 29), "dad", "thanksgiving"),
    (date(2025, 11, 30), "dad", "thanksgiving"),
    (date(2025, 12,  1), "mom", "default_custody"),
    (date(2026, 11, 20), "mom", "thanksgiving"),
    (date(2026, 11, 29), "mom", "thanksgiving"),
    (date(2026, 11, 30), "mom", "default_custody"),
]:
    check("T7 thanksgiving", d, exp_c, exp_r)

# ─────────────────────────────────────────────────────────────────────────────
# T8: Father's Day — §153.314: Fri 6pm → Sun 6pm
# No statutory Mon extension unless Mon itself is a no-school day.
# Mon after FD = regular summer day → summer_remainder (mom).
# ─────────────────────────────────────────────────────────────────────────────

for d, exp_c, exp_r in [
    (date(2025, 6, 13), "dad", "fathers_day"),
    (date(2025, 6, 14), "dad", "fathers_day"),
    (date(2025, 6, 15), "dad", "fathers_day"),
    (date(2025, 6, 16), "mom", "summer_remainder"),
    (date(2026, 6, 19), "dad", "fathers_day"),
    (date(2026, 6, 20), "dad", "fathers_day"),
    (date(2026, 6, 21), "dad", "fathers_day"),
    (date(2026, 6, 22), "mom", "summer_remainder"),
    (date(2027, 6, 18), "dad", "fathers_day"),
    (date(2027, 6, 19), "dad", "fathers_day"),
    (date(2027, 6, 20), "dad", "fathers_day"),
    (date(2027, 6, 21), "mom", "summer_remainder"),
]:
    check("T8 fathers_day", d, exp_c, exp_r)

# ─────────────────────────────────────────────────────────────────────────────
# T9: Summer 2027 — Dad Jul 1-30, Mom rest (May 28-30, Jul 31-Aug 17)
# SY 2026-2027 ends Thu May 27 2027 → summer starts Fri May 28
# Dad possessory: Jul 1-30 (at 6pm per statute, but we treat Jul 30 as last day)
# Mom remainder: May 28-30, Jul 31-Aug 17
# ─────────────────────────────────────────────────────────────────────────────

for d, exp_c, exp_r in [
    (date(2027, 5, 28), "mom", "summer_remainder"),   # first summer day (day after last school day)
    (date(2027, 6, 30), "mom", "summer_remainder"),   # last day before Dad's 30 days
    (date(2027, 7,  1), "dad", "summer_possessory"),   # Dad's 30 days begin
    (date(2027, 7, 15), "dad", "summer_possessory"),   # middle
    (date(2027, 7, 30), "dad", "summer_possessory"),   # last day of Dad's 30 days
    (date(2027, 8,  1), "mom", "summer_remainder"),   # Mom resumes
    (date(2027, 8, 17), "mom", "summer_remainder"),   # last day of summer window
]:
    check("T9 summer_2027", d, exp_c, exp_r)

# ─────────────────────────────────────────────────────────────────────────────
# T10: Spring break — statute §153.312(b)(1)
# Alternation base: calendar year when spring break BEGINS (br_start.year)
#   even year br_start → Dad (possessory)
#   odd year br_start → Mom (managing)
# Extended period: last school day before break → day before school resumes
# 2025-2026: br_start=Mar 16, 2026 (even year) → Dad
#   Last school day before break = Mar 13 (Fri). Period Mar13→Mar22 (Sun).
# 2026-2027: br_start=Mar 15, 2027 (odd year) → Mom
#   Last school day before break = Mar 13 (Fri). Period Mar13→Mar21 (Sun).
# ─────────────────────────────────────────────────────────────────────────────

for d, exp_c, exp_r in [
    # 2025-2026 (br_start=Mar 2026, even year): Dad
    (date(2026, 3, 13), "dad", "spring_break"),
    (date(2026, 3, 14), "dad", "spring_break_pre"),
    (date(2026, 3, 15), "dad", "spring_break_pre"),
    (date(2026, 3, 20), "dad", "spring_break"),
    (date(2026, 3, 21), "dad", "spring_break_post"),
    # 2026-2027 (br_start=Mar 2027, odd year): Mom
    (date(2027, 3, 13), "mom", "spring_break_pre"),
    (date(2027, 3, 15), "mom", "spring_break"),
    (date(2027, 3, 19), "mom", "spring_break"),
    (date(2027, 3, 20), "mom", "spring_break_post"),
    (date(2027, 3, 21), "mom", "spring_break_post"),
]:
    check("T10 spring_break", d, exp_c, exp_r)

# ─────────────────────────────────────────────────────────────────────────────
# Report
# ─────────────────────────────────────────────────────────────────────────────

if ERRORS:
    print(f"FAILURES ({len(ERRORS)}):")
    for e in ERRORS:
        print(f"  {e}")
else:
    print("OK")
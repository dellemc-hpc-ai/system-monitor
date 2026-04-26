import sys, os
proj = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal'
sys.path.insert(0, proj)

from src.statute_loader import load_statute
from src.rule_builder import build_custody_rules
from src.custody_calculator import CustodyCalculator, load_standard_calendar
from datetime import date

statute = load_statute('TX', os.path.join(proj, 'data', 'processed'))
cal = load_standard_calendar(os.path.join(proj, 'data', 'processed', 'rrisd_standard_calendar.json'))

rules = build_custody_rules(statute=statute, distance_miles=0.0, mode='espo',
    dad_lat=30.4425, dad_lon=-97.8134, mom_lat=30.4425, mom_lon=-97.8134)

calc = CustodyCalculator(rules, cal)

# Patch _get_custodian to add debug output
original_get = calc._get_custodian

def debug_get(d):
    print(f"\n>>> DEBUG: _get_custodian({d}) called")
    # Step 1 - parents
    fd = calc._fathers_day(d.year)
    if fd:
        fri_before_fd = fd - __import__('datetime').timedelta(days=2)
        if fri_before_fd <= d <= fd:
            print(f">>> Step1: fathers_day -> dad")
            return ("dad", "fathers_day")
    md = calc._mothers_day(d.year)
    if md:
        fri_before_md = md - __import__('datetime').timedelta(days=2)
        if fri_before_md <= d <= md:
            print(f">>> Step1: mothers_day")
            return ("mom", "mothers_day")
    
    # Step 2 - last school day before break
    from datetime import timedelta
    for sy in calc.school_years:
        for br_name, br in sy.get("breaks", {}).items():
            br_start = date.fromisoformat(br["start"])
            prev = br_start - timedelta(days=1)
            for _ in range(90):
                if prev.weekday() < 5:
                    noschool = {date.fromisoformat(n["date"]) for n in sy.get("noschool_days", [])}
                    if prev in noschool:
                        prev -= timedelta(days=1)
                        continue
                    in_other = any(
                        date.fromisoformat(b2["start"]) <= prev <= date.fromisoformat(b2["end"])
                        for n2, b2 in sy.get("breaks", {}).items()
                        if n2 != br_name
                    )
                    if not in_other:
                        break
                    prev -= timedelta(days=1)
                else:
                    prev -= timedelta(days=1)
            else:
                prev = br_start - timedelta(days=1)
            if d == prev:
                print(f">>> Step2: last_school_day_before_{br_name}")
                is_odd = d.year % 2 == 1
                return calc._break_custodian(br_name, br, d, is_odd)
    
    # Step 3 - in which break
    break_name, break_data = calc._in_which_break(d)
    if break_name:
        print(f">>> Step3: in_break_{break_name}")
        is_odd = d.year % 2 == 1
        return calc._break_custodian(break_name, break_data, d, is_odd)
    
    # Step 4 - extended weekend (1st/3rd/5th Fri)
    if d.weekday() == 4:
        import calendar as calmod
        fridays = sorted([date(d.year, d.month, day[0]) for day in calmod.Calendar().itermonthdays2(d.year, d.month) if day[0] != 0 and day[1] == 4])
        if d in fridays:
            fri_rank = fridays.index(d) + 1
            print(f">>> Step4: Fri rank {fri_rank}, checking [1,3,5] = {fri_rank in [1,3,5]}")
            if fri_rank in [1, 3, 5]:
                return ("dad", "weekend")
    
    if d.weekday() in (5, 6):
        import calendar as calmod
        fri = d - __import__('datetime').timedelta(days=d.weekday() - 4)
        fridays = sorted([date(fri.year, fri.month, day[0]) for day in calmod.Calendar().itermonthdays2(fri.year, fri.month) if day[0] != 0 and day[1] == 4])
        if fri in fridays:
            fri_rank = fridays.index(fri) + 1
            if fri_rank in [1, 3, 5]:
                return ("dad", "weekend")
    
    # Step 4b - non-qual Fri no-school
    from datetime import timedelta
    if d.weekday() == 4:
        thu = d - timedelta(days=1)
        fri_is_ns = calc._is_noschool_day(d)
        thu_was_school = thu.weekday() == 3 and not calc._is_noschool_day(thu)
        print(f">>> Step4b: fri_is_noschool={fri_is_ns}, thu_was_school={thu_was_school}")
        if fri_is_ns and thu_was_school:
            return ("dad", "no_school_day")
    
    # Step 4c - Sat/Sun after no-school Fri
    if d.weekday() in (5, 6):
        fri = d - timedelta(days=d.weekday() - 4)
        if calc._is_noschool_day(fri):
            return ("dad", "no_school_day")
    
    # Step 4d - Monday no-school
    if d.weekday() == 0:
        fri = d - timedelta(days=3)
        import calendar as calmod
        fridays = sorted([date(fri.year, fri.month, day[0]) for day in calmod.Calendar().itermonthdays2(fri.year, fri.month) if day[0] != 0 and day[1] == 4])
        was_dad_weekend = fri in fridays and (fridays.index(fri) + 1) in [1, 3, 5] if fri in fridays else False
        was_noschool_fri = calc._is_noschool_day(fri)
        if (was_dad_weekend or was_noschool_fri) and calc._is_noschool_day(d):
            return ("dad", "no_school_day")
    
    # Step 5
    if d.weekday() == 3:
        print(f">>> Step5: thursday -> {rules['thursday']['parent']}")
        return (rules["thursday"]["parent"], "thursday")
    if d.weekday() == 4:
        import calendar as calmod
        fridays = sorted([date(d.year, d.month, day[0]) for day in calmod.Calendar().itermonthdays2(d.year, d.month) if day[0] != 0 and day[1] == 4])
        if d in fridays:
            fri_rank = fridays.index(d) + 1
            print(f">>> Step5: Friday rank {fri_rank}, [1,3,5] = {fri_rank in [1,3,5]}")
            if fri_rank in [1, 3, 5]:
                return (rules["weekend"]["parent"], "weekend")
    
    # Step 6 - fallback
    print(f">>> Step6: fallback -> {rules['parents']['managing']}")
    return (rules["parents"]["managing"], "default_custody")

calc._get_custodian = debug_get

d = date(2026, 4, 10)
result = calc._get_custodian(d)
print(f"\n=== FINAL RESULT: {result} ===")
import json
from datetime import date, timedelta

# The correct logic for holiday intervals:
# Thanksgiving/Christmas/Spring: alternates by calendar YEAR (odd/even)
#   odd year (2025, 2027...): Dad first half, Mom second half
#   even year (2026, 2028...): Mom first half, Dad second half
# Christmas split: Dec 28 noon or Dec 29 midnight per §153.314
#
# The key insight for breaks:
# - "break end date" = last day of break = day BEFORE students return to school
# - Thanksgiving: students return on Dec 1 (Mon), so break ends Nov 30 (Sun)
# - Christmas: students return after Jan 5, so break ends Jan 5
# - Summer: last day of school + day before next school year starts
#
# For Thanksgiving:
# - 2025: Nov 24 - Nov 30 (students back Dec 1)
# - 2026: Nov 23 - Nov 29 (students back Nov 30)
#
# For Christmas:
# - Odd year (2025): Dad gets first half (Nov/Dec), Mom gets second half
#   2025: Dec 19 - Dec 28 Dad, Dec 29 - Jan 5 Mom
# - Even year (2026): Mom gets first half, Dad gets second half
#   2026: Dec 18 - Dec 28 Mom, Dec 29 - Jan 5 Dad
#
# The root causes of bugs found so far:
# 1. Thanksgiving end date in calendar data was set to day BEFORE the actual break end
#    (e.g. Nov 28 instead of Nov 29 for 2025-2026)
# 2. Summer custody logic used calendar summer break start instead of day after school end
# 3. Mom 2nd/4th weekends only checked Saturday in holiday_dates, not Sunday

# Check current state of all breaks
with open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

for sy in cal['schoolYears']:
    print(f"\n=== {sy['year']} ===")
    print(f"  School: {sy['start']} to {sy['end']}")
    for name, br in sy['breaks'].items():
        print(f"  {name}: {br['start']} to {br['end']}")

print("\n===逻辑验证===")
print("2025 Thanksgiving: 11/24-11/30 (学生12/1返校) -> Dad (odd year)")
print("2026 Thanksgiving: 11/23-11/29 (学生11/30返校) -> Mom (even year)")
print("2025 Christmas: 12/19-1/5 odd year -> Dad first half")
print("2026 Christmas: 12/18-1/5 even year -> Mom first half")
print("2025-2026 Summer: 5/22-8/12 (学校5/21结束, 下学年8/18开始)")
print("2026-2027 Summer: 5/28-8/16 (学校5/27结束, 下学年8/17开始)")
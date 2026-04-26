import json, sys
from datetime import date, timedelta

path = 'C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json'
with open(path, 'r', encoding='utf-8-sig') as f:
    cal = json.load(f)

sys.stdout.buffer.write(f'School years before: {[sy["year"] for sy in cal["schoolYears"]]}\n'.encode('utf-8'))

# Check if 2025-2026 exists
existing_years = [sy['year'] for sy in cal['schoolYears']]
if '2025-2026' not in existing_years:
    # Add 2025-2026 school year
    # School: Aug 13, 2025 - May 21, 2026
    # Summer: May 22 - Aug 12 (day before Aug 13 start)
    sy_2025_2026 = {
        "year": "2025-2026",
        "start": "2025-08-13",
        "end": "2026-05-21",
        "breaks": {
            "thanksgiving": {
                "start": "2025-11-24", "end": "2025-11-28",
                "label": {"en": "Thanksgiving Break", "cn": "感恩节假期"}
            },
            "christmas": {
                "start": "2025-12-19", "end": "2026-01-05",
                "label": {"en": "Christmas Break", "cn": "圣诞假期"}
            },
            "spring": {
                "start": "2026-03-16", "end": "2026-03-20",
                "label": {"en": "Spring Break", "cn": "春假"}
            },
            "summer": {
                "start": "2026-05-22", "end": "2026-08-12",
                "label": {"en": "Summer Break", "cn": "暑假"}
            }
        },
        "noschool_days": [
            {"date": "2025-09-01", "label": {"en": "Labor Day", "cn": "劳动节"}},
            {"date": "2025-09-22", "label": {"en": "Rosh Hashanah (Student & Staff Holiday)", "cn": "犹太新年"}},
            {"date": "2025-09-23", "label": {"en": "Rosh Hashanah (Student & Staff Holiday)", "cn": "犹太新年"}},
            {"date": "2025-10-13", "label": {"en": "Indigenous Peoples' Day / Columbus Day (Student Holiday)", "cn": "原住民日/哥伦布日"}},
            {"date": "2025-10-20", "label": {"en": "Diwali (Student & Staff Holiday)", "cn": "排灯节"}},
            {"date": "2025-11-07", "label": {"en": "Staff Dev / Student Holiday", "cn": "教师培训/学生假日"}},
            {"date": "2026-01-05", "label": {"en": "Martin Luther King Jr. Day (Student & Staff Holiday)", "cn": "马丁路德金日"}},
            {"date": "2026-02-16", "label": {"en": "Presidents' Day (Student & Staff Holiday)", "cn": "总统日"}},
            {"date": "2026-02-17", "label": {"en": "Lunar New Year (Student Holiday/Staff Dev)", "cn": "农历新年"}},
            {"date": "2026-04-03", "label": {"en": "Good Friday (Student & Staff Holiday)", "cn": "耶稣受难日"}},
            {"date": "2026-06-19", "label": {"en": "Juneteenth (Student Holiday)", "cn": "六月节"}},
        ]
    }
    cal['schoolYears'].insert(0, sy_2025_2026)
    sys.stdout.buffer.write(b'Added 2025-2026 school year\n')
else:
    sys.stdout.buffer.write(b'2025-2026 already exists\n')

# Fix summer end for 2026-2027: day before school starts Aug 18 = Aug 17
for sy in cal['schoolYears']:
    if sy['year'] == '2026-2027':
        old = sy['breaks']['summer']['end']
        sy['breaks']['summer']['end'] = '2027-08-17'
        sys.stdout.buffer.write(f"Updated 2026-2027 summer end: {old} -> 2027-08-17\n".encode('utf-8'))

sys.stdout.buffer.write(f'School years after: {[sy["year"] for sy in cal["schoolYears"]]}\n'.encode('utf-8'))

with open(path, 'w', encoding='utf-8') as f:
    json.dump(cal, f, indent=2, ensure_ascii=False)
sys.stdout.buffer.write(b'Saved.\n')
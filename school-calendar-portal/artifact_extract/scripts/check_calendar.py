import json
cal = json.load(open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/processed/rrisd_standard_calendar.json', encoding='utf-8'))
print("Keys:", list(cal.keys()))
print("School years count:", len(cal.get('schoolYears', [])))
if cal.get('schoolYears'):
    sy = cal['schoolYears'][0]
    print("SY keys:", list(sy.keys()))
    print("Breaks:", list(sy.get('breaks', {}).keys()))
    print("SY start/end:", sy.get('start'), '/', sy.get('end'))
    for k, v in sy.get('breaks', {}).items():
        print(f"  {k}: {v.get('start')} to {v.get('end')}")

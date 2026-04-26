"""
Debug: check what MONTH_DATA extraction produces per line.
"""
import pdfplumber
import calendar as cal_module

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    tables = pdf.pages[0].extract_tables()

grid = tables[0][4][1]
lines = grid.strip().split('\n')

print("Band 1 lines:")
for i, line in enumerate(lines):
    parts = line.strip().split()
    nums = [p for p in parts if p.isdigit()]
    print(f"  Line {i}: {len(parts)} parts, {len(nums)} numbers: {nums[:20]}")

# Try parsing with my logic
months = [8, 9, 10, 11]  # Aug, Sep, Oct, Nov
for line_idx, line in enumerate(lines):
    parts = line.strip().split()
    if not parts or not parts[0].isdigit():
        print(f"  Line {line_idx}: skip (header)")
        continue
    week_count = len(parts) // 4
    print(f"  Line {line_idx}: {week_count} weeks, parts={parts[:12]}...")
    for week_idx in range(week_count):
        for mi, mn in enumerate(months):
            try:
                day_num = int(parts[week_idx * 4 + mi])
            except:
                day_num = 0
            year = 2025 if mn >= 8 else 2026
            dim = cal_module.monthrange(year, mn)[1]
            valid = "ok" if 1 <= day_num <= dim else "INVALID"
            if valid == "ok":
                print(f"    week={week_idx} {['Aug','Sep','Oct','Nov'][mi]}: day={day_num} ({valid})")

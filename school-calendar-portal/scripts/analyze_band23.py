import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

# For band 2 (Dec-Mar, y~296-400), check x positions of all days
band2_days = []
band3_days = []
for w in words:
    try:
        d = int(w['text'])
        if 1 <= d <= 31:
            x, y = w['x0'], w['top']
            if 296.0 <= y <= 400.0:
                band2_days.append((x, d))
            elif 440.0 <= y <= 545.0:
                band3_days.append((x, d))
    except:
        pass

band2_days.sort()
band3_days.sort()

print("Band 2 days (x, day):")
for x, d in band2_days:
    print(f"  x={x:.0f} d={d}")

print("\nBand 3 days (x, day):")
for x, d in band3_days:
    print(f"  x={x:.0f} d={d}")

# Also check unique X values to see the column structure
print("\nBand 2 unique X ranges:")
x_by_50 = defaultdict(list)
for x, d in band2_days:
    x_by_50[int(x/50)*50].append(d)
for k in sorted(x_by_50.keys()):
    print(f"  x={k}-{k+50}: days {sorted(set(x_by_50[k]))}")

print("\nBand 3 unique X ranges:")
x_by_50 = defaultdict(list)
for x, d in band3_days:
    x_by_50[int(x/50)*50].append(d)
for k in sorted(x_by_50.keys()):
    print(f"  x={k}-{k+50}: days {sorted(set(x_by_50[k]))}")
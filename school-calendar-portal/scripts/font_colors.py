import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    chars = page.chars

# For band 2 and band 3, look at font colors (non_stroking_color) to distinguish months
# Colors are RGB tuples stored as (r, g, b) or CMYK

# Check colors of day chars in band 2 and band 3
band2_colors = []
band3_colors = []
for c in chars:
    if c['size'] < 12.9 or c['size'] > 13.1:
        continue
    try:
        d = int(c['text'])
        if 1 <= d <= 31:
            y = c['top']
            if 296.0 <= y <= 400.0:
                band2_colors.append((c['x0'], c['top'], d, c['non_stroking_color']))
            elif 440.0 <= y <= 545.0:
                band3_colors.append((c['x0'], c['top'], d, c['non_stroking_color']))
    except:
        pass

print("Band 2 - unique colors:")
color_days = defaultdict(list)
for x, y, d, col in band2_colors:
    color_days[col].append(d)
for col, days in sorted(color_days.items(), key=lambda x: str(x[0])):
    print(f"  {col}: days {sorted(set(days))}")

print("\nBand 3 - unique colors:")
color_days = defaultdict(list)
for x, y, d, col in band3_colors:
    color_days[col].append(d)
for col, days in sorted(color_days.items(), key=lambda x: str(x[0])):
    print(f"  {col}: days {sorted(set(days))}")
import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    chars = page.chars

# Extract only 13pt chars (month headers + day numbers in calendar grid)
cal_chars = [c for c in chars if 12.9 <= c['size'] <= 13.1]
print(f"Calendar chars (13pt): {len(cal_chars)}")

# Sort by position (top-to-bottom, left-to-right)
cal_chars.sort(key=lambda c: (c['top'], c['x0']))

# Build rows by Y
rows = defaultdict(list)
for c in cal_chars:
    rows[round(c['top'], 1)].append((c['x0'], c['text']))

print("\nAll rows (13pt chars):")
for y in sorted(rows.keys()):
    cells = sorted(rows[y])
    text = ''.join(t for _, t in cells)
    print(f"  y={y}: {text}")
import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

# Show day numbers with their X positions, grouped by Y row
rows = defaultdict(list)
for w in words:
    try:
        d = int(w['text'])
        if 1 <= d <= 31:
            rows[round(w['top'], 0)].append((w['x0'], d))
    except:
        pass

print("Day rows (y, x_pos, day):")
for y in sorted(rows.keys()):
    cells = sorted(rows[y])
    print(f"  y={y}: " + "  ".join(f"(x={x:.0f},d={d})" for x, d in cells))
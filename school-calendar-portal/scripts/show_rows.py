import pdfplumber
from collections import defaultdict

# Detailed analysis of the calendar grid
with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    words = page.extract_words()

# For each unique Y row, show all words
rows = defaultdict(list)
for w in words:
    rows[round(w['top'], 0)].append((w['x0'], w['text']))

print("All rows with content:")
for y in sorted(rows.keys()):
    cells = sorted(rows[y])
    texts = [t for _, t in cells]
    nums = [t for t in texts if t.isdigit() and 1 <= int(t) <= 31]
    if nums:
        print(f"  y={y}: {' '.join(nums)}")
import pdfplumber
from collections import defaultdict

with pdfplumber.open('C:/Users/frank/.openclaw/workspace/projects/TASK-001-allergy-report/school-calendar-portal/data/raw/rrisd_2025_2026_real.pdf') as pdf:
    page = pdf.pages[0]
    chars = page.chars

# Group chars by font size
font_sizes = defaultdict(list)
for c in chars:
    font_sizes[c['size']].append(c['text'])

print("Font sizes found:", sorted(font_sizes.keys()))
for size in sorted(font_sizes.keys()):
    texts = ''.join(font_sizes[size])
    print(f"  {size}pt: {texts[:100]}")